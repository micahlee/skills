#!/usr/bin/env python3
"""Conservative local Axon cleanup: preview by default, never clean Go caches."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import fcntl
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import time
import urllib.parse

REPOS = ('axon-mobile-node', 'axon-training', 'axon-bible-study', 'axon-punch-list', 'axon-client-swift', 'axon-core')
OUTPUTS = ('.axon-dev/qualification-cache', '.axon-dev/apple-health-compile',
           '.axon-dev/nutrition-health-build', '.axon-dev/location-focused', '.build')
HOME = Path.home()


class GithubUnavailable(RuntimeError):
    pass


def run(args, *, timeout=60):
    return subprocess.check_output([str(a) for a in args], text=True, stderr=subprocess.PIPE, timeout=timeout).strip()


def api(endpoint):
    try:
        return json.loads(run(['gh', 'api', endpoint]))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as error:
        raise GithubUnavailable('GitHub retirement lookup failed; deferring remaining cleanup without retries') from error


def git(root, *args):
    return run(['git', '-C', root, *args])


def worktrees(root):
    result = []
    for block in git(root, 'worktree', 'list', '--porcelain').split('\n\n'):
        data = dict(line.split(' ', 1) for line in block.splitlines() if ' ' in line)
        if 'worktree' in data and Path(data['worktree']).exists():
            result.append(data)
    return result


def process_paths():
    # lsof failure must block deletion, not look like an idle host. Do not log
    # process arguments (which may contain credentials).
    text = run(['lsof', '-a', '-u', str(os.getuid()), '-Fn'], timeout=30)
    paths = [Path(row[1:]).resolve() for row in text.splitlines() if row.startswith('n/')]
    if not paths:
        raise RuntimeError('Cannot establish active process directories')
    return paths


def busy(root, paths):
    return any(p == root or root in p.parents for p in paths)


def safe_output(root, relative):
    if relative not in OUTPUTS:
        raise ValueError('Output is not allowlisted')
    path = root / relative
    if not path.is_dir() or path.is_symlink() or path.resolve() != path.absolute():
        raise ValueError('Output missing, symlinked or outside its worktree')
    if git(root, 'ls-files', '--', relative):
        raise ValueError('Output contains tracked files')
    git(root, 'check-ignore', '--', relative)
    return path


def latest_change(path):
    # Directory mtime alone misses active incremental builds. Inspect all
    # entries without following symlinks; never mutate timestamps or files.
    latest = path.lstat().st_mtime
    for parent, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            latest = max(latest, (Path(parent) / name).lstat().st_mtime)
    return latest


def retired_branch(root, repo, record):
    branch = record.get('branch', '').removeprefix('refs/heads/')
    if not branch or branch in ('main', 'master') or not (root / '.git').is_file():
        return None
    if git(root, 'symbolic-ref', '--short', 'HEAD') != branch:
        return None
    if git(root, 'remote', 'get-url', 'origin') not in (
            f'https://github.com/micahlee/{repo}.git', f'https://github.com/micahlee/{repo}',
            f'git@github.com:micahlee/{repo}.git'):
        return None
    if git(root, 'status', '--porcelain', '--untracked-files=normal'):
        return None
    head = git(root, 'rev-parse', 'HEAD')
    if head != record.get('HEAD'):
        return None
    query = urllib.parse.urlencode({'state': 'all', 'head': 'micahlee:' + branch, 'per_page': 100})
    pulls = api(f'repos/micahlee/{repo}/pulls?{query}')
    if any(p['state'] == 'open' for p in pulls):
        return None
    for p in pulls:
        if p.get('merged_at') and p['head']['sha'] == head and p['head']['repo'] and p['head']['repo']['full_name'] == 'micahlee/' + repo:
            return {'repository': repo, 'head': head, 'branch': branch, 'pull': p['number'], 'url': p['html_url']}
    return None


def discover(age_hours):
    paths = process_paths()
    cutoff = time.time() - age_hours * 3600
    retired, preserved = {}, []
    outputs = []
    for repo in REPOS:
        source = HOME / 'projects' / repo
        if not source.exists():
            continue
        for record in worktrees(source):
            root = Path(record['worktree']).resolve()
            if busy(root, paths):
                preserved.append({'path': str(root), 'reason': 'active process cwd or open file in worktree'})
                continue
            # Only query branches with known generated output or an owned hash
            # simulator. Empty and unknown worktrees are not cleanup targets.
            stamp = hashlib.sha256(str(root).encode()).hexdigest()[:12]
            has_output = any((root / rel).is_dir() for rel in OUTPUTS)
            if not has_output and stamp not in DEVICE_HASHES:
                continue
            evidence = retired_branch(root, repo, record)
            if not evidence:
                preserved.append({'path': str(root), 'reason': 'dirty, open PR, or no exact merged PR'})
                continue
            retired[stamp] = {'root': str(root), 'record': record, 'evidence': evidence}
            for rel in OUTPUTS:
                if not (root / rel).exists():
                    continue
                try:
                    target = safe_output(root, rel)
                    if latest_change(target) > cutoff:
                        preserved.append({'path': str(target), 'reason': 'recently used'})
                        continue
                except (ValueError, subprocess.CalledProcessError) as error:
                    preserved.append({'path': str(root / rel), 'reason': str(error)[:160]})
                    continue
                outputs.append({'kind': 'build-output', 'root': str(root), 'relative': rel,
                                'record': record, 'evidence': evidence})
    devices = []
    issue_cache = {}
    for device in DEVICES:
        name = device['name']
        device_root = HOME / 'Library/Developer/CoreSimulator/Devices' / device['udid']
        if busy(device_root, paths):
            continue
        if device['state'] != 1 or device['last_used'] is None or device['last_used'] > cutoff:
            continue
        suffix = re.fullmatch(r'Axon CI Qualification ([0-9a-f]{12})', name)
        owner = retired.get(suffix[1]) if suffix else None
        if owner:
            devices.append(dict(device, kind='simulator', owner=owner))
            continue
        issue = re.match(r'AXON[- ]?(\d+)(?:[- ]|$)', name, re.I)
        if not issue:
            continue
        number = int(issue[1])
        if number not in issue_cache:
            issue_cache[number] = api(f'repos/micahlee/axon-engineering-hub/issues/{number}')
        evidence = issue_cache[number]
        # Legacy issues may have no state_reason. Reopened, open and
        # not-planned work is never retired by this policy.
        if evidence['state'] == 'closed' and evidence.get('state_reason') in (None, 'completed'):
            devices.append(dict(device, kind='simulator', issue=number,
                                evidence=evidence['html_url']))
    return devices + outputs, preserved


def load_devices():
    result = []
    for p in (HOME / 'Library/Developer/CoreSimulator/Devices').glob('*/device.plist'):
        d = plistlib.loads(p.read_bytes())
        used = d.get('lastUsedAt')
        if isinstance(used, dt.datetime):
            used = used.replace(tzinfo=used.tzinfo or dt.timezone.utc).timestamp()
        else:
            used = None
        result.append({'udid': p.parent.name, 'name': d.get('name', ''),
                       'state': d.get('state'), 'last_used': used})
    return result


def apply_item(item, age_hours):
    cutoff = time.time() - age_hours * 3600
    if item['kind'] == 'simulator':
        current = next((d for d in load_devices() if d['udid'] == item['udid']), None)
        if current is None:
            return 'already absent'
        if current != {k: item[k] for k in ('udid', 'name', 'state', 'last_used')}:
            raise RuntimeError('Simulator changed after discovery')
        if busy(HOME / 'Library/Developer/CoreSimulator/Devices' / item['udid'], process_paths()):
            raise RuntimeError('Simulator files are in active use')
        if 'issue' in item:
            evidence = api(f"repos/micahlee/axon-engineering-hub/issues/{item['issue']}")
            if evidence['state'] != 'closed' or evidence.get('state_reason') not in (None, 'completed'):
                raise RuntimeError('Owning issue is no longer completed')
        else:
            owner = item['owner']; root = Path(owner['root'])
            if busy(root, process_paths()) or not retired_branch(root, owner['evidence']['repository'], owner['record']):
                raise RuntimeError('Owning worktree is no longer retired')
        run([HOME / '.local/bin/axon-simulator-run', 'delete-retired', '--wait', '1', '--device', item['udid']], timeout=150)
        return 'deleted'
    root = Path(item['root'])
    if busy(root, process_paths()) or not retired_branch(root, item['evidence']['repository'], item['record']):
        raise RuntimeError('Worktree is no longer retired')
    target = safe_output(root, item['relative'])
    if latest_change(target) > cutoff:
        raise RuntimeError('Build output is now recent')
    shutil.rmtree(target)
    return 'deleted'


def main():
    global DEVICES, DEVICE_HASHES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--minimum-age-hours', type=float, default=24)
    parser.add_argument('--max-items', type=int, default=30)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()
    if not __import__('math').isfinite(args.minimum_age_hours) or args.minimum_age_hours < 1 or not 1 <= args.max_items <= 100:
        parser.error('minimum age must be >= 1 hour; max items must be 1..100')
    state = HOME / 'Library/Caches/axon-dev-cleanup'
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (state / 'cleanup.lock').open('a+')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('Cleanup already active; skipped', file=sys.stderr)
        return 0
    DEVICES = load_devices()
    DEVICE_HASHES = {d['name'].removeprefix('Axon CI Qualification ') for d in DEVICES}
    report = {'schemaVersion': 1, 'apply': args.apply, 'beforeFreeBytes': shutil.disk_usage(HOME).free,
              'items': [], 'preserved': []}
    try:
        candidates, report['preserved'] = discover(args.minimum_age_hours)
        report['candidateCount'] = len(candidates)
        for item in candidates[:args.max_items]:
            entry = dict(item, result='preview')
            if args.apply:
                try:
                    entry['result'] = apply_item(item, args.minimum_age_hours)
                except GithubUnavailable as error:
                    entry['result'] = 'preserved'; entry['reason'] = str(error)
                    report['items'].append(entry)
                    report['error'] = str(error)
                    break
                except Exception as error:
                    entry['result'] = 'preserved'; entry['reason'] = str(error)[:300]
            report['items'].append(entry)
    except Exception as error:
        report['error'] = str(error)[:300]
    report['afterFreeBytes'] = shutil.disk_usage(HOME).free
    content = json.dumps(report, indent=2) + '\n'
    if args.report:
        args.report.write_text(content)
    if not args.quiet:
        print(content)
    return 1 if report.get('error') else 0


if __name__ == '__main__':
    raise SystemExit(main())
