# Brief Mode

Use for `/personal-sync brief [preview|send]`.

The briefing renders prepared context and small current deltas. It does not write a Morning Briefing section into the human daily note.

1. Read today's human planning note, agent daily context, approved weekly plan, and agent weekly context.
2. Refresh only small deltas from calendar, urgent/actionable inbox signals, weather/logistics, health/food/fitness, and Axon decisions.
3. Produce a compact external message with:
   - one-sentence day thesis
   - non-obvious hard constraints
   - 1–3 realistic todos
   - one relevant body/food/fitness or prayer note when sourced
   - one watch item when needed
   - link to the human planning note
4. In `preview`, write nothing.
5. In `send`, publish `personal.morning-briefing` with the exact message in `payload.message`.
6. Record detailed coverage and warnings in agent context/run logs, not the human note or external message.

Summarize private sources. Do not quote full email or journal content. Calendar failures must be visible because they can make commitments incomplete.
