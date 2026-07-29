#!/usr/bin/env python3
"""Enrich and validate visual/instruction content for Axon Training movements."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CATALOG = SCRIPT_DIR.parent / "references" / "exercise-media.json"
RAW_BASE_URL = (
    "https://raw.githubusercontent.com/yuhonas/free-exercise-db/"
    "main/exercises"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--check-urls",
        action="store_true",
        help="Verify every generated image URL before writing the plan.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def media_for(source_id: str) -> dict[str, Any]:
    primary = f"{RAW_BASE_URL}/{source_id}/0.jpg"
    alternate = f"{RAW_BASE_URL}/{source_id}/1.jpg"
    return {
        "url": primary,
        "thumbnailURL": primary,
        "alternateURLs": [alternate],
        "attribution": "Free Exercise DB",
        "license": "Unlicense",
    }


def normalize(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def validate_media(media: Any, context: str) -> None:
    if not isinstance(media, dict):
        raise ValueError(f"{context}: media must be an object")
    if not str(media.get("url", "")).startswith("https://"):
        raise ValueError(f"{context}: media.url must be direct HTTPS")
    if not str(media.get("attribution", "")).strip():
        raise ValueError(f"{context}: media attribution is required")
    if not str(media.get("license", "")).strip():
        raise ValueError(f"{context}: media license is required")


def validate_instructions(instructions: Any, context: str) -> None:
    if not isinstance(instructions, dict):
        raise ValueError(f"{context}: detailed instructions are required")
    if not str(instructions.get("overview", "")).strip():
        raise ValueError(f"{context}: instructions overview is required")
    steps = instructions.get("steps")
    if not isinstance(steps, list) or len(steps) < 2 or not all(
        str(step).strip() for step in steps
    ):
        raise ValueError(f"{context}: instructions need at least two ordered steps")
    demonstration_url = str(instructions.get("demonstrationURL", ""))
    if demonstration_url and not demonstration_url.startswith("https://"):
        raise ValueError(f"{context}: demonstrationURL must use HTTPS")


def verify_url(url: str) -> None:
    request = Request(url, method="HEAD", headers={"User-Agent": "Axon-Fitness-Coach"})
    with urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError(f"{url}: HTTP {response.status}")
        if not response.headers.get_content_type().startswith("image/"):
            raise ValueError(f"{url}: response is not an image")


def catalog_aliases(catalog: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for movement_id, entry in catalog.items():
        if not isinstance(entry, dict):
            continue
        for alias in [movement_id, *(entry.get("aliases") or [])]:
            key = normalize(str(alias))
            existing = aliases.get(key)
            if existing and existing != movement_id:
                raise ValueError(
                    f"catalog alias {alias!r} maps to both {existing} and {movement_id}"
                )
            aliases[key] = movement_id
    return aliases


def catalog_media(entry: dict[str, Any]) -> dict[str, Any] | None:
    explicit = entry.get("media")
    if explicit is not None:
        return explicit
    source_id = entry.get("free_exercise_db_id")
    return media_for(source_id) if source_id else None


def enrich_plan(plan: dict[str, Any], catalog: dict[str, Any]) -> list[str]:
    enriched: list[str] = []
    aliases = catalog_aliases(catalog)
    for workout in plan.get("prescriptions", []):
        cards = workout.get("cards", [])
        cardio_ids = {
            segment.get("id")
            for segment in (workout.get("cardioProfile") or {}).get("segments", [])
        }
        by_movement: dict[str, list[dict[str, Any]]] = {}
        for card in cards:
            exercise_id = (card.get("set") or {}).get("exerciseID")
            movement_id = exercise_id or card.get("movementID")
            is_movement_timer = (
                card.get("kind") == "timer" and card.get("id") not in cardio_ids
            )
            if not exercise_id and is_movement_timer and not movement_id:
                movement_id = aliases.get(normalize(str(card.get("title", ""))))
                if not movement_id:
                    raise ValueError(
                        f"{workout.get('title', 'workout')} / "
                        f"{card.get('title', 'timer')}: no reviewed movement mapping"
                    )
                card["movementID"] = movement_id
                enriched.append(
                    f"{workout.get('title', 'workout')} / {movement_id} identity"
                )
            if exercise_id or is_movement_timer:
                if not movement_id:
                    raise ValueError(
                        f"{workout.get('title', 'workout')} / "
                        f"{card.get('title', 'movement')}: movementID is required"
                    )
                by_movement.setdefault(movement_id, []).append(card)

        for movement_id, movement_cards in by_movement.items():
            context = f"{workout.get('title', 'workout')} / {movement_id}"
            entry = catalog.get(movement_id)
            if not isinstance(entry, dict):
                raise ValueError(f"{context}: no reviewed movement catalog mapping")

            instructions = next(
                (
                    card["instructions"]
                    for card in movement_cards
                    if card.get("instructions")
                ),
                None,
            )
            if instructions is None:
                instructions = entry.get("instructions")
                if instructions is None:
                    raise ValueError(f"{context}: no reviewed instructions")
                movement_cards[0]["instructions"] = instructions
                enriched.append(f"{context} instructions")
            elif not movement_cards[0].get("instructions"):
                movement_cards[0]["instructions"] = instructions
            validate_instructions(instructions, context)

            illustrated = next(
                (card["media"] for card in movement_cards if card.get("media")),
                None,
            )
            if illustrated is None:
                illustrated = catalog_media(entry)
                if illustrated is not None:
                    movement_cards[0]["media"] = illustrated
                    enriched.append(f"{context} media")
                elif not instructions.get("illustrationAssetName"):
                    raise ValueError(
                        f"{context}: no reviewed media or bundled illustration"
                    )
            elif not movement_cards[0].get("media"):
                movement_cards[0]["media"] = illustrated

            if illustrated is not None:
                validate_media(illustrated, context)
    return enriched


def main() -> int:
    args = parse_args()
    try:
        plan = load_json(args.input)
        catalog = load_json(args.catalog)
        enriched = enrich_plan(plan, catalog)
        if args.check_urls:
            urls = {
                url
                for workout in plan.get("prescriptions", [])
                for card in workout.get("cards", [])
                for media in [card.get("media")]
                if media
                for url in [media["url"], *(media.get("alternateURLs") or [])]
            }
            for url in sorted(urls):
                verify_url(url)
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(plan, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"prepare_exercise_media: {error}", file=sys.stderr)
        return 1

    print(
        f"exercise media ready; enriched {len(enriched)} movement(s)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
