---
name: process-inbox
description: Process a single Obsidian Inbox note into PARA destinations, task lists, shopping lists, reading lists, daily notes, and calendar entries. Use when the user says /process-inbox, asks to process or triage their Obsidian inbox, or wants inbox items organized into their vault.
---

# Process Inbox

Use this skill to triage the user's single Obsidian `Inbox.md` into the configured vault destinations.

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory before first use. It writes:

```text
~/.config/agent-skills/process-inbox.json
```

Read that config before assuming vault paths, destination paths, daily note patterns, calendar IDs, or run limits.

## Run Modes

Manual `/process-inbox` defaults to an interactive run:

1. Read the Inbox and build a routing proposal.
2. Show numbered proposed moves, destination entries, new destinations, duplicate markings, failures, and calendar entries.
3. Wait for approval, partial approval, revisions, or cancellation.
4. Apply only approved moves.

Automation/AFK runs are explicit, for example `/process-inbox --auto`:

1. Skip items already tagged `#inbox/ambiguous`, `#inbox/failed`, or `#inbox/duplicate`.
2. Process only high-confidence eligible items, respecting the configured run limit.
3. Leave uncertain items in the Inbox with the correct tag and inline explanation.
4. Return a compact run summary.

## Required Reference

Before classifying or moving items, read [references/routing.md](references/routing.md). It contains the routing rules, tags, destination behavior, calendar boundary, and safe-write requirements.

## Core Workflow

1. Load the inbox processing config.
2. Build a fresh destination index from configured vault paths; do not use a persistent destination cache.
3. Parse the Inbox as top-level bullet blocks. Nested bullets and indented continuation lines belong to the parent item.
4. Classify each unprocessed item using the routing rules.
5. Inspect public links when needed; do not route URLs from domain alone.
6. Detect duplicates against the intended destination, not the whole vault.
7. In interactive mode, show the routing proposal before mutation.
8. Apply approved or automation-eligible moves as safe moves.
9. Prepend moved-item log entries to the Processing Log.
10. Return a run summary with moved, ambiguous, duplicate, and failed counts.

## Write Rules

Prefer the `obsidian` CLI for vault writes when Obsidian is available. For automation runs where Obsidian is unavailable, a configured filesystem fallback is allowed only as a safe move:

- Build all edits in memory first.
- Validate each original Inbox item still exists exactly once.
- Back up every file that will be mutated.
- Apply destination, inbox, daily note, and processing-log edits carefully.
- Treat calendar-worthy items as processed only after both the Obsidian move and calendar creation succeed.
- If a required write or integration fails, leave the original item in the Inbox with `#inbox/failed` and an inline error note.

## Calendar

Use the configured default Google Calendar for calendar-worthy items. If no Google Calendar connector or CLI is available, mark the item as `#inbox/failed` with the intended calendar details instead of moving it.

