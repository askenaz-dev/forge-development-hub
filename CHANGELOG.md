# Changelog

## Unreleased

### **BREAKING**

- Removed `skills/registry.yaml` (the legacy mirror) and `tools/regenerate-skills-registry-mirror.py` (the regenerator). The mirror was scheduled for removal ~2026-07-22 as documented in the original `hub-v2-manifest-state-profiles` apply; this change brings the deletion forward. Schema of `hub/registry.yaml` is identical to what the mirror exposed, so the migration is simply: **repoint any tool reading `skills/registry.yaml` to `hub/registry.yaml`**.

  Notes for downstream consumers:
  - The `fdh` CLI's hub-catalog reader was updated in `upgrade-hubregistry-to-v2` to prefer `hub/registry.yaml` with a v1-mirror fallback. After this deletion, the fallback path is dead code in any released `fdh` binary; impact is a clear `file not found` error if a stale CLI tries the legacy path on a freshly-pulled hub.
  - The `mirror-sync-check` job is gone from `.github/workflows/validate-registry.yml`; pull requests no longer fail on stale-mirror conditions.
