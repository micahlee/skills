---
name: gamocosm-server-commands
description: Send Minecraft server commands through the Gamocosm web console and verify the result. Use when the user asks to run, send, execute, or automate Minecraft commands via Gamocosm, the Gamocosm console, or their hosted Minecraft server dashboard.
---

# Gamocosm Server Commands

Use this skill to operate a Minecraft server through the Gamocosm web UI.

## Quick Start

1. Identify the command, target server, and intended player/entity from the user's request.
2. Use available browser automation to open or reuse the Gamocosm dashboard.
3. Select the intended Minecraft server.
4. If the server is stopped or sleeping, start it and wait until the console is available.
5. Open the server console or command input.
6. Send the command in server-console form, usually without the leading slash.
7. Read the console response and tell the user whether it succeeded.

## Command Formatting

- Gamocosm's console usually behaves like a Minecraft server console, so send `give snipexv minecraft:arrow 1`, not `/give snipexv minecraft:arrow 1`.
- If the UI explicitly says to include `/`, keep it.
- Preserve selectors, entity NBT, quoted JSON names, and bracketed item components exactly.
- If a command fails due to syntax, use the server's visible Minecraft version and the console error to correct it, then retry once.
- When adapting commands from chat form to console form, only remove one leading `/`; do not modify slashes inside JSON, paths, or text.

## Browser Workflow

- Prefer the Codex in-app Browser plugin when it is available. If browser automation is not already loaded, load the browser skill first.
- If Gamocosm is already open in the current tab, reuse that session.
- If login is required, ask the user to log in or open the authenticated dashboard; do not ask for passwords or tokens.
- Avoid changing account, billing, plan, backups, world reset, or server configuration settings unless the user explicitly asked for that.
- After sending a command, check for success text, command output, or an error message in the console. If the UI does not show output, report that the command was submitted but output was not visible.

## Safety Checks

Run normal reversible gameplay commands without extra confirmation, including `give`, targeted `tp`, targeted `effect`, targeted `summon`, `time`, `weather`, and targeted `kill` for a named or tagged entity.

Ask for explicit confirmation before sending commands that are broad, destructive, or admin-sensitive:

- `op`, `deop`, `ban`, `pardon`, `whitelist`, `kick`
- `stop`, `save-off`, `save-all flush`, `reload`
- `kill @e`, `kill @a`, or any broad selector without a tight `type`, `tag`, `name`, or `distance`
- `fill`, `setblock`, `clone`, `place`, `spreadplayers`, or TNT/fire/lava commands that can damage builds or strand players
- Game rules or difficulty changes that affect everyone
- Any command that deletes, resets, griefs, or permanently alters the world

## Response Pattern

Keep the user informed briefly:

- Say when the server is starting or the console is loading.
- After sending, summarize the command in console form and the result.
- If the command fails, include the important part of the error and the corrected command if one is obvious.

