---
name: run-analysis
description: Analyze a specific Apple Health run from Axon by run/workout ID, using healthFitnessRunAnalysis metrics, producing a coaching summary, and writing a durable Obsidian run journal entry. Use when the user says /run-analysis, asks to analyze a run ID, compare a run, journal a run, or summarize run HR, route, drift, dynamics, or training signals from Axon.
---

# Run Analysis

## Purpose

Analyze one run from Axon, turn the computed fitness signals into a coach-style summary, and save the result in Obsidian.

## Data Source

Use Axon GraphQL through the local CLI. Prefer the installed binary:

```sh
/Users/micahlee/.local/bin/axon graphql query --profile codex-health-fitness-fine --query-file /tmp/run-analysis.graphql --variables /tmp/run-analysis-vars.json
```

If the profile is missing or unauthorized, create a short-lived scoped client with:

```sh
/Users/micahlee/.local/bin/axon clients create \
  --scope graphql:schema \
  --scope graphql:query:healthFitnessRunAnalysis \
  --profile codex-health-fitness-fine \
  --expires 2h \
  codex-health-fitness-fine
```

Then add the returned profile snippet to `/Users/micahlee/.axon/config.toml`, validate, and reload Axon. Never print bearer tokens.

## Query

Use `--variables`; inline GraphQL arguments may not be passed reliably through this CLI path.

```graphql
query RunAnalysis(
  $id: String!,
  $start: String,
  $end: String,
  $includeRoute: Boolean,
  $routeLimit: Int,
  $routeSampleEvery: Int
) {
  healthFitnessRunAnalysis(
    id: $id,
    start: $start,
    end: $end,
    includeRoute: $includeRoute,
    routeLimit: $routeLimit,
    routeSampleEvery: $routeSampleEvery
  )
}
```

Default variables:

```json
{
  "id": "RUN_ID",
  "start": "YYYY-MM-DD",
  "end": "YYYY-MM-DD",
  "includeRoute": false,
  "routeLimit": 500,
  "routeSampleEvery": 0
}
```

If the user provides only a run ID, query with `days: 366` or infer the date from `healthFitnessWorkouts` first. Use `includeRoute: false` for ordinary summaries; use `includeRoute: true` only when route shape, bounds, mapping, or route quality matters.

## Coaching Summary

Read these fields first:

- `analysis.summary`: distance, duration, pace, calories, elevation, intensity, load.
- `analysis.heart_rate`: sample count, avg/min/max, p50/p90/p95, zone distribution.
- `analysis.drift`: speed-per-HR change, power-per-HR change, HR change, interpretation.
- `analysis.splits`: first-half and second-half HR/speed/power/efficiency.
- `analysis.running_dynamics`: cadence, power, speed, stride length, ground contact, vertical oscillation.
- `analysis.route`: point count, bounds, points per mile, start/end.
- `analysis.baselines` and `analysis.deltas_vs_recent_baseline`.
- `analysis.signals` and `analysis.data_quality`.
- `reflections` if available.

Response shape:

1. One short opener identifying the run.
2. `## Run Summary`
3. `## What It Means`
4. `## Watchouts`
5. `## Next Move`
6. Mention that watch-derived dynamics are trend signals, not gait diagnosis, only if using mechanics heavily.

Keep the tone coach-like: direct, practical, and specific. Prioritize effort distribution, drift, route/elevation context, and one next action.

## Obsidian Journal

Vault: `/Users/micahlee/Micah's Vault`

Run journal directory:

```text
01 - PERSONAL/02 - AREAS/Workouts/runs/
```

If the directory does not exist, create it. Each run gets its own Markdown file; do not append multiple runs into one journal file.

File naming:

```text
YYYY-MM-DD - Run - RUN_ID.md
```

If the run ID is long, keep the full ID in the file body and use a shortened safe suffix in the filename:

```text
YYYY-MM-DD - Run - D143921A.md
```

Use this file shape:

```markdown
---
date: YYYY-MM-DD
type: run-analysis
axon_run_id: RUN_ID
---

# YYYY-MM-DD — Run Analysis

- Axon run ID: `RUN_ID`
- Distance: X.XX mi
- Duration: XX.X min
- Pace: MM:SS/mi
- Avg HR: XXX bpm
- Max HR: XXX bpm
- Intensity: easy|moderate|threshold|high
- Load: XX.X

### Coaching Summary
...

### Key Metrics
- HR samples: ...
- HR zones: ...
- Drift: ...
- Route: ...
- Dynamics: ...

### Next Move
...
```

Also add a short link from that date's daily note if it exists:

```markdown
- Run analysis: [[YYYY-MM-DD - Run - RUN_ID]]
```

Prefer the `obsidian` CLI when available. If not, edit the Markdown file directly with care.

## Failure Handling

- If `found` is false, report the reason and do not write a journal entry.
- If HR samples are missing, say whether workout-level HR summary is still available.
- If route is unavailable, omit route coaching rather than guessing.
- If Obsidian write fails, still provide the coaching summary and say what was not saved.
