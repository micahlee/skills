#!/usr/bin/env python3
"""Remove legacy automation scaffolding from a daily note.

The cleaner preserves section content while removing HTML marker lines and
inline hidden task refs. When --path is provided, it reads and writes through
the Obsidian CLI; otherwise it transforms stdin to stdout.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys


MARKER_LINE_RE = re.compile(
    r"^\s*<!--\s*(?:daily-note|daily-dream|morning-briefing):[a-z0-9_-]+(?::(?:start|end))?\s*-->\s*$",
    re.IGNORECASE,
)
TASK_REF_RE = re.compile(r"\s*<!--\s*task-ref:\s*.*?\s*-->")
PROCESSING_SUMMARY_RE = re.compile(r"^\s*Task processing:\s+.*$", re.IGNORECASE)
BLANK_RUN_RE = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if MARKER_LINE_RE.match(line) or PROCESSING_SUMMARY_RE.match(line):
            continue
        line = TASK_REF_RE.sub("", line).rstrip()
        lines.append(line)
    cleaned = "\n".join(lines).rstrip() + "\n"
    return BLANK_RUN_RE.sub("\n\n", cleaned)


def obsidian_read(path: str, vault: str) -> str:
    args = ["obsidian", "read", f"path={path}"]
    if vault:
        args.append(f"vault={vault}")
    return subprocess.check_output(args, text=True)


def obsidian_write(path: str, vault: str, content: str) -> None:
    args = ["obsidian", "create", f"path={path}", f"content={content}", "overwrite"]
    if vault:
        args.append(f"vault={vault}")
    subprocess.check_call(args)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", help="Daily note path inside the vault.")
    parser.add_argument("--vault", default="", help="Obsidian vault name.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if cleaning would change content.")
    args = parser.parse_args()

    original = obsidian_read(args.path, args.vault) if args.path else sys.stdin.read()
    cleaned = clean_text(original)

    if args.check:
        if cleaned != original:
            sys.stdout.write(cleaned)
            return 1
        return 0

    if args.path:
        if cleaned != original:
            obsidian_write(args.path, args.vault, cleaned)
        return 0

    sys.stdout.write(cleaned)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
