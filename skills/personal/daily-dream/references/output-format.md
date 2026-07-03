# Daily Dream Output Format

Daily Dream writes reflective sections that should remain pleasant to read and edit. Machine refresh metadata belongs in the Dream run log and event outbox, not in daily-note HTML comments.

## Daily Dream Section

Daily note section:

```markdown
## Dream

### Snapshot
...

### Signals
- Body:
- Work/Projects:
- Home/Relationships:
- Faith/Interior:
- Money/Admin:

### Patterns
- Possible pattern: ...

### Open Questions
- ...

_Source coverage: ..._
```

Write in first person, with epistemic humility. Use "possible pattern" when evidence is thin. Do not sound like a case file.

Do not add `<!-- daily-dream:start -->` or `<!-- daily-dream:end -->` markers. When cleaning legacy notes, remove those markers and preserve the content inside them.

## Human Dream Notes

Add a separate human-owned section:

```markdown
## Dream Notes
```

Never overwrite this section. It is for the user's own reflections.

## Tomorrow Morning Nudge

The 11pm run writes tomorrow's nudge into tomorrow's daily note:

```markdown
## Morning Nudge

- Energy: ...
- Watch: ...
- Consider: ...
```

Rules:

- 1 short paragraph or 1-3 bullets max.
- It should seed the future morning briefing, not become the briefing.
- It should not become a task list.
- It should shape tomorrow only when there is a clear signal from today's synthesis.
- Do not add `<!-- daily-dream:nudge:start -->` or `<!-- daily-dream:nudge:end -->` markers. Remove old markers during cleanup while preserving nudge content.

## Refresh Rules

Refresh by heading boundaries:

- `## Dream` stops before the next `##` heading, and must not overwrite `## Dream Notes`.
- `## Morning Nudge` stops before the next `##` heading.

If the current section has substantial human edits and no previous generated snapshot is available, leave it unchanged, log a warning, and prefer writing the synthesis to the run log rather than making an unsafe edit.

## Tone

Good:

```markdown
Possible pattern: when on-call is active, evening food choices seem more convenience-driven.
```

Avoid:

```markdown
You failed to manage dinner well.
```

The Dream should notice, not prosecute.
