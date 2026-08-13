# Daily Mode

Use for `/personal-sync daily [DATE]`.

1. Load config; resolve/ensure the date's canonical Planning Note and run its one-day audit before changing the human note. Load the registry, optional prior sidecar, and agent daily/weekly context.
2. Reconcile completed sourced todos before selection.
3. Advance recurring tasks, promote clear manual todos, and emit decision events for ambiguity or repeated carryover.
4. Read the approved weekly outcomes and capacity prediction.
5. Add only non-obvious calendar implications to `Calendar Notes`; never render a daily agenda.
6. Select bounded Must/Should/Could todos using canonical state, day-specific reasons, current constraints, and weekly intent.
7. Preserve `Scripture Memory` exactly unless another explicit workflow owns an approved change.
8. Refresh only the three human areas defined in `surfaces.md`, using sidecar-assisted merges. If this is the first sidecar, bootstrap from the audited current note and recheck its fingerprint immediately before writing.
9. Put selection rationale, warnings, agent candidates, nudge context, and coverage in the agent daily note.
10. Write state, run log, snapshots, and events; rerun the one-day Planning Notes audit and require the per-day sidecar before reporting success.

An unavailable external source degrades coverage but does not block a safe note
refresh. A failed canonical audit, changed bootstrap baseline, unsafe source
mutation, failed note write, missing post-write sidecar, or failed post-write
audit is a refresh failure.

Do not copy every weekly outcome into the day. Do not put Dream, Morning Nudge, briefing, commitments, context dumps, agent queues, or processing details in the human note.

When explicitly migrating a legacy note, preview `python3 scripts/clean_planning_note.py --check` before removing old automation markers or hidden task refs. Do not delete old human content automatically.
