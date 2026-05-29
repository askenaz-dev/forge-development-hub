---
name: checklist
description: Standardized code review checklist used by every forge reviewer.
license: MIT
metadata:
  author: dx-platform
  sdlc_phase: code-review
---

# Code-review checklist

Walk the diff once for each concern below. If a concern doesn't apply,
say so explicitly in the review comment rather than skipping silently.

## Correctness
- Inputs are validated at the boundary (request handler, public API).
- Error returns are checked at every call site.
- Concurrent access is either obviously single-writer or guarded.
- Off-by-one and edge cases (empty input, max input, nil) covered.

## Readability
- Names express intent, not type.
- Functions are small enough to be understood without scrolling.
- Comments explain WHY, not WHAT. Delete a comment that paraphrases code.

## Testing
- New behavior has a test that fails without the change.
- Test names describe behavior, not implementation.
- No flakiness sources: time.Sleep, network without retry, randomness without seed.

## Convention adherence
- Logging format matches the project's logging convention.
- Public API additions follow the project's naming and versioning rules.
- Migration scripts are reversible or have a documented forward-only justification.

## Security
- Secrets are not introduced in source.
- User input is escaped at the point of rendering, not at storage.
- Authorization is enforced at every layer that needs it (don't trust the UI).

Approval bar:
- Approve only when the above are addressed AND CI is green.
- A single "looks good" without comments is rarely a useful review.
