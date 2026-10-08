# Set up another Codex host

Clone `micahlee/skills` to a durable checkout, normally `~/projects/skills`.
Fetch `origin/main` and use a clean checkout at that exact commit. Do not move
or archive the checkout while installed skills link to it.

```sh
bash scripts/validate-skills.sh
python3 scripts/install-local.py --rules
# Review the preview, then:
python3 scripts/install-local.py --rules --apply
```

The installer defaults to `~/.agents/skills`, which is shared agent discovery.
Use `--skill NAME` (repeatable) for a subset or `--destination DIR` for a custom
location. It preserves existing skills and rules, reports conflicts before
writing, and refuses application from a dirty or non-main checkout. Fetch
before applying: the local `origin/main` reference is not a freshness check.
It detects duplicate owners across standard shared and Codex skill locations.
The installer excludes `fitness-coach`, whose installed source receipt names
`micahlee/axon-personal/config/codex-training-skills`; use that managed delivery
path for fitness and the other training-generation skills. Reconcile conflicts by comparing and backing up existing content, not by
blindly replacing it. Preview is read-only and can inspect a task branch.

`--rules` copies the versioned user instructions from `rules/CODEX-AGENTS.md`
to `${CODEX_HOME:-~/.codex}/AGENTS.md`. Review differences on an existing host;
the installer never overwrites them. Future rule changes require a reviewed
update of that copy. Standard processing and permission-verification rules
are included. They do not change the app's actual model, processing tier,
sandbox, or approval settings: verify those separately in each runtime.

Skills contain instructions, not applications, credentials, or data. Install
CLI-owned skills through their repositories' supported installers; avoid a
second copy of the same skill. Discover the Obsidian vault and cloud-storage
folders on the destination host. Expand `~` in prose paths; shell scripts use
`$HOME`. Configure secrets through supported local login and Keychain flows.

## Dependency ownership

This table records sources inspected on the existing Mac on October 8, 2026.
Read the source's current installation documentation before installing.

| Client | Source / installation owner | Required companion setup |
| --- | --- | --- |
| `gh` | GitHub CLI / Homebrew | GitHub sign-in; access to private repositories |
| `gws`, `gws-axon` | `googleworkspace/cli`; shared gws skills or this repo's `gws` skill, with one chosen owner | Existing Google OAuth client; wrapper sets `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file` |
| `mog` | `micahlee/mogcli` fork; module `visionik/mogcli` | Microsoft app registration and OAuth; Office apps unnecessary for ordinary API access |
| `basecamp` | `basecamp/basecamp-cli` | OAuth; install its agent integration |
| `pco` | `micahlee/pco-cli`, bundled skill | Keychain credential setup; `pco` is the canonical command |
| `classreach` | `micahlee/homebrew-classreach` binary tap; `micahlee/classreach-cli` source and bundled skill | School tenant and Keychain setup |
| `crossbar` | `micahlee/crossbar-client`; this repo owns `crossbar-cli` | Python dependencies, certificate-signed native helpers, CrossbarClient login app, separate central/club login |
| `plantoeat` / `plantoeat-cli` | Local module `github.com/micahlee/plantoeat-cli` | Resolve source first: inspected checkout had no origin and GitHub REST lookup returned 404; consistent launcher name |
| `songselect` | `micahlee/songselect-cli` | Google Chrome and CCLI login |
| `mmoney` | `micahlee/mmoney-cli` fork; this repo's `monarch-money` skill | Python/uv and interactive Monarch login |
| `fitbod` | `micahlee/fitbod-cli`, bundled skill | Read supported import/auth flow; experimental cloud and local-app paths are distinct |
| `hevy` | `micahlee/hevy-cli` | Python/uv and supported API authentication |
| `shopping-cli` | `micahlee/shopping-cli`, bundled skill | Node >=22.5, Chrome, retailer profiles; Docker/Colima or Lima optional |
| `lpass` | LastPass CLI; this repo's `lastpass-cli` skill | Explicit confirmation before every lpass invocation, including status |
| `logos-cli` | `micahlee/logos-cli`, bundled skill | Signed-in Logos desktop, downloaded licensed resources, sqlite3, compatible .NET SDK 9 and packaged LogosHeadless helper |
| `prayermate-headless` | Local module `github.com/micahlee/prayermate-headless-client`, local bundled skill | Resolve source first: no origin and GitHub REST lookup returned 404; inspect bootstrap needs before assuming PrayerMate.app is required |
| `fly` / `flyctl` | Official Fly.io CLI | Authentication; installation does not authorize deployment |
| `axon` | `micahlee/axon-core`, bundled skill | Complete intended deployment and credential setup; the CLI alone is insufficient |
| `obsidian` | Obsidian desktop; separately installed `obsidian-cli` skill | Current CLI-capable installer, CLI registration, running app and synced vault |
| `hue-cli` | `micahlee/hue-cli`, bundled skill | Python, LAN access, physical bridge-button authorization |
| `roku-cli` | `micahlee/roku-cli`, bundled skill | Python, LAN access, applicable Roku mobile-control setting |
| `deco` | `jvreagan/deco` upstream; `micahlee/deco` fork | Router LAN/auth setup; Ollama optional for chat |

Other optional workflows in this collection refer to `sonos`, `spogo`, and
`instagram-cli`. Their presence as skills does not establish installed or
authenticated clients. Resolve them only when those workflows are needed.
Axon programming also uses the separately owned `workout-cli` skill/client.

## Existing-host reconciliation

The local audit found one substantive installed fitness instruction absent
from main: keep recipe validation, local persistence, publication, Training
visibility, Startability, and dated Session submission distinct. Its `.axon-source.json` receipt identifies
`micahlee/axon-personal` as the current installation owner. The reference copy
here preserves the instruction, but must not replace that managed skill. The NRC CSV difference was line endings only.
The installed school-agenda copy is older than main, including renderer-path
handling; retain the newer source rather than copying the old installation
back. An identical create-bible-study-recipe copy needs no content migration.
Crossbar's skill previously lived in a dated chat folder and is now part of
this collection with host-local launcher discovery.

Before replacing installed copies, back them up and compare their entire
skill directories. Keep credentials and personal snapshots outside this repo.
The old host also has project-tree `AGENTS.md` rules (including the usage
reserve check and Axon build workflow). Review those separately for the new
host; global rules alone do not carry directory-scoped instructions.

Installing these skills does not transfer chats, schedules, desktop privacy
permissions, vault data, or Axon's durable state. Handle those as a separate
primary-host migration, with one owner for each live writer and automation.
