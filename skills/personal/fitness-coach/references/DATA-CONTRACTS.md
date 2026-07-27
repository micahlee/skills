# Data and State Contracts

## Obsidian

Use `/Users/micahlee/Micah's Vault/01 - PERSONAL/02 - AREAS/Workouts/` for:

- `Workouts.md`: stable index linking goals, equipment profiles,
  constraints/injuries, confirmed events, and active block;
- `Fitness Goals.md`: approved goals and rankings;
- `Training Locations and Equipment.md`: confirmed location profiles, equipment
  specifications, availability, and unconfirmed import candidates;
- `training-blocks/*.md`: one durable note per proposed/active/closed block;
- `injuries/*.md`: one durable note per active or historical case.

Automatically record factual observations, interview answers, imports, and approved decisions. Draft interpretations and proposed changes. Never silently change approved goals, rankings, clinician constraints, events, or active blocks. Preserve revision history and provenance.

`Run Training Plan.md` and `runs/*.md` are retired historical projections.
Never use them as current inputs and never create new entries. Preserve the
existing files unless Micah explicitly asks to delete the archive.

## Axon

Treat events as canonical for execution. Future typed records include goals, blocks, constraints, injuries, tests, rehab protocols, prescriptions, substitutions, publications, completions, feedback, evidence, adaptations, approvals, questions, and self-sync packets.

Use the `fitness-coach-events` profile for agent-authored derived state:

- `dashboard.health-fitness.next-run-up.cached`: current compact dashboard recommendation;
- `fitness.coaching.workout-reviewed`: durable completed-workout interpretation and resulting next action.
- `fitness.training.plan.approved`: complete versioned block targets and
  execution-ready workout prescriptions consumed by Axon Training;
- `fitness.training.modification.proposed`: safety-checked structured response
  to an Axon Training modification request.

Create the profile when absent with only these publish scopes:

```sh
/Users/micahlee/.local/bin/axon clients create \
  --scope events:publish:dashboard.health-fitness.next-run-up.cached \
  --scope events:publish:fitness.coaching.workout-reviewed \
  --scope events:publish:fitness.training.plan.approved \
  --scope events:publish:fitness.training.modification.proposed \
  --profile fitness-coach-events \
  --expires 8760h \
fitness-coach-events
```

The Axon Training client uses a separate least-privilege token:

```text
events:subscribe:fitness.training.plan.approved
events:subscribe:fitness.training.modification.proposed
events:publish:fitness.training.workout.reported
events:publish:fitness.training.modification.requested
```

The plan payload, not mobile code, is canonical for current targets, required
versus optional sessions, cardio activity and environment, run/ride structure,
typed segment purpose and HR/pace/power/cadence/RPE targets, weather policy,
and every workout card. Mobile caches are replaceable projections keyed by
plan ID and revision. Device adapters may translate supported typed fields into
HealthKit or WorkoutKit representations; they may not derive programming from
freeform prose.

Never print bearer tokens. Query completed-workout reviews through
`healthFitnessWorkoutDetail` or `healthFitnessRunAnalysis`; both return a
`reviews` array matched primarily by workout ID.

The manual tracer may use Markdown/JSON, but it must keep the same boundaries and clearly label state that is not yet continuously maintained.

Before analyzing a newly completed workout, verify the whole data path:

1. the phone/watch recorded the completion;
2. the current source or mobile node exported it;
3. Axon ingested the workout event;
4. route and metric samples are attached when required.

Report the newest source and Axon timestamps when the workout is missing. Do not turn an empty query into a zero-data analysis.

Verify deployed mobile-node capabilities rather than assuming them. A node that subscribes to prescriptions and schedules Apple Workouts is not automatically an outbound HealthKit exporter. Until direct HealthKit upload is confirmed, identify any remaining Auto Export dependency explicitly.

Keep observed, derived, and joined data distinct:

- observed: HealthKit workout, HR, speed, power, cadence, route samples;
- derived: grade, drift, walk fraction, efficiency, load;
- joined: historical weather from route location and workout time;
- reported: RPE, symptoms, perceived difficulty, unusual context.

## Fitbod Seed

Run:

```sh
/Users/micahlee/projects/skills/skills/personal/fitness-coach/scripts/import-fitbod.sh
```

Snapshots live under `/Users/micahlee/.axon/imports/fitness/fitbod/`. Select the newest directory whose `manifest.json` has `"status": "complete"`.

The seed contains:

- consolidated detailed workouts and every returned set field;
- per-workout CLI responses;
- exercised-movement details and muscle mappings;
- Fitbod metrics;
- custom exercises, equipment, categories, and muscle groups;
- saved template summaries/details;
- manifest, counts, errors, and checksums.

### Equipment and location profiles

Keep equipment availability separate from exercise familiarity:

- `confirmed`: explicitly reported by Micah or read from an approved canonical
  profile;
- `imported_candidate`: present in a Fitbod gym configuration but not yet mapped
  to an active coaching location;
- `history_candidate`: implied by completed exercise history only;
- `unavailable`: explicitly absent or excluded.

Every equipment profile records a stable ID, label, default/fallback status,
confirmed equipment, implement specifications, unavailable equipment,
provenance, and `last_confirmed_at`. Record implement weight and the smallest
usable load increment when they affect prescription math.

The two primary profiles are:

- `home_gym`: default structured strength/stability/rehab context;
- `bodyweight_only`: no external training equipment assumed. A floor and wall
  may be used; do not assume a pull-up bar, bands, furniture, or improvised load.

An explicit per-session location/equipment override wins over the default
profile. Vacation remains opportunistic and defaults to `bodyweight_only`
unless Micah confirms other equipment.

Fitbod's `/api/v3/gyms` resource exposes gym profiles with `gym_equipment`,
`selected_equipment_weights`, and `selected_resistance_bands` relationships.
Prefer a future typed, cache-fronted Fitbod CLI gym-profile command over
history inference. Import those records as candidates, map the intended Fitbod
gym to `home_gym`, and require confirmation before promoting equipment to
`confirmed`. The global `catalog equipment` response is vocabulary, not
personal inventory.

Keep raw and normalized data local; never commit it to the skill repository. Source IDs remain for reconciliation. Count only completed working sets for strength volume; preserve warmup, AMRAP, assisted/bodyweight/unilateral, notes, anomalies, and cardio fields rather than deleting them.

Use recent 6-8 weeks for starting-load hypotheses and the year for longer trends/familiarity. Exercise comparisons must distinguish direct comparison, close substitute, pattern-only, and incomparable. Ask for confirmation when mapping is ambiguous.

The current CLI does not expose the entire global Fitbod standard-exercise catalog in one command. The importer therefore captures every exercised movement in the selected history, all custom exercises, all metric-bearing exercises, and taxonomy. Record this limitation rather than claiming a complete global catalog.

The current CLI also does not expose gym-profile contents as a typed read,
although its read-only probe confirms the live gym resource. Until that command
exists, use historical movements only to prepare a short confirmation list;
never promote those candidates automatically.
