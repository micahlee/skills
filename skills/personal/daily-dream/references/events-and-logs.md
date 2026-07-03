# Daily Dream Events And Logs

Daily Dream writes events to a structured outbox. Axon or future morning briefing workflows can ingest them later.

## Default Paths

```text
Tasks/Dream Event Outbox.jsonl
Tasks/Dream Runs/YYYY-MM-DD-HHMMSS/run.json
```

Use a separate outbox from daily-note task events.

## Event Types

Publish compact events for completed synthesis and workflow opportunities:

- `obsidian.daily_dream.generated`
- `obsidian.daily_dream.nudge_prepared`
- `obsidian.monthly_dream.day_updated`
- `obsidian.monthly_dream.synthesis_updated`
- `obsidian.daily_dream.decision_requested`
- `obsidian.daily_dream.action_candidate`

## Event Identity

Use deterministic event IDs:

- generated: event type + target date + daily note path
- nudge: event type + source date + tomorrow date
- monthly day updated: event type + date + month note path
- monthly synthesis updated: event type + year-month + synthesis version/fingerprint
- decision/action: event type + target date + evidence fingerprint + reason

Rerunning the same logical pass should not duplicate events.

## Payload Guidance

Payloads should include:

- target date
- note paths touched
- themes
- signal summaries
- open questions
- Morning Nudge bullets
- source coverage
- confidence: `strong`, `possible`, or `weak`
- warnings

Do not include full note bodies or full email bodies.

## Action And Decision Events

Emit only when the pattern is strong enough and the follow-up is clear.

Examples:

- repeated low recovery plus overloaded task plans -> decision about on-call task caps
- repeated late eating after evening commitments -> candidate experiment
- repeated unfinished project task -> probably leave to daily-note task decision events unless the reflection adds meaningful context

Most observations should remain observations.

## Run Log

Every run writes a structured log:

```json
{
  "run_id": "2026-05-29T230000-0400",
  "mode": "single-day",
  "target_dates": ["2026-05-29"],
  "daily_notes_touched": [],
  "monthly_notes_touched": [],
  "sources": {
    "tier1": [],
    "tier2": [],
    "tier3": []
  },
  "events": [],
  "warnings": []
}
```

The daily Dream gets a brief coverage line; the run log gets details.
