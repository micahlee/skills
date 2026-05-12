#!/usr/bin/env python3
"""
build_doc.py — Build a song block Google Doc from a structured plan JSON.

Usage:
  python3 build_doc.py <plan.json>

Creates a new Google Doc (or updates an existing one at plan["doc_id"]) with
the song pool, sermon-by-sermon blocks, and usage summary from the plan.

See the song-block SKILL.md for the plan JSON format.
"""

import json, sys, subprocess, os, tempfile
from urllib.request import Request, urlopen
from urllib.parse import urlencode


GWS = "gws.cmd" if os.name == "nt" else "gws"
DOCS_BASE = "https://docs.googleapis.com/v1"


def _gws_access_token():
    """Get a fresh access token using gws auth export + Google OAuth."""
    result = subprocess.run([GWS, "auth", "export"], capture_output=True, text=True, encoding="utf-8")
    lines = [l for l in result.stdout.splitlines() if not l.startswith("Using keyring")]
    creds = json.loads("\n".join(lines))
    # Exchange refresh token for access token
    token_url = "https://oauth2.googleapis.com/token"
    data = urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = Request(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(req) as r:
        return json.loads(r.read())["access_token"]


def docs_batch_update(doc_id, requests_list):
    """Call Google Docs batchUpdate directly via HTTP (avoids command-line length limits)."""
    token = _gws_access_token()
    url = f"{DOCS_BASE}/documents/{doc_id}:batchUpdate"
    body = json.dumps({"requests": requests_list}).encode("utf-8")
    req = Request(url, data=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    with urlopen(req) as r:
        return json.loads(r.read())


def gws_json(*args):
    """Run a gws command and return parsed JSON (skipping keyring prefix line)."""
    result = subprocess.run([GWS] + list(args), capture_output=True, text=True, encoding="utf-8")
    lines = [l for l in result.stdout.splitlines() if not l.startswith("Using keyring")]
    output = "\n".join(lines)
    if not output.strip():
        raise RuntimeError(f"gws returned no output. stderr: {result.stderr}")
    return json.loads(output)


def gws_with_body_file(body_file, *args, params=None):
    """Run a gws command passing a JSON body from a file via shell expansion."""
    parts = ["gws"] + list(args)
    if params:
        parts += ["--params", f"'{json.dumps(params)}'"]
    parts += ["--json", f'"$(cat {body_file})"']
    cmd = " ".join(parts)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    lines = [l for l in result.stdout.splitlines() if not l.startswith("Using keyring")]
    output = "\n".join(lines)
    if result.returncode != 0 and not output.strip():
        raise RuntimeError(f"gws error: {result.stderr}")
    return json.loads(output)


def create_doc(title):
    d = gws_json("docs", "documents", "create", "--json", json.dumps({"title": title}))
    return d["documentId"]


def get_doc_end_index(doc_id):
    d = gws_json(
        "docs", "documents", "get",
        "--params", json.dumps({"documentId": doc_id, "fields": "body.content"})
    )
    content = d.get("body", {}).get("content", [])
    return content[-1]["endIndex"] if content else 1


TIER_LABELS = {
    1: "TIER 1 \u2014 Essential (strongest thematic fit)",
    2: "TIER 2 \u2014 Strong Thematic Fit",
    3: "TIER 3 \u2014 Supporting Liturgical Roles",
}


def build_sections(plan):
    """Convert a plan dict into a list of (text, named_style) tuples."""
    sections = []

    def add(text, style="NORMAL_TEXT"):
        sections.append((text, style))

    # Title / subtitle
    add(f"{plan['title']}\n", "TITLE")
    if plan.get("subtitle"):
        add(f"{plan['subtitle']}\n", "SUBTITLE")

    # ── Song Pool ────────────────────────────────────────────────────────────
    add("SONG POOL \u2014 Ranked by Series Fit\n", "HEADING_1")
    add(
        "[fresh] = not used in past 20 weeks  |  "
        "[recent] = used within ~8 weeks  |  "
        "[deprioritized] = 3+ uses in 20 weeks\n\n"
    )

    current_tier = None
    for song in plan.get("song_pool", []):
        tier = song.get("tier", 3)
        if tier != current_tier:
            current_tier = tier
            add(f"{TIER_LABELS.get(tier, f'TIER {tier}')}\n", "HEADING_2")

        rank = song.get("rank", "")
        name = song["title"]
        author = song.get("author", "")
        tempo = song.get("tempo", "")
        tag = song.get("recency_tag", "")
        detail = song.get("recency_detail", "")
        roles = song.get("roles", "")
        desc = song.get("description", "")

        recency = f"{tag} ({detail})" if detail else tag
        header_parts = [p for p in [
            f"{rank}. {name}" if rank else name,
            author, tempo, recency
        ] if p]
        add(
            f"{'  |  '.join(header_parts)}\n"
            f"Roles: {roles}\n"
            f"{desc}\n\n"
        )

    # ── Sermon Blocks ────────────────────────────────────────────────────────
    add("SERMON SONG BLOCKS\n", "HEADING_1")
    add(
        "Songs listed in liturgy order: Adoration \u2192 Confession \u2192 "
        "Assurance \u2192 Thanksgiving/Petition \u2192 Charge. "
        "Brackets indicate a non-song liturgy element.\n\n"
    )

    for sermon in plan.get("sermons", []):
        num = sermon["number"]
        s_title = sermon["title"]
        passage = sermon["text"]
        main_idea = sermon.get("main_idea", "")

        add(f"Sermon {num} \u2014 {s_title}  |  {passage}\n", "HEADING_2")
        if main_idea:
            add(f"Main idea: {main_idea}\n\n")

        for song in sermon.get("songs", []):
            name = song["title"]
            role = song.get("role", "")
            use_count = song.get("use_count", "")
            note = song.get("note", "")

            if use_count and role:
                label = f"{role}, {use_count}"
            elif role:
                label = role
            else:
                label = None

            heading = f"{name}  [{label}]\n" if label else f"{name}\n"
            add(heading, "HEADING_3")
            add(f"{note}\n\n" if note else "\n")

    # ── Usage Summary ────────────────────────────────────────────────────────
    if plan.get("usage_summary"):
        add("SONG USAGE SUMMARY\n", "HEADING_1")
        add(f"{plan['usage_summary']}\n\n")

    return sections


def build_requests(sections, current_end):
    """Turn sections into a Docs API batchUpdate requests list."""
    full_text = ""
    heading_ranges = []
    idx = 1

    for text, style in sections:
        start = idx
        end = idx + len(text)
        if style != "NORMAL_TEXT":
            heading_ranges.append((start, end, style))
        full_text += text
        idx = end

    requests = []
    if current_end > 1:
        requests.append({
            "deleteContentRange": {
                "range": {"startIndex": 1, "endIndex": current_end - 1}
            }
        })
    requests.append({
        "insertText": {"location": {"index": 1}, "text": full_text}
    })
    for start, end, style in reversed(heading_ranges):
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end},
                "paragraphStyle": {"namedStyleType": style},
                "fields": "namedStyleType",
            }
        })
    return requests, len(full_text)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        plan = json.load(f)

    doc_id = plan.get("doc_id")

    if not doc_id:
        print(f"Creating new Google Doc: {plan['title']!r}")
        doc_id = create_doc(plan["title"])
        print(f"  doc_id: {doc_id}")
    else:
        print(f"Updating existing doc: {doc_id}")

    current_end = get_doc_end_index(doc_id)
    print(f"  current end index: {current_end}")

    sections = build_sections(plan)
    requests, text_len = build_requests(sections, current_end)
    print(f"  {len(requests)} requests, {text_len} chars")

    body = {"requests": requests}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(body, f, ensure_ascii=False)
        body_file = f.name

    try:
        params = json.dumps({"documentId": doc_id})
        # Convert Windows path to POSIX for bash if needed
        bash_body_file = body_file
        if os.name == "nt":
            r = subprocess.run(["bash", "-c", f"cygpath -u '{body_file}'"],
                               capture_output=True, text=True, encoding="utf-8")
            bash_body_file = r.stdout.strip()
        # Use bash explicitly to support $(cat ...) expansion on all platforms
        cmd = (
            f"gws docs documents batchUpdate "
            f"--params '{params}' "
            f'--json "$(cat {bash_body_file})"'
        )
        result = subprocess.run(
            ["bash", "-c", cmd], capture_output=True, text=True, encoding="utf-8"
        )
        lines = [l for l in result.stdout.splitlines() if not l.startswith("Using keyring")]
        output = "\n".join(lines)
        if result.returncode != 0 and not output.strip():
            print(f"Error: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        d = json.loads(output)
        url = f"https://docs.google.com/document/d/{d['documentId']}/edit"
        print(f"Done: {url}")
    finally:
        os.unlink(body_file)


if __name__ == "__main__":
    main()
