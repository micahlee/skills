# Morning Briefing Events And Logs

Morning Briefing runs unattended, so every run must be auditable. Use a structured outbox rather than directly writing Axon event stores.

## Default Paths

```text
Tasks/Morning Briefing Event Outbox.jsonl
Tasks/Morning Briefing Runs/YYYY-MM-DD-HHMMSS/run.json
```

The outbox is append-only JSONL. Axon can ingest, dedupe, deliver, and mark downstream status later.

## Event Types

Emit the domain event every run:

- `personal.morning-briefing`

Telegram is a subscriber to this event. The event is not named after Telegram; delivery success/failure belongs to Axon delivery logs.

## Event Identity

Use deterministic event IDs:

- morning briefing: event type + target date + daily note path + briefing fingerprint

Manual refreshes should not duplicate identical logical events.

## Event Payloads

Recommended payload:

```json
{
  "event_id": "morning-briefing:2026-05-29:abc123",
  "type": "personal.morning-briefing",
  "subject": "daily-note:2026-05-29",
  "occurred_at": "2026-05-29T05:12:00-04:00",
  "payload": {
    "target_date": "2026-05-29",
    "daily_note_path": "Daily Notes/2026/05/2026-05-29.md",
    "mode": "send",
    "thesis": "Today is a logistics-heavy day; win by keeping the plan narrow.",
    "focus_count": 2,
    "source_coverage": ["daily_note", "calendar", "tasks", "food"],
    "warnings": [],
    "message_fingerprint": "abc123",
    "message": "Morning Briefing · Fri May 29\n\nToday is a logistics-heavy day..."
  }
}
```

`payload.message` is the only field the Telegram subscriber should send. Keep it exactly equal to the compact Telegram-ready briefing. Do not include full email bodies, full private journal text, long source note bodies, or reasoning traces in payloads.

## Axon Event Publish

In `send` mode, after rendering the message, publish the Telegram request event through the Axon CLI:

```sh
/Users/micahlee/.local/bin/axon events publish \
  --profile morning-briefing-events \
  --json /tmp/morning-briefing-event.json \
  --subject "daily-note:YYYY-MM-DD" \
  --idempotency-key "morning-briefing:YYYY-MM-DD:MESSAGE_FINGERPRINT" \
  personal.morning-briefing
```

If the profile is missing, create it:

```sh
/Users/micahlee/.local/bin/axon clients create \
  --scope events:publish:personal.morning-briefing \
  --profile morning-briefing-events \
  --expires 8760h \
  morning-briefing-events
```

Never print bearer tokens.

## Run Log

Every write-mode run writes one `run.json`:

```json
{
  "run_id": "2026-05-29T051200-0400",
  "mode": "send",
  "target_date": "2026-05-29",
  "timezone": "America/New_York",
  "daily_note_path": "Daily Notes/2026/05/2026-05-29.md",
  "sources": {
    "read": ["daily_note", "calendar", "tasks"],
    "unavailable": []
  },
  "context_portfolio_paths": [],
  "context_portfolio_available": false,
  "sections_rendered": ["today", "hard_commitments", "focus", "body_food", "prayer", "watch"],
  "events": [],
  "telegram_subscriber_expected": true,
  "warnings": []
}
```

Preview mode should not write a run log unless explicitly requested for debugging.

## Rerun And Send Policy

- Scheduled `/morning-briefing send` publishes `personal.morning-briefing`; the scheduled workflow itself should use web-only delivery.
- Manual `/morning-briefing refresh` does not send Telegram by default.
- Manual `/morning-briefing send` may publish another event when the briefing content changes. Identical messages should reuse the same idempotency key.
- V1 does not attempt material-change notification. Document material-change detection as future work.
