---
name: sonos
description: Control Sonos speakers over the local network with the sonos CLI, including discovery, status, playback, groups, queue, favorites, scenes, TV/line-in, and Spotify playback. Use when the user asks about Sonos, a room speaker, whole-home audio, Sonos groups, Sonos volume, or playing audio on Sonos.
---

# Sonos

Use the `sonos` CLI to inspect and control Sonos speakers over the local network. The CLI defaults to `--name "Kitchen"` unless another room or `--ip` is provided.

## Quick Start

Use JSON for parsing and verify playback or grouping changes:

```bash
command -v sonos
sonos discover --format json
sonos status --name "Kitchen" --format json
sonos play --name "Kitchen"
sonos status --name "Kitchen" --format json
```

## Rooms And Status

- Discover speakers: `sonos discover --format json`
- Current track/state: `sonos status --name "Room" --format json`
- Watch live events: `sonos watch --name "Room"`
- Config defaults: `sonos config get`, `sonos config set name "Room"`

If the user names a room, pass `--name "Room"` on every command. If discovery fails or names are ambiguous, run `sonos discover` and ask a concise follow-up.

## Playback

- Play/pause/stop: `sonos play`, `sonos pause`, `sonos stop`
- Next/previous: `sonos next`, `sonos prev`
- Volume: `sonos volume get`, `sonos volume set 25`
- Mute: `sonos mute get`, `sonos mute set true|false`
- TV input: `sonos tv --name "Soundbar Room"`
- Line-in: `sonos linein --name "Room" --from "Source Room"`

For current-track questions, report room, transport state, title, artist, album, position, volume, and mute when available.

## Spotify And URLs

Search Spotify with Web API credentials, or use Sonos SMAPI when the user's linked Sonos music service is more appropriate:

```bash
sonos search spotify "song title artist" --type track --limit 10 --format json
sonos search spotify "album title artist" --type album --format json
sonos smapi search --service "Spotify" --category tracks "song title" --format json
```

Play or enqueue the selected URI:

```bash
sonos open --name "Kitchen" spotify:track:TRACK_ID
sonos enqueue --name "Kitchen" spotify:album:ALBUM_ID
sonos search spotify "miles davis" --type track --open --index 1 --name "Kitchen"
```

For arbitrary web media, prefer `sonos play-url URL`. Use `--no-playlist` for a single YouTube item and `--playlist-limit N` before enqueueing long playlists.

## Queue, Favorites, Groups, Scenes

Safe read commands:

```bash
sonos queue list --name "Room" --format json
sonos favorites list --name "Room" --format json
sonos group status --format json
sonos scene list --format json
```

Common actions:

- Queue: `sonos queue play 3`, `sonos queue remove 3`, `sonos queue clear`
- Favorites: `sonos favorites open "Favorite Name" --name "Room"`
- Groups: `sonos group join --name "Room" TARGET`, `sonos group solo --name "Room"`, `sonos group party --name "Room"`
- Group volume/mute: `sonos group volume set --name "Room" 25`, `sonos group mute set --name "Room" true|false`
- Scenes: `sonos scene save NAME`, `sonos scene apply NAME`, `sonos scene delete NAME`

## Safety

Act directly for requested reversible playback controls: play, pause, stop, next, previous, mute, modest volume changes, status, queue list, favorites list, and playing a clearly identified item.

Ask for confirmation before:

- Setting volume above 45, large volume jumps, or group volume changes.
- `group party`, `group dissolve`, scene apply/delete, or any whole-home/grouping change.
- Clearing the queue or removing many queue entries.
- Enqueueing a long playlist or using `play-url --playlist` without a limit.
- Saving persistent defaults with `sonos config set`.

## Errors

- No speakers found: confirm the user is on the same local network, then retry `sonos discover`.
- Room not found: run `sonos discover --format json` and select the closest matching room.
- Spotify search auth error: use SMAPI search if available, or ask the user to configure `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
- UPnP/SOAP timeout: retry once with `--timeout 30s`; if it persists, report the target room and error.
