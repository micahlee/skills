#!/usr/bin/env python3
"""plan-to-eat-curate — propose tag/metadata updates in named batches.

Pipeline:
  1. Load configured state; get live recipe IDs.
  2. For each non-excluded live recipe, pull `recipes show` into the cache
     (skipped if already cached; pass --refresh to refetch).
  3. Apply heuristics to propose leftover-friendly / freezer-friendly / effort.
  4. Group confident proposals into batches by dominant pattern.
  5. Write the review doc (per-batch heading + table).

Does NOT write to PTE. Review the doc, then commit batches in a follow-up.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime

CONFIG_PATH = os.path.expanduser("~/.config/agent-skills/plan-to-eat-curate.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


CONFIG = load_config()
STATE_PATH = os.path.expanduser(
    os.environ.get("PLANTOEAT_CURATE_STATE", CONFIG.get("state_file", "~/.config/agent-skills/plan-to-eat-curate-state.json"))
)
STATE_DIR = os.path.dirname(STATE_PATH)
PLANTOEAT_BIN = os.environ.get("PLANTOEAT_BIN", CONFIG.get("plantoeat_cli", "plantoeat"))
GWS_BIN = os.environ.get("GWS_BIN", CONFIG.get("google_workspace_cli", "gws"))
THROTTLE_S = 0.2
FETCH_RETRIES = 3
EXCLUDED_COURSES = {"Desserts", "Drinks", "Beverages", "Appetizers"}
TODAY = date.today()
PTE_RECIPE_URL = "https://app.plantoeat.com/recipes/{rid}"

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
# CLI wrappers
# ----------------------------------------------------------------------------

def run_plantoeat(*args: str) -> str:
    last = None
    for attempt in range(FETCH_RETRIES):
        try:
            return subprocess.run(
                [PLANTOEAT_BIN, *args],
                capture_output=True, text=True, check=True, timeout=60,
            ).stdout
        except subprocess.CalledProcessError as e:
            last = e
            if attempt + 1 < FETCH_RETRIES:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"plantoeat {' '.join(args)} failed: {last}")


def gws(*args: str, json_in: str | None = None) -> str:
    cmd = [GWS_BIN, *args]
    if json_in is not None:
        cmd += ["--json", json_in]
    return subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60).stdout


def gws_json(*args: str, json_in: str | None = None) -> dict:
    out = gws(*args, json_in=json_in)
    # gws occasionally prefixes "Using keyring backend:" on stderr; ensure we
    # parse only the JSON body.
    start = out.find("{")
    if start > 0:
        out = out[start:]
    return json.loads(out)


# ----------------------------------------------------------------------------
# Recipe cache
# ----------------------------------------------------------------------------

def live_recipe_ids() -> list[str]:
    return [str(i) for i in json.loads(run_plantoeat("recipes", "list", "--ids", "--json"))]


def fetch_recipe(rid: str) -> dict:
    r = json.loads(run_plantoeat("recipes", "show", rid, "--json"))
    return {
        "title": r.get("title", ""),
        "course": r.get("course", ""),
        "cuisine": r.get("cuisine", ""),
        "yield": r.get("yield", ""),
        "prep_time": r.get("prep_time", ""),
        "cook_time": r.get("cook_time", ""),
        "total_time": r.get("total_time", ""),
        "tags": r.get("tags") or [],
        "ingredients": r.get("ingredients") or [],
        "instructions": r.get("instructions") or [],
        "fetched_at": TODAY.isoformat(),
    }


def refresh_cache(state: dict, refresh: bool) -> None:
    cache = state.setdefault("recipe_cache", {})
    live = live_recipe_ids()
    state["live_ids"] = live

    todo = [r for r in live if refresh or r not in cache]
    print(f"{len(live)} live recipes, {len(todo)} to fetch "
          f"({'refresh' if refresh else 'new only'}).", file=sys.stderr)

    for i, rid in enumerate(todo, 1):
        try:
            cache[rid] = fetch_recipe(rid)
        except Exception as e:
            print(f"  [{i}/{len(todo)}] {rid} FAILED: {e}", file=sys.stderr)
            continue
        if i % 25 == 0:
            print(f"  [{i}/{len(todo)}] fetched...", file=sys.stderr)
        if i % 10 == 0 or i == len(todo):
            save_state(state)
        time.sleep(THROTTLE_S)
    save_state(state)


# ----------------------------------------------------------------------------
# Heuristics
# ----------------------------------------------------------------------------

# Regex helpers. We lowercase titles + ingredient + instruction text and
# match against these. "\b" boundary to avoid matching substrings.
def _re(*words) -> re.Pattern:
    return re.compile(r"\b(?:" + "|".join(words) + r")\b", re.IGNORECASE)

# Reheats poorly.
FISH_RX       = _re("salmon", "tuna", "cod", "tilapia", "halibut", "mahi[- ]?mahi",
                     "sea bass", "snapper", "trout", "swordfish", "sole", "flounder")
SHELLFISH_RX  = _re("shrimp", "prawn", "scallop", "crab(?!cake)", "lobster", "mussel", "clam")
GRILLED_SW_RX = _re("quesadilla", "quesadillas", "grilled cheese", "panini",
                     "pizza", "flatbread", "wrap", "wraps", "taco salad")
SALAD_RX      = _re("salad")

# Reheats well / freezes well.
SOUP_STEW_RX  = _re("soup", "stew", "chili", "chowder", "gumbo", "goulash",
                     "bisque", "curry", "dal", "daal", "ragu", "ragout")
BRAISE_RX     = _re("braise", "braised", "carnitas", "pot roast", "pulled",
                     "shredded", "barbacoa", "birria", "tinga", "ropa vieja")
CASSEROLE_RX  = _re("casserole", "enchilada", "enchiladas", "lasagna",
                     "bake", "baked", "gratin")
MEATBALL_RX   = _re("meatball", "meatballs", "meatloaf")
SLOW_COOK_RX  = _re("slow cooker", "slow[- ]cook", "crock[- ]?pot", "crockpot",
                     "instant pot", "pressure cooker")
SHEET_PAN_RX  = _re("sheet[- ]?pan", "one[- ]pan", "one[- ]pot", "skillet",
                     "stir[- ]?fry", "fried rice")
CREAM_RX      = _re("heavy cream", "cream cheese", "crème fraîche", "creme fraiche",
                     "mascarpone")
FRESH_GREENS_RX = _re("arugula", "spinach leaves", "fresh basil", "fresh cilantro",
                       "mixed greens", "baby greens", "romaine")
RICE_DOMINANT_RX = _re("risotto", "fried rice", "rice bowl", "paella")
DOUGH_FROM_SCRATCH_RX = _re("homemade dough", "homemade pizza dough", "homemade pasta",
                             "from scratch", "homemade stock", "homemade broth",
                             "homemade bread")
DEEP_FRY_RX   = _re("deep[- ]?fry", "deep[- ]?fried", "tempura")


@dataclass
class Proposal:
    value: str  # "yes" / "no" / "quick" / "medium" / "involved"
    confidence: float  # 0..1
    rationale: str = ""


@dataclass
class RecipeSignals:
    rid: str
    title: str
    course: str
    total_min: int | None  # minutes, or None
    blob: str  # lowercased title + joined ingredients + instructions


def parse_iso_duration_minutes(s: str) -> int | None:
    if not s:
        return None
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", s)
    if not m:
        return None
    h = int(m.group(1) or 0)
    mm = int(m.group(2) or 0)
    return h * 60 + mm


def build_signals(rid: str, rec: dict) -> RecipeSignals:
    title = rec.get("title", "") or ""
    blob_parts = [title, " ".join(rec.get("ingredients") or []),
                  " ".join(rec.get("instructions") or [])]
    return RecipeSignals(
        rid=rid,
        title=title,
        course=rec.get("course", "") or "",
        total_min=parse_iso_duration_minutes(rec.get("total_time", "")),
        blob=" ".join(blob_parts).lower(),
    )


def propose_leftover(s: RecipeSignals) -> Proposal | None:
    t = s.title.lower()
    b = s.blob
    # NO signals
    if FISH_RX.search(t) or (FISH_RX.search(b) and " fish " in f" {t} "):
        return Proposal("no", 0.9, "fresh fish reheats poorly")
    if FISH_RX.search(t):
        return Proposal("no", 0.9, "fresh fish reheats poorly")
    if SHELLFISH_RX.search(t):
        return Proposal("no", 0.8, "shellfish gets rubbery reheated")
    if DEEP_FRY_RX.search(b):
        return Proposal("no", 0.8, "deep-fried goes soggy")
    if GRILLED_SW_RX.search(t):
        return Proposal("no", 0.75, "bread/crust goes soggy on reheat")
    if SALAD_RX.search(t) and "chicken salad" not in t and "pasta salad" not in t:
        return Proposal("no", 0.75, "dressed salads wilt")

    # YES signals
    if SOUP_STEW_RX.search(t):
        return Proposal("yes", 0.95, "soups/stews improve overnight")
    if CASSEROLE_RX.search(t):
        return Proposal("yes", 0.9, "casseroles reheat well")
    if MEATBALL_RX.search(t):
        return Proposal("yes", 0.9, "meatballs reheat well")
    if BRAISE_RX.search(t) or BRAISE_RX.search(b):
        return Proposal("yes", 0.9, "braised/shredded meats reheat well")
    if SLOW_COOK_RX.search(b):
        return Proposal("yes", 0.85, "slow-cooker / IP meals reheat well")
    if SOUP_STEW_RX.search(b) and any(w in t for w in ("bowl", "rice")):
        return Proposal("yes", 0.7, "saucy bowl reheats well")
    return None


def propose_freezer(s: RecipeSignals) -> Proposal | None:
    t = s.title.lower()
    b = s.blob
    # NO signals
    if FISH_RX.search(t) or SHELLFISH_RX.search(t):
        return Proposal("no", 0.75, "seafood texture suffers frozen")
    if GRILLED_SW_RX.search(t) and "pizza" in t:
        return Proposal("no", 0.8, "pizza texture poor after freeze/thaw")
    if GRILLED_SW_RX.search(t):
        return Proposal("no", 0.7, "bread-wrapped items go soggy frozen")
    if SALAD_RX.search(t) and "chicken salad" not in t and "pasta salad" not in t:
        return Proposal("no", 0.85, "salads don't freeze")
    if FRESH_GREENS_RX.search(b) and not SOUP_STEW_RX.search(t):
        return Proposal("no", 0.65, "fresh greens turn to mush frozen")
    if RICE_DOMINANT_RX.search(t):
        return Proposal("no", 0.7, "rice-forward dishes go gummy")
    if DEEP_FRY_RX.search(b):
        return Proposal("no", 0.7, "deep-fried goes soggy after thaw")

    # YES signals
    if SOUP_STEW_RX.search(t):
        return Proposal("yes", 0.95, "soups/stews freeze perfectly")
    if MEATBALL_RX.search(t):
        return Proposal("yes", 0.95, "meatballs are a freezer staple")
    if CASSEROLE_RX.search(t):
        return Proposal("yes", 0.9, "casseroles freeze well")
    if BRAISE_RX.search(t) or BRAISE_RX.search(b):
        return Proposal("yes", 0.85, "shredded/braised meat freezes well")
    if SLOW_COOK_RX.search(b) and not CREAM_RX.search(b):
        return Proposal("yes", 0.8, "slow-cooker meat freezes well")
    return None


def propose_effort(s: RecipeSignals) -> Proposal | None:
    t = s.title.lower()
    b = s.blob
    slow = bool(SLOW_COOK_RX.search(b))
    # Use total_time if set.
    if s.total_min is not None:
        if slow:
            return Proposal("quick", 0.9,
                            f"slow-cooker (total {s.total_min}m, hands-off)")
        if s.total_min <= 30:
            return Proposal("quick", 0.95, f"total {s.total_min} min")
        if s.total_min <= 60:
            return Proposal("medium", 0.85, f"total {s.total_min} min")
        return Proposal("involved", 0.85, f"total {s.total_min} min")

    # Fallback: keyword heuristics.
    if slow:
        return Proposal("quick", 0.85, "slow-cooker / IP (hands-off)")
    if SHEET_PAN_RX.search(t):
        return Proposal("quick", 0.8, "sheet-pan / skillet / one-pot in title")
    if DOUGH_FROM_SCRATCH_RX.search(b):
        return Proposal("involved", 0.8, "from-scratch doughs/stocks")
    return None


# ----------------------------------------------------------------------------
# Batching
# ----------------------------------------------------------------------------

@dataclass
class RecipeRow:
    rid: str
    title: str
    course: str
    leftover: Proposal | None
    freezer: Proposal | None
    effort: Proposal | None
    bucket: str


def bucket_of(s: RecipeSignals) -> str:
    t = s.title.lower()
    b = s.blob
    # Priority ordered — first match wins so buckets are disjoint.
    if FISH_RX.search(t) or SHELLFISH_RX.search(t):
        return "Fish & Seafood"
    if SOUP_STEW_RX.search(t):
        return "Soups, Stews & Chili"
    if CASSEROLE_RX.search(t):
        return "Casseroles & Bakes"
    if MEATBALL_RX.search(t):
        return "Meatballs & Meatloaf"
    if BRAISE_RX.search(t) or BRAISE_RX.search(b):
        return "Slow-cooker & Braised Proteins"
    if SLOW_COOK_RX.search(b):
        return "Slow-cooker & Braised Proteins"
    if GRILLED_SW_RX.search(t):
        return "Pizza & Sandwiches"
    if SALAD_RX.search(t) and "chicken salad" not in t and "pasta salad" not in t:
        return "Salads"
    if "taco" in t or "burrito" in t or "quesadilla" in t:
        return "Tacos & Burritos"
    if "burger" in t:
        return "Burgers"
    if "pasta" in t or "spaghetti" in t or "ravioli" in t or "lasagna" in t or "noodle" in t:
        return "Pasta & Noodles"
    if SHEET_PAN_RX.search(t):
        return "Skillet & Sheet-Pan Dinners"
    if "bowl" in t or "rice" in t:
        return "Bowls & Rice Dishes"
    if "chicken" in t or "pork" in t or "beef" in t or "steak" in t or "turkey" in t:
        return "Other Proteins"
    return "Miscellaneous"


BUCKET_ORDER = [
    "Soups, Stews & Chili",
    "Slow-cooker & Braised Proteins",
    "Casseroles & Bakes",
    "Meatballs & Meatloaf",
    "Tacos & Burritos",
    "Burgers",
    "Bowls & Rice Dishes",
    "Skillet & Sheet-Pan Dinners",
    "Other Proteins",
    "Pasta & Noodles",
    "Fish & Seafood",
    "Pizza & Sandwiches",
    "Salads",
    "Miscellaneous",
]


BATCH_SIZE = 15


def letter_labels() -> list[str]:
    # A, B, ..., Z, AA, BB, CC, ..., ZZ (double letters only, matches spec).
    labels = [chr(ord("A") + i) for i in range(26)]
    labels += [chr(ord("A") + i) * 2 for i in range(26)]
    return labels


def filter_existing(row: RecipeRow, existing_tags: list[str]) -> RecipeRow:
    """Drop proposals that duplicate a tag already on the recipe."""
    lower_tags = {t.lower() for t in existing_tags}

    def skip(p: Proposal | None, names: list[str]) -> Proposal | None:
        if p is None:
            return None
        if p.value == "yes" and any(n in lower_tags for n in names):
            return None
        if p.value == "no" and any(f"not {n}" in lower_tags for n in names):
            return None
        return p

    row.leftover = skip(row.leftover, ["leftover-friendly", "leftovers"])
    row.freezer = skip(row.freezer, ["freezer-friendly", "freezer"])
    if row.effort and row.effort.value in lower_tags:
        row.effort = None
    return row


def build_rows(state: dict) -> list[RecipeRow]:
    cache = state.get("recipe_cache", {})
    live = set(state.get("live_ids", []))
    rows: list[RecipeRow] = []
    for rid, rec in cache.items():
        if rid not in live:
            continue
        if (rec.get("course") or "") in EXCLUDED_COURSES:
            continue
        s = build_signals(rid, rec)
        row = RecipeRow(
            rid=rid,
            title=rec.get("title", f"recipe #{rid}"),
            course=rec.get("course", ""),
            leftover=propose_leftover(s),
            freezer=propose_freezer(s),
            effort=propose_effort(s),
            bucket=bucket_of(s),
        )
        row = filter_existing(row, rec.get("tags") or [])
        # Only keep rows with at least one confident proposal.
        props = [p for p in (row.leftover, row.freezer, row.effort) if p]
        if not props or max(p.confidence for p in props) < 0.7:
            continue
        rows.append(row)
    return rows


def group_into_batches(rows: list[RecipeRow]) -> list[tuple[str, str, list[RecipeRow]]]:
    """Returns [(label, bucket_name, rows), ...]."""
    by_bucket: dict[str, list[RecipeRow]] = {}
    for r in rows:
        by_bucket.setdefault(r.bucket, []).append(r)
    for bucket in by_bucket:
        by_bucket[bucket].sort(key=lambda r: r.title.lower())

    ordered_buckets = [b for b in BUCKET_ORDER if b in by_bucket]
    ordered_buckets += [b for b in by_bucket if b not in BUCKET_ORDER]

    labels = letter_labels()
    out: list[tuple[str, str, list[RecipeRow]]] = []
    i = 0
    for bucket in ordered_buckets:
        items = by_bucket[bucket]
        chunks = [items[j:j + BATCH_SIZE] for j in range(0, len(items), BATCH_SIZE)]
        for idx, chunk in enumerate(chunks):
            label = labels[i]
            i += 1
            suffix = f" ({idx + 1}/{len(chunks)})" if len(chunks) > 1 else ""
            out.append((label, bucket + suffix, chunk))
    return out


# ----------------------------------------------------------------------------
# Google Docs rendering
# ----------------------------------------------------------------------------

def fmt_proposal(p: Proposal | None) -> str:
    if p is None:
        return "—"
    return f"{p.value.capitalize()} · {p.confidence:.2f}"


def ensure_doc_id(state: dict) -> str:
    if state.get("doc_id"):
        return state["doc_id"]
    if CONFIG.get("proposal_doc_id"):
        state["doc_id"] = CONFIG["proposal_doc_id"]
        save_state(state)
        return state["doc_id"]
    # Create a fresh doc.
    print("No doc_id in state — creating a new Google Doc.", file=sys.stderr)
    res = gws_json("docs", "documents", "create",
                   "--json", '{"title": "Plan to Eat — Tag Curation Proposals"}')
    doc_id = res["documentId"]
    state["doc_id"] = doc_id
    save_state(state)
    print(f"Created doc: https://docs.google.com/document/d/{doc_id}/edit",
          file=sys.stderr)
    return doc_id


def doc_end_index(doc_id: str) -> int:
    doc = gws_json("docs", "documents", "get",
                   "--params", json.dumps({"documentId": doc_id, "fields": "body.content(endIndex)"}))
    return max(c["endIndex"] for c in doc["body"]["content"])


def clear_doc(doc_id: str) -> None:
    end = doc_end_index(doc_id)
    if end <= 2:
        return
    gws("docs", "documents", "batchUpdate",
        "--params", json.dumps({"documentId": doc_id}),
        json_in=json.dumps({"requests": [
            {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end - 1}}}
        ]}))


def send_requests(doc_id: str, requests: list[dict]) -> None:
    if not requests:
        return
    gws("docs", "documents", "batchUpdate",
        "--params", json.dumps({"documentId": doc_id}),
        json_in=json.dumps({"requests": requests}))


def write_header(doc_id: str, total_recipes: int, batch_count: int) -> None:
    """Write title + subtitle at the top of an empty doc."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = "Plan to Eat — Tag Curation Proposals\n"
    subtitle = (
        f"Updated {now} · {total_recipes} recipes across {batch_count} batches · "
        f"heuristics: leftover-friendly, freezer-friendly, effort\n\n"
    )
    text = title + subtitle
    requests = [
        {"insertText": {"location": {"index": 1}, "text": text}},
        {"updateParagraphStyle": {
            "range": {"startIndex": 1, "endIndex": 1 + len(text)},
            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
            "fields": "namedStyleType",
        }},
        {"updateTextStyle": {
            "range": {"startIndex": 1, "endIndex": 1 + len(text)},
            "textStyle": {"bold": False},
            "fields": "bold",
        }},
        {"updateTextStyle": {
            "range": {"startIndex": 1, "endIndex": 1 + len(text)},
            "textStyle": {},
            "fields": "link",
        }},
        {"updateParagraphStyle": {
            "range": {"startIndex": 1, "endIndex": 1 + len(title)},
            "paragraphStyle": {"namedStyleType": "TITLE"},
            "fields": "namedStyleType",
        }},
        {"updateParagraphStyle": {
            "range": {"startIndex": 1 + len(title),
                      "endIndex": 1 + len(title) + len(subtitle)},
            "paragraphStyle": {"namedStyleType": "SUBTITLE"},
            "fields": "namedStyleType",
        }},
    ]
    send_requests(doc_id, requests)


def append_batch(doc_id: str, label: str, bucket: str, rows: list[RecipeRow]) -> None:
    """Append a heading + table for one batch. Two round-trips: one to insert
    the heading + empty table, one to populate cells."""
    header_text = f"Batch {label} — {bucket}\n"
    # Step 1: append heading + empty table at doc end.
    end = doc_end_index(doc_id)  # end points at final "\n"
    insert_at = end - 1  # insert before the trailing newline

    n_rows = 1 + len(rows)  # +1 for header row
    send_requests(doc_id, [
        {"insertText": {"location": {"index": insert_at}, "text": header_text}},
        {"updateParagraphStyle": {
            "range": {"startIndex": insert_at,
                      "endIndex": insert_at + len(header_text)},
            "paragraphStyle": {"namedStyleType": "HEADING_1"},
            "fields": "namedStyleType",
        }},
        {"insertTable": {
            "location": {"index": insert_at + len(header_text)},
            "rows": n_rows,
            "columns": 4,
        }},
    ])

    # Step 2: find the just-inserted table and populate its cells.
    # Re-fetch the doc and locate the table we just added (last table in doc).
    doc = gws_json("docs", "documents", "get",
                   "--params", json.dumps({"documentId": doc_id,
                                           "fields": "body.content"}))
    tables = [(c["startIndex"], c) for c in doc["body"]["content"] if "table" in c]
    if not tables:
        raise RuntimeError("expected at least one table in doc after insertTable")
    _, table_elem = tables[-1]
    table = table_elem["table"]

    # Walk rows/cells in document order, collect per-cell insertion indices.
    # Per the Docs API, each cell's first paragraph's first element starts
    # where we'll insert our text. We use tableCellInsertion indices.
    header_cells = ["Recipe", "Leftover-friendly", "Freezer-friendly", "Effort"]
    cell_texts: list[list[tuple[str, list[tuple[int, int]], list[tuple[int, int, str]]]]] = []
    # header
    cell_texts.append([(h, [(0, len(h))], []) for h in header_cells])
    # data rows
    for r in rows:
        title = r.title
        url = PTE_RECIPE_URL.format(rid=r.rid)
        cell_texts.append([
            (title, [(0, len(title))], [(0, len(title), url)]),
            (fmt_proposal(r.leftover), [], []),
            (fmt_proposal(r.freezer), [], []),
            (fmt_proposal(r.effort), [], []),
        ])

    # Collect cell start indices from the fetched table structure.
    populate_reqs: list[dict] = []
    # We need to insert into cells in REVERSE document order so indices earlier
    # in the doc remain valid as later insertions shift nothing before them.
    flat_cells: list[tuple[int, str, list, list]] = []
    for row_i, row in enumerate(table["tableRows"]):
        for col_i, cell in enumerate(row["tableCells"]):
            # cell["content"] is a list; first paragraph's first element index
            para = cell["content"][0]["paragraph"]
            first_el_start = para["elements"][0]["startIndex"]
            text, bolds, links = cell_texts[row_i][col_i]
            flat_cells.append((first_el_start, text, bolds, links))
    # Sort descending by start index.
    flat_cells.sort(key=lambda c: -c[0])
    for start, text, bolds, links in flat_cells:
        if not text:
            continue
        populate_reqs.append({
            "insertText": {"location": {"index": start}, "text": text}
        })

    # Apply bold + links + header-row styling in a separate batch AFTER text.
    # We'll compute fresh cell indices from another doc fetch once all text is in.
    send_requests(doc_id, populate_reqs)

    # Re-fetch, then apply bolds (header row + recipe titles) and links.
    doc = gws_json("docs", "documents", "get",
                   "--params", json.dumps({"documentId": doc_id,
                                           "fields": "body.content"}))
    tables = [c for c in doc["body"]["content"] if "table" in c]
    table = tables[-1]["table"]
    style_reqs: list[dict] = []
    for row_i, row in enumerate(table["tableRows"]):
        for col_i, cell in enumerate(row["tableCells"]):
            para = cell["content"][0]["paragraph"]
            elements = para.get("elements", [])
            if not elements:
                continue
            cell_start = elements[0]["startIndex"]
            # Header row — bold everything.
            if row_i == 0:
                cell_text = "".join(e.get("textRun", {}).get("content", "") for e in elements).rstrip("\n")
                if cell_text:
                    style_reqs.append({
                        "updateTextStyle": {
                            "range": {"startIndex": cell_start,
                                      "endIndex": cell_start + len(cell_text)},
                            "textStyle": {"bold": True},
                            "fields": "bold",
                        }
                    })
                continue
            # Data row — bold + link the recipe title (col 0).
            if col_i == 0:
                r = rows[row_i - 1]
                url = PTE_RECIPE_URL.format(rid=r.rid)
                title_len = len(r.title)
                style_reqs.append({
                    "updateTextStyle": {
                        "range": {"startIndex": cell_start,
                                  "endIndex": cell_start + title_len},
                        "textStyle": {"bold": True, "link": {"url": url}},
                        "fields": "bold,link",
                    }
                })
    send_requests(doc_id, style_reqs)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="refetch every recipe (ignoring cache)")
    ap.add_argument("--skip-fetch", action="store_true",
                    help="skip network fetch; use existing cache only")
    ap.add_argument("--limit", type=int, default=0,
                    help="render only the first N batches (dev/debug)")
    args = ap.parse_args()

    state = load_state()
    if not args.skip_fetch:
        refresh_cache(state, refresh=args.refresh)
    elif "live_ids" not in state:
        state["live_ids"] = live_recipe_ids()

    rows = build_rows(state)
    print(f"\n{len(rows)} recipes have at least one confident proposal.",
          file=sys.stderr)
    batches = group_into_batches(rows)
    print(f"Grouped into {len(batches)} batches across "
          f"{len(set(b[1].split(' (')[0] for b in batches))} buckets.",
          file=sys.stderr)

    if args.limit:
        batches = batches[:args.limit]
    doc_id = ensure_doc_id(state)
    clear_doc(doc_id)
    write_header(doc_id, sum(len(b[2]) for b in batches), len(batches))
    for i, (label, bucket, batch_rows) in enumerate(batches, 1):
        print(f"  [{i}/{len(batches)}] Batch {label} — {bucket} "
              f"({len(batch_rows)} rows)...", file=sys.stderr)
        append_batch(doc_id, label, bucket, batch_rows)

    print(f"\nDoc: https://docs.google.com/document/d/{doc_id}/edit", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
