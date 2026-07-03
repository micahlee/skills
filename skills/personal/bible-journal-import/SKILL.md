---
name: bible-journal-import
description: Import Bible study journal notes from handwritten photos, screenshots, or rough text into the user's Obsidian Bible Study Journal. Use when the user asks to import journal notes, transcribe Bible notes, process a sermon-notes photo, or add handwritten Bible study notes to Obsidian.
---

# Bible Journal Import

Use this skill to turn handwritten or rough Bible study notes into clean Obsidian notes in the user's Bible Study Journal area.

## Vault Defaults

- Vault name: `Micah's Vault`
- Area index: `01 - PERSONAL/02 - AREAS/Bible Study Journal/Bible Study Journal.md`
- Journal folder: `01 - PERSONAL/02 - AREAS/Bible Study Journal/Journal Notes`
- Prefer the `obsidian` CLI for reads and writes when available.
- Do not write directly to the vault filesystem unless Obsidian is unavailable and the user has approved a fallback.

## Workflow

1. Read the attached image or rough text carefully.
2. Transcribe the content into clean Markdown without over-expanding the user's notes.
3. Preserve the user's structure when it is clear: passage, main idea, observation, meaning, application, sermon title, numbered qualities, or prayer.
4. Correct obvious spelling and capitalization, but do not silently invent missing content.
5. Mark uncertain readings with `[unclear: ...]` only when the ambiguity affects meaning.
6. Choose a dated note title from the page date or sermon date when visible; otherwise use today's date.
7. Create or update a journal note in the Journal folder.
8. Add a wikilink to the note under `## Journal Notes` in the area index if it is not already listed.
9. Verify the note and index after writing.

## Note Shape

Use this structure as a default, omitting sections that clearly do not apply:

```md
# YYYY-MM-DD - Title

Area: [[Bible Study Journal]]
Tags: #bible-study #journal
Source: Handwritten notebook photo imported YYYY-MM-DD

## Passage

- 

## Main Idea


## Observations

- 

## Meaning

- 

## Application

- 

## Questions

- 

## Prayer


```

For sermon notes, add `#sermon-notes` and include a `## Sermon` section with title and aim when present.

## Obsidian CLI Pattern

Use exact vault paths with `vault="Micah's Vault"`.

Useful commands:

```sh
obsidian read path="01 - PERSONAL/02 - AREAS/Bible Study Journal/Bible Study Journal.md" vault="Micah's Vault"
obsidian create path="01 - PERSONAL/02 - AREAS/Bible Study Journal/Journal Notes/YYYY-MM-DD - Title.md" content="..." vault="Micah's Vault"
obsidian eval code="..." vault="Micah's Vault"
```

When using `obsidian eval`, wrap async work in `(async () => { ... })()` because top-level `await` may fail.

## Import Discipline

- Keep the note useful, not exhaustive.
- Do not turn terse notebook bullets into long teaching paragraphs.
- If a passage reference is visible, include it even if the note is sermon-focused.
- If there is only one photo of a multi-page sequence, import only what is visible and say what was imported.
- Never delete or overwrite existing journal content unless the target note is clearly the same import and the user asked to refresh it.

