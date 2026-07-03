---
name: instagram-read
description: Read Instagram reel or post metadata from URLs using the local instagram-cli session and a deterministic helper script. Use when the user asks to inspect Instagram links, read reels/posts, resolve Instagram inbox items, or classify saved Instagram URLs for Obsidian processing.
---

# Instagram Read

Use this skill to inspect Instagram reel/post URLs without driving the Instagram app or browser.

## Quick Start

From this skill directory:

```bash
node scripts/instagram-read.cjs --format json "https://www.instagram.com/reel/SHORTCODE/"
node scripts/instagram-read.cjs --format markdown "https://www.instagram.com/reel/SHORTCODE/"
```

The helper uses the active `instagram-cli` account by default. Check it with:

```bash
instagram-cli auth whoami
```

## Workflow

1. Extract Instagram URLs from the user's source material.
2. Run `scripts/instagram-read.cjs --format json URL...`.
3. Use the returned `caption`, `author`, `taken_at`, `product_type`, duration, audio, and metrics to classify the item.
4. For Obsidian inbox routing, treat successful reads as inspected public/social links; route only when the destination is clear.
5. If the helper returns an auth, checkpoint, private-media, or unavailable error, leave the item ambiguous with a short explanation.

## Options

```bash
node scripts/instagram-read.cjs [--format json|markdown] [--username USER] [--refresh] [--no-cache] URL...
```

- `--format json` is best for automation and parsing.
- `--format markdown` is best for pasting into notes.
- `--username USER` uses a specific saved `instagram-cli` session.
- `--refresh` bypasses the local metadata cache.
- `--no-cache` disables reading and writing cache files.

## Safety

- Read only; do not like, comment, follow, save, or message.
- Do not print or copy session files, cookies, passwords, or challenge codes.
- Keep runs small and user-directed. Instagram access is unofficial and can trigger checkpoints if abused.
- Cache files contain only normalized post metadata and live under `~/.cache/agent-skills/instagram-read`.
