#!/usr/bin/env python3
"""Validate, render, hash, and immutably publish agenda DOCX files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from validate_agenda import validate


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def choose_destination(source: Path, destination: Path) -> tuple[Path, bool]:
    source_hash = sha256(source)
    candidate = destination / source.name
    if not candidate.exists():
        return candidate, False
    if sha256(candidate) == source_hash:
        return candidate, True

    revision = 2
    while True:
        candidate = destination / f"{source.stem}-r{revision}{source.suffix}"
        if not candidate.exists():
            return candidate, False
        if sha256(candidate) == source_hash:
            return candidate, True
        revision += 1


def render(renderer: Path, docx: Path, output_dir: Path) -> list[Path]:
    completed = subprocess.run(
        [sys.executable, str(renderer), str(docx), "--output_dir", str(output_dir)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"renderer failed ({completed.returncode}): {completed.stderr.strip() or completed.stdout.strip()}"
        )
    pages = sorted(output_dir.glob("page-*.png"))
    if not pages:
        raise RuntimeError("renderer produced no page PNGs")
    return pages


def exclusive_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("xb") as dst:
        shutil.copyfileobj(src, dst)


def write_manifest(path: Path, manifest: dict) -> None:
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"existing manifest differs: {path}")
        return
    with path.open("x", encoding="utf-8") as handle:
        handle.write(rendered)


def persist_rendered_pages(pages: list[Path], render_root: Path, stem: str) -> Path:
    candidate = render_root / stem
    suffix = 2
    while candidate.exists():
        candidate = render_root / f"{stem}-r{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    for page in pages:
        shutil.copy2(page, candidate / page.name)
    return candidate


def prepare_one(
    normalized_json: Path,
    source_docx: Path,
    renderer: Path,
    temp_render: Path,
) -> dict:
    data = json.loads(normalized_json.read_text(encoding="utf-8"))
    validation = validate(data, source_docx)
    if not validation["ok"]:
        raise RuntimeError("agenda validation failed: " + "; ".join(validation["errors"]))

    temp_render.mkdir()
    pages = render(renderer, source_docx, temp_render)
    weekday = date.fromisoformat(data["date"]).strftime("%A")
    expected_pages = 2 if weekday in {"Monday", "Friday"} else 1
    if len(pages) != expected_pages:
        raise RuntimeError(f"page count: expected {expected_pages}, got {len(pages)}")
    return {
        "data": data,
        "normalized_json": normalized_json,
        "source_docx": source_docx,
        "pages": pages,
        "page_hashes": {page.name: sha256(page) for page in pages},
    }


def publish_prepared(prepared: dict, destination: Path, render_root: Path | None) -> dict:
    data = prepared["data"]
    normalized_json = prepared["normalized_json"]
    source_docx = prepared["source_docx"]
    pages = prepared["pages"]
    page_hashes = prepared["page_hashes"]

    published, reused = choose_destination(source_docx, destination)
    if not reused:
        exclusive_copy(source_docx, published)
    if sha256(published) != sha256(source_docx):
        raise RuntimeError("published DOCX hash does not match source")

    rendered_dir = None
    if render_root is not None:
        render_root.mkdir(parents=True, exist_ok=True)
        rendered_dir = persist_rendered_pages(pages, render_root, published.stem)

    manifest = {
        "student": data["student"],
        "date": data["date"],
        "docx": published.name,
        "docx_sha256": sha256(published),
        "normalized_json_sha256": sha256(normalized_json),
        "page_count": len(page_hashes),
        "page_sha256": page_hashes,
        "reused_identical_file": reused,
    }
    manifest_path = published.with_suffix(".manifest.json")
    write_manifest(manifest_path, manifest)
    return {
        "ok": True,
        "published_docx": str(published),
        "manifest": str(manifest_path),
        "rendered_pages": str(rendered_dir) if rendered_dir else None,
        "reused_identical_file": reused,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agenda",
        nargs=2,
        action="append",
        metavar=("NORMALIZED_JSON", "DOCX"),
        required=True,
    )
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--renderer", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path)
    args = parser.parse_args()

    if not args.renderer.is_file():
        print(json.dumps({"ok": False, "error": f"renderer not found: {args.renderer}"}), file=sys.stderr)
        return 1

    try:
        with tempfile.TemporaryDirectory(prefix="agenda-publish-batch-") as temporary:
            root = Path(temporary)
            prepared = [
                prepare_one(Path(normalized), Path(docx), args.renderer, root / f"agenda-{index}")
                for index, (normalized, docx) in enumerate(args.agenda)
            ]
            outputs = [
                publish_prepared(item, args.destination, args.render_dir)
                for item in prepared
            ]
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, "outputs": outputs}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
