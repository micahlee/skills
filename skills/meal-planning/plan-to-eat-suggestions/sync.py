#!/usr/bin/env python3
"""End-to-end sync for the plan-to-eat-suggestions skill.

Pipeline:
  1. Load or initialize the configured state file.
  2. Pull meal-plan history (full backfill on first run, incremental otherwise).
  3. Refresh the live-recipe ID set; enrich any new live+used recipes with
     course/cuisine metadata from `plantoeat recipes show`.
  4. Build the ranked list (excluding desserts/drinks/appetizers, single-use
     recipes tiered below multi-use, log2(uses+1) * days_since within tier).
  5. Render a styled Google Doc with sections:
        Top 10 — Make These Soon
        Try Something New — In Your Wheelhouse  (3 hand-curated suggestions)
        Feeling Adventurous — New Cuisines       (3 hand-curated suggestions)
        Full History — Ranked
  6. Replace the doc body and apply paragraph styles in one batchUpdate.

Idempotent. Safe to re-run any time.
"""
from __future__ import annotations

import calendar
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime

CONFIG_PATH = os.path.expanduser("~/.config/agent-skills/plan-to-eat-suggestions.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


CONFIG = load_config()
STATE_PATH = os.path.expanduser(
    os.environ.get("PLANTOEAT_SUGGESTIONS_STATE", CONFIG.get("state_file", "~/.config/agent-skills/plan-to-eat-suggestions-state.json"))
)
STATE_DIR = os.path.dirname(STATE_PATH)
PLANTOEAT_BIN = os.environ.get("PLANTOEAT_BIN", CONFIG.get("plantoeat_cli", "plantoeat"))
GWS_BIN = os.environ.get("GWS_BIN", CONFIG.get("google_workspace_cli", "gws"))
ALLOWED_PLANNER_SECTIONS = {"breakfast", "lunch", "dinner"}
EXCLUDED_COURSES = {"Desserts", "Drinks", "Beverages", "Appetizers"}
TODAY = date.today()
MAX_EMPTY_RUN = 3
ENRICH_THROTTLE_S = 0.2
ENRICH_RETRIES = 3

# Hand-curated recommendations. Rotate by editing this file. The intent:
#   IN_WHEELHOUSE  — recipes that match the user's existing taste pattern
#                    (chicken-heavy, Mexican/Italian/American, weeknight-friendly,
#                    bowls/skillet/instant-pot).
#   ADVENTUROUS    — cuisines or formats outside the current rotation.
IN_WHEELHOUSE = [
    {
        "title": "Marry Me Chicken",
        "blurb": "Creamy sun-dried tomato skillet chicken — fits the creamy-chicken + Italian patterns; one pan, ~30 min.",
        "url": "https://www.delish.com/cooking/recipe-ideas/a23436947/marry-me-chicken-recipe/",
    },
    {
        "title": "Chicken Tinga Tacos",
        "blurb": "Smoky chipotle shredded chicken — natural extension of the carnitas / shredded-beef + taco rotation.",
        "url": "https://www.gimmesomeoven.com/chicken-tinga-recipe/",
    },
    {
        "title": "Chipotle Honey Chicken Bowls",
        "blurb": "Bowl format you already love + a sweet/smoky glaze; meal-prep friendly.",
        "url": "https://www.halfbakedharvest.com/sweet-chili-chicken-bowls/",
    },
]

ADVENTUROUS = [
    {
        "title": "Filipino Chicken Adobo",
        "blurb": "Soy-vinegar-garlic braise — pantry ingredients you already keep; opens the door to Filipino cooking.",
        "url": "https://www.seriouseats.com/filipino-chicken-adobo-recipe",
    },
    {
        "title": "Khao Soi (Northern Thai Chicken Curry Noodle Soup)",
        "blurb": "Coconut curry broth over egg noodles, crispy noodle topping. Big jump from the current soup repertoire.",
        "url": "https://www.bonappetit.com/recipe/khao-soi",
    },
    {
        "title": "Shakshuka",
        "blurb": "Eggs poached in spiced tomato-pepper sauce. Middle Eastern comfort food, breakfast-for-dinner energy.",
        "url": "https://cooking.nytimes.com/recipes/1014721-shakshuka-with-feta",
    },
]

# ----------------------------------------------------------------------------
# State I/O
# ----------------------------------------------------------------------------

def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    os.replace(tmp, STATE_PATH)


# ----------------------------------------------------------------------------
# Plan to Eat pulls
# ----------------------------------------------------------------------------

def plantoeat(*args: str, retries: int = 1) -> str:
    last_err = None
    for attempt in range(retries):
        try:
            return subprocess.run(
                [PLANTOEAT_BIN, *args],
                capture_output=True, text=True, check=True, timeout=60,
            ).stdout
        except subprocess.CalledProcessError as e:
            last_err = e
            if attempt + 1 < retries:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"plantoeat {' '.join(args)} failed: {last_err}")


def month_range(year: int, month: int) -> tuple[str, str]:
    last = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}"


def prev_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def merge_pull(state: dict, days: list, sink) -> int:
    """Merge a plan-pull into state.recipes. Returns the count of new use entries added."""
    added = 0
    for day in days:
        d = day.get("date")
        for item in (day.get("items") or []):
            if item.get("kind") != "recipe":
                continue
            section = item.get("section", "")
            if section not in ALLOWED_PLANNER_SECTIONS:
                continue
            rid = str(item["recipe_id"])
            rec = state["recipes"].setdefault(rid, {"title": item["title"], "uses": []})
            rec["title"] = item["title"]
            use = {"date": d, "section": section}
            if use not in rec["uses"]:
                rec["uses"].append(use)
                added += 1
    return added


def backfill(state: dict) -> None:
    """First-run backfill: walk months backward until 3 empties in a row."""
    print("Backfilling history (first run)...", file=sys.stderr)
    empty_run = 0
    year, month = TODAY.year, TODAY.month
    earliest = state.get("first_synced_from")
    while empty_run < MAX_EMPTY_RUN:
        start, end = month_range(year, month)
        days = json.loads(plantoeat("plan", "--start", start, "--end", end, "--json", retries=2))
        before = sum(len(r["uses"]) for r in state["recipes"].values())
        merge_pull(state, days, sink=None)
        after = sum(len(r["uses"]) for r in state["recipes"].values())
        new_uses = after - before
        # Track earliest from any day with recipe data.
        for day in days:
            for item in (day.get("items") or []):
                if item.get("kind") == "recipe" and item.get("section") in ALLOWED_PLANNER_SECTIONS:
                    if earliest is None or day["date"] < earliest:
                        earliest = day["date"]
                    break
        if new_uses == 0:
            empty_run += 1
            tag = f"empty ({empty_run}/{MAX_EMPTY_RUN})"
        else:
            empty_run = 0
            tag = f"{new_uses} new uses"
        print(f"  {year:04d}-{month:02d}  {tag}", file=sys.stderr)
        # Save incrementally so a crash doesn't lose progress.
        state["first_synced_from"] = earliest
        save_state(state)
        year, month = prev_month(year, month)
    state["synced_through"] = TODAY.isoformat()
    save_state(state)


def incremental(state: dict) -> None:
    """Pull from synced_through+1 through today."""
    last = date.fromisoformat(state["synced_through"])
    if last >= TODAY:
        print(f"Already synced through {last}. Nothing to pull.", file=sys.stderr)
        return
    start = (last.replace(day=last.day) + (date.fromordinal(last.toordinal() + 1) - last)).isoformat()
    end = TODAY.isoformat()
    print(f"Incremental pull: {start} → {end}", file=sys.stderr)
    days = json.loads(plantoeat("plan", "--start", start, "--end", end, "--json", retries=2))
    new_uses = merge_pull(state, days, sink=None)
    state["synced_through"] = TODAY.isoformat()
    save_state(state)
    print(f"  {new_uses} new uses merged.", file=sys.stderr)


# ----------------------------------------------------------------------------
# Course enrichment
# ----------------------------------------------------------------------------

def enrich(state: dict) -> None:
    meta = state.setdefault("recipe_meta", {})
    live_ids = {str(i) for i in json.loads(plantoeat("recipes", "list", "--ids", "--json"))}
    used_ids = {rid for rid, rec in state["recipes"].items() if rec.get("uses")}
    todo = sorted(live_ids & used_ids - meta.keys())
    print(f"{len(live_ids)} live recipes, {len(used_ids)} used historically, "
          f"{len(todo)} need course lookup.", file=sys.stderr)
    if not todo:
        return
    failures = 0
    for i, rid in enumerate(todo, 1):
        ok = False
        for attempt in range(ENRICH_RETRIES):
            try:
                rec = json.loads(plantoeat("recipes", "show", rid, "--json"))
                meta[rid] = {"course": rec.get("course", ""), "cuisine": rec.get("cuisine", "")}
                ok = True
                break
            except Exception as e:
                if attempt + 1 < ENRICH_RETRIES:
                    time.sleep(2 * (attempt + 1))
                else:
                    print(f"  [{i}/{len(todo)}] {rid}  GAVE UP: {e}", file=sys.stderr)
                    failures += 1
        if ok and i % 25 == 0:
            print(f"  [{i}/{len(todo)}] enriched...", file=sys.stderr)
        if i % 10 == 0 or i == len(todo):
            save_state(state)
        time.sleep(ENRICH_THROTTLE_S)
    if failures:
        print(f"  {failures} recipes failed — re-run to retry.", file=sys.stderr)
    return live_ids


def live_recipe_ids() -> set[str]:
    return {str(i) for i in json.loads(plantoeat("recipes", "list", "--ids", "--json"))}


# ----------------------------------------------------------------------------
# Ranking
# ----------------------------------------------------------------------------

@dataclass
class Ranked:
    rid: str
    title: str
    course: str
    uses: int
    last: date
    days_since: int
    tier: int
    score: float


def rank(state: dict, live_ids: set[str]) -> tuple[list[Ranked], dict[str, int]]:
    meta = state.get("recipe_meta", {})
    out: list[Ranked] = []
    drops = {"not_live": 0, "no_uses": 0, "excluded_course": 0}
    for rid, rec in state["recipes"].items():
        if rid not in live_ids:
            drops["not_live"] += 1
            continue
        uses = rec.get("uses") or []
        if not uses:
            drops["no_uses"] += 1
            continue
        course = (meta.get(rid) or {}).get("course", "")
        if course in EXCLUDED_COURSES:
            drops["excluded_course"] += 1
            continue
        last = max(date.fromisoformat(u["date"]) for u in uses)
        days_since = max((TODAY - last).days, 0)
        n = len(uses)
        tier = 0 if n >= 2 else 1
        score = math.log2(n + 1) * days_since
        out.append(Ranked(
            rid=rid,
            title=rec.get("title", f"recipe #{rid}"),
            course=course or "(uncategorized)",
            uses=n,
            last=last,
            days_since=days_since,
            tier=tier,
            score=score,
        ))
    out.sort(key=lambda r: (r.tier, -r.score, r.last.isoformat(), -r.uses))
    return out, drops


# ----------------------------------------------------------------------------
# Render & write doc
# ----------------------------------------------------------------------------

PTE_RECIPE_URL = "https://app.plantoeat.com/recipes/{rid}"


def _title_paragraph(prefix: str, title: str, url: str) -> dict:
    line = f"{prefix}{title}"
    rng = (len(prefix), len(line))
    return {
        "text": line,
        "style": "NORMAL_TEXT",
        "bold": [rng],
        "links": [(rng[0], rng[1], url)],
    }


def fmt_history_paragraphs(idx: int, r: Ranked) -> list[dict]:
    d_str = "today" if r.days_since == 0 else f"{r.days_since}d ago"
    plural = "s" if r.uses != 1 else ""
    prefix = f"{idx}. "
    indent = " " * len(prefix)
    meta_line = f"{indent}{r.uses} use{plural}, last on {r.last.isoformat()} ({d_str}) · {r.course}"
    return [
        _title_paragraph(prefix, r.title, PTE_RECIPE_URL.format(rid=r.rid)),
        {"text": meta_line, "style": "NORMAL_TEXT", "bold": [], "links": []},
    ]


def fmt_suggestion_paragraphs(idx: int, sug: dict) -> list[dict]:
    prefix = f"{idx}. "
    indent = " " * len(prefix)
    return [
        _title_paragraph(prefix, sug["title"], sug["url"]),
        {"text": f"{indent}{sug['blurb']}", "style": "NORMAL_TEXT", "bold": [], "links": []},
    ]


def build_doc(ranked: list[Ranked], state: dict) -> tuple[str, list[dict]]:
    """Build the doc text plus all style requests to apply.

    Returns (text, style_requests). Style requests cover both paragraph
    styles (Title/Subtitle/Heading) and per-range text bolding for recipe
    titles.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    excl = ", ".join(sorted(EXCLUDED_COURSES))
    subtitle = (
        f"Updated {now} · {len(ranked)} ranked recipes from "
        f"{state['first_synced_from']} onward · excluding {excl}"
    )

    top10 = ranked[:10]
    rest = ranked[10:]

    parts: list[dict] = []  # {"text", "style", "bold": [(s,e),...], "links": [(s,e,url),...]}

    def add(text: str, style: str = "NORMAL_TEXT", bold: list | None = None,
            links: list | None = None) -> None:
        parts.append({"text": text, "style": style, "bold": bold or [], "links": links or []})

    add("Plan to Eat — Next Meals", "TITLE")
    add(subtitle, "SUBTITLE")
    add("", "NORMAL_TEXT")

    add("Top 10 — Make These Soon", "HEADING_1")
    for i, r in enumerate(top10, 1):
        parts.extend(fmt_history_paragraphs(i, r))
    add("", "NORMAL_TEXT")

    add("Try Something New — In Your Wheelhouse", "HEADING_1")
    for i, s in enumerate(IN_WHEELHOUSE, 1):
        parts.extend(fmt_suggestion_paragraphs(i, s))
    add("", "NORMAL_TEXT")

    add("Feeling Adventurous — New Cuisines", "HEADING_1")
    for i, s in enumerate(ADVENTUROUS, 1):
        parts.extend(fmt_suggestion_paragraphs(i, s))
    add("", "NORMAL_TEXT")

    add("Full History — Ranked", "HEADING_1")
    for i, r in enumerate(rest, start=11):
        parts.extend(fmt_history_paragraphs(i, r))

    text = "\n".join(p["text"] for p in parts) + "\n"

    # Compute absolute doc indices for paragraph styles + bold ranges.
    # Doc index 1 is the start; each paragraph spans [cursor, cursor+len(line)+1).
    style_requests: list[dict] = []
    cursor = 1
    for p in parts:
        line_len = len(p["text"])
        para_len = line_len + 1
        if p["style"] != "NORMAL_TEXT":
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": cursor, "endIndex": cursor + para_len},
                    "paragraphStyle": {"namedStyleType": p["style"]},
                    "fields": "namedStyleType",
                }
            })
        for b_start, b_end in p["bold"]:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": cursor + b_start, "endIndex": cursor + b_end},
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            })
        for l_start, l_end, url in p.get("links", []):
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": cursor + l_start, "endIndex": cursor + l_end},
                    "textStyle": {"link": {"url": url}},
                    "fields": "link",
                }
            })
        cursor += para_len

    return text, style_requests


def gws(*args: str, json_in: str | None = None) -> str:
    cmd = [GWS_BIN, *args]
    if json_in is not None:
        cmd += ["--json", json_in]
    return subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60).stdout


def doc_end_index(doc_id: str) -> int:
    out = gws("docs", "documents", "get",
              "--params", json.dumps({"documentId": doc_id, "fields": "body.content(endIndex)"}))
    doc = json.loads(out)
    return max(c["endIndex"] for c in doc["body"]["content"])


def write_doc(doc_id: str, text: str, style_requests: list[dict]) -> None:
    end = doc_end_index(doc_id)
    requests: list[dict] = []
    if end > 2:
        requests.append({"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end - 1}}})
    requests.append({"insertText": {"location": {"index": 1}, "text": text}})
    # Reset the whole inserted range to NORMAL_TEXT + bold off first so we
    # don't inherit styles left over from prior runs (e.g. the trailing
    # paragraph stays styled if the previous content ended on a heading).
    requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": 1, "endIndex": len(text) + 1},
            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
            "fields": "namedStyleType",
        }
    })
    requests.append({
        "updateTextStyle": {
            "range": {"startIndex": 1, "endIndex": len(text) + 1},
            "textStyle": {"bold": False},
            "fields": "bold",
        }
    })
    # Clear any inherited link across the whole range. Google Docs API expects
    # `link` to be omitted (with the field mask set) to clear it.
    requests.append({
        "updateTextStyle": {
            "range": {"startIndex": 1, "endIndex": len(text) + 1},
            "textStyle": {},
            "fields": "link",
        }
    })
    requests.extend(style_requests)
    gws("docs", "documents", "batchUpdate",
        "--params", json.dumps({"documentId": doc_id}),
        json_in=json.dumps({"requests": requests}))


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    state = load_state()
    if not state:
        print("No state file. This is a first run.", file=sys.stderr)
        print("Provide the Google Doc ID via PLANTOEAT_SUGGESTIONS_DOC_ID, "
              "or create one with: gws docs documents create --json "
              "'{\"title\":\"Plan to Eat — Next Meals\"}'", file=sys.stderr)
        doc_id = os.environ.get("PLANTOEAT_SUGGESTIONS_DOC_ID") or CONFIG.get("suggestions_doc_id")
        if not doc_id:
            return 2
        state = {
            "doc_id": doc_id,
            "synced_through": None,
            "first_synced_from": None,
            "recipes": {},
            "recipe_meta": {},
        }
        save_state(state)

    # Step 2 — pull history
    if not state.get("synced_through"):
        backfill(state)
    else:
        incremental(state)

    # Step 3 — enrich course metadata
    enrich(state)

    # Step 4 — rank
    live_ids = live_recipe_ids()
    ranked, drops = rank(state, live_ids)
    print(f"\n{len(ranked)} recipes ranked. Drops: {drops}", file=sys.stderr)

    # Step 5/6 — build & write doc
    text, styles = build_doc(ranked, state)
    write_doc(state["doc_id"], text, styles)
    print(f"Doc updated: https://docs.google.com/document/d/{state['doc_id']}/edit",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
