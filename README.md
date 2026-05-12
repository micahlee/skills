# Skills

Personal agent skills for reusable workflows.

## Available Skills

### General

- `gamocosm-server-commands`: Send Minecraft server commands through the Gamocosm web console and verify the result.
- `daily-note`: Create or populate a daily note from recurring tasks, carryovers, project notes, and meal context.

### Worship Leading

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
