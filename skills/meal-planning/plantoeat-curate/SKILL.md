---
name: plantoeat-curate
description: Propose tag/metadata updates (leftover-friendly, freezer-friendly, effort) for Plan to Eat recipes using heuristics. Writes a Google Doc of proposals organized into named batches (A, B, C, …, AA, BB, CC) so they can be reviewed and approved/revised in small chunks. Triggers on phrases like "curate PTE tags", "propose recipe metadata", "update leftover-friendly tags", "refine plan to eat recipes".
---

# plantoeat-curate

Generates a Google Doc of proposed tag/metadata updates for Plan to Eat recipes, grouped into named review batches. Does not write to PTE — review the doc, then tell Claude which batches to commit (or revise).

**State:** `~/.plantoeat/curate/state.json` — persistent cache of recipe metadata + the review doc ID.

## Run

```
python3 scripts/curate.py
```

First run: pulls `recipes show` for every non-excluded live recipe (~90s with throttling). Subsequent runs re-use the cache; pass `--refresh` to refetch.

## Tags proposed

- **leftover-friendly** — reheats well.
  - YES: soups/stews/chili/curry, braises, shredded proteins, casseroles, meatballs.
  - NO: fresh fish/seafood, deep-fried, pizza/quesadillas/grilled sandwiches, dressed salads.
- **freezer-friendly** — freezes and thaws well. Stricter subset of leftover-friendly.
  - NO: fresh leafy greens, heavy-cream-based, pizza, rice-dominant.
  - YES: soups/stews, cooked/shredded meats, meatballs, casseroles, tomato sauces.
- **effort** — quick / medium / involved. Uses PTE's `total_time` when set; falls back to keyword matching (slow cooker / sheet pan / one-pot = quick; from-scratch doughs/stocks = involved).

Proposals that would duplicate an already-set tag are skipped. Recipes with no confident proposal across all three signals are omitted from the doc.

## Review workflow

1. Run the script. It writes the doc and prints the URL.
2. Open the doc. Each batch is a Heading 1 (Batch A, B, …) with a table:
   `Recipe | Leftover-friendly | Freezer-friendly | Effort`. Recipe titles link to PTE.
3. Tell Claude what to do per batch:
   - "Commit A, B, and D."
   - "Batch C looks wrong — Chicken Taco Soup should NOT be freezer-friendly; redo that batch."
   - "Skip the rest for now."
4. The commit step writes back to PTE (via `plantoeat recipes update`, once that CLI command exists).

## Batch grouping

Recipes are bucketed by dominant heuristic pattern (Soups & Stews, Slow-cooker Proteins, Fish & Seafood, Casseroles & Bakes, Skillet Quick Dinners, Salads, Pizza & Sandwiches, Pasta, Misc). Each bucket is split into chunks of ~15 and labeled A, B, C, …, Z, AA, BB, CC, …

## Editing heuristics

All heuristics live in `curate.py`. Tweak the regex lists / scoring thresholds and re-run — the doc regenerates fully each time.
