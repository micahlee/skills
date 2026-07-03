#!/usr/bin/env python3
"""Create local configuration for the process-inbox skill."""

from __future__ import annotations

import json
import os
from pathlib import Path


CONFIG_PATH = Path.home() / ".config" / "agent-skills" / "process-inbox.json"


def ask(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def main() -> None:
    default_vault = Path.home() / "Micah's Vault"
    vault_path = ask("Obsidian vault path", str(default_vault))

    config = {
        "vault_path": vault_path,
        "timezone": ask("Timezone", "America/New_York"),
        "inbox_path": ask("Inbox path relative to vault", "Inbox.md"),
        "processing_log_path": ask(
            "Processing log path relative to vault",
            "Inbox Processing Log.md",
        ),
        "daily_note_pattern": ask(
            "Daily note pattern relative to vault",
            "Daily Notes/YYYY/MM/YYYY-MM-DD.md",
        ),
        "daily_note_template_path": ask(
            "Daily note template path relative to vault",
            "Templates/DailyNote.md",
        ),
        "default_calendar_id": ask("Default Google Calendar ID", "primary"),
        "run_limit": int(ask("Automation run limit", "25")),
        "destination_paths": {
            "general_backlog": ask("General backlog path", "Tasks/Backlog.md"),
            "read_later": ask(
                "Read later path",
                "01 - PERSONAL/03 - RESOURCES/Read later.md",
            ),
            "reading_list": ask(
                "Reading list path",
                "01 - PERSONAL/02 - AREAS/Reading List.md",
            ),
            "someday_maybe": ask(
                "Someday/Maybe path",
                "01 - PERSONAL/03 - RESOURCES/Someday-Maybe.md",
            ),
            "gift_ideas": ask(
                "Gift ideas path",
                "01 - PERSONAL/03 - RESOURCES/Gift Ideas.md",
            ),
            "people_note": ask(
                "People note path",
                "01 - PERSONAL/02 - AREAS/People I've Met.md",
            ),
            "shopping_dir": ask("Shopping list directory", "Tasks/Shopping"),
        },
        "destination_roots": {
            "personal_projects": ask(
                "Personal projects directory",
                "01 - PERSONAL/01 - PROJECTS",
            ),
            "church_projects": ask(
                "Church projects directory",
                "02 - CHURCH/01 - PROJECTS",
            ),
            "personal_areas": ask(
                "Personal areas directory",
                "01 - PERSONAL/02 - AREAS",
            ),
            "personal_resources": ask(
                "Personal resources directory",
                "01 - PERSONAL/03 - RESOURCES",
            ),
        },
        "excluded_destination_roots": [
            "01 - PERSONAL/04 - ARCHIVE",
            "Completed",
        ],
        "tags": {
            "ambiguous": "#inbox/ambiguous",
            "failed": "#inbox/failed",
            "duplicate": "#inbox/duplicate",
        },
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    os.chmod(CONFIG_PATH, 0o600)
    print(f"Wrote {CONFIG_PATH}")


if __name__ == "__main__":
    main()
