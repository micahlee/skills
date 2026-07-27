#!/usr/bin/env python3
"""Refresh the fitness-coach NRC speed-workout catalog."""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path


SHEET_ID = "15YHmk24n6qN6jwY7TxuwOorMeiLXjwkvYe1n7CSqu98"
SOURCE_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
    "?tqx=out:csv&sheet=Sheet1"
)
OUT = Path(__file__).resolve().parents[1] / "references" / "nrc-speed-workouts.csv"


def minutes(value: str) -> int | None:
    parts = value.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 60 + int(parts[1])
    return None


def main() -> None:
    with urllib.request.urlopen(SOURCE_URL) as response:
        rows = list(csv.reader(line.decode("utf-8-sig") for line in response.readlines()))

    normalized: list[dict[str, str]] = []
    for row in rows[2:]:
        if len(row) < 9 or not row[0].strip():
            continue
        title = row[0].strip()
        duration = row[1].strip()
        duration_minutes = minutes(duration)
        workout_type = row[4].strip()
        if not duration_minutes or not (20 <= duration_minutes <= 40):
            continue
        if not workout_type.startswith("Speed"):
            continue
        normalized.append(
            {
                "title": title,
                "duration": duration,
                "duration_minutes": str(duration_minutes),
                "distance_km": row[2].strip(),
                "distance_mi": row[3].strip(),
                "type": workout_type,
                "coach": row[5].strip(),
                "guest": row[6].strip(),
                "training_plans": row[7].strip(),
                "notes": row[8].strip().replace("\n", " "),
                "source": SOURCE_URL,
            }
        )

    normalized.sort(key=lambda item: (int(item["duration_minutes"]), item["type"], item["title"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "duration",
                "duration_minutes",
                "distance_km",
                "distance_mi",
                "type",
                "coach",
                "guest",
                "training_plans",
                "notes",
                "source",
            ],
        )
        writer.writeheader()
        writer.writerows(normalized)
    print(f"wrote {len(normalized)} workouts to {OUT}")


if __name__ == "__main__":
    main()
