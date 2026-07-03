# Daily Note Events And Logs

Daily-note processing is unattended, so every run must be auditable. Use a structured outbox rather than directly writing Axon event stores.

## Default Paths

```text
Tasks/Daily Note State.json
Tasks/Daily Note State/YYYY-MM-DD.json
Tasks/Daily Note Event Outbox.jsonl
Tasks/Daily Note Runs/YYYY-MM-DD-HHMMSS/run.json
Tasks/Daily Note Runs/YYYY-MM-DD-HHMMSS/snapshots/
```

`Tasks/Daily Note State.json` is the cross-day task registry. `Tasks/Daily Note State/YYYY-MM-DD.json` is the per-note sidecar for clean-note rendering and reconciliation.

The outbox is append-only JSONL. Each line is one compact task-scoped event. Axon can ingest, dedupe, and mark delivery later.

## Event Identity

Use deterministic event IDs for idempotent logical facts:

- `decision_requested`: event type + processing date + task ref + reason
- `completed`: event type + task ref + completion date
- `recurrence_advanced`: event type + task ref + completion date + old due + new due
- `promoted`: event type + original daily note path/line fingerprint + destination task ref
- `agent_candidate`: event type + processing date + task ref

Same logical fact means same event ID. New day or new state means new event ID.

## Event Types

Publish events for material state changes and workflow opportunities:

- `obsidian.task.completed`
- `obsidian.task.recurrence_advanced`
- `obsidian.task.promoted`
- `obsidian.task.decision_requested`
- `obsidian.task.agent_candidate`

Do not publish an event merely because a task was rendered into today's note unless another workflow explicitly needs that later.

## Decision Requested

Publish `obsidian.task.decision_requested` every processing run for every current stuck/unclear item. Axon owns notification cadence and dashboard state.

Recommended envelope:

```json
{
  "event_id": "daily-note:decision:2026-05-29:obsidian-task-buy-carrie-flowers:repeated_carryover",
  "type": "obsidian.task.decision_requested",
  "subject": "obsidian-task:task-buy-carrie-flowers",
  "occurred_at": "2026-05-29T07:10:00-04:00",
  "payload": {
    "source_task_id": "task-buy-carrie-flowers",
    "source_note_path": "Tasks/Recurring.md",
    "daily_note_path": "Daily Notes/2026/05/2026-05-29.md",
    "processing_date": "2026-05-29",
    "reason": "repeated_carryover",
    "occurrence_count": 4,
    "last_seen_dates": ["2026-05-26", "2026-05-27", "2026-05-28", "2026-05-29"],
    "suggested_actions": ["do_today", "clarify_next_action", "schedule", "snooze", "drop"],
    "prompt": "This task has carried forward 4 times. What should happen to it?"
  }
}
```

## Agent Candidate

Recommended payload fields:

- `task_ref`
- `source_uri`
- `task_text`
- `suggested_agent`
- `repo_path` when known
- `risk`: `low`, `medium`, or `high`
- `why_runnable`
- `blocking_questions`

Do not start work from the daily-note skill. Let Axon workflows decide.

## Run Log

Every run writes one `run.json` with enough detail to audit unattended behavior.

Recommended shape:

```json
{
  "run_id": "2026-05-29T071000-0400",
  "processing_date": "2026-05-29",
  "target_daily_note": "Daily Notes/2026/05/2026-05-29.md",
  "reconciled": [],
  "recurrence_advanced": [],
  "promoted": [],
  "decision_events": [],
  "agent_candidate_events": [],
  "selection": {
    "focus_tasks": [],
    "routines": [],
    "needs_decision_shown": [],
    "agent_queue_shown": []
  },
  "snapshots": [],
  "warnings": []
}
```

Snapshot only canonical files that will be changed. Keep daily notes as historical records.

## Daily Note Visibility

The daily note should not show routine event chatter or implementation/audit details. Put processing counts, event IDs, source warnings, and snapshots in sidecars and run logs.

Only add a short human-facing note to `## Context` when it changes how Micah should trust or use the daily note, for example:

```markdown
Basecamp was unavailable, so external assignment coverage may be incomplete.
```
