---
name: plantoeat-suggestions
description: Maintain a "next meals to make" Google Doc ranked from Plan to Eat usage history. Bubbles up beloved recipes (used multiple times) that haven't been made in a while; sinks recently-used and one-off recipes; excludes never-scheduled recipes, desserts, drinks, and appetizers. Triggers on phrases like "update meal suggestions", "refresh the next-meals doc", "what should I make next", "rebuild plan to eat suggestions".
---

# Plan to Eat — Next Meals Suggestions

Keeps the user's "next meals" Google Doc fresh by tracking how often each recipe gets scheduled in Plan to Eat and ranking them so under-used favorites bubble to the top.

## How to run

```
python3 scripts/sync.py
```

That's it. The script handles everything: incremental pull from the last watermark (or full backfill on first run), course-metadata enrichment for new live recipes, ranking, and rewriting the Google Doc with proper Title/Subtitle/Heading styling.

**CLIs required:** `plantoeat` (authenticated; run `plantoeat auth login` if not), `gws` (Google Workspace CLI).
**State:** `~/.plantoeat/suggestions/state.json` (auto-created on first run).

## What the doc looks like

The script renders four sections:

1. **Top 10 — Make These Soon** — top of the ranked list (under-used favorites).
2. **Try Something New — In Your Wheelhouse** — 3 hand-curated recipes matching the user's taste profile. Edit `IN_WHEELHOUSE` in `sync.py` to refresh.
3. **Feeling Adventurous — New Cuisines** — 3 hand-curated recipes from cuisines the user hasn't explored much. Edit `ADVENTUROUS` in `sync.py` to refresh.
4. **Full History — Ranked** — items 11+ from the ranked list.

Doc ID is stored in `state.json` after first run. On a fresh state, the script will prompt for a doc URL/ID or offer to create one.

## Storage layout

```json
{
  "doc_id": "1AbCdEf...",
  "synced_through": "2026-04-20",
  "first_synced_from": "2017-04-18",
  "recipes": {
    "12345": {
      "title": "Chicken Tacos",
      "uses": [
        {"date": "2024-01-15", "section": "dinner"},
        {"date": "2025-08-04", "section": "dinner"}
      ]
    }
  },
  "recipe_meta": {
    "12345": {"course": "Main Course", "cuisine": "Mexican"}
  }
}
```

- `synced_through` — last day (inclusive) we've already pulled and merged.
- `first_synced_from` — earliest day with any recipe data (informational).
- `recipes` — usage history keyed by recipe ID (string).
- `recipe_meta` — per-recipe course/cuisine cache. Lazy: only filled for recipes that are both live and used. Persists across runs so we don't refetch.

## Ranking formula (encoded in sync.py)

Filter: live in book + at least one use + course not in `{Desserts, Beverages, Drinks, Appetizers}`.

```
tier  = 0 if uses_count >= 2 else 1     # multi-use ranks above single-use
score = log2(uses_count + 1) * days_since_last_use
```

Sort by `(tier asc, score desc, last_used asc, uses_count desc)`.

## Critical CLI gotchas (learned the hard way)

- **Use `plantoeat recipes list --ids --json`** for the live recipe set. Plain `recipes list --json` may return only the first grid page, which can silently drop most of a recipe book.
- **Course/cuisine are only on `recipes show`**, not on `recipes list`. To filter desserts out, you must enrich each candidate recipe with one `show` call. Cache it in `state.recipe_meta`.
- **Section filtering is insufficient on its own.** Users may schedule desserts or drinks under the `dinner` section. Filter by recipe **course**, not by planner section.
- **`day["items"]` may be `None`**, not just missing — use `(day.get("items") or [])`.
- **PtE rate-limits aggressive bursts.** sync.py throttles enrichment at 200ms/call with 3-attempt retry+backoff and only persists successful lookups (so failures get retried next run).

## Editing the curated sections

The "In Your Wheelhouse" and "Feeling Adventurous" sections are hand-picked Python lists at the top of `sync.py`. Each entry is `{"title": ..., "blurb": ..., "url": ...}`. To refresh recommendations, edit those lists and re-run.

## Verification after a run

- Open the doc, confirm timestamp is fresh and styling came through (Title big at top, section headers as Heading 1).
- Re-run immediately. Expect: "Already synced through <today>. Nothing to pull. … 0 need course lookup. Doc updated."
- Spot-check that nothing in the top 30 is a dessert or drink.

## Reference

- CLI source: `~/projects/plantoeat-cli/`. The `--start/--end` flags on `plan`, the `--ids` flag on `recipes list`, and the `course`/`cuisine` fields on `recipes show` were all added specifically to support this skill.
- gws docs API surface: `gws schema docs.documents.batchUpdate --resolve-refs`.
