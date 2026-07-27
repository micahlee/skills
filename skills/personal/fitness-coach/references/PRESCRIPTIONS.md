# Prescriptions

## Always Return

For “what’s next,” provide:

1. best overall recommendation and why;
2. next strength/stability/rehab session;
3. recommended cardio session;
4. valid 60-minute and 30-minute cardio options, with the alternative’s tradeoff;
5. expected feel, up to three cues, success criteria, and symptom/weather modifications.

Write these as executable criteria, not motivational summaries. Name the
adaptation, dose or effort target, observable success test, and the condition
that triggers a modification. A purpose line that only says to be useful,
controlled, intentional, productive, or symptom-aware is incomplete.

For every symptom-sensitive exercise, include one ordered branch:

1. the observation that permits continuing;
2. the exact first regression, including load/dose/ROM change;
3. one named substitute with its complete prescription;
4. the condition that ends that movement pattern for the day.

Do not list possible adjustments for the athlete to choose among. Use prior
response data to rank them. If that data is missing, ask before publication or
choose and label a conservative calibration branch.

## Strength, Stability, and Rehab

- Use stable block-specific push, pull, legs, and full-body templates.
- Resolve the active location/equipment profile before selecting exercises or
  calculating loads. Use an explicit session override first, then recorded
  travel/vacation context, then `home_gym`.
- Prescribe only confirmed available equipment. Fitbod gym imports and
  historical equipment usage remain candidates until confirmed.
- For `bodyweight_only`, use bodyweight movements, floor/wall mobility, and
  equipment-free stability work. Do not assume a pull-up bar, bands, furniture,
  or improvised weights.
- Use actual implement specifications in load and plate math. The confirmed
  home-gym barbell weighs 35 lb; never default its plate calculator or minimum
  barbell load to 45 lb.
- If the active profile cannot support the planned exercise, choose a complete
  substitute before publication and state the adaptation tradeoff.
- Weekly coverage resets Monday. After push/pull/legs, a fourth work session is full body.
- Allow at most two consecutive strength work days. A third becomes purposeful mobility, stretching, stability, or rehab recovery.
- Cardio does not count in that streak.
- Progress within approved rep ranges and target RIR: add reps first, then the smallest practical load increment at the top of the range with acceptable effort, technique, and symptoms. Hold/regress otherwise.
- If load history is unreliable, use a conservative calibration set and record the baseline.
- Never prescribe a load that the available implement and recorded increments
  cannot produce. Round to a realizable load and state the rounding when it is
  material.

Every session targets 45 minutes and has a valid 20-minute minimum:

- 0-5: therapeutic/dynamic preparation;
- 5-18: highest-priority work and required rehab;
- about 18: checkpoint;
- by 20: abbreviated cooldown if stopping;
- 20-40: secondary/accessory volume and additional rehab;
- 40-45: full cooldown.

The 20-minute minimum independently delivers useful stimulus. Completing it advances split coverage, receives partial volume credit, and counts as a work day when it included meaningful resistance. Omitted volume is not debt.

Specify ordered exercises, sets, reps, load/calibration, RIR, rest, meaningful tempo/ROM, rehab dose, substitutions, stop rules, warmup, and cooldown.

### Strength Warmups and Cooldowns

- Program warmups and cooldown stretches as ordered exercises in the execution interface, not only as prose.
- Use a movement-specific warmup plus ramp sets for the priority lift. General heat may precede it when useful.
- For push sessions, use the established default unless the active block or symptoms require a change:
  - two rounds of light band external rotation, wall/incline scapular push-ups, and open-book thoracic rotation;
  - then exercise-specific ramp sets before working sets.
- Default strength cooldowns to stretches or mobility only. Do not add post-workout cycling, walking, or another aerobic cooldown unless Micah explicitly requests it or the session has a specific need.
- For push sessions, use low-angle chest stretching, gentle triceps stretching, and a supine spinal twist as the established default; modify or skip any position that conflicts with an active symptom constraint.
- Make the 20-minute path executable: abbreviate the warmup to one round, retain useful priority work, then jump directly to abbreviated stretches. Do not add omitted accessory volume as future debt.

When exporting to Hevy:

- Put every movement in the routine as an exercise so Hevy leads the sequence.
- Put critical 45-minute/20-minute directions, symptom rules, and branch instructions in exercise notes; do not rely on routine-level notes persisting.
- Group repeated warmup movements into one circuit-style superset when they are intended to alternate by round:
  - assign the same `superset_id` to every movement in the circuit;
  - use no rest timer on intermediate movements;
  - put the between-round `rest_seconds` only on the final movement;
  - leave general heat and priority-lift ramp sets outside the warmup superset.
- Group the ordered cooldown stretches into one superset so Hevy advances through them as a continuous sequence:
  - assign every cooldown stretch the same `superset_id`;
  - use no rest timer between stretches or after the final stretch when each is performed once;
  - if the prescription calls for multiple cooldown rounds, put any between-round rest only on the final stretch.
- Recommend enabling Hevy's Smart Superset Scrolling for automatic movement-to-movement navigation; do not assume the API can enable this user setting.
- Do not group movements merely to reduce interface clutter. Preserve exercise order, symptom checks, equipment transitions, and any rest that materially supports safe execution.
- Keep the post-strength ending stretch-only unless the prescription explicitly says otherwise.

## Cardio

- The 30-minute option may be speed, recovery run, incline walk, or cycling.
- Do not treat modalities as equivalent. State intended adaptation and general-aerobic versus running-specific credit.
- Never pair hard legs and speed the same day; normally place a non-hard day between them.
- Include environment, warmup, continuous/interval structure, HR/pace/power/RPE targets, recoveries, cooldown, success, and abort/regression rules.
- Preserve both Monday/Friday 60-minute endurance anchors when compatible with the block; neither is automatically hard.
- Do not turn ordinary fatigue or imperfect recovery into a default walking prescription. Prefer an easy run, run-walk, or scaled quality session unless acute pain, illness, marked soreness, severe fatigue, altered gait, or another specific risk signal makes pure walking the best option.
- Scale planned quality before deleting it: reduce repetitions or pace pressure, shorten work intervals, or lengthen recoveries according to the active block.

Use these starting recovery ranges, then adjust from actual symptoms and load:

- easy run to easy running or strides: usually 12-24 hours;
- moderate longer run: usually 24-36 hours before easy running and 36-48 before quality;
- hard run: usually 36-48 hours before easy running and 48-72 before another quality session;
- lower-body strength: usually 24-48 hours before quality, with easy running sooner only when legs and relevant symptoms are normal.

When a named Nike Run Club speed session fits the active block, read
`nrc-speed-workouts.csv` in this reference directory. Prefer a 25-35 minute
session and rotate intervals, fartlek, tempo, hills, pyramids, and ladders.
Avoid hills when heel, calf, or Achilles status is questionable. Refresh the
catalog only when needed with `scripts/update_nrc_catalog.py`. Return its exact
title, duration, type, and coach plus the reason it fits the current sequence.

### Duration integrity

Treat a stated 30- or 60-minute availability window as a contract. Before presenting or publishing a structured workout, calculate:

```text
timed total = warmup + Σ(block iterations × timed steps) + timed cooldown
```

- State the arithmetic and timed total.
- Match the requested slot unless Micah explicitly approves a shorter timed structure followed by an open segment.
- State open continuation separately; open time does not count toward the fixed duration shown by Apple Workout.
- If an exact 60-minute workout should also permit continuation, make the timed structure total 60 minutes and add open continuation afterward only when the execution representation supports it.
- Explain a platform limitation rather than describing a shorter fixed workout as a full slot.

Before Apple Workout publication, verify:

```text
Available slot: 60 min
Timed structure: 10 + 4×(4+2) + 26 = 60 min
Open continuation: optional after minute 60
```

Also verify title, scheduled time, stable plan ID, revision, targets, and completion policy. Never use a tracer/demo title, ID, or fixture for a production prescription. Reject `axon-watch-tracer`, `Axon Run Tracer`, and equivalent test identities at the production handoff.

The execution interface must receive the approved Axon prescription without silently shortening, weakening, or substituting it.

## Next-Workout Cache

After `/fitness-coach next`, publish
`dashboard.health-fitness.next-run-up.cached` through the
`fitness-coach-events` profile. Keep the existing schema-version-1 payload:
generated time, as-of date, trigger, primary recommendation, coaching
paragraph, optional second-best option, and avoid note. Do not include raw
workouts, route points, Obsidian notes, or full GraphQL responses.

Use a deterministic idempotency key:

```text
fitness-coach-next:YYYY-MM-DD:TRIGGER
```

Publish with:

```sh
/Users/micahlee/.local/bin/axon events publish \
  --profile fitness-coach-events \
  --json /tmp/fitness-coach-next.json \
  --idempotency-key "fitness-coach-next:YYYY-MM-DD:TRIGGER" \
  dashboard.health-fitness.next-run-up.cached
```

The JSON payload contains:

- `schema_version`, `generated_at`, `as_of_date`, and `trigger`;
- a primary `recommendation` with type, duration, targets, RPE, confidence,
  explanation, and what-would-change conditions;
- `coaching_paragraph`;
- optional `second_best_option` and `avoid_today`.

If publication fails, still return the recommendation and report that the
dashboard cache was not updated.

## Weather

Resolve location from permitted recent phone location, recorded travel context, then home default; ask only if ambiguity changes the recommendation.

- Active lightning/thunder or official severe/extreme warnings: remove outdoor options.
- Likely storms/advisories: strongly recommend indoors.
- Use WBGT when available for vigorous heat, heat index as fallback; use wind chill, precipitation, and surface conditions for cold.
- Preferred indoor substitutions: cycling or incline walking. Treadmill running is possible but strongly non-preferred.
- Explain when weather changed the ranking.
