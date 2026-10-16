from __future__ import annotations
import base64
import importlib.util
import json
import os
import shutil
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid
import zlib

spec=importlib.util.spec_from_file_location('evidence_vm',Path(__file__).resolve().parents[1]/'axon_ci_vm.py')
vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)

def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
def png(width=1,height=1,metadata=False):
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+(chunk(b'tEXt',b'Comment\x00synthetic-private-metadata') if metadata else b'')+chunk(b'IDAT',zlib.compress(b'\x00\xff\x00\x00\xff'))+chunk(b'IEND',b'')

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.job=str(uuid.uuid4());self.config={'tart':'/trusted/tart','tartHome':'/trusted/cache'}
        for name,value in [('ROOT',self.root/'vms'),('EVIDENCE_ROOT',self.root/'evidence')]:
            p=patch.object(vm,name,value);p.start();self.addCleanup(p.stop)
    def wire(self,data=None):
        return json.dumps({'version':1,'files':[{'testIdentifier':'SyntheticDiary/testRendering','name':'synthetic-native-diary','png':base64.b64encode(png() if data is None else data).decode()}]}).encode()
    def retain(self,data=None):
        with patch.object(vm,'bounded_guest_evidence',return_value=self.wire(data)):
            return vm.retain_evidence(self.config,self.job)
    def test_screenshot_survives_verified_guest_deletion_and_can_be_released(self):
        directory=self.retain();vm.write_record(self.job,self.config)
        with self.assertRaisesRegex(vm.Failure,'still owned'):
            vm.release_evidence(self.job)
        rows=[{'Name':vm.vm_name(self.job),'Source':'local','Running':False}]
        with patch.object(vm,'verify_tart'),patch.object(vm,'inventory',side_effect=[rows,rows,[]]),patch.object(vm,'call') as call:
            vm.cleanup(self.job)
        self.assertFalse(vm.record_path(self.job).exists())
        call.assert_called_once_with(self.config,'delete',vm.vm_name(self.job),timeout=15)
        receipt=vm.read_evidence(self.job);self.assertEqual(receipt['guest'],self.job)
        image=receipt['files'][0]
        self.assertEqual((directory/image['file']).read_bytes(),png())
        self.assertEqual(image['testIdentifier'],'SyntheticDiary/testRendering')
        self.assertEqual(os.stat(directory).st_mode&0o777,0o700)
        self.assertEqual(os.stat(directory/image['file']).st_mode&0o777,0o600)
        vm.release_evidence(self.job);self.assertFalse(directory.exists())
    def test_empty_and_linux_results_create_no_retained_directory(self):
        with patch.object(vm,'bounded_guest_evidence',return_value=b'{"version":1,"files":[]}') as collect:
            self.assertIsNone(vm.retain_evidence(self.config,self.job));collect.assert_called_once()
        with patch.object(vm,'bounded_guest_evidence') as collect:
            self.assertIsNone(vm.retain_evidence(dict(self.config,profile='linux'),self.job));collect.assert_not_called()
        self.assertFalse(vm.EVIDENCE_ROOT.exists())
    def test_png_metadata_is_removed_without_changing_pixels(self):
        receipt=self.retain(png(metadata=True));image=vm.read_evidence(self.job)['files'][0]
        self.assertEqual((receipt/image['file']).read_bytes(),png())
    def test_color_profile_is_preserved_but_decompression_is_bounded(self):
        original=png();prefix=original[:33];suffix=original[33:]
        image=prefix+chunk(b'iCCP',b'synthetic-profile\x00\x00'+zlib.compress(b'synthetic-color-profile'))+suffix
        self.assertEqual(vm.canonical_png(image)[0],image)
        bomb=prefix+chunk(b'iCCP',b'synthetic-profile\x00\x00'+zlib.compress(b'x'*(1024**2+1)))+suffix
        with self.assertRaisesRegex(vm.Failure,'profile exceeds'):
            vm.canonical_png(bomb)

    def test_invalid_or_oversized_images_fail_before_host_publication(self):
        for data in [b'not-png',png(width=9000),png()[:-1],png()[:40]+b'corruption'+png()[40:]]:
            with self.assertRaises(vm.Failure):self.retain(data)
            self.assertFalse(vm.EVIDENCE_ROOT.exists())
        with patch.object(vm,'EVIDENCE_JOB_BYTES',10):
            with self.assertRaises(vm.Failure):self.retain()
        self.assertFalse(vm.EVIDENCE_ROOT.exists())
    def test_host_budget_refuses_admission_without_evicting_existing_proof(self):
        self.retain();used,_=vm.evidence_usage()
        with patch.object(vm,'EVIDENCE_TOTAL_BYTES',used+vm.EVIDENCE_JOB_BYTES):
            with self.assertRaisesRegex(vm.Failure,'capacity full'):vm.evidence_capacity()
        self.assertEqual(len(vm.read_evidence(self.job)['files']),1)
    def test_symlink_traversal_and_tampering_cannot_escape_store(self):
        directory=self.retain();receipt=vm.read_evidence(self.job);image=directory/receipt['files'][0]['file']
        outside=self.root/'private.txt';outside.write_text('synthetic outside data')
        image.unlink();image.symlink_to(outside)
        with self.assertRaises(vm.Failure):vm.read_evidence(self.job)
        with self.assertRaises(vm.Failure):vm.release_evidence(self.job)
        self.assertEqual(outside.read_text(),'synthetic outside data')
        with self.assertRaises((vm.Failure,ValueError)):vm.release_evidence('../private.txt')
    def test_manifest_cannot_redirect_reads(self):
        directory=self.retain();path=directory/'manifest.json';data=json.loads(path.read_text());data['files'][0]['file']='../private.txt';path.write_text(json.dumps(data))
        with self.assertRaisesRegex(vm.Failure,'filename'):vm.read_evidence(self.job)
    def test_incomplete_owned_receipt_can_be_retired_only_after_guest_cleanup(self):
        vm.private_directory(vm.EVIDENCE_ROOT,create=True);directory=vm.EVIDENCE_ROOT/self.job;directory.mkdir(mode=0o700)
        (directory/'manifest.json').write_text('interrupted');(directory/'manifest.json').chmod(0o600)
        vm.write_record(self.job,self.config)
        with self.assertRaisesRegex(vm.Failure,'still owned'):vm.release_evidence(self.job)
        vm.record_path(self.job).unlink();vm.release_evidence(self.job);self.assertFalse(directory.exists())
    def executable(self,body):
        p=self.root/'fake-tart';p.write_text('#!'+sys.executable+'\n'+body);p.chmod(0o755);return dict(self.config,tart=str(p))
    def test_transport_byte_limit_and_deadline_bound_actual_child(self):
        config=self.executable('import os\nos.write(1,b"synthetic-sensitive-value"*1000)\n')
        with patch.object(vm,'EVIDENCE_WIRE_BYTES',1024):
            with self.assertRaisesRegex(vm.Failure,'transport exceeds') as e:vm.bounded_guest_evidence(config,self.job)
            self.assertNotIn('sensitive',str(e.exception))
        config=self.executable('import time\ntime.sleep(10)\n');start=time.monotonic()
        with patch.object(vm,'EVIDENCE_EXPORT_SECONDS',0.05):
            with self.assertRaisesRegex(vm.Failure,'deadline'):vm.bounded_guest_evidence(config,self.job)
        self.assertLess(time.monotonic()-start,3)
    def test_collector_is_valid_python_and_has_no_host_mount_or_credentials(self):
        compile(vm.EVIDENCE_COLLECTOR,'guest-evidence','exec')
        self.assertNotIn('GH_TOKEN',vm.EVIDENCE_COLLECTOR)
        self.assertIn("'--filter','*.png'",vm.EVIDENCE_COLLECTOR)

    def test_completion_hook_stages_before_runner_temp_cleanup(self):
        results=self.root/'runner-temp';results.mkdir()
        source=results/'synthetic.png';source.write_bytes(png())
        stage=self.root/'guest-stage'
        collector='import json,base64,pathlib\nprint(json.dumps({"version":1,"files":[{"testIdentifier":"Synthetic/testPNG","name":"synthetic","png":base64.b64encode(pathlib.Path('+repr(str(source))+').read_bytes()).decode()}]}))'
        with patch.object(vm,'EVIDENCE_STAGE',str(stage)),patch.object(vm,'EVIDENCE_COLLECTOR',collector):
            exec(vm.evidence_hook_setup(),{})
            subprocess.run(['/bin/bash','-e',str(stage/'complete.sh')],check=True)
            # Matches pinned Actions Runner: completion hooks precede temp cleanup,
            # and cleanup precedes listener exit and the host's export step.
            shutil.rmtree(results)
            output=subprocess.check_output([sys.executable,'-c',vm.evidence_reader()])
        with patch.object(vm,'bounded_guest_evidence',return_value=output):
            self.assertIsNotNone(vm.retain_evidence(self.config,self.job))
        self.assertEqual(vm.read_evidence(self.job)['files'][0]['testIdentifier'],'Synthetic/testPNG')
        self.assertFalse(results.exists())

    def test_failed_hook_preserves_test_result_and_never_publishes_partial_capture(self):
        stage=self.root/'guest-stage'
        with patch.object(vm,'EVIDENCE_STAGE',str(stage)),patch.object(vm,'EVIDENCE_COLLECTOR','raise RuntimeError("synthetic-sensitive-value")'):
            exec(vm.evidence_hook_setup(),{})
            result=subprocess.run(['/bin/bash','-e',str(stage/'complete.sh')],capture_output=True,check=True)
            self.assertEqual(result.stdout+result.stderr,b'')
            self.assertFalse((stage/'capture.partial').exists())
            self.assertFalse((stage/'capture.json').exists())
            reader=subprocess.run([sys.executable,'-c',vm.evidence_reader()],capture_output=True)
        self.assertNotEqual(reader.returncode,0)
        self.assertNotIn(b'sensitive',reader.stderr)
        self.assertEqual((stage/'failed').read_text(),'capture_unavailable')

    def test_hook_is_installed_only_in_mac_guest_with_explicit_runner_environment(self):
        with patch.object(vm,'call') as call:
            self.assertEqual(vm.prepare_evidence_hook(dict(self.config,profile='linux'),'synthetic'),[])
            call.assert_not_called()
            argv=vm.prepare_evidence_hook(self.config,'synthetic')
            self.assertEqual(argv,['/usr/bin/env','ACTIONS_RUNNER_HOOK_JOB_COMPLETED='+vm.EVIDENCE_STAGE+'/complete.sh'])
            self.assertEqual(call.call_args.args[:6],(self.config,'exec','-i','synthetic','/usr/bin/python3','-'))
            compile(call.call_args.kwargs['input'],'guest-hook-setup','exec')

    def test_hook_export_size_and_deadline_are_bounded(self):
        for label,collector in [('size','print("x"*4096)'),('deadline','import time;time.sleep(10)')]:
            stage=self.root/label
            with patch.object(vm,'EVIDENCE_STAGE',str(stage)),patch.object(vm,'EVIDENCE_COLLECTOR',collector),patch.object(vm,'EVIDENCE_WIRE_BYTES',1024),patch.object(vm,'EVIDENCE_HOOK_SECONDS',0.05 if label=='deadline' else 2):
                exec(vm.evidence_hook_setup(),{})
                start=time.monotonic()
                subprocess.run(['/bin/bash','-e',str(stage/'complete.sh')],capture_output=True,check=True,timeout=3)
                self.assertLess(time.monotonic()-start,3)
            self.assertTrue((stage/'failed').exists())
            self.assertFalse((stage/'capture.json').exists())
            self.assertFalse((stage/'capture.partial').exists())

if __name__=='__main__':unittest.main()
