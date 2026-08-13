# Task Model And Selection

The human planning note is a bounded work surface. Canonical task state remains in Obsidian task notes, Basecamp, or another source system.

## Task identity

Every generated todo has a stable TaskRef in sidecar state:

- `source_type`, `source_id`, and `source_uri`
- `completion_strategy`: `sync_back`, `advance_recurrence`, `external_complete`, `external_link_only`, or `no_sync`
- `owner`: `micah`, `agent`, `shared`, or `external`
- visible source link when useful

Never add hidden same-line task-ref comments to new human notes.

## Reconciliation order

1. Load current/recent planning notes, registry, and per-note sidecars.
2. Reconcile completed sourced instances to canonical sources.
3. Advance recurring tasks from their fixed scheduled date unless explicitly after-completion.
4. Promote clear human-created todos into canonical sources.
5. Request decisions for ambiguous, vague, or repeatedly carried tasks.
6. Update skip, completion, and decision history.
7. Select today's bounded todos from canonical state and the approved weekly plan.
8. Merge the clean Todos section and write sidecars/logs.

Use exact TaskRefs, source locations, visible links, or fingerprints. Never mutate a source by task text alone.

## Daily selection

- `Must`: deadline, commitment, blocker, required preparation, or explicitly chosen for today; default max 3.
- `Should`: valuable next actions that fit predicted capacity; default max 3.
- `Could`: genuinely optional work; default max 3.
- Routines may appear as ordinary todos when due and useful; do not create a separate Routines surface.
- Agent-doable work stays in agent context/events unless Micah must act.
- Calendar events never become checkboxes merely because they exist.

Weekly outcomes are candidates, not a command to schedule every outcome. Pre-seed future notes only for a real day-specific reason: deadline, preparation dependency, appointment, explicit commitment, or deliberate choice.

## Carryover

Prefer continuing plausible in-motion work, but treat repeated unchecked appearances as skip signals. After 2–3 skips, stop resurfacing automatically and request a decision: do, clarify, schedule, snooze, shrink, delegate, or drop.

## Failure policy

Hard fail on unsafe note/registry writes or ambiguous source mutation. Degrade when one external source is unavailable. Log technical detail in agent state; tell Micah only when the missing source changes trust in the visible plan.
