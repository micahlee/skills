#!/bin/sh
set -eu

preferred_cli=/Users/micahlee/.local/bin/classreach
if [ -x "$preferred_cli" ]; then
  cli_path=$preferred_cli
elif command -v classreach >/dev/null 2>&1; then
  cli_path=$(command -v classreach)
else
  echo "ERROR: classreach is not installed or is not on PATH." >&2
  exit 1
fi

cli_version=$("$cli_path" --version 2>&1)

printf 'ClassReach CLI: %s\n' "$cli_path"
printf 'Version: %s\n' "$cli_version"

if ! "$cli_path" prep agenda --help >/dev/null 2>&1; then
  echo "ERROR: this ClassReach CLI does not expose 'prep agenda'. Update the CLI before preparing agendas." >&2
  exit 1
fi

if ! "$cli_path" agenda week --help >/dev/null 2>&1; then
  echo "ERROR: this ClassReach CLI does not expose 'agenda week'. Update the CLI before preparing agendas." >&2
  exit 1
fi

if ! "$cli_path" students list --help >/dev/null 2>&1; then
  echo "ERROR: this ClassReach CLI does not expose 'students list'. Update the CLI before preparing agendas." >&2
  exit 1
fi

if ! "$cli_path" messages list --help >/dev/null 2>&1; then
  echo "ERROR: this ClassReach CLI does not expose 'messages list'. Update the CLI before preparing agendas." >&2
  exit 1
fi

echo "ClassReach CLI preflight passed."
