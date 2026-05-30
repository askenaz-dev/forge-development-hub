#!/usr/bin/env python3
"""Path-aware Conventional-Commit scope check
(capability component-versioning-and-release, decision D15).

Complements commitlint (which validates message shape + scope-enum). This check
is DIFF-aware: for every `feat`/`fix` commit in a PR range that touches a
component directory under skills/ rules/ agents/ hooks/, it requires the commit
scope to match that component's name. Housekeeping types (chore, ci, build,
docs, test, style, refactor, perf) and commits touching only non-component paths
are exempt and trigger no bump.

Usage:
    python tools/check-commit-scopes.py --base <sha> --head <sha>
    python tools/check-commit-scopes.py            # defaults to origin/main..HEAD

Exit codes: 0 ok, 1 violations, 2 usage/git error.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

KIND_DIRS = {"skills", "rules", "agents", "hooks"}
BUMPING_TYPES = {"feat", "fix"}
HEADER_RE = re.compile(r"^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<bang>!)?:\s")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def commit_list(base: str, head: str) -> list[str]:
    out = git("rev-list", f"{base}..{head}")
    return [c for c in out.splitlines() if c]


def commit_subject(sha: str) -> str:
    return git("show", "-s", "--format=%s", sha)


def commit_files(sha: str) -> list[str]:
    out = git("show", "--name-only", "--format=", sha)
    return [f for f in out.splitlines() if f]


def components_touched(files: list[str]) -> set[str]:
    comps: set[str] = set()
    for f in files:
        parts = Path(f).parts
        if len(parts) >= 2 and parts[0] in KIND_DIRS:
            comps.add(parts[1])
    return comps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()

    try:
        commits = commit_list(args.base, args.head)
    except subprocess.CalledProcessError as exc:
        print(f"git error: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    for sha in commits:
        subject = commit_subject(sha)
        m = HEADER_RE.match(subject)
        if not m:
            continue  # non-conventional shape is commitlint's job, not ours
        ctype = m.group("type")
        scope = m.group("scope")
        if ctype not in BUMPING_TYPES:
            continue  # housekeeping types are exempt
        comps = components_touched(commit_files(sha))
        if not comps:
            continue  # touches no component dir → exempt
        short = sha[:8]
        if len(comps) > 1:
            errors.append(
                f"{short} {subject!r}: {ctype} commit touches multiple components "
                f"{sorted(comps)}; split into one scoped commit per component"
            )
            continue
        comp = next(iter(comps))
        if scope != comp:
            errors.append(
                f"{short} {subject!r}: {ctype} touches component '{comp}' but scope is "
                f"{scope!r}; expected 'feat({comp}): …' / 'fix({comp}): …'"
            )

    if errors:
        print("commit-scope check failed:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print(f"commit-scope check: {len(commits)} commit(s) ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
