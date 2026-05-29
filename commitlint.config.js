// commitlint config for the Forge hub (capability component-versioning-and-release).
//
// Enforces Conventional Commits at the MESSAGE level. The scope, when present,
// must be a real component (a directory name under skills/ rules/ agents/ hooks/)
// or one of a small set of infra scopes. The complementary, DIFF-aware rule
// ("a feat/fix touching a component dir MUST carry that component's scope") lives
// in tools/check-commit-scopes.py — commitlint cannot see the diff.
const fs = require("fs");
const path = require("path");

const KIND_DIRS = ["skills", "rules", "agents", "hooks"];
// Non-component areas that may legitimately scope a commit.
const INFRA_SCOPES = ["ci", "deps", "release", "hub", "tools", "docs", "tests"];

function componentScopes() {
  const scopes = [];
  for (const dir of KIND_DIRS) {
    const abs = path.join(__dirname, dir);
    if (!fs.existsSync(abs)) continue;
    for (const entry of fs.readdirSync(abs, { withFileTypes: true })) {
      // skip files like skills/registry.yaml and skills/README.md
      if (entry.isDirectory()) scopes.push(entry.name);
    }
  }
  return scopes;
}

module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    // Scope is optional (housekeeping commits may omit it), but if present it
    // must be a known component or infra scope.
    "scope-enum": [
      2,
      "always",
      [...new Set([...componentScopes(), ...INFRA_SCOPES])],
    ],
  },
};
