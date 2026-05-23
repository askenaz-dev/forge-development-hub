#!/usr/bin/env node
// Refresh ../references/ from a local clone of FTI00575-design-system and rewrite ../.ds-version.
// Usage: node scripts/sync.mjs [--source <path-to-DS-clone>]
// No external dependencies. Idempotent: running twice against an unchanged source leaves no diff.

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  access,
  copyFile,
  mkdir,
  readFile,
  writeFile,
} from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, "..");
const REFERENCES_DIR = join(SKILL_DIR, "references");
const SEMANTIC_DIR = join(REFERENCES_DIR, "semantic-design");
const DS_VERSION_FILE = join(SKILL_DIR, ".ds-version");

const TOP_LEVEL_FILES = [
  "AGENTS.md",
  "COMPONENTS.md",
  "DESIGN.md",
  "components.meta.json",
];

const SEMANTIC_FILES = [
  "ds-react.md",
  "tokens.md",
  "actions.md",
  "forms.md",
  "surfaces.md",
  "feedback.md",
  "navigation.md",
  "layout.md",
];

function parseArgs(argv) {
  let source = "../FTI00575-design-system";
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--source") {
      source = argv[++i];
    } else if (arg.startsWith("--source=")) {
      source = arg.slice("--source=".length);
    } else if (arg === "--help" || arg === "-h") {
      printUsageAndExit(0);
    } else {
      console.error(`unknown argument: ${arg}`);
      printUsageAndExit(2);
    }
  }
  return { source: resolve(SKILL_DIR, source) };
}

function printUsageAndExit(code) {
  const usage = [
    "usage: node scripts/sync.mjs [--source <path>]",
    "",
    "  --source <path>   path to a local clone of FTI00575-design-system",
    "                    (default: ../FTI00575-design-system relative to the skill)",
  ].join("\n");
  console.log(usage);
  process.exit(code);
}

async function fileExists(p) {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

async function validateSource(source) {
  const required = [
    join(source, "AGENTS.md"),
    join(source, "tokens", "tokens.json"),
  ];
  const missing = [];
  for (const p of required) {
    if (!(await fileExists(p))) missing.push(p);
  }
  if (missing.length > 0) {
    console.error(
      `error: source at ${source} is missing required files:\n  - ${missing.join("\n  - ")}\n` +
        `hint: pass --source <path> pointing to a clone of FTI00575-design-system`,
    );
    process.exit(1);
  }
}

async function sha256OfFile(path) {
  const buf = await readFile(path);
  return createHash("sha256").update(buf).digest("hex");
}

function gitSha(source) {
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], {
      cwd: source,
      encoding: "utf8",
    }).trim();
  } catch (err) {
    console.error(`error: 'git rev-parse HEAD' failed in ${source}: ${err.message}`);
    process.exit(1);
  }
}

async function readPackageVersion(source) {
  const pkgPath = join(source, "packages", "ui", "package.json");
  if (!(await fileExists(pkgPath))) {
    console.error(`error: missing ${pkgPath}`);
    process.exit(1);
  }
  const pkg = JSON.parse(await readFile(pkgPath, "utf8"));
  if (!pkg.version) {
    console.error(`error: 'version' missing in ${pkgPath}`);
    process.exit(1);
  }
  return pkg.version;
}

async function copyRequiredFiles(source) {
  await mkdir(SEMANTIC_DIR, { recursive: true });
  for (const name of TOP_LEVEL_FILES) {
    await copyFile(join(source, name), join(REFERENCES_DIR, name));
  }
  for (const name of SEMANTIC_FILES) {
    await copyFile(
      join(source, "semantic-design", name),
      join(SEMANTIC_DIR, name),
    );
  }
}

async function writeDsVersion(commit, version, today) {
  const body =
    `# YAML: pins this skill's references/ snapshot to an exact upstream version. Regenerate with scripts/sync.mjs.\n` +
    `commit: ${commit}\n` +
    `package-version: ${version}\n` +
    `sync-date: ${today}\n`;
  await writeFile(DS_VERSION_FILE, body, "utf8");
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

async function main() {
  const { source } = parseArgs(process.argv.slice(2));
  await validateSource(source);

  const sourceAgentsPath = join(source, "AGENTS.md");
  const localAgentsPath = join(REFERENCES_DIR, "AGENTS.md");
  const sourceAgentsHash = await sha256OfFile(sourceAgentsPath);
  const previousAgentsHash = (await fileExists(localAgentsPath))
    ? await sha256OfFile(localAgentsPath)
    : null;

  await copyRequiredFiles(source);

  const commit = gitSha(source);
  const version = await readPackageVersion(source);
  await writeDsVersion(commit, version, todayIso());

  console.log(`synced references/ from ${source}`);
  console.log(`  commit: ${commit}`);
  console.log(`  package-version: ${version}`);
  console.log(`  sync-date: ${todayIso()}`);

  if (previousAgentsHash !== null && previousAgentsHash !== sourceAgentsHash) {
    console.warn(
      "\nWARNING: upstream AGENTS.md changed since the previous sync.\n" +
        "The 20 non-negotiable rules embedded in SKILL.md were copied from AGENTS.md.\n" +
        "Re-review the 'Rules' section of SKILL.md against references/AGENTS.md and\n" +
        "update by hand if any rule wording, addition, or removal applies.\n" +
        "(This script never rewrites SKILL.md automatically.)",
    );
  }
}

await main();
