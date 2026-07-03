# Daily Note Task Model

Daily-note task processing has one user-facing entry point but several task sources. The daily note is a work surface. Canonical task state lives in source systems and in the daily-note task registry.

## TaskRef

Every system-generated task must have a stable task reference in the registry and in the per-note sidecar. Do not expose that reference as a hidden HTML comment in the daily note.

Fields:

- `source_type`: `obsidian`, `basecamp`, `pco`, `calendar`, `generated`, or another explicit external source.
- `source_id`: stable external ID when available.
- `source_uri`: Obsidian block link, external URL, or source-specific URI.
- `source_label`: usually `src`.
- `completion_strategy`: `sync_back`, `advance_recurrence`, `external_complete`, `external_link_only`, or `no_sync`.
- `owner`: `micah`, `agent`, `shared`, or `external`.

Reconciliation must key off sidecar `task_ref` data, not task text. Legacy inline `task-ref` comments may be read only when a sidecar is unavailable.

## Obsidian Source Tasks

Canonical Obsidian tasks should receive stable block IDs so daily tasks can link to exact source tasks.

Example source task:

```markdown
- [ ] BUY: Carrie flowers every month on the 20th due 2026-06-20 ^task-buy-carrie-flowers
```

Preserve the vault's existing Obsidian Tasks syntax when editing real source tasks, including priority, recurrence, due-date, and completion-date tokens.

Example clean daily instance:

```markdown
- [ ] BUY: Carrie flowers ([[Tasks/Recurring#^task-buy-carrie-flowers|src]])
```

Use Obsidian-native compact source links for Obsidian sources. Use Markdown URL links for external systems.

## External Sources

External tasks also get TaskRefs as best as the source allows:

- Basecamp todos or assignments: use stable todo/assignment IDs and source URLs; completion strategy is `external_complete` when safe.
- Calendar commitments: use source URLs or event IDs when available; completion strategy is `external_link_only`.
- Generated next actions: link back to the source task or note that caused the generated action.

Calendar events are context, not tasks. Do not mark calendar events complete because a daily-note checkbox was checked.

## Human-Owned Daily Tasks

A checkbox is human-owned when it is not represented in the per-note sidecar and cannot be matched to a generated source by a legacy inline `task-ref` fallback. Newly rendered generated checkboxes should still be readable as plain Markdown.

Rules:

- Preserve no-ref human tasks when refreshing machine-owned sections.
- Do not reconcile no-ref tasks to source systems.
- If an unchecked no-ref task remains from a recent daily note, classify it.
- Promote clear, actionable no-ref tasks into a canonical Obsidian source and assign a TaskRef.
- Publish a decision-requested event for no-ref tasks that need routing or clarification.
- Leave historical daily notes unchanged after promotion.

## Registry

The daily-note task registry is the authority for machine task history across days. Default path:

```text
Tasks/Daily Note State.json
```

Recommended registry fields:

```json
{
  "task_ref": "obsidian:Tasks/Recurring.md#^task-buy-carrie-flowers",
  "source_type": "obsidian",
  "source_uri": "Tasks/Recurring.md#^task-buy-carrie-flowers",
  "last_surfaced": "2026-05-29",
  "last_completed": "2026-05-20",
  "completion_count": 3,
  "skip_count": 2,
  "decision_state": "needed",
  "last_decision_event_at": "2026-05-29T07:10:00-04:00",
  "last_generated_text": "BUY: Carrie flowers"
}
```

Keep completion history in the registry, not as noisy history under every source task line.

## Per-Note Sidecar

The per-note sidecar is the authority for what automation rendered into one daily note. Default folder:

```text
Tasks/Daily Note State/YYYY-MM-DD.json
```

Store rendered task refs, visible source links, section paths, line fingerprints, completion strategies, and the previous generated section bodies there. This keeps the daily note simple while preserving enough structure for reconciliation and safe refreshes.
