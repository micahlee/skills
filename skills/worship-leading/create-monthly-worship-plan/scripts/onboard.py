#!/usr/bin/env python3
import json
import os
from pathlib import Path

SKILL_NAME = "create-monthly-worship-plan"
QUESTIONS = [
    ("basecamp_account_id", "Basecamp account ID"),
    ("basecamp_project_id", "Basecamp worship ministry project ID"),
    ("basecamp_todoset_id", "Basecamp todoset ID"),
    ("core_class_assignee_id", "Fixed assignee ID for core class tasks, if any", ""),
    ("known_leaders", "Known monthly leaders as JSON array with name, basecamp_person_id, first_name", "[]"),
    ("leader_pattern", "Optional alternating leader pattern as JSON array of first names", "[]"),
]


def ask(key, prompt, default=""):
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def main():
    config_dir = Path(os.environ.get("AGENT_SKILLS_CONFIG_DIR", Path.home() / ".config" / "agent-skills"))
    config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = config_dir / f"{SKILL_NAME}.json"

    existing = {}
    if path.exists():
        existing = json.loads(path.read_text())

    config = {}
    for item in QUESTIONS:
        key, prompt, *rest = item
        default = existing.get(key, rest[0] if rest else "")
        config[key] = ask(key, prompt, default)

    path.write_text(json.dumps(config, indent=2) + "\n")
    path.chmod(0o600)
    print(f"Wrote {path}")
    print("Use this config to replace placeholders in the create-monthly-worship-plan skill.")


if __name__ == "__main__":
    main()

