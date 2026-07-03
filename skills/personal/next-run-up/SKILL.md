---
name: next-run-up
description: Recommend Micah's top one or two best next run, walk, or run-walk sessions, including how much rest is needed before each and what pace, heart-rate range, duration, feel, and outcome to expect, by reading the current Run Training Plan, recent run-analysis notes, and the last week of Axon run/Fitbod workout data. Use when the user says /next-run-up, asks what run to do next, asks how long to rest before running, or wants the next best run/walk option from recent training.
---

# Next Run Up

## Purpose

Pick the best next run, walk, or run-walk options from the current training plan and the last week of actual training. Output the recommendation directly in chat and publish a compact Axon cache event for the health dashboard. Do not write to Obsidian.

## Inputs

Vault: `/Users/micahlee/Micah's Vault`

Read:

```text
01 - PERSONAL/02 - AREAS/Workouts/Run Training Plan.md
01 - PERSONAL/02 - AREAS/Workouts/runs/*.md
```

For run-analysis notes, use only the last 7 days unless the user asks for broader context. Also read today's daily note if useful for subjective notes, soreness, schedule, or food/fueling context.

When a speed session is due, also read the local NRC speed catalog:

```text
references/nrc-speed-workouts.csv
```

This catalog is generated from a public community-maintained Nike Guided Runs spreadsheet. To refresh it, run:

```sh
python3 /Users/micahlee/projects/skills/skills/personal/next-run-up/scripts/update_nrc_catalog.py
```

## Axon Queries

Use the installed Axon CLI:

```sh
/Users/micahlee/.local/bin/axon graphql query --profile codex-health-fitness-fine --query-file /tmp/next-run-up.graphql --variables /tmp/next-run-up-vars.json
```

Use bounded `start` and `end` dates for the last 7 days. Unbounded or broad queries can exceed the GraphQL frame limit. Never print bearer tokens.

### Last-Week Runs

```graphql
query RecentRuns($start: String!, $end: String!, $limit: Int!, $type: String) {
  healthFitnessWorkouts(start: $start, end: $end, limit: $limit, type: $type)
}
```

Variables:

```json
{"start":"YYYY-MM-DD","end":"YYYY-MM-DD","limit":20,"type":"run"}
```

### Last-Week Strength Work

```graphql
query RecentStrength($start: String!, $end: String!, $limit: Int!, $source: String) {
  healthFitnessWorkouts(start: $start, end: $end, limit: $limit, source: $source)
}
```

Variables:

```json
{"start":"YYYY-MM-DD","end":"YYYY-MM-DD","limit":20,"source":"Fitbod"}
```

### Specific Run Analysis

If a recent run has an ID and date, query bounded run analysis:

```graphql
query RunAnalysis($id: String!, $start: String!, $end: String!) {
  healthFitnessRunAnalysis(id: $id, start: $start, end: $end, includeRoute: false, routeLimit: 0)
}
```

Use this when deciding whether the next run should be easy, quality, or long based on drift, HR zone distribution, and notes.

## Decision Rules

Start from the current `Run Training Plan.md`, then adjust from the last week.

Prefer the next session that best satisfies all three:

- Fits the plan's current emphasis.
- Does not stack hard stress on recent hard runs or lower-body Fitbod work.
- Moves the 5K and aerobic-efficiency goals forward.

Training bias:

- Do not treat "not perfectly recovered" as an automatic reason to recommend walking.
- Prefer a long easy run over walking when there is no acute pain, illness, marked soreness, or clear recovery red flag.
- Walking is a recovery/pain-management recommendation, not the default conservative substitute for an easy run.
- Pure walking should be the best option only when there is acute pain, illness, marked soreness, a very poor subjective report, severe fatigue, or a specific injury-risk signal. Otherwise keep walking as a fallback/watch condition, not the primary prescription.
- If dashboard signals show only moderate fatigue, such as TSB better than about -15 and readiness at or above about 45, do not recommend a pure walk solely because yesterday included lower-body strength or the last run was long/easy. Choose a short easy run or run-walk with conservative HR caps.
- Planned speed work is required for the user's goals. If recovery is imperfect, scale the speed session before skipping it: reduce reps, reduce pace pressure, or make recoveries longer.
- Nike Run Club speed sessions are valid quality workouts. When the user has an NRC speed run planned or when the plan needs speed work, recommend it as a first-class option unless recent data shows a specific reason to defer.
- Use the local NRC catalog to recommend a named workout. Prefer 25-35 minute workouts for ordinary weekly speed work.
- Rotate NRC speed categories and structures for variety: generic intervals, fartlek, tempo, hills, pyramids, and ladder-style workouts. Avoid hill sessions when heel/calf status is questionable.
- Generic interval workouts are valid and useful. Do not exclude them; just make sure pyramids, ladders, and fartleks are not missed in the rotation.
- Treat pyramid and ladder workouts as especially useful variety for 5K work because they practice changing gears without turning every speed day into identical repeats.
- Prefer workouts tagged for 5K or 10K when choosing between otherwise similar NRC options.

Classify recent training stress:

- Hard run: interval/fartlek/tempo, HR max high for the user, or Axon `intensity_bucket` hard.
- Moderate run: longer aerobic run with mild drift, hilly run, or HR mostly moderate.
- Easy run: clearly easy HR/RPE and no late fade.
- Walk: valid recovery, aerobic support, or soreness-management option, especially after hard runs, lower-body Fitbod work, heel/calf symptoms, or poor recovery.
- Run-walk: valid bridge option when aerobic work is desired but continuous running would likely push HR too high.
- Heavy lower-body conflict: recent Fitbod lower-body session, calf-heavy session, or user-reported heel/calf soreness.

Rest guidance:

- After easy run only: next easy/strides can usually happen after 12-24 hours.
- After moderate long run or mild drift: wait 24-36 hours before another easy run; 36-48 hours before quality.
- After hard run: wait 36-48 hours before easy; 48-72 hours before another quality run.
- After lower-body Fitbod: wait 24-48 hours before quality; easy running can happen sooner if legs feel normal.
- If heel/calf/foot symptoms are present: no speed work; recommend walk, run-walk, easy-only, or rest until symptoms settle.
- If the only concern is ordinary training fatigue, recommend an easy run or scaled NRC session rather than a walk.
- If an easy run is plausible but not guaranteed, make the best option an easy run or run-walk with a clear first-10-to-15-minute check. Put "switch to walking if pain/soreness appears" in Watch, not as the main session.

Prediction guidance:

- Base easy-run predictions on recent comparable easy efforts. Current useful anchor: 2026-06-04 was 5.63 mi at 11:53/mi, avg HR 142, max HR 153, with hills and mild drift.
- For aerobic-efficiency runs, predict a conservative pace range that should keep HR near the target, not the fastest pace Micah can hold.
- For easy runs, expected HR should usually be around 135-145 bpm unless heat, hills, fatigue, or soreness argue otherwise.
- For easy walks, estimate duration and HR as recovery-focused; do not pretend walking pace is performance-critical.
- For strides, intervals, and tempo, give target effort and rough pace ranges, but make repeatability and form the primary success criteria.
- For Nike Run Club speed sessions, preserve the session's intent. Give target effort, likely pace/HR ranges, and scaling rules rather than replacing it with an easy walk.
- When recommending an NRC workout, include its exact title, duration, type, coach, and why it fits this week.
- If prediction data is weak, say "rough target" or "expectation" and explain the uncertainty in one short phrase.

## Output Shape

Keep the response concise and coach-like.

Use this structure:

```markdown
**Next Run Up**

Best option: ...
Rest first: ...
Session: ...
Shoot for: ...
Expect: ...
Why: ...
Watch: ...

Coach's pep talk: ...

Second-best option: ...
Rest first: ...
Session: ...
Shoot for: ...
Expect: ...
Why: ...
Watch: ...

Coach's pep talk: ...

Avoid today: ...
```

For each option include:

- Session type: run, walk, run-walk, strides, fartlek, intervals, tempo, or longer aerobic.
- Concrete structure.
- Required rest before starting.
- Target duration.
- Predicted or target pace range when useful.
- Predicted or target heart-rate range.
- Expected RPE and subjective feel.
- What a successful version of the session looks like.
- Why it is ranked there.
- Indicators to watch during and after.
- A coach's pep talk paragraph tied to that specific session: confident, practical, and personal to the current training context. Avoid generic hype.
- If using the NRC catalog, the named NRC workout and its catalog metadata.

If data is sparse, say so plainly and make a conservative recommendation. If Axon is unavailable, use the current training plan and recent Obsidian run notes, then mention the missing data.

## Dashboard Cache Event

After producing the recommendation, publish a compact event so the health dashboard can show the same next-run recommendation without re-running an agent turn.

Use this profile:

```sh
/Users/micahlee/.local/bin/axon events publish \
  --profile next-run-up-cache \
  --json /tmp/next-run-up-cache.json \
  --idempotency-key "next-run-up:YYYY-MM-DD:TRIGGER" \
  dashboard.health-fitness.next-run-up.cached
```

If the profile is missing, create it:

```sh
/Users/micahlee/.local/bin/axon clients create \
  --scope events:publish:dashboard.health-fitness.next-run-up.cached \
  --profile next-run-up-cache \
  --expires 8760h \
  next-run-up-cache
```

Never print bearer tokens.

Payload shape:

```json
{
  "schema_version": 1,
  "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
  "as_of_date": "YYYY-MM-DD",
  "trigger": "daily|apple-health-workout|fitbod-workout|manual",
  "recommendation": {
    "type": "run|walk|run-walk|strides|fartlek|intervals|tempo|longer aerobic",
    "nrc_workout": "Optional NRC title",
    "duration_minutes": 35,
    "hr_target": "135-145 bpm",
    "pace_target": "rough target or use effort / HR",
    "rpe": "3-4",
    "confidence": "low|medium|high",
    "explanation": "Short dashboard-ready reason.",
    "what_would_change": ["Short condition that would change the recommendation"]
  },
  "coaching_paragraph": "One concise coach-style paragraph.",
  "second_best_option": "Optional one-sentence fallback.",
  "avoid_today": "Optional one-sentence avoid note."
}
```

Keep the payload small. Do not include full GraphQL responses, raw workouts, raw route points, run-analysis notes, or Obsidian note contents. If event publish fails, still return the chat recommendation and mention that the dashboard cache was not updated.
