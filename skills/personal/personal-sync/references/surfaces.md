# Human And Agent Surfaces

## Human daily planning note

Keep exactly three functional areas:

```markdown
## Scripture Memory

## Calendar Notes
- Only preparation, conflict, travel, or relational context not obvious from the calendar itself.

## Todos
### Must
- [ ] ...
### Should
- [ ] ...
### Could
- [ ] ...
```

Omit empty todo subheadings if that reads better. Do not add agenda dumps, Dream, Morning Nudge, Morning Briefing, Context, Commitments, Needs Decision, Agent Queue, coverage, warnings, or processing summaries.

Use the configured Planning Notes resolver. Multi-day planning blocks still get one canonical note.

## Human weekly note

Default path: `Weekly Notes/YYYY/YYYY-Www.md`.

```markdown
# Week of YYYY-MM-DD

## Look Back
- Wins:
- Learned:
- Carry forward or release:

## Direction
One short weekly thesis.

## Outcomes
- [ ] Outcome with a concrete “done enough” definition.

## Constraints
- Only constraints that should shape choices.

## Two-Week Horizon
- Preparations or decisions that should begin before they become urgent.
```

Keep this concise. Link outcomes to canonical sources when useful.

## Agent daily context

Default path: `Agent Context/Daily/YYYY/MM/YYYY-MM-DD.md`.

May contain bounded sections such as `Evidence`, `Dream`, `Tomorrow Nudge`, `Briefing Context`, `Decisions`, `Source Coverage`, and `Refresh History`. This is readable Markdown, not hidden reasoning traces. State evidence and conclusions, not private chain-of-thought.

## Agent weekly context

Default path: `Agent Context/Weekly/YYYY/YYYY-Www.md`.

May contain source coverage/freshness, look-back evidence, capacity prediction, goal/project map, calendar implications, task/inbox/mail signals, outcome rationale, risks, unresolved decisions, two-week horizon, and refresh history.

## Machine state

JSON sidecars hold task refs, generated-section snapshots, fingerprints, capacity observations, event IDs, and merge metadata. Do not put machine metadata in human notes.

## Safe refresh

Use heading-bounded three-way merges with previous generated snapshots. Preserve human additions and no-ref tasks. If the human changed a managed section substantially and intent is unclear, do not overwrite it.

The per-day sidecar is a merge aid and a successful-write postcondition, not a
prerequisite that can exist before the first run. When it is missing, first
require a passing canonical Planning Notes audit, fingerprint the current note,
and use that exact content as the initial merge baseline. Abort if the note
changes before the write. Create the sidecar atomically with the successful
refresh and verify it afterward.
