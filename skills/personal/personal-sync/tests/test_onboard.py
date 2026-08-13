#!/usr/bin/env python3
"""Regression tests for Personal Sync onboarding configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "onboard.py"


class OnboardTests(unittest.TestCase):
    def run_onboard(self, config_dir: Path, output: Path) -> dict[str, object]:
        env = dict(os.environ)
        env["AGENT_SKILLS_CONFIG_DIR"] = str(config_dir)
        subprocess.run(
            ["python3", str(SCRIPT), "--import-existing", "--output", str(output)],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_scheduled_commands_are_present_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            config_dir = Path(raw_dir)
            config = self.run_onboard(config_dir, config_dir / "personal-sync.json")

        self.assertEqual(config["scheduled_calendar_command"], "")
        self.assertEqual(config["scheduled_external_tasks_command"], "")
        self.assertEqual(config["external_tasks_command"], "basecamp assignments --agent")

    def test_scheduled_commands_import_from_legacy_config(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            config_dir = Path(raw_dir)
            (config_dir / "daily-note.json").write_text(
                json.dumps(
                    {
                        "scheduled_calendar_command": "axon events tail --type calendar.snapshot",
                        "scheduled_external_tasks_command": "axon events tail --type tasks.snapshot",
                    }
                ),
                encoding="utf-8",
            )
            config = self.run_onboard(config_dir, config_dir / "personal-sync.json")

        self.assertEqual(
            config["scheduled_calendar_command"],
            "axon events tail --type calendar.snapshot",
        )
        self.assertEqual(
            config["scheduled_external_tasks_command"],
            "axon events tail --type tasks.snapshot",
        )


if __name__ == "__main__":
    unittest.main()
