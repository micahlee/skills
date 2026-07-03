#!/usr/bin/env python3
import json
import os
from pathlib import Path

SKILL_NAME = "morning-briefing"
QUESTIONS = [
    ("vault_path", "Obsidian vault path", "~/vault"),
    ("daily_note_pattern", "Daily note path pattern relative to vault", "Daily Notes/YYYY/MM/YYYY-MM-DD.md"),
    ("daily_template_path", "Daily note template path relative to vault", "Templates/DailyNote.md"),
    ("event_outbox_path", "Morning Briefing event outbox path relative to vault", "Tasks/Morning Briefing Event Outbox.jsonl"),
    ("run_log_folder", "Morning Briefing run log folder relative to vault", "Tasks/Morning Briefing Runs"),
    ("timezone", "Local timezone", "America/New_York"),
    ("context_portfolio_paths", "Comma-separated context portfolio paths relative to vault", ""),
    ("interim_goal_paths", "Comma-separated interim goal paths relative to vault", "01 - PERSONAL/01 - PROJECTS/14-Day Eating Audit/nutrition-goals.md"),
    ("calendar_command", "Optional calendar command template", "gws calendar events list --params '{\"calendarId\":\"primary\",\"timeMin\":\"{start_rfc3339}\",\"timeMax\":\"{end_rfc3339}\",\"singleEvents\":true,\"orderBy\":\"startTime\"}' --format json"),
    ("email_command", "Optional email/inbox summary command", ""),
    ("weather_command", "Optional weather/logistics command", ""),
    ("health_summary_command", "Optional health/food/fitness summary command", ""),
    ("axon_events_command", "Optional Axon event query command", ""),
    ("telegram_send_policy", "Telegram send policy", "send_mode_axon_event"),
    ("axon_event_publish_profile", "Axon CLI profile for publishing briefing events", "morning-briefing-events"),
    ("boundaries", "Briefing boundaries or exclusions to respect", ""),
]


def ask(key, prompt, default=""):
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def normalize_value(key, value):
    if key in {"context_portfolio_paths", "interim_goal_paths"}:
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


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
        existing_value = existing.get(key)
        if isinstance(existing_value, list):
            existing_value = ", ".join(existing_value)
        default = existing_value if existing_value is not None else (rest[0] if rest else "")
        config[key] = normalize_value(key, ask(key, prompt, default))

    path.write_text(json.dumps(config, indent=2) + "\n")
    path.chmod(0o600)
    print(f"Wrote {path}")
    print("Use this config before running morning-briefing.")


if __name__ == "__main__":
    main()
