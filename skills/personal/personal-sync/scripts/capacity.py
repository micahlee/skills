#!/usr/bin/env python3
"""Recommend an explainable weekly capacity band from recent history and constraints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXAMPLE = {
    "history": [
        {"planned_outcomes": 3, "completed_outcomes": 2.5, "carryovers": 1},
        {"planned_outcomes": 3, "completed_outcomes": 3, "carryovers": 0},
    ],
    "upcoming": {
        "full_commitment_days": 1,
        "evening_commitments": 2,
        "travel_days": 0,
        "on_call_days": 0,
        "non_work_days": 0,
        "health_constraint": False,
    },
}


def number(value: Any, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def assess(data: dict[str, Any]) -> dict[str, Any]:
    raw_history = data.get("history", [])
    history = raw_history[-4:] if isinstance(raw_history, list) else []
    planned = sum(max(0.0, number(item.get("planned_outcomes"))) for item in history if isinstance(item, dict))
    completed = sum(max(0.0, number(item.get("completed_outcomes"))) for item in history if isinstance(item, dict))
    carryovers = sum(max(0.0, number(item.get("carryovers"))) for item in history if isinstance(item, dict))
    completion_rate = min(1.25, completed / planned) if planned else None

    upcoming = data.get("upcoming", {})
    upcoming = upcoming if isinstance(upcoming, dict) else {}
    factors: list[str] = []
    load = 0

    rules = (
        ("full_commitment_days", 2, "two or more commitment-heavy days"),
        ("evening_commitments", 3, "three or more committed evenings"),
        ("travel_days", 1, "travel in the planning week"),
        ("on_call_days", 3, "three or more on-call days"),
        ("non_work_days", 2, "two or more non-work days"),
    )
    for key, threshold, label in rules:
        if number(upcoming.get(key)) >= threshold:
            load += 1
            factors.append(label)
    if upcoming.get("health_constraint") is True:
        load += 1
        factors.append("relevant health or energy constraint")
    if carryovers >= max(2.0, len(history) * 0.75):
        load += 1
        factors.append("recent repeated carryover")

    if completion_rate is None:
        band, suggested = "normal", 3
        factors.append("insufficient outcome history; using baseline")
    elif completion_rate < 0.55:
        band, suggested = "constrained", 2
        factors.append("recent outcome completion below 55%")
    elif completion_rate >= 0.9 and load == 0 and len(history) >= 2:
        band, suggested = "open", 4
        factors.append("recent completion at or above 90% with no major upcoming constraint")
    else:
        band, suggested = "normal", 3

    if load >= 2:
        band, suggested = "constrained", min(suggested, 2)
    elif load == 1 and band == "open":
        band, suggested = "normal", 3

    return {
        "schema_version": 1,
        "band": band,
        "suggested_outcomes": suggested,
        "history_weeks_used": len(history),
        "completion_rate": round(completion_rate, 3) if completion_rate is not None else None,
        "planned_outcomes": planned,
        "completed_outcomes": completed,
        "carryovers": carryovers,
        "upcoming_constraint_score": load,
        "factors": factors or ["recent delivery and upcoming constraints support the baseline"],
        "advisory": "Recommendation only; an explicit user choice may override it.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("assess",), default="assess")
    parser.add_argument("--input")
    parser.add_argument("--example", action="store_true")
    args = parser.parse_args()
    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.input:
        parser.error("--input is required unless --example is used")
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("capacity input must be a JSON object")
    print(json.dumps(assess(data), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
