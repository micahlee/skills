#!/usr/bin/env python3
import json
import os
from pathlib import Path

SKILL_NAME = "monarch-money"
QUESTIONS = [
    ("mmoney_cli", "Monarch Money CLI command name", "mmoney"),
    ("output_format", "Preferred structured output format", "json"),
    ("default_lookback_days", "Default transaction lookback window in days", "90"),
    ("timezone", "Timezone for date windows", "America/New_York"),
    ("privacy_level", "Privacy level for summaries (compact, normal, detailed)", "normal"),
]


def ask(prompt, default=""):
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
    for key, prompt, default_value in QUESTIONS:
        default = existing.get(key, default_value)
        config[key] = ask(prompt, default)

    path.write_text(json.dumps(config, indent=2) + "\n")
    path.chmod(0o600)
    print(f"Wrote {path}")
    print("This file stores local preferences only. Keep Monarch credentials in mmoney auth/config, not in this skill config.")


if __name__ == "__main__":
    main()
