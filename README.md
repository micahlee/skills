# Skills

Personal Codex skills for reusable workflows.

## Available Skills

- `gamocosm-server-commands`: Send Minecraft server commands through the Gamocosm web console and verify the result.
- `plan-to-eat-suggestions`: Maintain a ranked "next meals to make" Google Doc from Plan to Eat history.

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

Install a skill from this repo with the Codex skill installer:

```sh
scripts/install-skill-from-github.py --repo micahlee/skills --path skills/gamocosm-server-commands
```
