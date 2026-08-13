# Refresh Mode

Use for `/personal-sync refresh`, especially scheduled Axon runs.

1. Read the last approved weekly plan and current agent weekly context.
2. Refresh calendar, tasks, Inbox, assigned external work, Axon events, and relevant bounded sources.
3. Reconcile factual changes and update managed agent context.
4. Detect changed constraints, completed outcomes, emerging deadlines, stale assumptions, and overcapacity.
5. Update human notes only for high-confidence factual changes that do not alter approved priority, such as a canceled constraint or completed sourced todo.
6. Do not reschedule, reprioritize, invent goals, or replace outcomes.
7. Publish a decision request when a priority choice is necessary; keep the last approved plan until resolved.
8. Feed current approved context to daily mode through agent state.

Quiet refreshes return only a compact operator summary. Missing sources are warnings unless they make the plan unsafe to trust.
