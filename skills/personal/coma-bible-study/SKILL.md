---
name: coma-bible-study
description: Produce concise COMA Bible study prompts from one or two Scripture passages, optionally saving them to Obsidian. Use when the user sends a Scripture reference by itself in a Bible Study thread, asks for a COMA study, or provides passages with an optional theme such as sovereignty, humility, suffering, wisdom, or work.
---

# COMA Bible Study

Use this skill to produce a structured Bible study prompt using the COMA method: Context, Observation, Meaning, Application.

## Defaults

- Bible translation: CSB unless the user specifies another translation.
- Tone: pastoral, grounded, Scripture-centered, doctrinally serious, and Reformed-friendly.
- Do not imitate a living author or named theologian's voice directly.
- Length: concise; keep notes short and questions immediately usable.
- Bullets: use plain `-` bullets only.
- Distillation: each COMA heading should present the best findings in exactly 3 note bullets and exactly 3 question bullets.
- Do not add summaries, teaching paragraphs, caveats, or extra headers beyond the required format.
- If the user gives two passages, make one unified study with one theological thread.
- If the user gives a theme, weave it naturally through all sections without forcing it.

## Passage Handling

1. Treat a bare Scripture reference as a request for this exact output format.
2. Do not quote the full biblical text unless the user asks.
3. If the reference is ambiguous, make the most likely assumption and proceed.
4. For a pair of passages, do not produce two separate studies.

## Obsidian Behavior

When the current chat/thread context is Bible Study Journal work, a bare Scripture passage means:

1. Generate the COMA study in the required format.
2. Save it to Obsidian using the `obsidian` CLI.
3. Create or update a note in `01 - PERSONAL/02 - AREAS/Bible Study Journal/Journal Notes`.
4. Add a wikilink to `01 - PERSONAL/02 - AREAS/Bible Study Journal/Bible Study Journal.md` under `## Journal Notes`.
5. Reply with the note path and a brief confirmation, not the full study text unless the user asks to see it.

Use vault `Micah's Vault`. Prefer note titles like `YYYY-MM-DD - Galatians 1 6-10` or a short theological title when obvious.

If the user explicitly asks for a chat-only COMA prompt, do not write to Obsidian.

## Required Output Format

```text
Main Idea (1 sentence)

Context
Notes
-
-
-
Questions
-
-
-

Observation
Notes
-
-
-
Questions
-
-
-

Meaning
Notes
-
-
-
Questions
-
-
-

Application
Notes
-
-
-
Questions
-
-
-

Reference Material
Translation Comparison
-
-
-
Commentary Highlights
-
-
-
```

## Section Guidance

Main Idea:
- Write one sentence that captures the theological thrust, not merely the event or topic.

Context:
- Orient the reader to the literary, historical, canonical, and covenantal setting.
- Ask questions that help the reader frame the passage before interpreting it.

Observation:
- Attend to repeated words, contrasts, structure, commands, promises, images, and key phrases.
- Ask questions that make the reader look back at the text.

Meaning:
- Explain the theological significance of the observations.
- Ask questions that press toward understanding, meditation, and worship.

Application:
- Connect the meaning to personal, relational, and communal obedience.
- Ask concrete questions suitable for personal reflection or small group discussion.

Reference Material:
- Put translation comparison details and commentary highlights here, not inside the COMA sections.
- Keep this material clearly secondary: it supports the study but should not crowd the main Context, Observation, Meaning, and Application sections.
- If there is little meaningful translation or commentary material, keep these bullets brief rather than padding.

## Current Study Memory

Passages already studied in this series:
- Psalm 119:25-32
- Proverbs 1:1-7
- Proverbs 1:1-7 and Proverbs 16:1-9
- Proverbs 3:1-12 and Proverbs 23:22-25

Recurring themes:
- Fear of the Lord as the foundation of wisdom
- Human planning held under divine sovereignty
- Intergenerational transmission of wisdom
- Humility versus pride as the fork in the road
- Obedience as the fruit of a formed heart, not mere willpower
