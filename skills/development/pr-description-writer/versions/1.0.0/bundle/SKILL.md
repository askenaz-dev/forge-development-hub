---
name: pr-description-writer
description: Compose a clear pull-request description from a diff. Produces summary, rationale, test plan, and risks.
license: MIT
metadata:
  author: dx-platform
  sdlc_phase: development
---

# Pull-request description writer

Use the structure below for every non-trivial pull request:

## Summary
One sentence stating what changes for the user or downstream system.
Do not narrate code mechanics.

## Why
Two to four sentences on the underlying motivation. Reference issue
trackers by ID, not by URL.

## What changed
Bulleted list grouped by area (api, ui, infra, docs, tests). Each bullet
is one short clause. Highlight breaking changes with **BREAKING**.

## Test plan
A checkbox list. Each item is a concrete, repeatable verification step a
reviewer can run. Include negative cases where they matter.

## Risks and rollback
- Risks: what could go wrong and who will notice first.
- Rollback: the exact sequence to revert if it does.

## Out of scope
A short list of related work this PR deliberately does NOT do, with
references to the follow-up tickets.

Anti-patterns:
- "Refactor stuff" — too vague, rewrite.
- A test plan that says "ran the existing tests" — list the new
  observable behavior instead.
- Hidden behavior changes packaged inside "small refactor" PRs.
