"""Exercise installer safety in disposable repos and home directories."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

INSTALLER = Path(__file__).resolve().parents[1] / 'install-local.py'


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / 'repo'
        self.home = self.root / 'home'
        (self.repo / 'scripts').mkdir(parents=True)
        self.home.mkdir()
        shutil.copyfile(INSTALLER, self.repo / 'scripts/install-local.py')
        for name in ['alpha', 'beta', 'fitness-coach']:
            folder = self.repo / 'skills/personal' / name
            folder.mkdir(parents=True)
            (folder / 'SKILL.md').write_text(f'---\nname: {name}\n---\n')
        (self.repo / 'rules').mkdir()
        (self.repo / 'rules/CODEX-AGENTS.md').write_text('Use Standard processing.\n')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Installer Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)

    def run_installer(self, *args):
        env = dict(os.environ, HOME=str(self.home), CODEX_HOME=str(self.home / '.codex'), PYTHONDONTWRITEBYTECODE='1')
        return subprocess.run([sys.executable, '-S', str(self.repo / 'scripts/install-local.py'), *args], env=env, text=True, capture_output=True)

    def test_preview_is_read_only(self):
        result = self.run_installer('--rules')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_apply_links_and_rules_and_repeat_is_safe(self):
        for _ in range(2):
            result = self.run_installer('--apply', '--rules')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ['alpha', 'beta']:
            self.assertEqual((self.home / '.agents/skills' / name).resolve(), self.repo / 'skills/personal' / name)
        rules = self.home / '.codex/AGENTS.md'
        self.assertEqual(rules.read_text(), 'Use Standard processing.\n')
        self.assertEqual(rules.stat().st_mode & 0o777, 0o600)

    def test_conflict_preserves_files_and_prevents_other_installations(self):
        existing = self.home / '.agents/skills/beta'
        existing.mkdir(parents=True)
        (existing / 'SKILL.md').write_text('Local custom content')
        result = self.run_installer('--apply', '--rules')
        self.assertEqual(result.returncode, 1)
        self.assertEqual((existing / 'SKILL.md').read_text(), 'Local custom content')
        self.assertFalse((existing.parent / 'alpha').exists())
        self.assertFalse((self.home / '.codex').exists())

    def test_codex_duplicate_is_preserved(self):
        existing = self.home / '.codex/skills/alpha'
        existing.mkdir(parents=True)
        result = self.run_installer('--apply')
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.home / '.agents').exists())

    def test_changed_rules_are_preserved(self):
        rules = self.home / '.codex/AGENTS.md'
        rules.parent.mkdir()
        rules.write_text('Existing rules')
        result = self.run_installer('--apply', '--rules')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(rules.read_text(), 'Existing rules')
        self.assertFalse((self.home / '.agents').exists())

    def test_external_owner_is_not_installed(self):
        result = self.run_installer('--apply')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.home / '.agents/skills/fitness-coach').exists())
        result = self.run_installer('--skill', 'fitness-coach', '--apply')
        self.assertEqual(result.returncode, 2)
        self.assertIn('managed source', result.stderr)

    def test_dirty_and_non_main_sources_cannot_install(self):
        extra = self.repo / 'untracked.txt'
        extra.write_text('dirty')
        result = self.run_installer('--apply')
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.home / '.agents').exists())
        extra.unlink()
        self.git('update-ref', '-d', 'refs/remotes/origin/main')
        result = self.run_installer('--apply')
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.home / '.agents').exists())


if __name__ == '__main__':
    unittest.main()
