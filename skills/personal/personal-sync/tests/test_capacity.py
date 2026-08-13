#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "capacity.py"
SPEC = importlib.util.spec_from_file_location("capacity", MODULE_PATH)
capacity = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["capacity"] = capacity
SPEC.loader.exec_module(capacity)


def main() -> int:
    assert capacity.assess({})["band"] == "normal"
    open_week = capacity.assess(
        {
            "history": [
                {"planned_outcomes": 3, "completed_outcomes": 3, "carryovers": 0},
                {"planned_outcomes": 3, "completed_outcomes": 3, "carryovers": 0},
            ],
            "upcoming": {},
        }
    )
    assert open_week["band"] == "open", open_week
    assert open_week["suggested_outcomes"] == 4, open_week

    constrained = capacity.assess(
        {
            "history": [{"planned_outcomes": 4, "completed_outcomes": 3, "carryovers": 1}],
            "upcoming": {"travel_days": 2, "on_call_days": 5},
        }
    )
    assert constrained["band"] == "constrained", constrained
    assert constrained["suggested_outcomes"] == 2, constrained

    recent_only = capacity.assess(
        {
            "history": [
                {"planned_outcomes": 3, "completed_outcomes": 0, "carryovers": 3},
                {"planned_outcomes": 3, "completed_outcomes": 0, "carryovers": 3},
                {"planned_outcomes": 3, "completed_outcomes": 3, "carryovers": 0},
                {"planned_outcomes": 3, "completed_outcomes": 3, "carryovers": 0},
                {"planned_outcomes": 3, "completed_outcomes": 3, "carryovers": 0},
                {"planned_outcomes": 3, "completed_outcomes": 3, "carryovers": 0},
            ]
        }
    )
    assert recent_only["history_weeks_used"] == 4, recent_only
    assert recent_only["band"] == "open", recent_only
    print("capacity tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
