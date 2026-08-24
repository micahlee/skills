#!/usr/bin/env python3
"""Classify every next-day ClassReach item and emit deterministic prep notes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CLASSIFICATIONS = {
    "actionable_preparation",
    "required_material",
    "ordinary_in_class",
    "optional",
    "informational",
}

MATERIAL_PATTERNS = (
    re.compile(r"\bbring\b", re.I),
    re.compile(r"\bwith you\b", re.I),
    re.compile(r"\bwear\b", re.I),
    re.compile(r"\b(?:spiral |composition |class )?notebook\b", re.I),
    re.compile(r"\b(?:binder|folder|calculator|instrument|textbook|workbook)\b", re.I),
)


def source_url(item: dict[str, Any]) -> str:
    source = item.get("source") or {}
    return str(
        item.get("url")
        or item.get("Url")
        or source.get("url")
        or source.get("Url")
        or ""
    )


def sentences(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def material_evidence(details: str) -> str:
    matches = [
        sentence
        for sentence in sentences(details)
        if any(pattern.search(sentence) for pattern in MATERIAL_PATTERNS)
    ]
    return " ".join(matches)


def classify_item(course: str, item: dict[str, Any]) -> dict[str, Any]:
    item_type = str(item.get("type") or "").strip()
    meeting_day = bool(item.get("meetingDay", item.get("meeting_day", False)))
    title = str(item.get("title") or "").strip()
    details = str(item.get("details") or "").strip()
    combined = " ".join(part for part in (title, details) if part)
    material = material_evidence(details)

    if re.search(r"\boptional\b", combined, re.I):
        classification = "optional"
        evidence = details or title
        reason = "item explicitly says optional"
    elif item_type == "TaskItem" and not meeting_day:
        classification = "actionable_preparation"
        evidence = details or title
        reason = "non-meeting TaskItem requires action before the selected school day"
    elif material:
        classification = "required_material"
        evidence = material
        reason = "exact item text identifies material the student must have available"
    elif meeting_day and item_type in {"TaskItem", "AgendaItem"}:
        classification = "ordinary_in_class"
        evidence = details or title
        reason = "meeting-day lesson description without a separate preparation requirement"
    elif item_type in {"AgendaItem", "Handout", "Message", "Discussion"}:
        classification = "informational"
        evidence = details or title
        reason = "informational ClassReach item without a preparation requirement"
    else:
        raise ValueError(
            f"unclassified item for {course}: type={item_type!r}, meetingDay={meeting_day}, title={title!r}"
        )

    if classification not in CLASSIFICATIONS:
        raise AssertionError(f"invalid classification: {classification}")
    if not evidence:
        raise ValueError(f"classified item for {course} has no evidence text")

    return {
        "course": course,
        "date": item.get("date"),
        "title": title,
        "type": item_type,
        "meeting_day": meeting_day,
        "classification": classification,
        "evidence_text": evidence,
        "reason": reason,
        "source_url": source_url(item),
    }


def select_student(raw: dict[str, Any], requested: str | None) -> tuple[dict[str, Any], str]:
    students = raw.get("students")
    if students is None:
        name = str(raw.get("student") or requested or "").strip()
        if not name:
            raise ValueError("student name is required")
        return raw, name

    matches = []
    for record in students:
        student = record.get("student") or {}
        name = str(student.get("Name") or student.get("name") or "").strip()
        if requested is None or name == requested:
            matches.append((record, name))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one student match, got {len(matches)}")
    return matches[0]


def classify(raw: dict[str, Any], student_name: str | None = None, selected_date: str | None = None) -> dict[str, Any]:
    record, name = select_student(raw, student_name)
    selected_date = selected_date or raw.get("startDate") or raw.get("date")
    if not selected_date:
        raise ValueError("selected date is required")

    classified = []
    for section in record.get("sections") or []:
        course = str(section.get("courseName") or section.get("course") or "ClassReach").strip()
        for item in section.get("agendaItems") or section.get("items") or []:
            if item.get("date") and item.get("date") != selected_date:
                continue
            classified.append(classify_item(course, item))

    prep = [
        {
            "course": item["course"],
            "text": item["evidence_text"],
            "url": item["source_url"],
            "classification": item["classification"],
        }
        for item in classified
        if item["classification"] in {"actionable_preparation", "required_material"}
    ]
    return {
        "student": name,
        "date": selected_date,
        "items": classified,
        "next_day_prep": prep,
        "no_special_preparation_allowed": not prep,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("next_day_json", type=Path)
    parser.add_argument("--student")
    parser.add_argument("--date")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--expect-empty",
        action="store_true",
        help="fail if actionable preparation or required materials are present",
    )
    args = parser.parse_args()

    try:
        raw = json.loads(args.next_day_json.read_text(encoding="utf-8"))
        result = classify(raw, args.student, args.date)
        if args.expect_empty and not result["no_special_preparation_allowed"]:
            raise ValueError("No special preparation is forbidden: preparation items remain")
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    result["ok"] = True
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
