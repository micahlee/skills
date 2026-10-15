#!/usr/bin/env python3
"""Install the shared runner only from clean, freshly fetched protected main."""
import os
from pathlib import Path
import subprocess
import tempfile
import sys
import plistlib
schedule = '--install-cleanup-schedule' in sys.argv[1:]
if any(arg != '--install-cleanup-schedule' for arg in sys.argv[1:]):
    raise SystemExit('Usage: install_simulator_runner.py [--install-cleanup-schedule]')
root = Path(__file__).resolve().parent.parent
subprocess.run(["git", "-C", str(root), "fetch", "origin", "main"], check=True)
def git(*args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
if git("rev-parse", "HEAD") != git("rev-parse", "origin/main") or git("status", "--porcelain", "--untracked-files=all"):
    raise SystemExit("Install requires a clean checkout at freshly fetched origin/main")
source = root / "scripts/axon_simulator_runner.py"
subprocess.run(["python3", "-B", str(source), "--help"], check=True)
target = Path.home() / ".local/bin/axon-simulator-run"
target.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
    temporary.write(source.read_bytes())
    stage = Path(temporary.name)
try:
    stage.chmod(0o755)
    os.replace(stage, target)
finally:
    stage.unlink(missing_ok=True)
print("Installed", target, "from", git("rev-parse", "HEAD"))
cleanup_target = target.parent / 'axon-dev-cleanup'
with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
    temporary.write((root / 'scripts/axon_dev_cleanup.py').read_bytes())
    stage = Path(temporary.name)
try:
    stage.chmod(0o755)
    os.replace(stage, cleanup_target)
finally:
    stage.unlink(missing_ok=True)
print('Installed', cleanup_target)
vm_target = target.parent / 'axon-ci-vm'
with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
    temporary.write((root / 'scripts/axon_ci_vm.py').read_bytes())
    stage = Path(temporary.name)
try:
    stage.chmod(0o755)
    os.replace(stage, vm_target)
finally:
    stage.unlink(missing_ok=True)
print('Installed', vm_target, '(no VM or runner started)')
if schedule:
    state = Path.home() / 'Library/Caches/axon-dev-cleanup'
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    label = 'com.micahlee.axon-dev-cleanup'
    agent = Path.home() / 'Library/LaunchAgents' / (label + '.plist')
    agent.parent.mkdir(parents=True, exist_ok=True)
    config = {
        'Label': label,
        'ProgramArguments': [sys.executable, '-B', str(cleanup_target), '--apply', '--projects-only', '--quiet', '--report', str(state / 'last-run.json')],
        'EnvironmentVariables': {'PATH': str(target.parent) + ':/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'},
        'StartCalendarInterval': {'Hour': 3, 'Minute': 30},
        'ProcessType': 'Background', 'LowPriorityIO': True, 'Nice': 10,
        'StandardOutPath': '/dev/null', 'StandardErrorPath': '/dev/null',
    }
    payload = plistlib.dumps(config)
    existing = subprocess.run(['launchctl', 'print', f'gui/{os.getuid()}/{label}'], capture_output=True, text=True)
    if existing.returncode == 0:
        if agent.exists() and agent.read_bytes() == payload:
            print('Cleanup schedule already installed')
            raise SystemExit(0)
        raise SystemExit('Existing cleanup agent differs; preserve it and update while idle')
    agent.write_bytes(payload)
    subprocess.run(['launchctl', 'bootstrap', f'gui/{os.getuid()}', str(agent)], check=True)
    print('Installed daily 03:30 local cleanup; no persistent worker or RunAtLoad')
