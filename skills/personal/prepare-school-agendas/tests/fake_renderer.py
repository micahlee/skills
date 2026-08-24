#!/usr/bin/env python3
import argparse
import base64
from pathlib import Path

from docx import Document


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

parser = argparse.ArgumentParser()
parser.add_argument("docx", type=Path)
parser.add_argument("--output_dir", type=Path, required=True)
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
for number in range(1, len(Document(args.docx).sections) + 1):
    (args.output_dir / f"page-{number}.png").write_bytes(PNG)
