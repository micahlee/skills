#!/usr/bin/env python3
import json
import os
from pathlib import Path

SKILL_NAME = "daily-dream"
QUESTIONS = [
    ("vault_path", "Obsidian vault path", "~/vault"),
    ("daily_note_pattern", "Daily note path pattern relative to vault", "Daily Notes/YYYY/MM/YYYY-MM-DD.md"),
    ("monthly_note_pattern", "Monthly note path pattern relative to vault", "Daily Notes/YYYY/MM/MM.md"),
    ("daily_template_path", "Daily note template path relative to vault", "Templates/DailyNote.md"),
    ("month_template_path", "Month note template path relative to vault", "Templates/Month.md"),
    ("event_outbox_path", "Dream event outbox path relative to vault", "Tasks/Dream Event Outbox.jsonl"),
    ("run_log_folder", "Dream run log folder relative to vault", "Tasks/Dream Runs"),
    ("google_workspace_command", "Optional Google Workspace CLI command", "gws"),
    ("axon_events_command", "Optional Axon event query command", ""),
    ("health_summary_command", "Optional health/fitness summary command", ""),
    ("boundaries", "Reflection/source boundaries or exclusions to respect", ""),
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
    print("Use this config before running daily-dream synthesis.")


if __name__ == "__main__":
    main()
