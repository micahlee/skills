---
name: chord-chart-builder
description: Build Planning Center native Lyrics & Chords charts from PDFs, images, pasted chord charts, or existing PCO song attachments. Use when converting chord charts into PCO native format, removing key changes, improving chord placement, or uploading a native chart to a Planning Center song arrangement.
---

# Chord Chart Builder

CLI/API: `pco`, Planning Center Services API.

## Core Rule

Use text extraction as a scaffold, but use rendered images as the authority for chord placement. Extracted PDF text often collapses floating chord positions and places chords too early in a lyric line.

## Workflow

1. **Find the source**
   - If the chart is in PCO, search the song first: `pco songs search --query "<title>" --json`.
   - Inspect arrangements, keys, and attachments through the Services API when the CLI does not expose them.
   - Back up the arrangement JSON before changing anything.

2. **Download PCO attachments when needed**
   - List arrangement attachments: `/services/v2/songs/<song_id>/arrangements/<arrangement_id>/attachments`.
   - For an attachment file, `POST /services/v2/attachments/<attachment_id>/open`, then download `data.attributes.attachment_url`.
   - Keep the original PDF/image locally for review.

3. **Create two passes**
   - Text pass: extract layout text to capture lyrics, section order, chord names, key, meter, tempo, and tags.
   - Image pass: render the PDF/page to images and inspect chord locations visually.
   - The final chart should be image-guided. Save the text-only pass separately when it helps compare decisions.

4. **Build Planning Center native format**
   - Use PCO Lyrics & Chords / ChordPro style: place chords inline in square brackets, e.g. `Christ our [G]wisdom`.
   - Put a chord at the lyric syllable or word where it visually lands, not merely at the start of the source line.
   - Preserve useful sections like `INTRO`, `VERSE 1`, `TURN`, `TAG`.
   - Keep instrumental bars as bracketed chord tokens, e.g. `[G/B] [C] [G/D] [C/E]`.
   - Remove printed copyright/CCLI blocks from the bottom; Planning Center adds those on its own.

5. **Handle key changes intentionally**
   - If the user asks to remove a key change, transpose the changed section back into the target key.
   - Transpose slash chords and turnarounds too, not only lyric-line chords.
   - Example: removing a G-to-A lift means `A/C# | D | A/E | D/F#` becomes `G/B | C | G/D | C/E`.
   - Verify there are no leftover changed-key chord tokens unless intentionally retained.

6. **Quality checks before upload**
   - Compare the image-guided chart against rendered source images section by section.
   - Check for leftover key-change commands or chords from the removed key.
   - Check that the chart does not include bottom copyright text.
   - Prefer a local diff between earlier and final passes so the user can see what changed.

7. **Upload to Planning Center**
   - PATCH only the arrangement fields needed:
     - `chord_chart`
     - `chord_chart_key`
     - `lyrics_enabled` if needed
   - Use the existing arrangement unless the user asks for a new one.
   - Do not remove existing PDF attachments unless the user explicitly asks.

8. **Verify readback**
   - Read the arrangement from the API after PATCH.
   - Confirm `has_chord_chart: true`, `has_chords: true`, expected `chord_chart_key`, and a nonzero chart length.
   - Diff the remote `chord_chart` against the local final chart. PCO may add a trailing newline; ignore trailing whitespace only.

## API Notes

Planning Center stores the native Lyrics & Chords chart on the arrangement's `chord_chart` attribute. The key used for native transposition is `chord_chart_key`.
