# Morning Briefing Source Model

Morning Briefing renders context that other workflows prepared, then adds small current-day deltas. It should not redo Daily Dream synthesis or rebuild daily-note task selection.

## Required Sources

- today's daily note
- Morning Nudge from Daily Dream
- daily-note human-facing sections: Commitments, Focus Tasks, Routines, Needs Decision, Agent Queue, Context
- human sections that are already part of the daily note: Scripture Memory, Prayer Journal, Notes, Outcomes, Dream Notes

If today's daily note is missing or unreadable, fail loudly and do not send a partial Telegram briefing.

## Freshness Sources

Use configured commands when available:

- calendar command: day shape, hard commitments, locations, travel/prep implications, conflicts
- email/inbox command: counts/categories and urgent/actionable exceptions
- weather command: only actionable weather or logistics constraints
- health summary command: sleep/recovery/workout/food signals that affect today's choices
- Axon events command: unresolved decision events, task agent candidates, overnight workflow warnings

Command templates may use `{date}`, `{start_rfc3339}`, and `{end_rfc3339}` placeholders. Replace them after resolving the local target date and before execution.

Missing source behavior:

- calendar unavailable: mention in Telegram because commitments may be incomplete
- weather unavailable: omit and log unless weather was clearly needed
- health unavailable: omit and log unless a health-specific nudge would otherwise be expected
- email unavailable: mention only if inbox state is central to the day

## Goal Context

The personal context portfolio is not ready yet. Until configured, use a thin interim goal profile:

- configured `interim_goal_paths`
- existing nutrition goal notes when configured
- explicit goals present in today's daily note or Morning Nudge
- active project/task signals only as weak evidence

Do not infer deep life priorities from scattered notes. If `context_portfolio_paths` is empty or missing, record that gap in the run log.

Encouragement rules:

- Encourage when evidence shows progress toward a known goal.
- Nudge when evidence shows drift from a known goal.
- Keep encouragement concrete and brief.
- Do not use generic wellness advice disconnected from the sources.

## Privacy Boundaries

Telegram is an outside-the-vault surface. Prefer summaries over raw content:

- Summarize email bodies; do not quote full messages.
- Avoid detailed money/account data.
- Avoid private journal/prayer details unless already suitable for the daily note briefing.
- Health metrics should be interpreted only when actionable; raw values are optional and should be sparse.
- Use links back to the daily note/source notes for detail.

## Links

Prefer one daily-note link plus sparse source links for selected focus tasks and decisions.

Use `obsidian://open?...` links when practical. Fall back to readable vault paths if URI construction is uncertain.
