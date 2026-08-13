# Skills

Personal agent skills for reusable workflows.

## Available Skills

### General

- `gamocosm-server-commands`: Send Minecraft server commands through the Gamocosm web console and verify the result.
- `personal-sync`: Run the unified weekly, refresh, daily, reflection, briefing, and progress planning loop with separate human and agent-facing surfaces.
- `daily-note`: Deprecated compatibility alias for `personal-sync daily`.
- `progress-check`: Deprecated compatibility alias for `personal-sync progress`.
- `daily-dream`: Deprecated compatibility alias for `personal-sync reflect`.
- `morning-briefing`: Deprecated compatibility alias for `personal-sync brief`.
- `bible-journal-import`: Import handwritten Bible study or sermon notes into the Obsidian Bible Study Journal.
- `coma-bible-study`: Produce concise COMA Bible study prompts from Scripture passages.
- `create-bible-study-recipe`: Create or revise seasonal and external-resource Bible Study plans and stage them in Axon for connected app review.
- `obsidian-food-tracker`: Maintain the Obsidian food logging workflow using the Food Tracker plugin.
- `process-inbox`: Process the Obsidian Inbox into PARA destinations, task lists, shopping lists, reading lists, daily notes, and calendar entries.
- `fitness-coach`: Plan, publish, review, and adapt holistic strength, rehabilitation, running, cardio, mobility, and recovery programming from goals, constraints, history, and feedback.
- `instagram-read`: Read Instagram reel/post metadata from saved URLs using the local `instagram-cli` session.
- `gws`: Use the local Google Workspace CLI for Drive, Docs, Sheets, Gmail, Calendar, and related Workspace tasks.

### Finance

- `monarch-money`: Analyze Monarch Money accounts, transactions, cashflow, budgets, recurring charges, and investments with the `mmoney` CLI.

### Security

- `lastpass-cli`: Safely access LastPass vault entries with mandatory explicit confirmation before every direct or indirect `lpass` invocation.

### Music

- `sonos`: Control Sonos speakers, rooms, groups, queue, scenes, favorites, and playback with the `sonos` CLI.
- `spotify`: Control Spotify playback, search, queue, devices, and library state with the `spogo` CLI.

### Worship Leading

- `chord-chart-builder`: Build Planning Center native Lyrics & Chords charts from PDFs, images, pasted charts, or PCO attachments.
- `create-monthly-worship-plan`: Create a monthly worship team planning todo list in Basecamp.
- `schedule-music-team`: Schedule the music team on Planning Center for a given month.
- `schedule-songs`: Schedule worship songs into Planning Center services for a sermon series.
- `schedule-worship-leaders`: Schedule worship leaders in Planning Center for a given month.
- `song-block`: Plan song blocks for a church sermon series.

### Meal Planning

- `plan-to-eat-notes`: Annotate a Plan to Eat monthly planner with dinner-affecting calendar events.
- `plan-to-eat-curate`: Propose tag and metadata updates for Plan to Eat recipes.

## Development

List skills:

```sh
bash scripts/list-skills.sh
```

Validate the repo:

```sh
bash scripts/validate-skills.sh
```

## Install

Install the skills collection:

```sh
npx skills@latest add micahlee/skills
```

Install a single skill from this repo with the Codex skill installer:

```sh
scripts/install-skill-from-github.py --repo micahlee/skills --path skills/worship-leading/song-block
```
