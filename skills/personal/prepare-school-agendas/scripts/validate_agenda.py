#!/usr/bin/env python3
"""Deterministically validate a normalized agenda JSON against a DOCX."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml.ns import qn


CHECKED = "☒"
UNCHECKED = "☐"
EXPECTED_MARGINS = (0.55, 0.55, 0.48, 0.48)


def element_text(element) -> str:
    return "".join(node.text or "" for node in element.xpath(".//w:t")).strip()


def next_content_after_heading(document, heading: str):
    children = list(document._element.body)
    for index, child in enumerate(children):
        if child.tag == qn("w:p") and element_text(child) == heading.upper():
            for candidate in children[index + 1 :]:
                if candidate.tag == qn("w:tbl"):
                    return ("table", candidate)
                if candidate.tag == qn("w:p") and element_text(candidate):
                    return ("paragraph", candidate)
    return (None, None)


def table_rows(table_element) -> list[dict[str, Any]]:
    rows = []
    for row in table_element.findall(qn("w:tr")):
        cells = row.findall(qn("w:tc"))
        if not cells:
            continue
        marker = element_text(cells[0]) if len(cells) > 1 else ""
        text_cell = cells[-1]
        text = element_text(text_cell)
        strike_nodes = text_cell.xpath(".//w:strike | .//w:dstrike")
        strike = any(
            (node.get(qn("w:val")) or "true").lower() not in {"0", "false", "off", "no"}
            for node in strike_nodes
        )
        rows.append({"marker": marker, "text": text, "strike": strike})
    return rows


def expected_school_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    courses = data.get("courses") or []
    if not any(int(course.get("assignment_count", 0)) > 0 for course in courses):
        checked_at = data.get("checked_at", "verification time unavailable")
        return [{"text": f"No assignments listed in ClassReach  Checked on {checked_at}", "checked": False}]

    rows = []
    bible_printed = False
    for course in courses:
        count = int(course.get("assignment_count", 0))
        if count <= 0:
            continue
        name = str(course.get("name") or "").strip()
        bible_printed = bible_printed or name == "Bible"
        noun = "assignment" if count == 1 else "assignments"
        complete = int(course.get("completed_count", 0)) >= count
        rows.append({"text": f"{name} - {count} {noun}", "checked": complete})
    if not bible_printed:
        rows.append({"text": "Bible", "checked": False})
    return rows


def expected_incomplete_rows(data: dict[str, Any]) -> list[str]:
    items = ((data.get("parent_report") or {}).get("incomplete") or [])
    counts: OrderedDict[str, int] = OrderedDict()
    for item in items:
        course = str(item.get("course") or "ClassReach").strip()
        counts[course] = counts.get(course, 0) + 1
    return [
        f"{course} - {count} {'assignment' if count == 1 else 'assignments'}"
        for course, count in counts.items()
    ]


def validate(data: dict[str, Any], docx_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    document = Document(docx_path)
    target = date.fromisoformat(data["date"])
    weekday = target.strftime("%A")
    expected_sections = 2 if weekday in {"Monday", "Friday"} else 1

    if len(document.sections) != expected_sections:
        errors.append(f"section count: expected {expected_sections}, got {len(document.sections)}")

    for index, section in enumerate(document.sections, start=1):
        actual = (
            round(section.left_margin.inches, 2),
            round(section.right_margin.inches, 2),
            round(section.top_margin.inches, 2),
            round(section.bottom_margin.inches, 2),
        )
        if actual != EXPECTED_MARGINS:
            errors.append(f"section {index} margins: expected {EXPECTED_MARGINS}, got {actual}")
        page = (round(section.page_width.inches, 2), round(section.page_height.inches, 2))
        if page != (8.5, 11.0):
            errors.append(f"section {index} page size: expected (8.5, 11.0), got {page}")

    title = f"{data['student']} - {target.strftime('%A, %B %-d, %Y')}"
    visible_paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    if not visible_paragraphs or visible_paragraphs[0] != title:
        errors.append(f"title: expected {title!r}")

    kind, school = next_content_after_heading(document, "School")
    if kind != "table":
        errors.append("School must be followed by a table")
        actual_school = []
    else:
        actual_school = table_rows(school)
    expected_school = expected_school_rows(data)
    if len(actual_school) != len(expected_school):
        errors.append(f"School row count: expected {len(expected_school)}, got {len(actual_school)}")
    for index, expected in enumerate(expected_school):
        if index >= len(actual_school):
            break
        actual = actual_school[index]
        if re.sub(r"\s+", " ", actual["text"]).strip() != expected["text"]:
            errors.append(
                f"School row {index + 1}: expected {expected['text']!r}, got {actual['text']!r}"
            )
        expected_marker = CHECKED if expected["checked"] else UNCHECKED
        if actual["marker"] != expected_marker:
            errors.append(
                f"School row {index + 1} marker: expected {expected_marker!r}, got {actual['marker']!r}"
            )
        if actual["strike"] != expected["checked"]:
            errors.append(
                f"School row {index + 1} strike: expected {expected['checked']}, got {actual['strike']}"
            )

    kind, additional = next_content_after_heading(document, "Additional Tasks")
    if kind != "table":
        errors.append("Additional Tasks must be followed by a table")
    else:
        additional_rows = table_rows(additional)
        if len(additional_rows) != 3:
            errors.append(f"Additional Tasks row count: expected 3, got {len(additional_rows)}")
        for index, row in enumerate(additional_rows, start=1):
            if row["marker"] != UNCHECKED or "_" not in row["text"]:
                errors.append(f"Additional Tasks row {index} is not a blank checkbox line")

    if expected_sections == 2:
        expected_incomplete = expected_incomplete_rows(data)
        kind, incomplete = next_content_after_heading(document, "Incomplete Work")
        if expected_incomplete:
            if kind != "table":
                errors.append("Incomplete Work must be followed by a table")
            else:
                actual_incomplete = [row["text"].lstrip("☐☒ ").strip() for row in table_rows(incomplete)]
                if actual_incomplete != expected_incomplete:
                    errors.append(
                        f"Incomplete Work rows: expected {expected_incomplete!r}, got {actual_incomplete!r}"
                    )
        elif kind != "paragraph" or element_text(incomplete) != "Nothing to report":
            errors.append("Incomplete Work must say 'Nothing to report' when empty")

    return {
        "ok": not errors,
        "student": data.get("student"),
        "date": data.get("date"),
        "docx": str(docx_path),
        "expected_sections": expected_sections,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_docx", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    data = json.loads(args.input_json.read_text(encoding="utf-8"))
    result = validate(data, args.output_docx)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
