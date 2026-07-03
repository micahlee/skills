---
name: spotify
description: Control Spotify playback, search, queue, devices, and library state with the spogo CLI. Use when the user asks about Spotify, the current track, playback controls, playing a song/album/playlist, queue changes, device selection, or Spotify library/playlist tasks.
---

# Spotify

Use the `spogo` CLI to inspect and control Spotify. `spogo` uses local browser cookies and can also drive the local Spotify app through AppleScript.

## Quick Start

Use JSON for parsing and verify playback changes:

```bash
command -v spogo
spogo status --json
spogo search track "Let it be jesus" --json
spogo play spotify:track:TRACK_ID --json
spogo status --json
```

## Playback

- Current track: `spogo status --json`
- Play/pause: `spogo play`, `spogo pause`
- Play a specific item: `spogo play SPOTIFY_ID_OR_URL_OR_URI`
- Next/previous: `spogo next`, `spogo prev`
- Seek: `spogo seek 1:23`
- Volume: `spogo volume 55`
- Shuffle/repeat: `spogo shuffle on`, `spogo repeat off|track|context`

For current-track questions, report both playback state and item. `is_playing: false` means stopped or paused even if an item is loaded.

## Search And Play

When the user asks to play a track, album, artist, playlist, show, or episode:

1. Search the appropriate type, using the user's title plus artist/album clues if provided.
2. Prefer an exact title match, then the requested artist/album, then the top result.
3. If several plausible matches differ materially, ask a concise follow-up unless the user's wording makes a default obvious.
4. Play the selected item's `uri`, then run `spogo status --json` to confirm.

```bash
spogo search track "song title artist" --json
spogo search album "album title artist" --json
spogo play spotify:track:TRACK_ID --json
```

## Devices And Engines

When the active device is wrong or missing:

```bash
spogo device list
spogo device set "Device Name"
spogo --device "Device Name" play spotify:track:TRACK_ID
```

For web/connect rate limits or device errors, try the local app engine:

```bash
spogo --engine applescript play spotify:track:TRACK_ID --plain
spogo --engine applescript play --plain
spogo --engine applescript status --json
```

The AppleScript engine may change the loaded track without starting playback; if status shows the right item but `is_playing` is false, run `spogo --engine applescript play --plain` once more.

## Queue, Library, And Playlists

```bash
spogo queue show
spogo library playlists list --json
spogo playlist tracks PLAYLIST_ID_OR_URL --json
```

For reversible playback changes like play, pause, next, previous, seek, volume, shuffle, repeat, and queue add, act directly when requested.

Ask for confirmation before destructive or persistent changes:

- Removing tracks from a playlist or library.
- Clearing the queue.
- Creating a playlist with many items or adding many items to a playlist/library.
- Any ambiguous playlist/library edit where the target is not clear.

## Authentication And Errors

Check auth with:

```bash
spogo auth status
```

If auth is missing, guide the user through `spogo auth import` or `spogo auth paste`. Do not ask the user to paste passwords, MFA codes, raw cookies, or session tokens into chat unless they explicitly chose a CLI paste workflow and understand it stays local to their shell.

Common handling:

- `429` or "rate limit exceeded": wait briefly, retry once, or use `--engine applescript` for local playback.
- Device not found or no active device: run `spogo device list`, choose a device, then retry with `--device`.
- Unsupported operation: report the limitation and offer the closest available `spogo` command.
