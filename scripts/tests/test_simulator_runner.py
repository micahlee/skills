from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
SOURCE = Path(__file__).resolve().parents[1] / 'axon_simulator_runner.py'
FAKE = '''import json,sys
from pathlib import Path
p=Path(sys.argv[1]); args=sys.argv[2:]; data=json.loads(p.read_text())
if args[:2]==['list','devices']: print(json.dumps({'devices':{'com.apple.CoreSimulator.SimRuntime.iOS-26-5':list(data.values())}}))
elif args[0]=='boot': data[args[1]]['state']='Booted'; p.write_text(json.dumps(data))
elif args[0]=='shutdown' and Path(str(p)+'.fail').exists(): raise SystemExit(1)
elif args[0]=='shutdown': data[args[1]]['state']='Shutdown'; p.write_text(json.dumps(data))
elif args[0] in ('bootstatus','spawn','erase'): pass
else: raise SystemExit(2)
'''
class SimulatorRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name); self.inventory=self.root/'devices.json'
        self.inventory.write_text(json.dumps({d:{'udid':d,'name':d,'state':'Shutdown','isAvailable':True} for d in ['phone','other']}))
        self.fake=self.root/'simctl.py'; self.fake.write_text(FAKE)
        self.launcher=self.root/'runner.py'
        self.launcher.write_text("import importlib.util,sys\nfrom pathlib import Path\n" +
            "spec=importlib.util.spec_from_file_location('runner',"+repr(str(SOURCE))+");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\n" +
            "m.ROOT=Path("+repr(str(self.root/'state'))+"); original=m.Runner\n" +
            "m.Runner=lambda:original(m.ROOT,[sys.executable,"+repr(str(self.fake))+","+repr(str(self.inventory))+"])\n" +
            "m.__file__=str(Path(__file__).resolve()); sys.exit(m.entry())\n")
        self.processes=[]; self.addCleanup(self.stop_all)
    def stop_all(self):
        for p in self.processes:
            if p.poll() is None: p.terminate()
        for p in self.processes:
            try: p.wait(timeout=8)
            except subprocess.TimeoutExpired: p.kill(); p.wait()
            if p.stdout: p.stdout.close()
            if p.stderr: p.stderr.close()
    def launch(self, code, *options):
        p=subprocess.Popen([sys.executable,str(self.launcher),'run','--device','phone',*options,'--',sys.executable,'-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.processes.append(p); return p
    def wait_for(self, predicate):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            if predicate(): return
            time.sleep(.05)
        self.fail('condition did not become true')
    def booted(self):
        return json.loads(self.inventory.read_text())['phone']['state']=='Booted'
    def assert_clean(self, p, expected):
        out,err=p.communicate(timeout=12); self.assertEqual(p.returncode,expected,(out,err))
        self.assertFalse(self.booted()); self.assertFalse((self.root/'state/session.json').exists())
    def assert_dead(self, pid):
        result=subprocess.run(['ps','-p',str(pid),'-o','stat='],capture_output=True,text=True)
        self.assertTrue(not result.stdout.strip() or result.stdout.strip().startswith('Z'),result.stdout)
    def sleeper(self, path):
        return 'import os,time; from pathlib import Path; Path('+repr(str(path))+').write_text(str(os.getpid())); time.sleep(60)'
    def test_success_and_failure_shutdown(self):
        for code in [0,7]: self.assert_clean(self.launch('import sys; sys.exit('+str(code)+')'),code)
    def test_sigterm_and_sigint(self):
        for sig in [signal.SIGTERM,signal.SIGINT]:
            child=self.root/('child-'+str(sig)); p=self.launch(self.sleeper(child)); self.wait_for(child.exists)
            p.send_signal(sig); self.assert_clean(p,128+sig); self.assert_dead(child.read_text())
    def test_timeout(self):
        self.assert_clean(self.launch('import time; time.sleep(60)','--timeout','0.3'),1)
    def test_contention(self):
        start=self.root/'started'; release=self.root/'release'; second=self.root/'second'
        first=self.launch('import time; from pathlib import Path; Path('+repr(str(start))+').touch(); p=Path('+repr(str(release))+'); \nwhile not p.exists(): time.sleep(.05)')
        self.wait_for(start.exists); following=self.launch('from pathlib import Path; Path('+repr(str(second))+').touch()')
        time.sleep(.6); self.assertFalse(second.exists()); release.touch()
        self.assert_clean(first,0); self.assert_clean(following,0); self.assertTrue(second.exists())
    def test_supervisor_killed_recovery(self):
        child=self.root/'orphan'; first=self.launch(self.sleeper(child)); self.wait_for(child.exists)
        first.kill(); first.wait(); self.assert_clean(self.launch('pass'),0); self.assert_dead(child.read_text())
    def test_actual_supervisor_killed_recovery(self):
        child=self.root/'orphan-supervisor'; first=self.launch(self.sleeper(child)); self.wait_for(child.exists)
        state=json.loads((self.root/'state/session.json').read_text())
        signal_pid=state['supervisorPID']
        import os
        os.kill(signal_pid,signal.SIGKILL)
        first.wait(timeout=8)
        self.assert_clean(self.launch('pass'),0); self.assert_dead(child.read_text())

    def test_detached_phase_cancelled(self):
        child=self.root/'detached'; code=self.sleeper(child)
        p=self.launch('import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",'+repr(code)+'],start_new_session=True); time.sleep(60)')
        self.wait_for(child.exists); time.sleep(.6); p.terminate(); self.assert_clean(p,143); self.assert_dead(child.read_text())
    def test_external_device_blocks(self):
        data=json.loads(self.inventory.read_text()); data['other']['state']='Booted'; self.inventory.write_text(json.dumps(data))
        p=self.launch('raise Exception("must not run")'); _,err=p.communicate(timeout=8)
        self.assertEqual(p.returncode,1); self.assertIn('Other simulators',err)
        self.assertEqual(json.loads(self.inventory.read_text())['other']['state'],'Booted')
    def test_cleanup_failure_blocks_then_recovers(self):
        marker=Path(str(self.inventory)+'.fail'); marker.touch()
        first=self.launch('pass'); _,err=first.communicate(timeout=8)
        self.assertEqual(first.returncode,1); self.assertIn('Cleanup incomplete',err)
        self.assertTrue((self.root/'state/session.json').exists())
        second=self.launch('raise Exception("must not run")'); _,err=second.communicate(timeout=8)
        self.assertEqual(second.returncode,1); self.assertNotIn('must not run',err)
        marker.unlink(); self.assert_clean(self.launch('pass'),0)

    def test_wait_timeout_does_not_interrupt_owner(self):
        child=self.root/'waiting-owner'; first=self.launch(self.sleeper(child)); self.wait_for(child.exists)
        second=self.launch('pass','--wait','0.2'); _,err=second.communicate(timeout=8)
        self.assertEqual(second.returncode,1); self.assertIn('waiting',err)
        self.assertIsNone(first.poll()); first.terminate(); self.assert_clean(first,143)

    def test_xcode_flags(self):
        spec=importlib.util.spec_from_file_location('runner',SOURCE); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        command,devices=m.xcode_job(['test','-destination','platform=iOS Simulator,id=phone','-parallel-testing-enabled','YES'],json.loads(self.inventory.read_text()))
        self.assertEqual(devices,['phone']); self.assertNotIn('YES',command); self.assertIn('NO',command)
if __name__=='__main__': unittest.main()
