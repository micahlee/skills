#!/usr/bin/env python3
import json
import os
from pathlib import Path

SKILL_NAME = "schedule-songs"
QUESTIONS = [
    ("sunday_worship_service_type_id", "Planning Center Sunday worship service type ID"),
    ("song_history_weeks", "How many weeks of song history to inspect", "20"),
    ("default_service_name", "Default service type name", "Sunday Morning Worship"),
    ("google_doc_read_command", "Command template to read a Google Doc", "gws doc read <doc_id>"),
    ("basecamp_message_read_command", "Command template to read a Basecamp message", "basecamp message read <message_id>"),
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
    print("Use this config to replace placeholders in the schedule-songs skill.")


if __name__ == "__main__":
    main()

