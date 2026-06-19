#!/usr/bin/env python3
"""Deterministic Daily Note progress-check helper."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.8 fallback.
    ZoneInfo = None  # type: ignore[assignment]


DEFAULT_CONFIG_PATH = Path("~/.config/agent-skills/progress-check.json").expanduser()
DAILY_NOTE_CONFIG_PATH = Path("~/.config/agent-skills/daily-note.json").expanduser()
DEFAULT_STATE_PATH = Path("~/.local/state/axon/progress-check.json").expanduser()
DEFAULT_TIMEZONE = "America/New_York"
EVENT_TYPE = "personal.progress-nudge.created"
DEFAULT_PROFILE = "progress-check-nudges"

TASK_RE = re.compile(r"^(?P<indent>\s*)[-*]\s+\[(?P<mark>[ xX])\]\s+(?P<body>.*)$")
HEADING_RE = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+?)\s*$")
BLOCK_START_RE = re.compile(r"<!--\s*daily-note:(?P<name>[a-z0-9_-]+):start\s*-->")
BLOCK_END_RE = re.compile(r"<!--\s*daily-note:(?P<name>[a-z0-9_-]+):end\s*-->")
TASK_REF_RE = re.compile(r"<!--\s*task-ref:\s*(?P<ref>.*?)\s*-->")
DATE_RE = re.compile(r"(?:📅|due:|due)\s*(?P<date>\d{4}-\d{2}-\d{2})", re.IGNORECASE)
PRIORITY_TAG_RE = re.compile(r"(?:^|\s)#?(?P<tag>must|should|could|p[1-4])(?:\b|:)", re.IGNORECASE)
TRIAGE_RE = re.compile(r"\b(deferred|snoozed|downgraded|resized|triaged|decided|intentionally)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Task:
    text: str
    completed: bool
    line: int
    source_path: str
    section: str
    block: str
    priority: str
    task_id: str
    due_date: str
    triaged: bool

    def ref(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "text": self.text,
            "priority": self.priority,
            "source_path": self.source_path,
            "section": self.section,
            "line": self.line,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--checkpoint", choices=("midday", "afternoon", "evening"), default="midday")
    analyze.add_argument("--date", dest="local_date", help="Local date in YYYY-MM-DD format.")
    analyze.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    analyze.add_argument("--state", default="")

    publish = subparsers.add_parser("publish")
    publish.add_argument("--analysis", required=True)
    publish.add_argument("--message", required=True)
    publish.add_argument("--profile", default="")
    publish.add_argument("--axon-bin", default="/Users/micahlee/.local/bin/axon")
    publish.add_argument("--state", default="")
    publish.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    if args.command == "analyze":
        result = analyze_checkpoint(args.checkpoint, args.local_date, Path(args.config).expanduser(), optional_path(args.state))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "publish":
        result = publish_nudge(Path(args.analysis), args.message, args.profile, args.axon_bin, optional_path(args.state), args.dry_run)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    return 64


def analyze_checkpoint(checkpoint: str, local_date_arg: str | None, config_path: Path, state_path_arg: Path | None) -> dict[str, Any]:
    config = load_config(config_path)
    timezone_name = string_value(config.get("timezone")) or DEFAULT_TIMEZONE
    local_date = local_date_arg or today_string(timezone_name)
    state_path = state_path_arg or Path(string_value(config.get("state_path")) or DEFAULT_STATE_PATH).expanduser()
    state = load_state(state_path)
    daily_note_path = resolve_daily_note_path(config, local_date)

    if not daily_note_path.exists():
        return data_unavailable(checkpoint, local_date, state_path, state, f"daily note not found: {daily_note_path}")

    try:
        text = daily_note_path.read_text(encoding="utf-8")
    except OSError as exc:
        return data_unavailable(checkpoint, local_date, state_path, state, str(exc))

    tasks = parse_tasks(text, daily_note_path)
    risk = score_risk(tasks, checkpoint, local_date, timezone_name)
    if risk is None:
        clear_data_failure(state, local_date, state_path)
        return {
            "schema_version": 1,
            "status": "no_nudge",
            "checkpoint": checkpoint,
            "local_date": local_date,
            "state_path": state_path.as_posix(),
            "task_count": len(tasks),
            "reason": "No high-priority daily commitment risk found.",
        }

    if risk["dedupe_key"] in sent_keys(state):
        return {
            "schema_version": 1,
            "status": "duplicate",
            "checkpoint": checkpoint,
            "local_date": local_date,
            "category": risk["category"],
            "state_path": state_path.as_posix(),
            "dedupe_key": risk["dedupe_key"],
            "reason": "A progress nudge for this category already exists today.",
        }

    clear_data_failure(state, local_date, state_path)
    return {
        "schema_version": 1,
        "status": "nudge_required",
        "checkpoint": checkpoint,
        "local_date": local_date,
        "generated_at": now_iso(timezone_name),
        "state_path": state_path.as_posix(),
        **risk,
    }


def score_risk(tasks: list[Task], checkpoint: str, local_date: str, timezone_name: str) -> dict[str, Any] | None:
    weekend = is_weekend(local_date, timezone_name)
    priority_tasks = [task for task in tasks if is_priority_task(task)]
    open_priority = [task for task in priority_tasks if not task.completed and not task.triaged]
    progressed_priority = [task for task in priority_tasks if task.completed or task.triaged]
    open_due_today = [task for task in tasks if task.due_date == local_date and not task.completed and not task.triaged]

    if checkpoint == "midday" and open_priority and not progressed_priority:
        return risk_payload("must", "medium", "No must/p1 tasks are complete or triaged by midday.", checkpoint, local_date, open_priority)
    if checkpoint == "afternoon" and open_due_today:
        return risk_payload("due-today", "medium", "A due-today task is still open late afternoon.", checkpoint, local_date, open_due_today)
    if checkpoint == "evening" and open_priority:
        return risk_payload("must", "high", "A must/p1 task remains open in the evening.", checkpoint, local_date, open_priority)

    if weekend:
        return None

    return None


def risk_payload(category: str, severity: str, explanation: str, checkpoint: str, local_date: str, tasks: list[Task]) -> dict[str, Any]:
    refs = [task.ref() for task in tasks[:3]]
    dedupe_key = f"{local_date}:{checkpoint}:{category}"
    seed = concrete_action_seed(tasks[0]) if tasks else "Choose one small next action."
    return {
        "category": category,
        "severity": severity,
        "risk_explanation": explanation,
        "suggested_action_seed": seed,
        "task_refs": refs,
        "dedupe_key": dedupe_key,
        "idempotency_key": f"progress-nudge:{local_date}:{checkpoint}:{category}",
        "subject": f"progress-check:{local_date}:{checkpoint}:{category}",
    }


def parse_tasks(text: str, path: Path) -> list[Task]:
    tasks: list[Task] = []
    headings: dict[int, str] = {}
    current_block = ""
    for index, line in enumerate(text.splitlines(), start=1):
        block_start = BLOCK_START_RE.search(line)
        if block_start:
            current_block = block_start.group("name")
        block_end = BLOCK_END_RE.search(line)
        if block_end and block_end.group("name") == current_block:
            current_block = ""
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group("level"))
            headings[level] = heading.group("title").strip()
            for existing in list(headings):
                if existing > level:
                    del headings[existing]
            continue
        match = TASK_RE.match(line)
        if not match:
            continue
        raw_body = match.group("body").strip()
        text_body = clean_task_text(raw_body)
        section = nearest_section(headings)
        priority = task_priority(text_body, section, current_block)
        task_id = task_ref(raw_body) or f"daily-note:{path.as_posix()}:{index}"
        due_date = task_due_date(raw_body)
        tasks.append(
            Task(
                text=text_body,
                completed=match.group("mark").lower() == "x",
                line=index,
                source_path=path.as_posix(),
                section=section,
                block=current_block,
                priority=priority,
                task_id=task_id,
                due_date=due_date,
                triaged=bool(TRIAGE_RE.search(text_body)),
            )
        )
    return tasks


def clean_task_text(raw: str) -> str:
    value = TASK_REF_RE.sub("", raw)
    value = re.sub(r"<!--.*?-->", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def nearest_section(headings: dict[int, str]) -> str:
    if not headings:
        return ""
    return " > ".join(headings[level] for level in sorted(headings))


def task_priority(text: str, section: str, block: str) -> str:
    section_tail = section.split(">")[-1].strip().lower()
    if block == "focus" and section_tail in {"must", "should", "could"}:
        return section_tail
    match = PRIORITY_TAG_RE.search(text)
    if match:
        return match.group("tag").lower()
    return ""


def task_ref(raw: str) -> str:
    match = TASK_REF_RE.search(raw)
    return match.group("ref").strip() if match else ""


def task_due_date(raw: str) -> str:
    match = DATE_RE.search(raw)
    return match.group("date") if match else ""


def is_priority_task(task: Task) -> bool:
    return task.priority in {"must", "p1"}


def concrete_action_seed(task: Task) -> str:
    text = task.text.rstrip(".")
    if len(text) > 100:
        text = text[:97].rstrip() + "..."
    return f"Start with the smallest visible step for: {text}."


def data_unavailable(checkpoint: str, local_date: str, state_path: Path, state: dict[str, Any], reason: str) -> dict[str, Any]:
    failures = state.setdefault("data_failures", {})
    date_failures = failures.setdefault(local_date, {})
    count = int(date_failures.get("count", 0)) + 1
    date_failures["count"] = count
    date_failures["last_reason"] = reason
    save_state(state_path, state)

    category = "task-data-unavailable"
    dedupe_key = f"{local_date}:{checkpoint}:{category}"
    if count == 1:
        return {
            "schema_version": 1,
            "status": "data_unavailable_first",
            "checkpoint": checkpoint,
            "local_date": local_date,
            "state_path": state_path.as_posix(),
            "reason": reason,
        }
    if dedupe_key in sent_keys(state):
        return {
            "schema_version": 1,
            "status": "duplicate",
            "checkpoint": checkpoint,
            "local_date": local_date,
            "category": category,
            "state_path": state_path.as_posix(),
            "dedupe_key": dedupe_key,
            "reason": "Persistent task-data failure nudge already sent.",
        }
    return {
        "schema_version": 1,
        "status": "nudge_required",
        "checkpoint": checkpoint,
        "local_date": local_date,
        "generated_at": now_iso(DEFAULT_TIMEZONE),
        "state_path": state_path.as_posix(),
        "category": category,
        "severity": "medium",
        "risk_explanation": f"Progress checks cannot read task data: {reason}",
        "suggested_action_seed": "Check the Daily Note task data source before relying on progress nudges.",
        "task_refs": [],
        "dedupe_key": dedupe_key,
        "idempotency_key": f"progress-nudge:{local_date}:{checkpoint}:{category}",
        "subject": f"progress-check:{local_date}:{checkpoint}:{category}",
    }


def build_event_payload(analysis: dict[str, Any], message: str) -> dict[str, Any]:
    if analysis.get("status") != "nudge_required":
        raise ValueError("analysis status is not nudge_required")
    message = message.strip()
    if not message:
        raise ValueError("message is required")
    return {
        "schema_version": 1,
        "nudge_id": f"progress:{analysis['local_date']}:{analysis['checkpoint']}:{analysis['category']}",
        "checkpoint": analysis["checkpoint"],
        "local_date": analysis["local_date"],
        "generated_at": analysis.get("generated_at") or now_iso(DEFAULT_TIMEZONE),
        "category": analysis["category"],
        "severity": analysis["severity"],
        "source": "progress-check",
        "message": message,
        "suggested_action": analysis.get("suggested_action_seed", ""),
        "risk_explanation": analysis.get("risk_explanation", ""),
        "task_refs": analysis.get("task_refs", []),
        "dedupe_key": analysis["dedupe_key"],
    }


def publish_nudge(analysis_path: Path, message: str, profile: str, axon_bin: str, state_path_arg: Path | None, dry_run: bool) -> dict[str, Any]:
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    payload = build_event_payload(analysis, message)
    profile = profile or DEFAULT_PROFILE
    state_path = state_path_arg or Path(string_value(analysis.get("state_path")) or DEFAULT_STATE_PATH).expanduser()
    if dry_run:
        return {"status": "dry_run", "event_type": EVENT_TYPE, "payload": payload}

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        payload_path = handle.name
    try:
        command = [
            axon_bin,
            "events",
            "publish",
            "--profile",
            profile,
            "--json",
            payload_path,
            "--subject",
            analysis.get("subject", f"progress-check:{analysis['local_date']}"),
            "--idempotency-key",
            analysis["idempotency_key"],
            EVENT_TYPE,
        ]
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        if completed.returncode != 0:
            return {
                "status": "publish_failed",
                "returncode": completed.returncode,
                "stderr": completed.stderr.strip(),
            }
        mark_sent(state_path, analysis["dedupe_key"])
        return {
            "status": "published",
            "event_type": EVENT_TYPE,
            "dedupe_key": analysis["dedupe_key"],
            "stdout": completed.stdout.strip(),
        }
    finally:
        try:
            os.unlink(payload_path)
        except OSError:
            pass


def load_config(path: Path) -> dict[str, Any]:
    config = read_json_object(path)
    daily = read_json_object(DAILY_NOTE_CONFIG_PATH)
    merged = dict(daily)
    merged.update(config)
    merged.setdefault("timezone", DEFAULT_TIMEZONE)
    merged.setdefault("state_path", str(DEFAULT_STATE_PATH))
    return merged


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def resolve_daily_note_path(config: dict[str, Any], local_date: str) -> Path:
    vault_path = Path(string_value(config.get("vault_path")) or ".").expanduser()
    pattern = string_value(config.get("daily_note_pattern")) or "Daily Notes/YYYY/MM/YYYY-MM-DD.md"
    yyyy, mm, dd = local_date.split("-")
    rel = pattern.replace("YYYY", yyyy).replace("MM", mm).replace("DD", dd)
    return vault_path / rel


def load_state(path: Path) -> dict[str, Any]:
    return read_json_object(path)


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sent_keys(state: dict[str, Any]) -> set[str]:
    value = state.get("sent_dedupe_keys", [])
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def mark_sent(path: Path, dedupe_key: str) -> None:
    state = load_state(path)
    keys = sorted(sent_keys(state) | {dedupe_key})
    state["sent_dedupe_keys"] = keys
    save_state(path, state)


def clear_data_failure(state: dict[str, Any], local_date: str, state_path: Path) -> None:
    failures = state.get("data_failures")
    if isinstance(failures, dict) and local_date in failures:
        del failures[local_date]
        save_state(state_path, state)


def today_string(timezone_name: str) -> str:
    return datetime.now(local_timezone(timezone_name)).date().isoformat()


def now_iso(timezone_name: str) -> str:
    return datetime.now(local_timezone(timezone_name)).isoformat(timespec="seconds")


def local_timezone(timezone_name: str):
    if ZoneInfo is None:
        return timezone.utc
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return timezone.utc


def is_weekend(local_date: str, timezone_name: str) -> bool:
    _ = timezone_name
    return date.fromisoformat(local_date).weekday() >= 5


def optional_path(value: str) -> Path | None:
    return Path(value).expanduser() if value else None


def string_value(value: Any) -> str:
    return value if isinstance(value, str) else ""


if __name__ == "__main__":
    raise SystemExit(main())
