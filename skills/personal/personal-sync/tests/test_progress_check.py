#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "progress_check.py"
SPEC = importlib.util.spec_from_file_location("progress_check", MODULE_PATH)
progress_check = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["progress_check"] = progress_check
SPEC.loader.exec_module(progress_check)


def main() -> int:
    test_midday_must_risk_requires_nudge()
    test_clean_heading_must_risk_requires_nudge()
    test_completed_must_is_no_nudge()
    test_afternoon_due_today_risk()
    test_weekend_could_task_does_not_nudge()
    test_data_unavailable_first_then_persistent()
    test_sent_dedupe_key_suppresses_duplicate()
    test_event_payload_requires_generated_message()
    print("progress-check tests passed")
    return 0


def test_midday_must_risk_requires_nudge() -> None:
    with fixture("2026-06-18", focus_must("- [ ] Write first draft <!-- task-ref: t1 -->")) as env:
        result = analyze(env, "midday")
    assert result["status"] == "nudge_required", result
    assert result["category"] == "must", result
    assert result["task_refs"][0]["task_id"] == "t1", result
    assert result["task_refs"][0]["priority"] == "must", result


def test_clean_heading_must_risk_requires_nudge() -> None:
    with fixture("2026-06-18", focus_must("- [ ] Write first draft"), legacy_markers=False) as env:
        result = analyze(env, "midday")
    assert result["status"] == "nudge_required", result
    assert result["category"] == "must", result
    assert result["task_refs"][0]["priority"] == "must", result
    assert result["task_refs"][0]["task_id"].startswith("daily-note:"), result


def test_completed_must_is_no_nudge() -> None:
    with fixture("2026-06-18", focus_must("- [x] Write first draft <!-- task-ref: t1 -->")) as env:
        result = analyze(env, "midday")
    assert result["status"] == "no_nudge", result


def test_afternoon_due_today_risk() -> None:
    with fixture("2026-06-18", focus_should("- [ ] File paperwork due 2026-06-18 <!-- task-ref: due1 -->")) as env:
        result = analyze(env, "afternoon")
    assert result["status"] == "nudge_required", result
    assert result["category"] == "due-today", result
    assert result["task_refs"][0]["task_id"] == "due1", result


def test_weekend_could_task_does_not_nudge() -> None:
    with fixture("2026-06-20", focus_could("- [ ] Organize bookmarks <!-- task-ref: c1 -->")) as env:
        result = analyze(env, "midday")
    assert result["status"] == "no_nudge", result


def test_data_unavailable_first_then_persistent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = write_config(root, "2026-06-18")
        state = root / "state.json"
        first = progress_check.analyze_checkpoint("midday", "2026-06-18", config, state)
        second = progress_check.analyze_checkpoint("afternoon", "2026-06-18", config, state)
    assert first["status"] == "data_unavailable_first", first
    assert second["status"] == "nudge_required", second
    assert second["category"] == "task-data-unavailable", second


def test_sent_dedupe_key_suppresses_duplicate() -> None:
    with fixture("2026-06-18", focus_must("- [ ] Write first draft <!-- task-ref: t1 -->")) as env:
        env.state.write_text(json.dumps({"sent_dedupe_keys": ["2026-06-18:midday:must"]}), encoding="utf-8")
        result = analyze(env, "midday")
    assert result["status"] == "duplicate", result


def test_event_payload_requires_generated_message() -> None:
    analysis = {
        "status": "nudge_required",
        "checkpoint": "midday",
        "local_date": "2026-06-18",
        "generated_at": "2026-06-18T12:30:00-04:00",
        "category": "must",
        "severity": "medium",
        "dedupe_key": "2026-06-18:midday:must",
        "task_refs": [],
    }
    try:
        progress_check.build_event_payload(analysis, "")
    except ValueError:
        pass
    else:
        raise AssertionError("empty message should not build an event payload")
    payload = progress_check.build_event_payload(analysis, "Start the draft with three bullets.")
    assert payload["message"] == "Start the draft with three bullets.", payload
    assert payload["source"] == "personal-sync", payload


class fixture:
    def __init__(self, local_date: str, body: str, legacy_markers: bool = True) -> None:
        self.local_date = local_date
        self.body = body
        self.legacy_markers = legacy_markers

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.config = write_config(root, self.local_date)
        self.state = root / "state.json"
        note = root / "vault" / "Daily Notes" / self.local_date[:4] / self.local_date[5:7] / f"{self.local_date}.md"
        note.parent.mkdir(parents=True)
        lines = ["# Daily Note", "", "## Focus Tasks"]
        if self.legacy_markers:
            lines.append("<!-- daily-note:focus:start -->")
        lines.append(self.body)
        if self.legacy_markers:
            lines.append("<!-- daily-note:focus:end -->")
        lines.append("")
        note.write_text("\n".join(lines), encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.tmp.cleanup()


def write_config(root: Path, local_date: str) -> Path:
    _ = local_date
    config = root / "config.json"
    config.write_text(
        json.dumps(
            {
                "vault_path": str(root / "vault"),
                "daily_note_pattern": "Daily Notes/YYYY/MM/YYYY-MM-DD.md",
                "timezone": "America/New_York",
                "state_path": str(root / "state.json"),
            }
        ),
        encoding="utf-8",
    )
    return config


def analyze(env: fixture, checkpoint: str) -> dict:
    return progress_check.analyze_checkpoint(checkpoint, env.local_date, env.config, env.state)


def focus_must(line: str) -> str:
    return "### Must\n" + line


def focus_should(line: str) -> str:
    return "### Should\n" + line


def focus_could(line: str) -> str:
    return "### Could\n" + line


if __name__ == "__main__":
    raise SystemExit(main())
