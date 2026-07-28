#!/usr/bin/env python3
"""Generate and embed deduplicated coaching audio in an Axon Training plan."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.error
import urllib.request
from typing import Any


DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "verse"
DEFAULT_FORMAT = "aac"
DEFAULT_INSTRUCTIONS = (
    "Speak like an excellent personal fitness coach talking one-to-one through earbuds during a "
    "workout: warm, natural, attentive, and confident. Use conversational pacing, contractions, "
    "subtle changes in energy, and natural intonation. Never sound like an announcer, navigation "
    "system, or someone reading bullet points. Do not add or omit words. Pronounce exercise names "
    "and numbers clearly."
)
SIDE_SWITCH_SCRIPT = "Switch sides."
MAX_PLAN_BYTES = 12 * 1024 * 1024


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Plan JSON or Axon events JSONL")
    parser.add_argument("output", type=Path, help="Enriched plan JSON")
    parser.add_argument("--revision", type=int)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--format", default=DEFAULT_FORMAT)
    parser.add_argument("--instructions", default=DEFAULT_INSTRUCTIONS)
    parser.add_argument("--axon-config", type=Path, default=Path.home() / ".axon" / "config.toml")
    args = parser.parse_args()

    plan = load_plan(args.input)
    if args.revision is not None:
        if args.revision < 1:
            raise SystemExit("--revision must be positive")
        plan["revision"] = args.revision

    fake_audio = os.environ.get("FITNESS_COACH_TTS_FAKE_AUDIO_BASE64")
    api_key = "" if fake_audio is not None else openai_api_key(args.axon_config)
    if fake_audio is None and not api_key:
        raise SystemExit("OpenAI API key is not configured in the environment or Axon keychain")

    existing = {
        asset.get("id"): asset
        for asset in plan.get("coachingAudio", [])
        if isinstance(asset, dict) and isinstance(asset.get("id"), str)
    }
    generated: dict[str, dict[str, Any]] = dict(existing)
    requested = 0

    for prescription in plan.get("prescriptions", []):
        if not isinstance(prescription, dict):
            continue
        for card in prescription.get("cards", []):
            if not isinstance(card, dict):
                continue
            coaching = card.get("spokenCoaching")
            if not isinstance(coaching, dict):
                continue
            script = spoken_script(coaching)
            if script:
                asset, made_request = audio_asset(
                    script,
                    generated,
                    api_key=api_key,
                    model=args.model,
                    voice=args.voice,
                    audio_format=args.format,
                    instructions=args.instructions,
                    fake_audio=fake_audio,
                )
                generated[asset["id"]] = asset
                coaching["audioAssetID"] = asset["id"]
                requested += int(made_request)
            timer = card.get("timer")
            if isinstance(timer, dict) and integer(timer.get("sides")) > 1:
                asset, made_request = audio_asset(
                    SIDE_SWITCH_SCRIPT,
                    generated,
                    api_key=api_key,
                    model=args.model,
                    voice=args.voice,
                    audio_format=args.format,
                    instructions=args.instructions,
                    fake_audio=fake_audio,
                )
                generated[asset["id"]] = asset
                coaching["sideSwitchAudioAssetID"] = asset["id"]
                requested += int(made_request)

    plan["coachingAudio"] = sorted(generated.values(), key=lambda item: item["id"])
    encoded = json.dumps(plan, indent=2, separators=(",", ": "), ensure_ascii=False).encode()
    if len(encoded) > MAX_PLAN_BYTES:
        raise SystemExit(
            f"enriched plan is {len(encoded)} bytes; maximum is {MAX_PLAN_BYTES}. "
            "Move coaching audio to external assets before publication."
        )
    atomic_write(args.output, encoded + b"\n")
    print(
        f"prepared {len(generated)} unique coaching clips "
        f"({requested} generated, {len(generated) - requested} reused); "
        f"plan size {len(encoded)} bytes"
    )
    return 0


def load_plan(path: Path) -> dict[str, Any]:
    if path.suffix == ".jsonl":
        latest: dict[str, Any] | None = None
        with path.open() as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    event.get("namespace") == "fitness"
                    and event.get("type") == "training.plan.approved"
                    and isinstance(event.get("payload"), dict)
                ):
                    latest = event["payload"]
        if latest is None:
            raise SystemExit(f"no fitness.training.plan.approved event in {path}")
        return latest
    decoded = json.loads(path.read_text())
    if not isinstance(decoded, dict):
        raise SystemExit("plan JSON must be an object")
    return decoded


def spoken_script(coaching: dict[str, Any]) -> str:
    narration = string(coaching.get("narration"))
    if narration:
        return narration

    # Backward compatibility for plans published before narration became a
    # separate authored surface.
    transition = string(coaching.get("transition"))
    if not transition:
        return ""
    parts = [transition]
    if coaching.get("announceCues") is True:
        for cue in coaching.get("cues", []):
            cue_text = string(cue)
            if cue_text:
                parts.append(cue_text)
    return " ".join(ensure_sentence(part) for part in parts)


def ensure_sentence(value: str) -> str:
    value = value.strip()
    if value and value[-1] not in ".!?":
        value += "."
    return value


def audio_asset(
    script: str,
    existing: dict[str, dict[str, Any]],
    *,
    api_key: str,
    model: str,
    voice: str,
    audio_format: str,
    instructions: str,
    fake_audio: str | None,
) -> tuple[dict[str, Any], bool]:
    digest_input = "\0".join([model, voice, audio_format, instructions, script]).encode()
    asset_id = "coach_" + hashlib.sha256(digest_input).hexdigest()[:24]
    if asset_id in existing:
        return existing[asset_id], False
    if fake_audio is not None:
        audio_base64 = fake_audio
    else:
        print(f"generating coaching clip {asset_id}", flush=True)
        audio_base64 = base64.b64encode(
            generate_speech(
                script,
                api_key=api_key,
                model=model,
                voice=voice,
                audio_format=audio_format,
                instructions=instructions,
            )
        ).decode()
    return (
        {
            "id": asset_id,
            "format": audio_format,
            "base64": audio_base64,
            "model": model,
            "voice": voice,
        },
        True,
    )


def generate_speech(
    script: str,
    *,
    api_key: str,
    model: str,
    voice: str,
    audio_format: str,
    instructions: str,
) -> bytes:
    payload = json.dumps(
        {
            "model": model,
            "voice": voice,
            "input": script,
            "instructions": instructions,
            "response_format": audio_format,
        },
        separators=(",", ":"),
    ).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise SystemExit(f"OpenAI speech generation failed: {exc.code}: {detail}") from exc


def openai_api_key(config_path: Path) -> str:
    for name in ("OPENAI_API_KEY", "MODEL_OPENAI_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    try:
        account = model_openai_secret_account(config_path.read_text())
    except OSError:
        return ""
    if not account:
        return ""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "Axon", "-a", account, "-w"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=5,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def model_openai_secret_account(config: str) -> str:
    """Read one string setting without imposing a third-party TOML dependency."""
    in_model_openai = False
    for raw_line in config.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            in_model_openai = line == "[plugin.model-openai]"
            continue
        if not in_model_openai or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key != "api-key-secret":
            continue
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            decoded = value.strip("'\"")
        return string(decoded)
    return ""


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def integer(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def string(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


if __name__ == "__main__":
    raise SystemExit(main())
