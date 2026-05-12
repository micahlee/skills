#!/usr/bin/env python3
import json
import os
from pathlib import Path

SKILL_NAME = "schedule-music-team"
QUESTIONS = [
    ("band_team_id", "Planning Center Band team ID"),
    ("service_responsibilities_team_id", "Planning Center Service Responsibilities / Music Lead team ID"),
    ("music_month_command", "Command to show monthly music overview", "pco music month <YYYY-MM>"),
    ("enable_signups_command", "Command template to enable sign-ups", "pco enable-signups <plan_id>"),
    ("band_roster", "Band roster as JSON array with person_id, name, positions", "[]"),
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
    print("Use this config to replace placeholders in the schedule-music-team skill.")


if __name__ == "__main__":
    main()

