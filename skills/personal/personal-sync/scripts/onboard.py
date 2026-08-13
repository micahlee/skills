#!/usr/bin/env python3
"""Create unified Personal Sync configuration, importing legacy defaults."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(os.environ.get("AGENT_SKILLS_CONFIG_DIR", Path.home() / ".config" / "agent-skills"))
TARGET = CONFIG_DIR / "personal-sync.json"
LEGACY = ("daily-note.json", "daily-dream.json", "morning-briefing.json", "progress-check.json")
SHARED_IMPORT_KEYS = {
    "vault_path",
    "vault_name",
    "timezone",
    "daily_note_pattern",
    "recurring_tasks_note",
    "backlog_note",
    "planning_note_cli",
    "external_tasks_command",
    "scheduled_external_tasks_command",
    "calendar_command",
    "scheduled_calendar_command",
    "email_command",
    "health_summary_command",
    "weather_command",
    "axon_events_command",
    "boundaries",
}

DEFAULTS: dict[str, Any] = {
    "vault_path": "~/vault",
    "vault_name": "",
    "timezone": "America/New_York",
    "daily_note_pattern": "Daily Notes/YYYY/MM/YYYY-MM-DD.md",
    "weekly_note_pattern": "Weekly Notes/YYYY/YYYY-Www.md",
    "agent_daily_pattern": "Agent Context/Daily/YYYY/MM/YYYY-MM-DD.md",
    "agent_weekly_pattern": "Agent Context/Weekly/YYYY/YYYY-Www.md",
    "recurring_tasks_note": "Tasks/Recurring.md",
    "backlog_note": "Tasks/Backlog.md",
    "projects_folders": ["01 - PERSONAL/01 - PROJECTS", "02 - CHURCH/01 - PROJECTS"],
    "goal_paths": [],
    "inbox_path": "Inbox.md",
    "task_registry_path": "Tasks/Personal Sync State.json",
    "daily_note_state_folder": "Tasks/Personal Sync State",
    "event_outbox_path": "Tasks/Personal Sync Event Outbox.jsonl",
    "run_log_folder": "Tasks/Personal Sync Runs",
    "planning_note_cli": "",
    "external_tasks_command": "basecamp assignments --agent",
    "scheduled_external_tasks_command": "",
    "calendar_command": "",
    "scheduled_calendar_command": "",
    "email_command": "",
    "health_summary_command": "",
    "weather_command": "",
    "planning_center_command": "",
    "meal_plan_command": "",
    "axon_events_command": "",
    "axon_briefing_publish_profile": "morning-briefing-events",
    "axon_progress_publish_profile": "progress-check-nudges",
    "boundaries": "",
}

PROMPTS = {
    "vault_path": "Obsidian vault path",
    "vault_name": "Obsidian vault name",
    "timezone": "Local timezone",
    "daily_note_pattern": "Human planning-note path pattern",
    "weekly_note_pattern": "Human weekly-note path pattern",
    "agent_daily_pattern": "Agent daily-context path pattern",
    "agent_weekly_pattern": "Agent weekly-context path pattern",
    "recurring_tasks_note": "Recurring task source",
    "backlog_note": "Backlog task source",
    "projects_folders": "Project roots (comma-separated)",
    "goal_paths": "Authoritative goal/current-season notes (comma-separated)",
    "inbox_path": "Obsidian Inbox path",
    "planning_note_cli": "Planning Notes CLI script path",
    "external_tasks_command": "External assigned-task command",
    "scheduled_external_tasks_command": "Scheduled-safe assigned-task command",
    "calendar_command": "Calendar command template",
    "scheduled_calendar_command": "Scheduled-safe calendar command",
    "email_command": "Email/inbox summary command",
    "health_summary_command": "Health/fitness summary command",
    "weather_command": "Weather/logistics summary command",
    "planning_center_command": "Planning Center summary command",
    "meal_plan_command": "Meal-plan summary command",
    "axon_events_command": "Axon event query command",
    "boundaries": "Privacy, source, or task boundaries",
}


def read_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def merged_defaults() -> dict[str, Any]:
    result = dict(DEFAULTS)
    for name in LEGACY:
        for key, value in read_object(CONFIG_DIR / name).items():
            if key in SHARED_IMPORT_KEYS and value not in ("", None, []):
                result[key] = value
    daily = read_object(CONFIG_DIR / "daily-note.json")
    project = daily.get("projects_folder")
    if isinstance(project, str) and project:
        result["projects_folders"] = list(dict.fromkeys([project, *DEFAULTS["projects_folders"]]))
    briefing = read_object(CONFIG_DIR / "morning-briefing.json")
    goals = briefing.get("context_portfolio_paths") or briefing.get("interim_goal_paths")
    if isinstance(goals, list) and goals:
        result["goal_paths"] = goals
    briefing_profile = briefing.get("axon_event_publish_profile")
    if isinstance(briefing_profile, str) and briefing_profile:
        result["axon_briefing_publish_profile"] = briefing_profile
    vault_path = result.get("vault_path")
    if not result.get("vault_name") and isinstance(vault_path, str) and vault_path:
        result["vault_name"] = Path(vault_path).expanduser().name
    return result


def normalized(key: str, value: str) -> Any:
    if key in {"projects_folders", "goal_paths"}:
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


def interactive(config: dict[str, Any]) -> dict[str, Any]:
    for key, prompt in PROMPTS.items():
        current = config.get(key, "")
        display = ", ".join(current) if isinstance(current, list) else str(current)
        suffix = f" [{display}]" if display else ""
        answer = input(f"{prompt}{suffix}: ").strip()
        config[key] = normalized(key, answer or display)
    return config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-existing", action="store_true", help="Write merged defaults without prompting.")
    parser.add_argument("--output", default=str(TARGET))
    args = parser.parse_args()

    config = merged_defaults()
    existing = read_object(Path(args.output).expanduser())
    config.update(existing)
    if not args.import_existing:
        config = interactive(config)

    output = Path(args.output).expanduser()
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    output.chmod(0o600)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
