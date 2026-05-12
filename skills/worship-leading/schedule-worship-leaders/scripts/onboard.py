#!/usr/bin/env python3
import json
import os
from pathlib import Path

SKILL_NAME = "schedule-worship-leaders"
QUESTIONS = [
    ("sunday_worship_service_type_id", "Planning Center Sunday worship service type ID"),
    ("service_responsibilities_team_id", "Planning Center Service Responsibilities / Music Lead team ID"),
    ("band_team_id", "Planning Center Band team ID"),
    ("leader_roster", "Worship leader roster as JSON array with person_id, name, instrument", "[]"),
    ("leader_rotation", "Repeating leader rotation as JSON array of names", "[]"),
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
    print("Use this config to replace placeholders in the schedule-worship-leaders skill.")


if __name__ == "__main__":
    main()

