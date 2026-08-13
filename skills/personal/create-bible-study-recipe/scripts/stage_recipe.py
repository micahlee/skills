#!/usr/bin/env python3
"""Privately normalize and stage an agent-authored Bible Study recipe bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid


MAX_BUNDLE_BYTES = 16 * 1024 * 1024
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CAPABILITY = "personal.bible-study.recipe.command"
SCOPES = (
    "graphql:query:personalBibleStudyProgramLibrary",
    "graphql:query:personalBibleStudyRecipeDraft",
    "graphql:query:personalBibleStudyRecipeCommand",
    f"capabilities:call:{CAPABILITY}",
)


class StageError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--bundle-id")
    parser.add_argument("--config", type=Path, default=Path.home() / ".axon" / "config.toml")
    parser.add_argument("--axon-bin", type=Path, default=Path.home() / ".local" / "bin" / "axon")
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser.parse_args()


def load_config(path: Path) -> tuple[Path, str]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StageError("Axon config is unavailable") from exc
    root = source.split("\n[", 1)[0]
    values: dict[str, str] = {}
    for line in root.splitlines():
        match = re.fullmatch(r'\s*(data_dir|http_addr)\s*=\s*"([^"\\]*)"\s*(?:#.*)?', line)
        if match:
            values[match.group(1)] = match.group(2)
    data_dir = Path(os.path.expanduser(values.get("data_dir", "~/.axon")))
    address = values.get("http_addr", "127.0.0.1:8080").strip()
    if not address:
        raise StageError("Axon http_addr is unavailable")
    if not address.startswith(("http://", "https://")):
        address = "http://" + address
    return data_dir, address.rstrip("/")


def read_bundle(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise StageError("bundle must be a regular non-symlink file")
    mode = path.stat().st_mode
    if not stat.S_ISREG(mode) or path.stat().st_size > MAX_BUNDLE_BYTES:
        raise StageError("bundle is not regular or exceeds 16 MiB")
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise StageError("bundle is not readable JSON") from exc
    if not isinstance(value, dict):
        raise StageError("bundle root must be an object")
    if value.get("contract") != "personal.bible-study.program-library@1" or value.get("schemaVersion") != 1:
        raise StageError("bundle contract must be personal.bible-study.program-library@1")
    recipe = value.get("recipe")
    program = value.get("program")
    if not isinstance(recipe, dict) or recipe.get("reviewState") != "draft":
        raise StageError("recipe.reviewState must be draft")
    if recipe.get("family") not in {"seasonal", "external_resource"}:
        raise StageError("agent-authored recipe family must be seasonal or external_resource")
    if not isinstance(program, dict):
        raise StageError("bundle program is required")
    return value


def http_json(url: str, token: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    encoded = json.dumps(body, separators=(",", ":")).encode()
    request = Request(url, data=encoded, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    })
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.length is not None and response.length > 4 * 1024 * 1024:
                raise StageError("Axon response exceeded 4 MiB")
            payload = response.read(4 * 1024 * 1024 + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise StageError("Axon request failed") from exc
    if len(payload) > 4 * 1024 * 1024:
        raise StageError("Axon response exceeded 4 MiB")
    try:
        result = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise StageError("Axon returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise StageError("Axon returned an invalid response")
    return result


def graphql(base: str, token: str, query: str, variables: dict[str, Any] | None, timeout: float) -> Any:
    body: dict[str, Any] = {"query": query}
    if variables is not None:
        body["variables"] = variables
    response = http_json(base + "/api/graphql", token, body, timeout)
    if response.get("errors"):
        raise StageError("Axon GraphQL query was rejected")
    data = response.get("data")
    if not isinstance(data, dict):
        raise StageError("Axon GraphQL response omitted data")
    return data


def next_library_revision(base: str, token: str, timeout: float) -> int:
    data = graphql(base, token, "query { personalBibleStudyProgramLibrary }", None, timeout)
    library = data.get("personalBibleStudyProgramLibrary")
    if library is None:
        return 2
    if not isinstance(library, dict) or not isinstance(library.get("revision"), int):
        raise StageError("installed Program library revision is invalid")
    return library["revision"] + 1


def draft_revision(base: str, token: str, timeout: float) -> int:
    data = graphql(base, token, "query { personalBibleStudyRecipeDraft }", None, timeout)
    projection = data.get("personalBibleStudyRecipeDraft")
    if not isinstance(projection, dict) or not isinstance(projection.get("revision"), int):
        raise StageError("recipe draft projection revision is invalid")
    return projection["revision"]


def write_private_bundle(data_dir: Path, bundle_id: str, encoded: bytes) -> Path:
    parent = data_dir / "imports" / "bible-study"
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(parent, 0o700)
    target = parent / f"{bundle_id}.json"
    if target.is_symlink():
        raise StageError("refusing to replace a symlinked staged bundle")
    if target.exists():
        if not target.is_file() or target.read_bytes() != encoded:
            raise StageError("bundle ID already exists with different content; use a new bundle ID")
        return target
    descriptor, temporary = tempfile.mkstemp(prefix=".recipe-", dir=parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        os.chmod(target, 0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return target


def create_client(axon_bin: Path, config: Path, token_path: Path) -> tuple[str, str]:
    name = "bible-study-recipe-author-" + uuid.uuid4().hex[:12]
    command = [str(axon_bin), "clients", "create", "--config", str(config), "--expires", "10m",
               "--profile", name, "--token-file", str(token_path)]
    for scope in SCOPES:
        command.extend(["--scope", scope])
    command.append(name)
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise StageError("failed to create short-lived Axon recipe client")
    try:
        response = json.loads(completed.stdout)
        client_id = response["client"]["id"]
        core_url = response["profile"]["core_url"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise StageError("Axon client response was invalid") from exc
    return str(client_id), str(core_url).rstrip("/")


def revoke_client(axon_bin: Path, config: Path, client_id: str) -> None:
    subprocess.run(
        [str(axon_bin), "clients", "revoke", "--config", str(config), client_id],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )


def main() -> int:
    args = parse_args()
    bundle_id = args.bundle_id or args.bundle.stem
    if not IDENTIFIER.fullmatch(bundle_id):
        raise StageError("bundle ID must match [A-Za-z0-9][A-Za-z0-9._-]*")
    bundle = read_bundle(args.bundle)
    data_dir, configured_base = load_config(args.config)
    client_id = ""
    with tempfile.TemporaryDirectory(prefix="axon-recipe-client-") as directory:
        token_path = Path(directory) / "token"
        try:
            client_id, core_url = create_client(args.axon_bin, args.config, token_path)
            if core_url != configured_base:
                raise StageError("Axon client profile URL does not match configured http_addr")
            token = token_path.read_text(encoding="utf-8").strip()
            if not token:
                raise StageError("Axon client token is unavailable")
            new_revision = next_library_revision(core_url, token, args.timeout)
            bundle["revision"] = new_revision
            bundle["program"]["revision"] = new_revision
            encoded = json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
            if len(encoded) > MAX_BUNDLE_BYTES:
                raise StageError("normalized bundle exceeds 16 MiB")
            digest = hashlib.sha256(encoded).hexdigest()
            write_private_bundle(data_dir, bundle_id, encoded)
            expected_revision = draft_revision(core_url, token, args.timeout)
            command_id = "recipe-stage-" + uuid.uuid4().hex
            idempotency_key = "recipe-stage-idem-" + uuid.uuid4().hex
            requested_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            arguments = {
                "contract": "personal.bible-study.recipe-command@1",
                "schemaVersion": 1,
                "commandID": command_id,
                "idempotencyKey": idempotency_key,
                "kind": "recipe.stage",
                "expectedRevision": expected_revision,
                "bundleID": bundle_id,
                "bundleSha256": digest,
                "requestedAt": requested_at,
            }
            receipt = http_json(core_url + "/api/v1/capabilities/" + CAPABILITY, token, {
                "request_id": command_id,
                "idempotency_key": idempotency_key,
                "arguments": arguments,
            }, args.timeout)
            if receipt.get("call_id") != command_id:
                raise StageError("Axon returned an invalid capability receipt")
            result = None
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                data = graphql(
                    core_url, token,
                    "query RecipeCommand($commandID: ID!) { personalBibleStudyRecipeCommand(commandID: $commandID) }",
                    {"commandID": command_id}, args.timeout,
                )
                result = data.get("personalBibleStudyRecipeCommand")
                if result is not None:
                    break
                time.sleep(0.25)
            if not isinstance(result, dict) or result.get("commandID") != command_id:
                raise StageError("recipe stage command timed out")
            projection = graphql(core_url, token, "query { personalBibleStudyRecipeDraft }", None, args.timeout).get(
                "personalBibleStudyRecipeDraft"
            )
            if result.get("result") != "applied":
                raise StageError("recipe stage was rejected: " + str(result.get("error", "unknown_error")))
            draft = projection.get("draft") if isinstance(projection, dict) else None
            if not isinstance(draft, dict) or draft.get("bundleSha256") != digest:
                raise StageError("staged draft did not match the submitted digest")
            safe = {
                "result": "applied",
                "revision": result.get("revision"),
                "draft": draft,
            }
            print(json.dumps(safe, indent=2, sort_keys=True, ensure_ascii=True))
        finally:
            if client_id:
                revoke_client(args.axon_bin, args.config, client_id)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StageError as exc:
        print(f"stage_recipe: {exc}", file=os.sys.stderr)
        raise SystemExit(1)
