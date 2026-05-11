#!/usr/bin/env bash
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

find "$repo/skills" \
  -name SKILL.md \
  -not -path '*/node_modules/*' \
  | sed "s|^$repo/||" \
  | sort

