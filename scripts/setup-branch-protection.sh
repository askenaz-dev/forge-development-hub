#!/usr/bin/env bash
# Strict branch protection for the hub's default branch
# (capability hub-contribution-policy, gate 1 + gate 2 enforcement).
#
# Run ONCE by an org/repo admin, AFTER the CI workflows have run at least once
# (so GitHub recognizes the required check names). Idempotent: re-running
# re-applies the same protection.
#
#   ./scripts/setup-branch-protection.sh [owner/repo] [branch]
#
# Defaults: askenaz-dev/forge-development-hub, main.
#
# Notes:
#   - enforce_admins=true disables admin bypass in normal operation; break-glass
#     means an admin deliberately + temporarily turns it off (an audited act).
#   - require_code_owner_reviews + 1 approval => the author cannot self-merge
#     (you cannot approve your own PR), satisfying the "non-author review" rule.
#   - "restrictions" (who may merge to main) is left null until the publisher
#     team is provisioned; set it to the publisher team to enforce gate 2
#     (publisher-only release merges) at the platform level.
set -euo pipefail

REPO="${1:-askenaz-dev/forge-development-hub}"
BRANCH="${2:-main}"

echo "Applying strict branch protection to ${REPO}@${BRANCH}…"

gh api -X PUT "repos/${REPO}/branches/${BRANCH}/protection" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["validate-registry", "commitlint"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

echo "Done. Verify in Settings → Branches, and add the publisher team to"
echo "'restrictions' once it is provisioned to enforce publisher-only release merges."
