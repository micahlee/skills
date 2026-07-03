---
name: run-training-plan
description: Produce or refresh Micah's next 30-day running training plan from Obsidian fitness goals, the current plan, recent run-analysis notes, and Axon health/fitness data. Use when the user says /run-training-plan, asks for a 30-day running plan, wants key run types or milestones, or wants the current running plan replaced from recent fitness signals.
---

# Run Training Plan

## Purpose

Refresh a durable 30-day running plan that describes the key workout types, fitness milestones, indicators to watch, and coaching priorities. This is not a day-by-day schedule.

Each run replaces the previous plan entirely.

## Canonical Obsidian Inputs

Vault: `/Users/micahlee/Micah's Vault`

Read these first:

```text
01 - PERSONAL/02 - AREAS/Workouts/Fitness Goals.md
01 - PERSONAL/01 - PROJECTS/🏃🏻‍♂️‍➡️ Run a faster 5k/🏃🏻‍♂️‍➡️ Run a faster 5k.md
```

Then read the current plan if it exists:

```text
01 - PERSONAL/02 - AREAS/Workouts/Run Training Plan.md
```

Read recent run journal entries:

```text
01 - PERSONAL/02 - AREAS/Workouts/runs/*.md
```

Use only the last 30 days of run-analysis notes unless the user asks for a longer horizon.

## Axon Inputs

Use Axon GraphQL through the local CLI. Prefer the installed binary:

```sh
/Users/micahlee/.local/bin/axon graphql query --profile codex-health-fitness-fine --query-file /tmp/run-training-plan.graphql --variables /tmp/run-training-plan-vars.json
```

Use `--variables`; inline GraphQL arguments may not be passed reliably through this CLI path. Never print bearer tokens.

### Recent Workouts Query

Use this to identify recent runs and supporting workouts:

```graphql
query RecentWorkouts($days: Int!, $limit: Int!) {
  healthFitnessWorkouts(days: $days, limit: $limit)
}
```

Default variables:

```json
{"days": 30, "limit": 100}
```

### Per-Run Analysis Query

For each recent run ID, query:

```graphql
query RunAnalysis($id: String!, $days: Int!) {
  healthFitnessRunAnalysis(id: $id, days: $days, includeRoute: false, routeLimit: 0)
}
```

Default variables:

```json
{"id": "RUN_ID", "days": 45}
```

Read `analysis.summary`, `analysis.heart_rate`, `analysis.drift`, `analysis.splits`, `analysis.running_dynamics`, `analysis.data_quality`, and `reflections`.

### Supporting Metrics Query

Use this when useful for readiness, recovery, or trend context:

```graphql
query FitnessMetrics($days: Int!, $limit: Int!) {
  healthFitnessMetrics(days: $days, limit: $limit)
}
```

Default variables:

```json
{"days": 30, "limit": 1000}
```

Prefer observed data over assumptions. If VO2 max, resting HR, HRV, sleep, body mass, or workout recovery data is absent, omit it or say it was not available.

## Planning Method

Start from the goals, not the data. Current standing goals include:

- Run the October 5K at 8:00/mile pace or faster.
- Build aerobic efficiency to run at least 11:00/mile while keeping heart rate under 140 bpm.

Then use the last 30 days of evidence to tune the plan:

- Recent run frequency and longest run.
- Easy-run HR and pace relationship.
- Aerobic drift on longer runs.
- Time in easy/moderate/threshold/high zones.
- Signs of durability or fatigue from run notes, Fitbod workouts, and supporting metrics.
- Whether routes, hills, heat, or fueling made pace/HR harder to interpret.

Do not overfit to one run. Call out low data quality or sparse history plainly.

Coaching bias:

- The user's goals require planned running stress, including long easy runs and speed work.
- Do not let the plan drift into mostly walking unless pain, illness, or clear fatigue signals make running inappropriate.
- Include one protected speed-work slot most weeks. Nike Run Club speed sessions are valid for this slot.
- If recovery is imperfect, scale the speed session before removing it: reduce reps, reduce pace pressure, or lengthen recoveries.
- Long easy runs should remain a default aerobic-development tool, not something replaced by walking because of mild drift alone.
- When variety is useful, use `/next-run-up` with its local NRC speed-workout catalog to choose a named 25-35 minute NRC speed session for the week. Generic intervals are valid, but make sure pyramids, fartleks, tempo, and ladder-style workouts are also represented in the rotation.

## Plan Shape

The output should describe training types, not assign specific calendar days. Include enough detail that Micah can choose workouts around life, weather, races, and lifting.

Required sections:

```markdown
---
date: YYYY-MM-DD
type: run-training-plan
window_start: YYYY-MM-DD
window_end: YYYY-MM-DD
source: axon+obsidian
---

# 30-Day Run Training Plan

## Goals This Block

## Recent Signals

## Weekly Shape

## Key Run Types

## Fitness Milestones

## Indicators To Watch

## Adjustment Rules

## Current Plan Replaced
```

### Key Run Types

Include 3-5 run types. For each type, include:

- Purpose.
- Example structure.
- How hard it should feel.
- Indicators to watch during and after.
- When to skip, shorten, or swap.

Useful run types for the current goals:

- Easy aerobic run: build HR-controlled efficiency.
- Easy run plus strides: keep form and turnover without heavy fatigue.
- Intervals or fartlek: practice faster-than-goal rhythm and leg speed.
- Tempo or cruise intervals: build threshold control near 5K support pace.
- Longer aerobic run or steady progression: build durability and late-run control.
- Nike Run Club speed run: use NRC-guided intervals/fartlek/tempo as the weekly protected quality session when available.

### Fitness Milestones

Milestones should be observable and coaching-useful, not vanity metrics. Examples:

- Easy aerobic pace moves toward 11:30/mi, then 11:00/mi, at or below 140 bpm on comparable routes.
- Long run finishes with no more than mild drift.
- Strides feel smooth and controlled without shoulder, heel, or calf flare-ups.
- 5K-specific intervals feel repeatable without spilling into all-out effort.
- Recovery metrics and subjective energy support keeping two quality run touches per week.

### Adjustment Rules

Write practical if/then rules:

- If HR is elevated at normal easy pace, make the run easy-only.
- If heel/calf complains, remove speed and keep soft, low-impact aerobic work.
- If Fitbod leg day is heavy or soreness is high, shift intervals to strides or easy run.
- If there is a road race, reduce leg intensity and prioritize freshness.
- If drift exceeds the recent norm, shorten the next long run or fuel earlier.
- If an NRC speed session is due but recovery is imperfect, scale it before skipping it.

## Save Behavior

Overwrite this file completely each time:

```text
01 - PERSONAL/02 - AREAS/Workouts/Run Training Plan.md
```

Do not append a new plan below the old one. Preserve the old plan only by summarizing the most important change in `## Current Plan Replaced`.

Prefer the `obsidian` CLI when available. If not, edit the Markdown file directly with care.

## Coaching Tone

Write like a practical health and fitness coach: direct, specific, and calm. Avoid pretending the plan is a medical diagnosis. Mention uncertainty when data is missing, but still make the best plan from the available evidence.
