from __future__ import annotations
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import uuid

spec = importlib.util.spec_from_file_location('ci_vm',Path(__file__).resolve().parents[1]/'axon_ci_vm.py')
vm = importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)

class VMExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.patch=patch.object(vm,'ROOT',self.root/'state');self.patch.start();self.addCleanup(self.patch.stop)
        self.job=str(uuid.uuid4());self.config={'tart':'/trusted/tart','tartHome':'/trusted/cache'}
    def test_request_rejects_relative_command_malformed_and_oversized_payload(self):
        for value in ({'argv':['relative'],'stdin':''},{'argv':[],'stdin':''},{'argv':['/bin/true'],'stdin':'','share':'/Users'}, {'argv':['/bin/true'],'stdin':42}):
            with self.assertRaises(vm.Failure):vm.payload(io.StringIO(json.dumps(value)))
        with self.assertRaises(vm.Failure):vm.payload(io.StringIO('x'*(256*1024+1)))
        value={'argv':['/bin/sh','-c','true'],'stdin':'single-job-credential'}
        self.assertEqual(vm.payload(io.StringIO(json.dumps(value))),value)
    def test_config_only_allows_absolute_tool_and_cache_paths(self):
        path=self.root/'config'
        for value in ({'tart':'relative','tartHome':'/cache'},dict(self.config,share='/Users')):
            path.write_text(json.dumps(value))
            with self.assertRaises(vm.Failure):vm.frozen_config(path)
        path.write_text(json.dumps(self.config));self.assertEqual(vm.frozen_config(path),self.config)
    def test_config_rejects_unpinned_guest_profile_or_image(self):
        path=self.root/'config'
        for profile in ('custom', '../linux', {}, None):
            path.write_text(json.dumps(dict(self.config,profile=profile)))
            with self.assertRaises(vm.Failure):vm.frozen_config(path)
        path.write_text(json.dumps(dict(self.config,profile='linux',image='unreviewed')))
        with self.assertRaises(vm.Failure):vm.frozen_config(path)
        path.write_text(json.dumps(dict(self.config,profile='linux')))
        self.assertEqual(vm.guest_image(vm.frozen_config(path)),vm.LINUX_IMAGE)

    def test_linux_admission_preserves_disk_reserve_and_exact_base(self):
        config=dict(self.config,profile='linux')
        for gib,image,admitted in ((40,vm.LINUX_IMAGE,False),(50,vm.LINUX_IMAGE,True),(50,vm.IMAGE,False)):
            def output(argv,**kwargs):
                return "Now drawing from 'AC Power'" if 'pmset' in argv[0] else str(24*1024**3)
            rows=[{'Name':image,'Source':'OCI','Running':False}]
            with patch.object(vm.sys,'platform','darwin'),patch.object(vm.subprocess,'check_output',side_effect=output),patch.object(vm.shutil,'disk_usage',return_value=type('Usage',(),{'free':gib*1024**3})()),patch.object(vm,'verify_tart') as verify,patch.object(vm,'verify_helper'),patch.object(vm,'inventory',return_value=rows):
                if admitted:vm.eligible(config)
                else:
                    with self.assertRaises(vm.Failure):vm.eligible(config)
                    if gib==40:verify.assert_not_called()

    def test_linux_toolchain_never_mutates_an_xcode_alias(self):
        for system,valid in (('Linux',True),('Darwin',False)):
            with patch.object(vm,'call',return_value=subprocess.CompletedProcess([],0,system+'\n','')) as call:
                if valid:vm.prepare_toolchain(dict(self.config,profile='linux'),'owned')
                else:
                    with self.assertRaises(vm.Failure):vm.prepare_toolchain(dict(self.config,profile='linux'),'owned')
                self.assertEqual(call.call_args.args[1:],('exec','owned','/usr/bin/uname','-s'))
                self.assertEqual(call.call_count,1)

    def test_linux_dns_requires_one_explicit_interface_before_changes(self):
        config=dict(self.config,profile='linux')
        for routes in ([],[{'dev':'eth0'},{'dev':'eth1'}],[{'dev':'bad;command'}],{'dev':'eth0'}):
            with patch.object(vm,'call',return_value=subprocess.CompletedProcess([],0,json.dumps(routes),'')) as call:
                with self.assertRaises(vm.Failure):vm.prepare_network(config,'owned')
                self.assertEqual(call.call_count,1)
        with patch.object(vm,'call',return_value=subprocess.CompletedProcess([],0,'[{"dev":"enp0s1"}]','')) as call:
            vm.prepare_network(config,'owned')
            self.assertEqual(call.call_args_list[1].args[1:],('exec','owned','/usr/bin/sudo','/usr/bin/resolvectl','dns','enp0s1','1.1.1.1','8.8.8.8'))
            self.assertEqual(call.call_args_list[2].args[1:],('exec','owned','/usr/bin/sudo','/usr/bin/resolvectl','domain','enp0s1','~.'))

    def test_linux_worker_keeps_shared_ownership_isolation_and_small_resources(self):
        home=self.root/'home';session=home/'Library/Caches/axon-simulator-runner/session.json'
        session.parent.mkdir(parents=True)
        session.write_text(json.dumps({'mode':'host','worker':{'pid':vm.os.getpid()},'supervisorPID':42}))
        config=dict(self.config,profile='linux')
        request={'argv':['/usr/bin/true'],'stdin':'synthetic-job-input'}
        completed=subprocess.CompletedProcess([],0,'','')
        with patch.object(vm.Path,'home',return_value=home),patch.dict(vm.os.environ,{'AXON_SIMULATOR_SESSION_PID':'42'}),patch.object(vm,'payload',return_value=request),patch.object(vm,'eligible') as eligible,patch.object(vm,'write_record') as record,patch.object(vm,'call',return_value=completed) as call,patch.object(vm,'prepare_network') as network,patch.object(vm,'prepare_toolchain') as toolchain,patch.object(vm.subprocess,'Popen') as launch,patch.object(vm.subprocess,'run',return_value=completed):
            self.assertEqual(vm.worker(config,self.job),0)
        eligible.assert_called_once_with(config)
        record.assert_called_once_with(self.job,config)
        name=vm.vm_name(self.job)
        self.assertEqual(call.call_args_list[0].args[1:],('clone',vm.LINUX_IMAGE,name))
        self.assertEqual(call.call_args_list[1].args[1:],('set',name,'--cpu','4','--memory','6144'))
        command=launch.call_args.args[0]
        for flag in ('--no-graphics','--no-audio','--no-clipboard','--no-usb-accessories','--net-softnet','--net-softnet-block'):self.assertIn(flag,command)
        self.assertIn(vm.BLOCK,command)
        self.assertNotIn('--dir',command)
        self.assertEqual(set(launch.call_args.kwargs['env']),{'HOME','PATH','TART_HOME','TART_NO_AUTO_PRUNE','LANG'})
        network.assert_called_once_with(config,name)
        toolchain.assert_called_once_with(config,name)

    def test_attempt_identity_prevents_path_traversal(self):
        for value in ('../foreign','',self.job.upper()):
            with self.assertRaises((vm.Failure,ValueError)):vm.record_path(value)
    def test_record_creation_is_exclusive_and_no_guest_stdin_is_retained(self):
        vm.write_record(self.job,self.config)
        self.assertEqual(json.loads(vm.record_path(self.job).read_text()),{'job':self.job,'config':self.config})
        with self.assertRaises(FileExistsError):vm.write_record(self.job,self.config)
    def test_cleanup_stops_owned_guest_before_delete_and_is_idempotent(self):
        vm.write_record(self.job,self.config);name=vm.vm_name(self.job)
        rows=[[{'Name':name,'Source':'local','Running':True}], [{'Name':name,'Source':'local','Running':False}], []]
        with patch.object(vm,'verify_tart'),patch.object(vm,'inventory',side_effect=rows),patch.object(vm,'call') as call:
            vm.cleanup(self.job)
            self.assertEqual([c.args[1] for c in call.call_args_list],['stop','delete'])
        self.assertFalse(vm.record_path(self.job).exists());vm.cleanup(self.job)
    def test_failed_stop_preserves_record_and_prevents_delete(self):
        vm.write_record(self.job,self.config);name=vm.vm_name(self.job)
        row={'Name':name,'Source':'local','Running':True}
        with patch.object(vm,'verify_tart'),patch.object(vm,'inventory',return_value=[row]),patch.object(vm,'call',side_effect=vm.Failure('stop failed')) as call:
            with self.assertRaises(vm.Failure):vm.cleanup(self.job)
            self.assertEqual(len(call.call_args_list),1)
        self.assertTrue(vm.record_path(self.job).exists())
    def test_cleanup_never_deletes_foreign_vm_or_wrong_source(self):
        vm.write_record(self.job,self.config)
        with patch.object(vm,'verify_tart'),patch.object(vm,'inventory',return_value=[{'Name':'foreign','Source':'local','Running':True}]),patch.object(vm,'call') as call:
            vm.cleanup(self.job);call.assert_not_called()
        vm.write_record(self.job,self.config)
        with patch.object(vm,'verify_tart'),patch.object(vm,'inventory',return_value=[{'Name':vm.vm_name(self.job),'Source':'OCI','Running':False}]),patch.object(vm,'call') as call:
            with self.assertRaises(vm.Failure):vm.cleanup(self.job)
            call.assert_not_called()
    def test_pause_and_battery_block_before_tool_or_guest_effects(self):
        for paused,power in ((True,"Now drawing from 'AC Power'"),(False,"Now drawing from 'Battery Power'")):
            vm.ROOT.mkdir(exist_ok=True)
            marker=vm.ROOT/'paused';marker.touch() if paused else marker.unlink()
            with patch.object(vm.sys,'platform','darwin'),patch.object(vm.subprocess,'check_output',return_value=power),patch.object(vm,'verify_tart') as verify:
                with self.assertRaises(vm.Failure):vm.eligible(self.config)
                verify.assert_not_called()
    def test_stock_clone_reserves_whole_disk_rewrite_before_effects(self):
        rows=[{'Name':vm.IMAGE,'Source':'OCI','Running':False}]
        for gib,admitted in ((150,False),(170,True)):
            def output(argv,**kwargs):
                return "Now drawing from 'AC Power'" if 'pmset' in argv[0] else str(24*1024**3)
            with patch.object(vm.sys,'platform','darwin'),patch.object(vm.subprocess,'check_output',side_effect=output),patch.object(vm.shutil,'disk_usage',return_value=type('Usage',(),{'free':gib*1024**3})()),patch.object(vm,'verify_tart') as verify,patch.object(vm,'verify_helper'),patch.object(vm,'inventory',return_value=rows):
                if admitted:
                    vm.eligible(self.config)
                    verify.assert_called_once()
                else:
                    with self.assertRaises(vm.Failure):vm.eligible(self.config)
                    verify.assert_not_called()

    def test_guest_toolchain_rejects_other_sdk_before_alias_creation(self):
        selected=subprocess.CompletedProcess([],0,'/Applications/Xcode_26.app/Contents/Developer\n','')
        with patch.object(vm,'call',return_value=selected) as call:
            with self.assertRaises(vm.Failure):vm.prepare_toolchain(self.config,'owned')
            self.assertEqual(len(call.call_args_list),1)
    def test_guest_toolchain_failure_prevents_job_execution(self):
        selected=subprocess.CompletedProcess([],0,'/Applications/Xcode_27.app/Contents/Developer\n','')
        with patch.object(vm,'call',side_effect=[selected,vm.Failure('existing alias conflicts')]):
            with self.assertRaises(vm.Failure):vm.prepare_toolchain(self.config,'owned')

    def test_no_operator_environment_is_forwarded(self):
        with patch.dict(vm.os.environ,{'GH_TOKEN':'private','SSH_AUTH_SOCK':'private','HTTPS_PROXY':'private'}):
            env=vm.environment(self.config)
        self.assertEqual(set(env),{'HOME','PATH','TART_HOME','TART_NO_AUTO_PRUNE','LANG'})
    def test_tart_failure_does_not_print_provider_output_or_credentials(self):
        result=subprocess.CompletedProcess([],1,'single-job-credential','private provider detail')
        with patch.object(vm.subprocess,'run',return_value=result):
            with self.assertRaisesRegex(vm.Failure,'^Tart operation failed: exec$'):
                vm.call(self.config,'exec','guest','single-job-credential')

if __name__=='__main__':unittest.main()
