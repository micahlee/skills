# Skills

Personal agent skills for reusable workflows.

## Available Skills

### General

- `gamocosm-server-commands`: Send Minecraft server commands through the Gamocosm web console and verify the result.
- `daily-note`: Create or populate a daily note from recurring tasks, carryovers, project notes, and meal context.
- `progress-check`: Check Daily Note priority tasks at scheduled checkpoints and publish compact progress-nudge events only when deterministic risk rules say a nudge is warranted.
- `daily-dream`: Synthesize daily learnings from notes, health/food/fitness, calendar/email, and other bounded sources; prepare tomorrow's nudge and monthly rollups.
- `morning-briefing`: Render a compact morning briefing from daily-note/dream context, light fresh deltas, and goal-aware signals; write the daily note block and return a Telegram-ready message.
- `bible-journal-import`: Import handwritten Bible study or sermon notes into the Obsidian Bible Study Journal.
- `coma-bible-study`: Produce concise COMA Bible study prompts from Scripture passages.
- `obsidian-food-tracker`: Maintain the Obsidian food logging workflow using the Food Tracker plugin.
- `process-inbox`: Process the Obsidian Inbox into PARA destinations, task lists, shopping lists, reading lists, daily notes, and calendar entries.
- `instagram-read`: Read Instagram reel/post metadata from saved URLs using the local `instagram-cli` session.
- `next-run-up`: Recommend the next running workout from recent training context and recovery signals.
- `run-analysis`: Analyze running workout data and identify training, pacing, cadence, and fitness trends.
- `run-training-plan`: Build and maintain running training plans from goals, constraints, and workout history.
- `workout-prep`: Generate structured warmups and cooldowns from Fitbod screenshots, workout lists, or `/workout-prep` requests.
- `gws`: Use the local Google Workspace CLI for Drive, Docs, Sheets, Gmail, Calendar, and related Workspace tasks.

### Finance

- `monarch-money`: Analyze Monarch Money accounts, transactions, cashflow, budgets, recurring charges, and investments with the `mmoney` CLI.

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
