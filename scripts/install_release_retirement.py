#!/usr/bin/env python3
"""Install the nightly release-retirement job from clean, freshly fetched main."""
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys


def install():
    repository = Path(__file__).resolve().parents[1]
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repository), *args], text=True).strip()
    if git('remote', 'get-url', 'origin') not in ['https://github.com/micahlee/skills.git', 'https://github.com/micahlee/skills', 'git@github.com:micahlee/skills.git']:
        raise RuntimeError('Unexpected source repository')
    subprocess.run(['git', '-C', str(repository), 'fetch', 'origin', 'main'], check=True)
    if git('status', '--porcelain') or git('rev-parse', 'HEAD') != git('rev-parse', 'origin/main'):
        raise RuntimeError('Installation requires a clean checkout equal to freshly fetched origin/main')
    home = Path.home()
    binary = home / '.local/bin/axon-release-retirement'
    binary.parent.mkdir(parents=True, exist_ok=True)
    temporary = binary.with_suffix('.tmp')
    shutil.copyfile(repository / 'scripts/axon_release_retirement.py', temporary)
    temporary.chmod(0o755); temporary.replace(binary)
    label = 'com.micahlee.axon-release-retirement'
    agent = home / 'Library/LaunchAgents' / (label + '.plist')
    agent.parent.mkdir(parents=True, exist_ok=True)
    log = home / 'Library/Logs/axon-release-retirement.log'; log.parent.mkdir(parents=True, exist_ok=True)
    data = {'Label': label, 'ProgramArguments': [sys.executable, '-B', str(binary), '--apply'],
            'WorkingDirectory': str(home / 'projects'),
            'EnvironmentVariables': {'PATH': str(home / '.local/bin') + ':/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'},
            'StartCalendarInterval': {'Hour': 3, 'Minute': 45}, 'Nice': 10,
            'LowPriorityIO': True, 'ProcessType': 'Background',
            'StandardOutPath': str(log), 'StandardErrorPath': str(log)}
    agent.write_bytes(plistlib.dumps(data, sort_keys=False))
    subprocess.run(['plutil', '-lint', str(agent)], check=True)
    target = 'gui/' + str(os.getuid())
    exists = subprocess.run(['launchctl', 'print', target + '/' + label], capture_output=True).returncode == 0
    if exists:
        subprocess.run(['launchctl', 'bootout', target + '/' + label], check=True)
    subprocess.run(['launchctl', 'bootstrap', target, str(agent)], check=True)
    print('Installed nightly release retirement at 03:45; revision ' + git('rev-parse', 'HEAD'))


if __name__ == '__main__':
    install()
