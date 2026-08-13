# Events, State, And Logs

Every write-mode run is auditable. Prefer structured outboxes that Axon can ingest and deduplicate.

## Default paths

```text
Tasks/Personal Sync State.json
Tasks/Personal Sync State/YYYY-MM-DD.json
Tasks/Personal Sync Event Outbox.jsonl
Tasks/Personal Sync Runs/YYYY-MM-DD-HHMMSS/run.json
```

State stores task history, capacity observations, approvals, generated-section snapshots, and delivery dedupe keys. Human notes stay clean.

## Event types

- `personal.sync.weekly.updated`
- `personal.sync.daily.updated`
- `personal.sync.reflection.updated`
- `personal.sync.decision_requested`
- `personal.sync.agent_candidate`
- `personal.morning-briefing`
- `personal.progress-nudge.created`

## Identity

Use deterministic IDs based on event type plus the logical date/week, stable subject, reason, and content fingerprint. A rerun of the same logical fact reuses its ID. A changed approval or new state gets a new fingerprint.

Decision payloads include the evidence summary, reason, current approved state, recommended answer, and allowed actions. Never include full email bodies, full journals, or reasoning traces.

## Run log

Record:

- mode, local date, look-back and look-forward windows
- human and agent surfaces read/changed
- source coverage, freshness, and warnings
- reconciliation and selection results
- capacity inputs/output
- approvals and decisions requested
- events emitted
- snapshots of canonical files changed
- pre-write and post-write Planning Notes audit results
- whether sidecar state was loaded or bootstrapped, plus its final existence

Preview mode writes nothing unless debugging was explicitly requested.

A write-mode run is successful only when every intended human write can be
re-read, the post-write one-day Planning Notes audit passes, and the per-day
sidecar exists. Sidecar absence at the beginning of the first run is recorded
as `bootstrapped`, not as a failure.

## Axon behavior

Scheduled refreshes publish decision events rather than silently changing approved priorities. `brief send` publishes `personal.morning-briefing` with the compact external message in `payload.message`. `progress` publishes only after the deterministic helper returns `nudge_required`.
