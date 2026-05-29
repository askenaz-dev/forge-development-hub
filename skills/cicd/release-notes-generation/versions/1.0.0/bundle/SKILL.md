---
name: release-notes-generation
description: Compose release notes from a list of merged PRs grouped by category.
license: MIT
metadata:
  author: platform-engineering
  sdlc_phase: cicd
---

# Release-notes generation

Given a list of merged PRs (titles, descriptions, labels), produce release
notes in this exact structure:

## Headline
One sentence summarizing the most user-impacting change.

## Highlights
Two to five bullets, each a single sentence describing a user-visible
improvement. No internal jargon, no PR numbers in this section.

## Changes by category
Group every PR under one of:
- Added
- Changed
- Fixed
- Removed
- Security
- Deprecated

For each entry: "<verb> <subject> (#<pr-number>, @<author>)". Order entries
within a category by user impact, not by merge time.

## Upgrade notes
Steps a user must take to move to this release. If none, write
"No action required." explicitly. Call out any breaking changes here even
if they appear under "Changed" above.

## Known issues
A short list of open issues users should be aware of, each with a link.

Quality bar:
- Marketing tone is OK in Highlights, technical tone elsewhere.
- A user reading ONLY Headline + Upgrade notes can decide whether to upgrade.
- Every PR in the input list appears under exactly one category.
