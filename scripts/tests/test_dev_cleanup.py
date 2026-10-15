import importlib.util
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('cleanup',Path(__file__).resolve().parents[1]/'axon_dev_cleanup.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()/'tree';self.root.mkdir();(self.root/'.git').write_text('gitdir: unused')
        self.record={'HEAD':'abc','branch':'refs/heads/task'}
    def git(self,root,*args):
        if args[:1]==('symbolic-ref',):return 'task'
        if args[:2]==('remote','get-url'):return 'https://github.com/micahlee/axon-training.git'
        if args[:1]==('status',):return ''
        if args[:1]==('rev-parse',):return 'abc'
        if args[:1]==('ls-files',):return ''
        if args[:1]==('check-ignore',):return '.build'
        raise AssertionError(args)
    def pull(self,**changes):
        p={'state':'closed','merged_at':'today','head':{'sha':'abc','repo':{'full_name':'micahlee/axon-training'}},'number':2,'html_url':'https://example.invalid/pr'};p.update(changes);return p
    def test_retirement_requires_exact_merged_head_and_no_open_pr(self):
        with patch.object(m,'git',side_effect=self.git),patch.object(m,'api',return_value=[self.pull()]):
            self.assertIsNotNone(m.retired_branch(self.root,'axon-training',self.record))
        for pulls in ([self.pull(merged_at=None)],[self.pull(head={'sha':'other'})],[self.pull(),self.pull(state='open')],[]):
            with patch.object(m,'git',side_effect=self.git),patch.object(m,'api',return_value=pulls):
                self.assertIsNone(m.retired_branch(self.root,'axon-training',self.record))
    def test_dirty_main_and_detached_preserved(self):
        for record in ({'HEAD':'abc'},dict(self.record,branch='refs/heads/main')):
            self.assertIsNone(m.retired_branch(self.root,'axon-training',record))
        original=self.git
        with patch.object(m,'git',side_effect=lambda root,*args:' M source.go' if args[0]=='status' else original(root,*args)):
            self.assertIsNone(m.retired_branch(self.root,'axon-training',self.record))
    def test_allowlist_and_symlink_guards(self):
        outside=self.root.parent/'outside';outside.mkdir();(outside/'valuable').write_text('keep')
        (self.root/'.build').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):m.safe_output(self.root,'.build')
        for path in ('../outside','.git','.axon-dev/qualification-results','Library/Caches/go-build'):
            with self.assertRaises(ValueError):m.safe_output(self.root,path)
        self.assertEqual((outside/'valuable').read_text(),'keep')
    def test_tracked_or_nonignored_output_preserved(self):
        (self.root/'.build').mkdir()
        with patch.object(m,'git',return_value='tracked'):
            with self.assertRaises(ValueError):m.safe_output(self.root,'.build')
        def nonignored(root,*args):
            if args[0]=='check-ignore':raise subprocess.CalledProcessError(1,args)
            return ''
        with patch.object(m,'git',side_effect=nonignored):
            with self.assertRaises(subprocess.CalledProcessError):m.safe_output(self.root,'.build')
    def test_revalidation_blocks_new_activity_and_recent_output(self):
        target=self.root/'.build';target.mkdir();(target/'object').write_text('keep')
        item={'kind':'build-output','root':str(self.root),'relative':'.build','record':self.record,'evidence':{'repository':'axon-training'}}
        with patch.object(m,'process_paths',return_value=[self.root]):
            with self.assertRaises(RuntimeError):m.apply_item(item,24)
        with patch.object(m,'process_paths',return_value=[]),patch.object(m,'retired_branch',return_value={'pull':2}),patch.object(m,'git',side_effect=self.git):
            with self.assertRaises(RuntimeError):m.apply_item(item,24)
        self.assertTrue((target/'object').exists())
    def test_build_cleanup_only_removes_allowlisted_output(self):
        target=self.root/'.build';target.mkdir();(target/'object').write_text('generated');(self.root/'source.swift').write_text('keep')
        item={'kind':'build-output','root':str(self.root),'relative':'.build','record':self.record,'evidence':{'repository':'axon-training'}}
        with patch.object(m,'process_paths',return_value=[]),patch.object(m,'retired_branch',return_value={'pull':2}),patch.object(m,'latest_change',return_value=0),patch.object(m,'git',side_effect=self.git):
            self.assertEqual(m.apply_item(item,24),'deleted')
        self.assertFalse(target.exists());self.assertEqual((self.root/'source.swift').read_text(),'keep')
    def test_reopened_issue_and_changed_device_block_simulator_deletion(self):
        item={'kind':'simulator','udid':'old','name':'AXON-1-old','state':1,'last_used':0,'issue':1}
        current={k:item[k] for k in ('udid','name','state','last_used')}
        with patch.object(m,'process_paths',return_value=[]),patch.object(m,'load_devices',return_value=[current]),patch.object(m,'api',return_value={'state':'open'}),patch.object(m,'run') as command:
            with self.assertRaises(RuntimeError):m.apply_item(item,24)
            command.assert_not_called()
        with patch.object(m,'load_devices',return_value=[dict(current,state=3)]),patch.object(m,'run') as command:
            with self.assertRaises(RuntimeError):m.apply_item(item,24)
            command.assert_not_called()

if __name__=='__main__':unittest.main()
