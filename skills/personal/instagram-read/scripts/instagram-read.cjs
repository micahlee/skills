#!/usr/bin/env node
"use strict";

const childProcess = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const SHORTCODE_ALPHABET =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage: instagram-read [options] URL...

Read Instagram reel/post metadata using the saved instagram-cli session.

Options:
  --format json|markdown   Output format (default: json)
  --username USER          Saved instagram-cli username to use
  --refresh                Ignore cached metadata and fetch live data
  --no-cache               Disable reading and writing cache files
  -h, --help               Show this help

Examples:
  instagram-read --format json https://www.instagram.com/reel/SHORTCODE/
  instagram-read --format markdown --refresh URL1 URL2
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const options = {
    format: "json",
    username: undefined,
    refresh: false,
    cache: true,
    urls: [],
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "-h" || arg === "--help") usage(0);
    if (arg === "--refresh") {
      options.refresh = true;
      continue;
    }
    if (arg === "--no-cache") {
      options.cache = false;
      continue;
    }
    if (arg === "--format") {
      options.format = argv[++index];
      continue;
    }
    if (arg.startsWith("--format=")) {
      options.format = arg.slice("--format=".length);
      continue;
    }
    if (arg === "--username") {
      options.username = argv[++index];
      continue;
    }
    if (arg.startsWith("--username=")) {
      options.username = arg.slice("--username=".length);
      continue;
    }
    if (arg.startsWith("-")) {
      throw new Error(`Unknown option: ${arg}`);
    }
    options.urls.push(arg);
  }

  if (!["json", "markdown"].includes(options.format)) {
    throw new Error("--format must be json or markdown");
  }
  if (options.urls.length === 0) usage(1);
  return options;
}

function expandHome(filePath) {
  if (!filePath) return filePath;
  if (filePath === "~") return os.homedir();
  if (filePath.startsWith("~/")) return path.join(os.homedir(), filePath.slice(2));
  return filePath;
}

function parseSimpleYamlConfig(configPath) {
  const config = {};
  if (!fs.existsSync(configPath)) return config;

  let section = "";
  for (const rawLine of fs.readFileSync(configPath, "utf8").split(/\r?\n/)) {
    const line = rawLine.replace(/\s+$/, "");
    if (!line || line.trimStart().startsWith("#")) continue;
    const topLevel = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line);
    if (topLevel && !line.startsWith(" ")) {
      section = topLevel[1];
      if (topLevel[2]) config[section] = topLevel[2].replace(/^"|"$/g, "");
      continue;
    }
    const nested = /^\s+([A-Za-z0-9_-]+):\s*(.*)$/.exec(line);
    if (nested && section) {
      config[section] = config[section] || {};
      config[section][nested[1]] = nested[2].replace(/^"|"$/g, "");
    }
  }
  return config;
}

function findInstagramCliPackageRoot() {
  const explicitRoot = process.env.INSTAGRAM_CLI_PACKAGE_ROOT;
  if (explicitRoot) return explicitRoot;

  const cliPath = findOnPath("instagram-cli");
  if (!cliPath) {
    throw new Error("instagram-cli is not on PATH");
  }

  const realCliPath = fs.realpathSync(cliPath);
  let current = path.dirname(realCliPath);
  while (current !== path.dirname(current)) {
    if (
      fs.existsSync(path.join(current, "package.json")) &&
      fs.existsSync(path.join(current, "node_modules", "instagram-private-api"))
    ) {
      return current;
    }
    current = path.dirname(current);
  }
  throw new Error("Could not locate instagram-cli package root");
}

function findOnPath(executable) {
  const pathDirs = (process.env.PATH || "").split(path.delimiter);
  for (const dir of pathDirs) {
    if (!dir) continue;
    const candidate = path.join(dir, executable);
    try {
      fs.accessSync(candidate, fs.constants.X_OK);
      return candidate;
    } catch {
      // Keep looking.
    }
  }
  return undefined;
}

function loadInstagramPrivateApi() {
  const packageRoot = findInstagramCliPackageRoot();
  const modulePath = path.join(
    packageRoot,
    "node_modules",
    "instagram-private-api",
  );
  return require(modulePath);
}

function shortcodeFromUrl(url) {
  const match = String(url).match(
    /instagram\.com\/(?:reel|p|tv)\/([^/?#]+)/i,
  );
  if (!match) {
    throw new Error(`Not an Instagram reel/post URL: ${url}`);
  }
  return match[1];
}

function shortcodeToMediaId(shortcode) {
  let id = 0n;
  for (const char of shortcode) {
    const value = SHORTCODE_ALPHABET.indexOf(char);
    if (value < 0) throw new Error(`Invalid shortcode character: ${char}`);
    id = id * 64n + BigInt(value);
  }
  return id.toString();
}

function cachePathFor(shortcode) {
  return path.join(
    os.homedir(),
    ".cache",
    "agent-skills",
    "instagram-read",
    `${shortcode}.json`,
  );
}

function readCache(shortcode) {
  const cachePath = cachePathFor(shortcode);
  if (!fs.existsSync(cachePath)) return undefined;
  return JSON.parse(fs.readFileSync(cachePath, "utf8"));
}

function writeCache(shortcode, result) {
  const cachePath = cachePathFor(shortcode);
  fs.mkdirSync(path.dirname(cachePath), { recursive: true, mode: 0o700 });
  fs.writeFileSync(cachePath, `${JSON.stringify(result, null, 2)}\n`, {
    encoding: "utf8",
    mode: 0o600,
  });
}

function isoFromUnixSeconds(value) {
  if (!value) return null;
  return new Date(Number(value) * 1000).toISOString();
}

function bestMediaUrl(item) {
  const videos = item.video_versions || [];
  if (videos.length > 0) {
    const best = videos.reduce((winner, candidate) => {
      const winnerPixels = Number(winner.width || 0) * Number(winner.height || 0);
      const candidatePixels =
        Number(candidate.width || 0) * Number(candidate.height || 0);
      return candidatePixels > winnerPixels ? candidate : winner;
    }, videos[0]);
    return { type: "video", width: best.width, height: best.height };
  }

  const images = item.image_versions2?.candidates || [];
  if (images.length > 0) {
    const best = images.reduce((winner, candidate) => {
      const winnerPixels = Number(winner.width || 0) * Number(winner.height || 0);
      const candidatePixels =
        Number(candidate.width || 0) * Number(candidate.height || 0);
      return candidatePixels > winnerPixels ? candidate : winner;
    }, images[0]);
    return { type: "image", width: best.width, height: best.height };
  }

  return null;
}

function audioSummary(item) {
  const music = item.clips_metadata?.music_info?.music_asset_info;
  if (music) {
    return {
      title: music.title || null,
      artist: music.display_artist || null,
      source: "music",
    };
  }

  const original = item.clips_metadata?.original_sound_info;
  if (original) {
    return {
      title:
        original.original_audio_title ||
        original.ig_artist?.username ||
        item.user?.username ||
        null,
      artist: original.ig_artist?.username || "Original audio",
      source: "original",
    };
  }

  return null;
}

function normalizeItem({ item, url, shortcode, decodedMediaId, fromCache }) {
  return {
    ok: true,
    source: "instagram-private-api",
    from_cache: Boolean(fromCache),
    fetched_at: new Date().toISOString(),
    url,
    shortcode,
    decoded_media_id: decodedMediaId,
    media_id: item.id || null,
    pk: item.pk ? String(item.pk) : null,
    code: item.code || shortcode,
    product_type: item.product_type || null,
    media_type: item.media_type ?? null,
    taken_at: isoFromUnixSeconds(item.taken_at),
    author: item.user
      ? {
          username: item.user.username || null,
          full_name: item.user.full_name || null,
          is_verified: Boolean(item.user.is_verified),
          pk: item.user.pk ? String(item.user.pk) : null,
        }
      : null,
    caption: item.caption?.text || null,
    metrics: {
      like_count: item.like_count ?? null,
      comment_count: item.comment_count ?? null,
      play_count: item.play_count ?? null,
      view_count: item.view_count ?? null,
    },
    video_duration_seconds: item.video_duration
      ? Number(item.video_duration)
      : null,
    audio: audioSummary(item),
    media: bestMediaUrl(item),
  };
}

function normalizeError({ error, url, shortcode, decodedMediaId }) {
  return {
    ok: false,
    source: "instagram-private-api",
    fetched_at: new Date().toISOString(),
    url,
    shortcode,
    decoded_media_id: decodedMediaId,
    error: {
      message: error.message,
      name: error.name,
      status_code: error.response?.statusCode || error.response?.status_code || null,
      body: error.response?.body || null,
    },
  };
}

function currentUsernameFromConfig() {
  const configPath = path.join(os.homedir(), ".instagram-cli", "config.ts.yaml");
  const config = parseSimpleYamlConfig(configPath);
  return config.login?.currentUsername || config.login?.defaultUsername;
}

function usersDirFromConfig() {
  const configPath = path.join(os.homedir(), ".instagram-cli", "config.ts.yaml");
  const config = parseSimpleYamlConfig(configPath);
  return expandHome(
    config.advanced?.usersDir ||
      path.join(os.homedir(), ".instagram-cli", "users"),
  );
}

async function buildClient({ username }) {
  const { IgApiClient } = loadInstagramPrivateApi();
  const resolvedUsername = username || currentUsernameFromConfig();
  if (!resolvedUsername) {
    throw new Error(
      "No instagram-cli username configured. Run `instagram-cli auth login` first.",
    );
  }

  const sessionPath = path.join(
    usersDirFromConfig(),
    resolvedUsername,
    "session.ts.json",
  );
  if (!fs.existsSync(sessionPath)) {
    throw new Error(
      `No saved instagram-cli session found for ${resolvedUsername}: ${sessionPath}`,
    );
  }

  const ig = new IgApiClient();
  ig.state.generateDevice(resolvedUsername);
  const session = JSON.parse(fs.readFileSync(sessionPath, "utf8"));
  await ig.state.deserialize(session);
  return { ig, username: resolvedUsername };
}

async function readUrl({ ig, url, options }) {
  const shortcode = shortcodeFromUrl(url);
  const decodedMediaId = shortcodeToMediaId(shortcode);

  if (options.cache && !options.refresh) {
    const cached = readCache(shortcode);
    if (cached) return { ...cached, from_cache: true };
  }

  try {
    const response = await ig.media.info(decodedMediaId);
    const item = response.items?.[0] || response.item || response;
    const result = normalizeItem({
      item,
      url,
      shortcode,
      decodedMediaId,
      fromCache: false,
    });
    if (options.cache) writeCache(shortcode, result);
    return result;
  } catch (error) {
    return normalizeError({ error, url, shortcode, decodedMediaId });
  }
}

function formatMarkdown(results) {
  return results
    .map((result) => {
      if (!result.ok) {
        return [
          `## ${result.url}`,
          "",
          `- Error: ${result.error.message}`,
          result.error.status_code ? `- Status: ${result.error.status_code}` : null,
        ]
          .filter(Boolean)
          .join("\n");
      }

      const author = result.author
        ? `@${result.author.username}${
            result.author.full_name ? ` (${result.author.full_name})` : ""
          }`
        : "unknown";
      const metrics = Object.entries(result.metrics)
        .filter(([, value]) => value !== null && value !== undefined)
        .map(([key, value]) => `${key.replace(/_/g, " ")}: ${value}`)
        .join(", ");
      return [
        `## ${result.url}`,
        "",
        `- Author: ${author}`,
        result.taken_at ? `- Posted: ${result.taken_at}` : null,
        result.product_type ? `- Type: ${result.product_type}` : null,
        result.video_duration_seconds
          ? `- Duration: ${result.video_duration_seconds.toFixed(1)}s`
          : null,
        metrics ? `- Metrics: ${metrics}` : null,
        result.audio
          ? `- Audio: ${[result.audio.title, result.audio.artist]
              .filter(Boolean)
              .join(" - ")}`
          : null,
        result.caption ? `\n${result.caption}` : null,
      ]
        .filter(Boolean)
        .join("\n");
    })
    .join("\n\n");
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const { ig, username } = await buildClient(options);
  const results = [];

  for (const url of options.urls) {
    results.push(await readUrl({ ig, url, options }));
  }

  if (options.format === "json") {
    process.stdout.write(
      `${JSON.stringify({ account: username, results }, null, 2)}\n`,
    );
  } else {
    process.stdout.write(`${formatMarkdown(results)}\n`);
  }
}

main().catch((error) => {
  process.stderr.write(`instagram-read: ${error.message}\n`);
  process.exit(1);
});
