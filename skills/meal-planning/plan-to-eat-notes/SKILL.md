---
name: plan-to-eat-notes
description: Annotate a Plan to Eat monthly meal planner with notes for family calendar events that affect dinner. Idempotent and safe to re-run. Triggers on phrases like "add calendar notes to plan to eat", "annotate the meal plan for [month]", "sync the family calendar into plan to eat", or "plan to eat notes for [month]".
---

# Plan to Eat — Family Calendar Notes

Annotate the Plan to Eat planner with one note per dinner-affecting event from the user's family calendar, so the user can pick meals that match the shape of each day. Scope is annotation only — no meal suggestions.

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory to collect the family calendar ID, timezone, dinner-event threshold, and CLI names. The script writes `~/.config/agent-skills/plan-to-eat-notes.json`. Read that file before replacing `<family-calendar-id>` or assuming a timezone.

**Source calendar:** ask the user which calendar to use, or use the configured family-calendar ID.
**PTE CLI:** `plantoeat` (already installed and authenticated)

## Classification heuristic

Flag an event as dinner-affecting if either:

1. **Timed event starts at or after 4:00pm** local time (America/New_York), OR
2. **All-day / multi-day event** — flag every day in the range.

Later evening events are still flagged — they don't necessarily displace dinner, but they shape meal planning (timing, portability, leftovers strategy). The user makes that call from the event name.

Do **not** flag: events starting before 4:00pm (e.g., morning meeting, afternoon lesson).

**Note text format:** just the event name (trimmed). No start time, no editorializing.

Examples:
- `Skating practice`
- `Restaurant reservation`
- `Family trip`

Don't add times, don't add "dinner out", "food likely provided", "quick dinner", etc. The user draws those conclusions from the event name alone.

## Workflow

### Step 1 — resolve the target month

User gives a month ("May 2026", "next month", etc.). Compute:
- `month_start` = first day of month (YYYY-MM-DD)
- `month_end` = first day of following month (YYYY-MM-DD, exclusive)

### Step 2 — pull family calendar events

Use an available Google Calendar connector or CLI:

```
calendarId: "<family-calendar-id>"
startTime: "<month_start>T00:00:00-04:00"
endTime: "<month_end>T00:00:00-04:00"
orderBy: "startTime"
pageSize: 250
timeZone: "America/New_York"
```

Handle pagination if `nextPageToken` is returned.

### Step 3 — classify events → desired notes

For each event, produce zero or more `(date, title)` tuples:

- **All-day / multi-day** (event has `start.date`, no `start.dateTime`): emit one tuple per day in `[start.date, end.date)` (end is exclusive in Google Calendar for all-day events). Title = event `summary`, trimmed.
- **Timed event** (`start.dateTime`): parse the start time in America/New_York. If the start time is at or after 16:00, emit one tuple `(date, "<summary>")` — event name only, trimmed, no time. Otherwise skip.

Dedupe exact `(date, title)` duplicates.

### Step 4 — pull existing PTE notes

```
plantoeat plan --days <N> --json
```

Choose `N` large enough to cover `month_end`. If today is before `month_start`, `N = (month_end − today).days`. If today is inside the month, same formula.

Parse the output. Build a set `existing = { (item.date, item.title) : item.kind == "note" }` filtered to the target month.

### Step 5 — compute and present the diff

```
to_create = desired - existing
```

Present `to_create` as a compact table grouped by date so the user can scan it:

```
May 1   Family trip
May 2   Family trip
May 4   Skating practice 5:30pm
May 5   Evening event 6:30pm
...
```

Also report how many notes were already in place (skipped).

Ask for confirmation before writing.

### Step 6 — write notes

For each entry in `to_create`:

```
plantoeat note <YYYY-MM-DD> "<title>"
```

Do this sequentially (one at a time) — easier to report failures, and the volume is small (≈10–20/month). No delay needed.

Track successes and failures. Report at the end:

```
Created 12 notes, skipped 3 already present. 0 failures.
```

## Idempotency

The `(date, title)` check in Step 5 is the only idempotency mechanism. Re-running for the same month after it's already been applied creates zero new notes.

The skill is **purely additive** — it never deletes notes. If a calendar event is later cancelled, the corresponding PTE note stays until manually removed. This is a deliberate tradeoff for simplicity and safety (no risk of deleting a user-added note).

## Edge cases

- **Multi-day trips that extend past month_end** — only flag days within the target month.
- **Multi-day trips that start before month_start** — only flag days within the target month.
- **Recurring events** — Google Calendar returns expanded instances when `orderBy=startTime`. No special handling needed; each instance is classified independently.
- **Events with no summary** — skip.
- **Events marked `transparency: transparent`** — still flag if they meet the time criteria. "Free/busy" is orthogonal to dinner impact (e.g., a transparent "3v3 Hockey" wouldn't meet the time bar anyway).
- **Timezone** — family calendar is `America/New_York`. Always resolve start times in that zone when classifying.

## Verification

After a run:
- Spot-check one day in the Plan to Eat UI (https://app.plantoeat.com/planner).
- Re-run immediately; expect "0 notes created, N skipped."

## Reference

- Calendar pull pattern: use the configured Google Workspace CLI.
- CLI-wrapping skill style: keep commands explicit, dry-run before writes, then verify after writes.
