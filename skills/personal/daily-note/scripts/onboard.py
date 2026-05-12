#!/usr/bin/env python3
import json
import os
from pathlib import Path

SKILL_NAME = "daily-note"
QUESTIONS = [
    ("vault_path", "Obsidian vault path", "~/vault"),
    ("daily_note_pattern", "Daily note path pattern relative to vault", "Daily Notes/YYYY/MM/YYYY-MM-DD.md"),
    ("recurring_tasks_note", "Recurring tasks note path relative to vault", "Tasks/Recurring.md"),
    ("backlog_note", "Backlog note path relative to vault", "Tasks/Backlog.md"),
    ("projects_folder", "Projects folder path relative to vault", "01 - PERSONAL/01 - PROJECTS"),
    ("external_tasks_command", "Optional external task command template", ""),
    ("boundaries", "Task boundaries or exclusions to respect", ""),
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
    print("Use this config to replace placeholders in the daily-note skill.")


if __name__ == "__main__":
    main()

