#!/usr/bin/env python3
"""Preview or install skills from a clean origin/main checkout without overwriting."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess


EXTERNAL_OWNERS = {'fitness-coach': 'micahlee/axon-personal config/codex-training-skills'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Apply the preview; otherwise read-only.')
    parser.add_argument('--skill', action='append', default=[], help='Install only this folder name; repeatable.')
    parser.add_argument('--destination', type=Path, default=Path.home() / '.agents/skills')
    parser.add_argument('--rules', action='store_true', help='Also install rules/CODEX-AGENTS.md as global Codex AGENTS.md.')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    skills = {p.parent.name: p.parent for p in sorted((repo / 'skills').rglob('SKILL.md'))}
    unknown = sorted(set(args.skill) - skills.keys())
    if unknown:
        parser.error('Unknown skills: ' + ', '.join(unknown))
    external = sorted(set(args.skill) & EXTERNAL_OWNERS.keys())
    if external:
        parser.error('Install from its managed source instead: ' + ', '.join(f'{name}: {EXTERNAL_OWNERS[name]}' for name in external))
    names = sorted(set(args.skill)) if args.skill else sorted(skills.keys() - EXTERNAL_OWNERS.keys())
    for name in sorted(skills.keys() & EXTERNAL_OWNERS.keys()):
        if not args.skill:
            print(f'EXTERNAL {name}: install through {EXTERNAL_OWNERS[name]}')
    destination = args.destination.expanduser().absolute()
    actions = []
    conflicts = []
    home = Path.home()
    roots = {home / '.agents/skills', Path(os.environ.get('CODEX_HOME', str(home / '.codex'))) / 'skills'}
    for name in names:
        source = skills[name]
        target = destination / name
        # Both locations are discoverable by Codex: avoid creating a second owner.
        if destination in roots:
            for other in roots - {destination}:
                existing = other / name
                if existing.exists() or existing.is_symlink():
                    if existing.is_symlink() and existing.resolve() == source:
                        target = existing
                    else:
                        conflicts.append(f'{name}: also installed at {existing}; reconcile its owner first')
        if target.is_symlink() and target.resolve() == source:
            print(f'OK {name}: {target}')
        elif target.exists() or target.is_symlink():
            conflicts.append(f'{name}: preserve existing {target}; compare before replacing')
        else:
            actions.append(('link', source, target))
    if args.rules:
        source = repo / 'rules/CODEX-AGENTS.md'
        target = Path(os.environ.get('CODEX_HOME', str(home / '.codex'))) / 'AGENTS.md'
        if target.is_symlink():
            conflicts.append(f'Preserve existing rules symlink: {target}')
        elif target.exists():
            if target.is_file() and target.read_bytes() == source.read_bytes():
                print(f'OK rules: {target}')
            else:
                conflicts.append(f'Preserve existing rules: compare {target} with {source}')
        else:
            actions.append(('copy', source, target))
    for kind, source, target in actions:
        print(f'{kind.upper()} {source.relative_to(repo)} -> {target}')
    if conflicts:
        for conflict in conflicts:
            print(f'CONFLICT {conflict}')
        print('No files changed. Resolve conflicts and rerun the preview.')
        return 1
    if not args.apply:
        print('Preview only. Rerun with --apply after reviewing.')
        return 0
    def git(*arguments: str) -> str:
        return subprocess.check_output(['git', '-C', str(repo), *arguments], text=True).strip()
    try:
        if git('status', '--porcelain') or git('rev-parse', 'HEAD') != git('rev-parse', 'origin/main'):
            print('Refusing installation: fetch origin/main and use a clean checkout at that exact commit.')
            return 1
    except subprocess.CalledProcessError:
        print('Refusing installation: clean origin/main provenance is unavailable.')
        return 1
    for kind, source, target in actions:
        target.parent.mkdir(parents=True, exist_ok=True)
        if kind == 'link':
            target.symlink_to(source, target_is_directory=True)
        else:
            # Exclusive creation preserves a concurrently-created rules file.
            with target.open('xb') as output, source.open('rb') as input_file:
                shutil.copyfileobj(input_file, output)
            target.chmod(0o600)
    print(f'Installed {len(actions)} entries; existing entries preserved.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
