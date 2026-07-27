# Completed Run Analysis

## Availability Preflight

Before interpreting a newly completed run:

1. Confirm it exists in Axon workout history and per-run analysis.
2. Confirm the workout occurred after the newest source refresh.
3. Distinguish among watch/phone sync delay, source-export delay, Axon-ingestion delay, missing route/metrics, and an incorrect ID/date.
4. Stop before numerical coaching when the requested run is not present. State the exact missing boundary and the quickest honest next step.

Do not analyze the newest available workout as though it were the requested run.

## Intended Versus Actual

Read the approved prescription and execution publication alongside the completion.

- Recalculate the prescribed timed duration.
- Compare intended targets, structure, completion policy, and slot with what the execution app displayed.
- Identify whether a mismatch originated in coaching generation, publication/translation, platform behavior, or completion data.
- Keep tracer fixtures separate from production prescriptions.

## Core Analysis

Use:

- distance, duration, pace, elevation, calories, and calculated load;
- HR samples, average/maximum/percentiles, zones, and time above the intended cap;
- speed-per-HR and power-per-HR drift;
- first-half versus second-half speed, power, HR, and efficiency;
- cadence, stride length, ground contact, and vertical oscillation when data quality supports them;
- route elevation and local grade;
- sustained low-speed periods or run/walk transitions;
- recent comparable sessions and subjective feedback.

Separate the watch's observed measurements from derived metrics and coaching inference.

## Environment-Adjusted Exertion

Use this workflow when Micah mentions heat, humidity, hills, undulation, wind, unusually high HR, late slowing, or increasing walking.

1. Request route data and derive grade/elevation demand.
2. Join historical weather at the route coordinates and workout time. Ask for location only when route location is unavailable or ambiguous.
3. Capture temperature, relative humidity, dew point, wind, and, when available, WBGT or solar load. Relative humidity alone is not comparable across temperatures.
4. Compare HR, speed, power, and walk fraction against recent similar easy or steady runs.
5. Assess:
   - observed internal load and time above target;
   - mechanical demand after accounting for grade;
   - pace/power decay and cardiac drift;
   - whether walking successfully controlled the prescribed load;
   - likely terrain, environment, and durability contributions.
6. Estimate cool/flat equivalent pace or excess HR only when a personal baseline supports it.

Use `low`, `medium`, or `high` confidence and name missing variables. One run cannot support a precise causal percentage split.

## Coaching Output

Lead with whether the run delivered the intended stimulus. Then report:

1. what the watch measured;
2. what terrain explains;
3. what historical weather likely added;
4. what late-run drift or walking suggests;
5. how this changes recovery or the next prescription.

Record useful factual feedback and calculated state in Axon. Require approval only when the evidence suggests a meaningful block or priority change outside existing guardrails.

## Durable Review

After a successful completed-workout analysis, publish
`fitness.coaching.workout-reviewed` through the `fitness-coach-events` profile.
Do not create or update a per-run Markdown journal.

Include:

- schema version, workout ID/date/type, review type, and reviewed time;
- prescription ID/revision when known;
- intended-versus-actual duration and intended stimulus;
- concise observed, derived, environmental, and reported findings;
- whether the intended stimulus was delivered;
- next action and whether an active-block change needs approval;
- confidence and material missing data.

Use `initial`, `followup`, or `manual` as the review type and publish with:

```text
fitness-coach-review:WORKOUT_ID:REVIEW_TYPE:YYYY-MM-DD
```

as the idempotency key. Keep the payload interpretive and compact; raw workout,
metric, route, and weather data remain in their source events. If publication
fails, return the analysis and identify the missing durable write.
