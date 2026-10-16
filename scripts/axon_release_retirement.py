#!/usr/bin/env python3
"""Preview or retire unused sealed release artifacts, preserving their metadata."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time
import uuid

SECTIONS = {
    'installation-candidates': ('installation-candidate.json', 'axon.production-installation-sealed-candidate.v1'),
    'installation-derivations': ('derivation.json', 'axon.production-installation-derivation.v1'),
    'production-candidates': ('candidate.json', 'axon.production-sealed-candidate.v1'),
}
IDENTITY = re.compile(r'^[a-f0-9]{64}$')
METADATA = {'.json', '.toml', '.yaml', '.yml', '.plist', '.md', '.txt'}
DATA = re.compile(r'(?:\.sqlite3?|\.db)(?:-(?:wal|shm|journal))?(?:\.gz)?$|\.jsonl(?:\.gz)?$', re.I)


class Unsafe(RuntimeError):
    pass


def command(argv, timeout=60):
    try:
        return subprocess.check_output([str(x) for x in argv], text=True, stderr=subprocess.PIPE, timeout=timeout)
    except (subprocess.SubprocessError, OSError) as error:
        # Never include argv, response bodies, process arguments or credentials.
        raise Unsafe('Required read failed: ' + Path(str(argv[0])).name) from error


def safe_directory(path):
    if path.resolve() != path.absolute():
        raise Unsafe('Directory is symlinked')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)


def save(path, value):
    safe_directory(path.parent)
    temporary = path.with_name(path.name + '.tmp')
    if temporary.is_symlink() or path.is_symlink():
        raise Unsafe('Report path is symlinked')
    with temporary.open('w') as out:
        os.chmod(temporary, 0o600)
        json.dump(value, out, indent=2)
        out.write('\n'); out.flush(); os.fsync(out.fileno())
    temporary.replace(path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def read_json(path):
    return json.loads(path.read_text())


def open_paths():
    paths = {line[1:] for line in command(['lsof', '-nP', '-a', '-u', os.getuid(), '-Fn']).splitlines()
             if line.startswith('n/')}
    if not paths:
        raise Unsafe('Cannot establish open files and process directories')
    return paths


def busy(path, paths):
    return any(p == str(path) or p.startswith(str(path) + '/') for p in paths)


def references(home, root):
    """Inspect all registered resource kinds and startup references, without logging content."""
    axon = home / '.local/bin/axon'; resource_home = home / '.axon/resources'
    definitions = json.loads(command([axon, 'api-resources', '--home', resource_home]))
    if not isinstance(definitions, list) or not definitions:
        raise Unsafe('Resource definitions unavailable')
    texts = []
    for definition in definitions:
        if 'list' in definition.get('metadata', {}).get('operations', {}).get('verbs', []):
            records = json.loads(command([axon, 'get', '--home', resource_home, definition['id']]))
            if not isinstance(records, list):
                raise Unsafe('Resource list unavailable')
            texts.append(json.dumps(records))
    roots = [p for p in [home / '.axon', home / '.local/share/axon'] if p.exists()]
    if roots:
        args = ['rg', '--hidden', '--no-messages', '-o', '--no-filename',
                re.escape(str(root)) + r'/[^\s"\\<>]+|\b[a-f0-9]{64}\b']
        for glob in ['*.json', '*.toml', '*.yaml', '*.yml', '*.plist', '*.conf',
                     '!**/client-candidates/**', '!**/runtime-retention/**']:
            args += ['-g', glob]
        try:
            texts.append(command(args + roots, timeout=120))
        except Unsafe as error:
            cause = error.__cause__
            if not isinstance(cause, subprocess.CalledProcessError) or cause.returncode != 1:
                raise
    for directory in [home / '.local/bin', home / 'Library/LaunchAgents',
                      Path('/Library/LaunchAgents'), Path('/Library/LaunchDaemons')]:
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if path.is_symlink():
                texts.append(str(path.resolve(strict=True)))
            if path.is_file() and path.stat().st_size <= 2_000_000:
                texts.append(path.read_bytes().decode('utf-8', errors='replace'))
    texts.append(command(['ps', '-axo', 'args=']))
    return '\n'.join(texts)


def completed(tags, cache=None):
    if not tags or not all(re.fullmatch(r'AXON-\d+', str(t)) for t in tags):
        return False
    cache = {} if cache is None else cache
    for tag in set(tags):
        if tag not in cache:
            issue = json.loads(command(['gh', 'api', 'repos/micahlee/axon-engineering-hub/issues/' + tag[5:]]))
            cache[tag] = issue.get('state') == 'closed' and issue.get('state_reason') == 'completed'
        if not cache[tag]:
            return False
    return True


def inventory(root):
    rows = {}
    for section, (manifest, kind) in SECTIONS.items():
        directory = root / section
        if not directory.exists():
            continue
        if directory.is_symlink() or directory.resolve() != directory.absolute():
            raise Unsafe('Artifact section is symlinked')
        for path in directory.iterdir():
            if not path.is_dir() or not IDENTITY.fullmatch(path.name):
                continue
            if path.is_symlink():
                raise Unsafe('Artifact directory is symlinked')
            record = path / manifest
            if not record.is_file() or record.is_symlink():
                raise Unsafe('Artifact manifest missing or symlinked')
            data = read_json(record)
            if data.get('kind') != kind or data.get('schemaVersion') != 1:
                raise Unsafe('Unknown artifact manifest format')
            tags = data.get('changes', []); texts = [record.read_text()]
            if section == 'production-candidates':
                release = path / 'release.json'
                if release.is_symlink():
                    raise Unsafe('Release record is symlinked')
                tags = read_json(release).get('changes', []); texts.append(release.read_text())
            for sub in ['configuration', 'config']:
                if (path / sub).is_symlink():
                    raise Unsafe('Artifact configuration is symlinked')
                if (path / sub).is_dir():
                    for config in (path / sub).rglob('*'):
                        if config.is_symlink():
                            raise Unsafe('Artifact configuration is symlinked')
                        if config.is_file():
                            texts.append(config.read_text())
            rows[str(path)] = {'path': path, 'manifest': manifest, 'tags': tags,
                               'references': '\n'.join(texts)}
    return rows


def inspect(path, cutoff):
    if path.is_symlink() or path.resolve() != path.absolute():
        raise Unsafe('Artifact path is symlinked')
    files = []
    for base, dirs, names in os.walk(path, followlinks=False):
        parent = Path(base)
        for entry in [parent] + [parent / name for name in dirs + names]:
            info = entry.lstat()
            if info.st_mtime >= cutoff or entry.is_symlink() or entry.name == '.git':
                raise Unsafe('Recent, symlinked or repository content')
            if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                raise Unsafe('Special filesystem entry')
            if entry.is_file():
                if DATA.search(entry.name):
                    raise Unsafe('Possible persistent data')
                with entry.open('rb') as inp:
                    if inp.read(16) == b'SQLite format 3\x00':
                        raise Unsafe('Possible persistent data')
                files.append((entry, info.st_size, info.st_mtime_ns, info.st_blocks * 512))
    return sorted(files)


def needed(row, rows, refs, opened):
    path = row['path']
    return (str(path) in refs or path.name in refs or busy(path, opened) or
            any(other['path'] != path and (path.name in other['references'] or str(path) in other['references'])
                for other in rows.values()))


def backup(row, destination, files):
    """Preserve every metadata file, with no size-based omissions."""
    path = row['path']; records = []
    for source, size, modified, allocated in files:
        if source.parent != path and source.suffix.lower() not in METADATA:
            continue
        target = destination / 'files' / source.relative_to(path)
        safe_directory(target.parent)
        if target.is_symlink() or target.parent.resolve() != target.parent.absolute():
            raise Unsafe('Evidence destination is symlinked')
        if target.exists() and hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(source.read_bytes()).digest():
            raise Unsafe('Evidence already exists for different contents')
        with source.open('rb') as inp, target.open('wb') as out:
            os.chmod(target, 0o600); shutil.copyfileobj(inp, out)
            out.flush(); os.fsync(out.fileno())
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise Unsafe('Metadata backup verification failed')
        records.append({'path': str(source.relative_to(path)), 'sha256': digest})
    if row['manifest'] not in {r['path'] for r in records}:
        raise Unsafe('Manifest backup absent')
    save(destination / 'retirement-metadata.json', {'files': records})


def remove_staged(root, state, journal, refs, opened):
    identity = journal['identity']; section = journal['section']
    if section not in SECTIONS or not IDENTITY.fullmatch(identity):
        raise Unsafe('Invalid retirement receipt')
    source = root / section / identity
    staged = root / '.retirement-staging' / section / identity
    evidence = state / 'evidence' / section / identity
    if staged.exists():
        if source.exists() or staged.is_symlink() or staged.resolve() != staged.absolute():
            raise Unsafe('Staged artifact ownership conflict')
        if identity in refs or str(source) in refs or str(staged) in refs or busy(staged, opened):
            raise Unsafe('Staged artifact now referenced or open')
        manifest = evidence / 'files' / SECTIONS[section][0]
        if not manifest.is_file() or hashlib.sha256(manifest.read_bytes()).hexdigest() != journal['manifestSha256']:
            raise Unsafe('Recovery manifest unavailable')
        index = read_json(evidence / 'retirement-metadata.json')
        for record in index['files']:
            relative = Path(record['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise Unsafe('Invalid metadata backup path')
            archived = evidence / 'files' / relative
            if archived.is_symlink() or not archived.is_file() or hashlib.sha256(archived.read_bytes()).hexdigest() != record['sha256']:
                raise Unsafe('Recovery metadata unavailable')
        expected = journal.get('fileInventory')
        if not isinstance(expected, dict):
            raise Unsafe('Recovery file inventory unavailable')
        for base, dirs, files in os.walk(staged, followlinks=False):
            parent = Path(base)
            if any((parent / name).is_symlink() for name in dirs + files):
                raise Unsafe('Staged tree changed to contain symlinks')
            for name in files:
                file = parent / name; info = file.stat()
                if expected.get(str(file.relative_to(staged))) != [info.st_size, info.st_mtime_ns]:
                    raise Unsafe('Staged payload changed after retirement was prepared')
            parent.chmod(stat.S_IMODE(parent.stat().st_mode) | stat.S_IWUSR)
        shutil.rmtree(staged)
        journal['state'] = 'retired'; save(state / 'receipts' / (section + '-' + identity + '.json'), journal)
    elif not source.exists():
        journal['state'] = 'retired'; save(state / 'receipts' / (section + '-' + identity + '.json'), journal)


def retire(row, home, root, state, cutoff):
    path = row['path']; identity = path.name; section = path.parent.name
    if path.parent.parent != root or section not in SECTIONS or not IDENTITY.fullmatch(identity):
        raise Unsafe('Artifact outside retirement scope')
    files = inspect(path, cutoff)
    manifest = path / row['manifest']; digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    backup(row, state / 'evidence' / section / identity, files)
    if not completed(row['tags']):
        raise Unsafe('Owning issue no longer completed')
    refs = references(home, root); opened = open_paths()
    if needed(row, inventory(root), refs, opened):
        raise Unsafe('Artifact is now referenced or open')
    if inspect(path, cutoff) != files:
        raise Unsafe('Artifact changed during backup')
    staged = root / '.retirement-staging' / section / identity
    safe_directory(staged.parent)
    if staged.parent.resolve() != staged.parent.absolute() or staged.exists():
        raise Unsafe('Retirement staging conflict')
    journal = {'identity': identity, 'section': section, 'state': 'prepared',
               'manifestSha256': digest, 'owners': row['tags'],
               'allocatedBytesBefore': sum(f[3] for f in files), 'preparedAt': time.time(),
               'fileInventory': {str(f.relative_to(path)): [size, modified] for f, size, modified, allocated in files}}
    receipt = state / 'receipts' / (section + '-' + identity + '.json')
    save(receipt, journal)
    path.chmod(stat.S_IMODE(path.stat().st_mode) | stat.S_IWUSR)
    path.rename(staged)
    journal['state'] = 'staged'; save(receipt, journal)
    remove_staged(root, state, journal, refs, open_paths())
    return journal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--minimum-age-days', type=float, default=14)
    parser.add_argument('--max-items', type=int, default=30)
    parser.add_argument('--home', type=Path, default=Path.home())
    args = parser.parse_args(argv)
    if not math.isfinite(args.minimum_age_days) or args.minimum_age_days < 7 or not 1 <= args.max_items <= 100:
        parser.error('minimum age must be >=7 days and max items 1..100')
    home = args.home.resolve(); root = home / 'projects/axon-release-production-prep'
    state = home / '.local/state/axon-release-retirement'
    safe_directory(state)
    if state.resolve() != state.absolute() or root.resolve() != root.absolute():
        raise Unsafe('Retirement root or state directory is symlinked')
    with (state / 'run.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Release retirement already running'); return 0
        report = {'schemaVersion': 1, 'apply': args.apply, 'startedAt': time.time(),
                  'beforeFreeBytes': shutil.disk_usage(home).free, 'items': []}
        try:
            refs = references(home, root); opened = open_paths()
            recovered = 0
            for receipt in sorted((state / 'receipts').glob('*.json')):
                journal = read_json(receipt)
                if args.apply and journal['state'] in ['prepared', 'staged'] and recovered < args.max_items:
                    staged = root / '.retirement-staging' / journal['section'] / journal['identity']
                    if staged.exists():
                        remove_staged(root, state, journal, refs, open_paths())
                        recovered += 1
            cutoff = time.time() - args.minimum_age_days * 86400
            report['recoveredCount'] = recovered
            rows = inventory(root); selected = []; owner_cache = {}
            for row in sorted(rows.values(), key=lambda r: str(r['path'])):
                if len(selected) + recovered >= args.max_items:
                    break
                if needed(row, rows, refs, opened):
                    continue
                try:
                    inspect(row['path'], cutoff)
                except Unsafe:
                    continue
                if completed(row['tags'], owner_cache):
                    selected.append(row)
            report['candidateCount'] = len(selected)
            for row in selected:
                if args.apply:
                    report['items'].append(retire(row, home, root, state, cutoff))
                else:
                    report['items'].append({'identity': row['path'].name, 'section': row['path'].parent.name, 'state': 'preview'})
                save(state / 'last-run.json', report)
        except Exception as error:
            report['error'] = str(error) if isinstance(error, Unsafe) else type(error).__name__
        report['afterFreeBytes'] = shutil.disk_usage(home).free
        save(state / 'last-run.json', report)
        save(state / 'reports' / (time.strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex + '.json'), report)
        print(json.dumps({k: v for k, v in report.items() if k != 'items'}))
        return 1 if report.get('error') else 0


if __name__ == '__main__':
    raise SystemExit(main())
