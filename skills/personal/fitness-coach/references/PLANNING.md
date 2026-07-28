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
| Tuesday | Main legs or pull session; prefer legs when Friday endurance should be protected |
| Wednesday | No main split strength; preferred quality-cardio slot, optional mobility/recovery, or eligible full body |
| Thursday | Remaining main legs or pull session |
| Friday | No main split strength; 60-minute endurance anchor, optional mobility/recovery, or eligible full body |
| Saturday | No main split strength; optional mobility/recovery or eligible full body |
| Sunday | No main split strength; normally rest and whole-person self-sync, with optional recovery work only when useful |

Main push, pull, and legs sessions are anchored exclusively to Monday,
Tuesday, and Thursday. A missed split session remains next in sequence until
the next permitted anchor day; do not move it to Wednesday, Friday, Saturday,
or Sunday. Recovery needs may replace an anchor-day strength session with
mobility/recovery, but they do not make an off-day eligible for a main split
session.

Optional full-body work may occur on Wednesday, Friday, Saturday, or Sunday
only after push, pull, and legs coverage is complete and load, symptoms, and
the two-consecutive-work-day rule permit it. Sunday remains rest by default.
Monday and Friday endurance may serve different purposes. When legs are
scheduled Thursday, modify their dose so Friday's endurance target remains
achievable. Consecutive strength work counting spans week boundaries.

Normally program one deliberate quality-cardio exposure in every Monday-Sunday
week. Wednesday is the preferred slot. This is an intensity floor, not a demand
for an all-out session: choose running intervals, controlled tempo/threshold
work, strides, or bike intervals according to the block and current
constraints. Prefer running-specific quality while preparing for a running
event, but use bike intensity when impact loading is the limiting constraint.

Regress the dose or modality before deleting quality. Omit intensity only when
a specific signal makes even the regressed option inappropriate: acute pain,
altered gait, illness, unusual accumulated load/fatigue, clinician direction,
or environmental conditions that cannot be solved indoors. Record the reason
and the replacement. Do not let the weekly target silently become all easy
aerobic work.

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
