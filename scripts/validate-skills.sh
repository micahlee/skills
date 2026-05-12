#!/usr/bin/env bash
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo"

fail=0
names_file="$(mktemp)"
manifest_skills_file="$(mktemp)"
found_skills_file="$(mktemp)"
trap 'rm -f "$names_file" "$manifest_skills_file" "$found_skills_file"' EXIT

error() {
  local file="$1"
  local message="$2"
  echo "::error file=$file::$message"
  fail=1
}

if [ ! -d skills ]; then
  echo "::error::Missing skills directory"
  exit 1
fi

while IFS= read -r skill_file; do
  skill_dir="$(dirname "$skill_file")"
  skill_name="$(basename "$skill_dir")"
  echo "$skill_name" >> "$names_file"

  case "$skill_name" in
    ""|"-"*|*"-"|*"--"*|*[!a-z0-9-]*)
      error "$skill_file" "Skill folder must be lowercase hyphen-case: $skill_name"
      ;;
  esac

  if [ "$(sed -n '1p' "$skill_file")" != "---" ]; then
    error "$skill_file" "SKILL.md must start with YAML frontmatter"
    continue
  fi

  frontmatter_end="$(awk 'NR > 1 && $0 == "---" { print NR; exit }' "$skill_file")"
  if [ -z "$frontmatter_end" ]; then
    error "$skill_file" "SKILL.md frontmatter must close with ---"
    continue
  fi

  if ! sed -n "2,$((frontmatter_end - 1))p" "$skill_file" | grep -qx "name: $skill_name"; then
    error "$skill_file" "Frontmatter name must exactly match folder: name: $skill_name"
  fi

  if ! sed -n "2,$((frontmatter_end - 1))p" "$skill_file" | grep -Eq '^description: .{20,}$'; then
    error "$skill_file" "Frontmatter description must be present and descriptive"
  fi

  if [ -f "$skill_dir/README.md" ]; then
    error "$skill_dir/README.md" "Skill folders should keep instructions in SKILL.md, not README.md"
  fi

  if [ -f README.md ] && ! grep -Fq "\`$skill_name\`" README.md; then
    error "README.md" "README must list $skill_name"
  fi
done < <(find skills -mindepth 2 -maxdepth 3 -name SKILL.md -type f | sort)

find skills -mindepth 2 -maxdepth 3 -name SKILL.md -type f \
  | sed 's#/SKILL.md$##' \
  | sort > "$found_skills_file"

if [ ! -s "$names_file" ]; then
  echo "::error::No skills found"
  exit 1
fi

duplicates="$(sort "$names_file" | uniq -d)"
if [ -n "$duplicates" ]; then
  while IFS= read -r duplicate; do
    [ -n "$duplicate" ] && echo "::error::Duplicate skill name: $duplicate"
  done <<< "$duplicates"
  fail=1
fi

if [ -f .claude-plugin/plugin.json ]; then
  python3 - <<'PY' > "$manifest_skills_file"
import json

with open(".claude-plugin/plugin.json", encoding="utf-8") as f:
    manifest = json.load(f)

for skill in manifest.get("skills", []):
    print(skill.removeprefix("./").rstrip("/"))
PY

  while IFS= read -r skill_dir; do
    if [ -z "$skill_dir" ]; then
      continue
    fi
    if [ ! -f "$skill_dir/SKILL.md" ]; then
      error ".claude-plugin/plugin.json" "Manifest skill path is missing SKILL.md: $skill_dir"
    fi
  done < "$manifest_skills_file"

  missing_manifest_entries="$(comm -23 "$found_skills_file" <(sort "$manifest_skills_file"))"
  if [ -n "$missing_manifest_entries" ]; then
    while IFS= read -r skill_dir; do
      [ -n "$skill_dir" ] && error ".claude-plugin/plugin.json" "Manifest missing skill path: ./$skill_dir"
    done <<< "$missing_manifest_entries"
  fi
fi

exit "$fail"
