# Planning and Review

## Block Shape

Each block records:

- date range and four-week formal review date;
- one primary adaptation, limited secondary goals, and maintenance doses;
- for each goal: outcome measure, process target, and guardrail;
- constraints, confirmed events, taper/travel windows, and clinician directions;
- weekly dose and intensity ranges;
- stable session archetypes and sequence rules;
- progression/regression/deload rules;
- exit criteria, uncertainties, and evidence reviewed.

Dates trigger review, not automatic phase changes. A productive phase may continue 6-12 weeks. Deload only from evidence such as accumulated fatigue, symptoms, disrupted schedule, event timing, or failed performance—not because a fourth week arrived.

Prefer benchmarks embedded in ordinary training. Dedicated tests must be safe, decision-useful, nonmaximal when possible, and postponed when injury, fatigue, illness, or weather would distort them.

## Onboarding

1. Read the latest successful Fitbod snapshot, recent Axon/Apple Health history, existing Obsidian goals/events/constraints, calendar context, and current plans.
2. Summarize historical patterns and recent 6-8-week baselines as hypotheses.
3. Ask focused questions about goals, rankings, schedule, cardio history, preferences, injury status, and clinician directions.
4. Produce a baseline assessment and first block proposal.
5. Require explicit approval. Until then, offer only labeled conservative provisional sessions.

Never equate prior Fitbod behavior with future intent or prescribe an old best as a current load without calibration.

## Preferred Weekly Forecast

| Day | Preferred work |
| --- | --- |
| Monday | Push first thing; 60-minute endurance at lunch |
| Tuesday | Pull when Wednesday speed is planned; otherwise pull or legs |
| Wednesday | Preferred speed slot when prescribed |
| Thursday | Legs after Wednesday speed; otherwise legs or pull |
| Friday | 60-minute endurance anchor |
| Saturday | Optional full body after push/pull/legs if load permits; otherwise recovery/rest |
| Sunday | Rest and whole-person self-sync |

Monday and Friday endurance may serve different purposes. Modify or relocate Thursday leg stress when Friday is important. Sunday is normally rest, but consecutive strength work counting spans week boundaries.

## Weekly Self-Sync

Always contribute a compact packet containing:

```json
{
  "domain": "fitness",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "summary": "",
  "wins": [],
  "concerns": [],
  "upcoming_constraints": [],
  "proposals": [],
  "questions_or_approvals": [],
  "urgency": "low|medium|high",
  "confidence": "low|medium|high"
}
```

The global self-sync may aggregate and ask questions but may not mutate fitness. Consume its returned fitness answer packet, validate it, record accepted facts/approvals, and refresh the plan. If unfinished Monday, use a conservative provisional plan, list material unknowns, and remind once; block only genuine safety or plan-integrity decisions.
