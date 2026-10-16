import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('retirement', Path(__file__).resolve().parents[1] / 'axon_release_retirement.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.root = self.home / 'projects/axon-release-production-prep'
        self.state = self.home / '.local/state/axon-release-retirement'
        self.identity = 'a' * 64
        self.path = self.root / 'installation-candidates' / self.identity
        self.path.mkdir(parents=True)
        self.manifest = 'installation-candidate.json'
        (self.path / self.manifest).write_text(json.dumps({'schemaVersion': 1, 'kind': m.SECTIONS['installation-candidates'][1], 'changes': ['AXON-1']}))
        (self.path / 'core').mkdir(); (self.path / 'core/binary').write_bytes(b'generated executable')
        (self.path / 'core/component.json').write_text('{"revision":"pinned-source"}')
        self.age(self.path)
        self.cutoff = time.time() - 14 * 86400
        self.row = m.inventory(self.root)[str(self.path)]

    def age(self, root):
        old = time.time() - 30 * 86400
        for p in [root] + list(root.rglob('*')):
            os.utime(p, (old, old))

    def test_runtime_open_and_transitive_artifact_references_preserved(self):
        self.assertTrue(m.needed(self.row, {str(self.path): self.row}, str(self.path / 'core/binary'), set()))
        self.assertTrue(m.needed(self.row, {}, self.identity, set()))
        self.assertTrue(m.needed(self.row, {}, '', {str(self.path / 'core/binary')}))
        other = dict(self.row, path=self.path.parent / ('b' * 64), references='sha256:' + self.identity)
        self.assertTrue(m.needed(self.row, {'other': other}, '', set()))
        self.assertFalse(m.needed(self.row, {str(self.path): self.row}, '', set()))

    def test_reopened_unknown_and_uncompleted_owners_preserved(self):
        for state, reason in [('open', 'reopened'), ('closed', 'not_planned'), ('closed', None)]:
            with patch.object(m, 'command', return_value=json.dumps({'state': state, 'state_reason': reason})):
                self.assertFalse(m.completed(['AXON-1']))
        for tags in [[], ['other'], ['AXON-1', 'unknown']]:
            with patch.object(m, 'command') as call:
                self.assertFalse(m.completed(tags)); call.assert_not_called()
        with patch.object(m, 'command', return_value='{"state":"closed","state_reason":"completed"}') as call:
            cache = {}; self.assertTrue(m.completed(['AXON-1'], cache)); self.assertTrue(m.completed(['AXON-1'], cache))
            self.assertEqual(call.call_count, 1)

    def test_new_write_data_and_symlink_block_retirement(self):
        for name in ['personal.sqlite', 'personal.db', 'events.jsonl', 'archive.sqlite-wal', 'events.jsonl.gz']:
            p = self.path / name; p.write_text('original'); self.age(self.path)
            with self.assertRaises(m.Unsafe): m.inspect(self.path, self.cutoff)
            p.unlink()
        self.age(self.path); (self.path / 'core/binary').write_text('new build')
        with self.assertRaises(m.Unsafe): m.inspect(self.path, self.cutoff)
        self.age(self.path); (self.path / 'linked').symlink_to(self.home)
        with self.assertRaises(m.Unsafe): m.inspect(self.path, self.cutoff)

    def test_unknown_manifest_fails_closed_and_config_reference_is_read(self):
        (self.path / 'configuration').mkdir(); (self.path / 'configuration/service.toml').write_text('artifact = "' + 'b' * 64 + '"')
        self.assertIn('b' * 64, m.inventory(self.root)[str(self.path)]['references'])
        (self.path / self.manifest).write_text('{"kind":"unknown","schemaVersion":1}')
        with self.assertRaises(m.Unsafe): m.inventory(self.root)

    def test_missing_process_inventory_or_resource_read_fails_closed(self):
        with patch.object(m, 'command', return_value=''):
            with self.assertRaises(m.Unsafe): m.open_paths()
        with patch.object(m, 'command', side_effect=m.Unsafe('unavailable')):
            with self.assertRaises(m.Unsafe): m.references(self.home, self.root)

    def test_reference_appearing_after_backup_blocks_rename(self):
        with patch.object(m, 'completed', return_value=True), patch.object(m, 'references', return_value=self.identity), patch.object(m, 'open_paths', return_value=set()):
            with self.assertRaises(m.Unsafe): m.retire(self.row, self.home, self.root, self.state, self.cutoff)
        self.assertTrue((self.path / 'core/binary').exists())
        self.assertTrue((self.state / 'evidence/installation-candidates' / self.identity / 'files' / self.manifest).exists())

    def test_retirement_preserves_verified_manifests_and_metadata(self):
        # Sealed artifacts have read-only directories, as on the real host.
        (self.path / 'core').chmod(0o555); self.path.chmod(0o555)
        with patch.object(m, 'completed', return_value=True), patch.object(m, 'references', return_value=''), patch.object(m, 'open_paths', return_value=set()):
            journal = m.retire(self.row, self.home, self.root, self.state, self.cutoff)
        self.assertEqual(journal['state'], 'retired'); self.assertFalse(self.path.exists())
        evidence = self.state / 'evidence/installation-candidates' / self.identity
        self.assertEqual((evidence / 'files/core/component.json').read_text(), '{"revision":"pinned-source"}')
        self.assertFalse((evidence / 'files/core/binary').exists())
        self.assertTrue((evidence / 'files' / self.manifest).exists())

    def test_interrupted_retirement_resumes_only_receipt_bound_staging(self):
        original = m.remove_staged
        with patch.object(m, 'completed', return_value=True), patch.object(m, 'references', return_value=''), patch.object(m, 'open_paths', return_value=set()), patch.object(m, 'remove_staged', side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError): m.retire(self.row, self.home, self.root, self.state, self.cutoff)
        receipt = next((self.state / 'receipts').glob('*.json')); journal = m.read_json(receipt)
        self.assertFalse(self.path.exists()); self.assertEqual(journal['state'], 'staged')
        staged = self.root / '.retirement-staging/installation-candidates' / self.identity
        with self.assertRaises(m.Unsafe): original(self.root, self.state, journal, self.identity, set())
        self.assertTrue(staged.exists())
        original(self.root, self.state, journal, '', set())
        self.assertFalse(staged.exists()); self.assertEqual(m.read_json(receipt)['state'], 'retired')
        with self.assertRaises(m.Unsafe): original(self.root, self.state, dict(journal, identity='../unrelated'), '', set())

    def stage(self):
        with patch.object(m, 'completed', return_value=True), patch.object(m, 'references', return_value=''), patch.object(m, 'open_paths', return_value=set()), patch.object(m, 'remove_staged', side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError): m.retire(self.row, self.home, self.root, self.state, self.cutoff)
        receipt = next((self.state / 'receipts').glob('*.json'))
        return m.read_json(receipt), self.root / '.retirement-staging/installation-candidates' / self.identity

    def test_recovery_preserves_new_data_and_changed_payload(self):
        journal, staged = self.stage()
        (staged / 'new-original.txt').write_text('must keep')
        with self.assertRaises(m.Unsafe): m.remove_staged(self.root, self.state, journal, '', set())
        self.assertTrue((staged / 'new-original.txt').exists())
        (staged / 'new-original.txt').unlink(); (staged / 'core/binary').write_text('changed payload')
        with self.assertRaises(m.Unsafe): m.remove_staged(self.root, self.state, journal, '', set())
        self.assertTrue(staged.exists())

    def test_recovery_requires_every_metadata_backup_not_only_manifest(self):
        journal, staged = self.stage()
        archive = self.state / 'evidence/installation-candidates' / self.identity / 'files/core/component.json'
        archive.write_text('corrupted evidence')
        with self.assertRaises(m.Unsafe): m.remove_staged(self.root, self.state, journal, '', set())
        self.assertTrue(staged.exists())

    def test_evidence_failure_leaves_payload_in_place(self):
        with patch.object(m, 'backup', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): m.retire(self.row, self.home, self.root, self.state, self.cutoff)
        self.assertTrue((self.path / 'core/binary').exists())

    def test_metadata_conflict_and_symlinked_evidence_fail_before_mutation(self):
        files = m.inspect(self.path, self.cutoff)
        destination = self.state / 'evidence/test'
        m.backup(self.row, destination, files)
        (destination / 'files' / self.manifest).write_text('different original evidence')
        with self.assertRaises(m.Unsafe): m.backup(self.row, destination, files)
        self.assertTrue((self.path / 'core/binary').exists())
        outside = self.home / 'outside'; outside.mkdir()
        linked = self.home / 'linked'; linked.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(m.Unsafe): m.safe_directory(linked / 'must-not-be-created')
        self.assertFalse((outside / 'must-not-be-created').exists())

    def test_database_without_extension_is_preserved(self):
        (self.path / 'personal-data').write_bytes(b'SQLite format 3\x00' + b'private')
        self.age(self.path)
        with self.assertRaises(m.Unsafe): m.inspect(self.path, self.cutoff)

    def test_owner_lookup_failure_stops_run_without_retirement(self):
        with patch.object(m, 'references', return_value=''), patch.object(m, 'open_paths', return_value=set()), patch.object(m, 'completed', side_effect=m.Unsafe('owner unavailable')), patch.object(m, 'retire') as retire:
            self.assertEqual(m.main(['--home', str(self.home), '--apply']), 1)
            retire.assert_not_called()
        self.assertTrue(self.path.exists())

    def test_installer_rejects_feature_branch_before_copy_or_launchd(self):
        spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'install_release_retirement.py')
        installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        outputs = ['https://github.com/micahlee/skills.git', '', 'feature', 'main']
        with patch.object(installer.subprocess, 'check_output', side_effect=outputs), patch.object(installer.subprocess, 'run') as run, patch.object(installer.shutil, 'copyfile') as copy:
            with self.assertRaisesRegex(RuntimeError, 'clean checkout'): installer.install()
            copy.assert_not_called()
            self.assertEqual(run.call_count, 1)  # only the read-only fetch

    def test_preview_and_maximum_limit_do_not_mutate_sources(self):
        other = self.path.parent / ('b' * 64)
        import shutil
        shutil.copytree(self.path, other); self.age(other)
        with patch.object(m, 'references', return_value=''), patch.object(m, 'open_paths', return_value=set()), patch.object(m, 'completed', return_value=True), patch.object(m, 'retire') as retire:
            self.assertEqual(m.main(['--home', str(self.home), '--max-items', '1']), 0)
            retire.assert_not_called()
        report = m.read_json(self.state / 'last-run.json')
        self.assertEqual(report['candidateCount'], 1); self.assertEqual(report['items'][0]['state'], 'preview')
        self.assertTrue(self.path.exists()); self.assertTrue(other.exists())


if __name__ == '__main__':
    unittest.main()
