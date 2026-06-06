# Maintainer Runbook

For **maintainers and admins** who operate the catalog: promoting a component to
`default`, deprecating or yanking a version, running the release/versioning
pipeline, managing permissions and CODEOWNERS, and reading `scan_status`. Every
gated action below names **who is authorized**.

Authoring a component is the [Authoring Guide](./authoring-guide.md); the
primitives overview is the [Hub Guide](./hub-guide.md).

---

## Roles and authority

Contribution authority lives on **GitHub** (permissions + branch protection +
CODEOWNERS), enforced through `gh`. The portal's OIDC roles (`anonymous`,
`consumer`, `author`, `reviewer`, `publisher`, `admin`) govern the **web UI
only** and are kept coherent with GitHub by **aligned naming**, not identity
federation. The roles map to the three gates:

| Role | GitHub mechanism | Authorized to |
|---|---|---|
| **author** | Write (or a fork) | Open a contribution PR (`fdh <kind> share` or manual). Cannot self-merge. |
| **reviewer** | CODEOWNERS review | Approve a contribution PR (**gate 1**). Must not be the author. |
| **publisher** | Maintain/Admin, restricted on the release PR | Merge the release PR to publish a version (**gate 2**); deprecate/yank a version. |
| **admin** | Admin on `hub/` | Set `default` / harness membership (**gate 3**); manage CODEOWNERS and branch protection. |

The design deliberately **does not rely on one person holding every role**.
Branch protection forbids self-merge and restricts the release-PR merge to the
publisher team; admin bypass is an audited break-glass action, not a normal step.

---

## Mark a component `default` (gate 3 — adoption)

**Who:** an **admin** (Admin on `hub/`).

A merged, published component is **opt-in** until an admin adopts it. There are
two adoption levers — use either or both:

1. **Pre-select it in `fdh init`.** Edit its entry in
   [`hub/registry.yaml`](../hub/registry.yaml):

   ```yaml
   - name: card-grid
     kind: skill
     # …
     default: true        # was false
   ```

   The `default` flag in the **registry is authoritative** — any `default` in the
   component's own frontmatter is ignored. Changing it is a one-line commit; the
   next `fdh init` (wizard or non-interactive) pre-selects/includes the component.

2. **Add it to a harness.** Reference it by name under the right kind in
   [`hub/harnesses.yaml`](../hub/harnesses.yaml) (e.g. add `card-grid` to
   `frontend-team.skills`). Projects on that harness pick it up on the next
   `fdh install`/`update`.

The `default` harness's membership *is* the catalog's `default: true` set, so
flipping `default: true` effectively grows the `default` harness too.

> **Orthogonality.** `default` (adoption) is independent of `version`
> (evolution). Bumping a component's version never changes its `default`; mass
> adoption always remains an explicit admin decision. Both changes go through the
> normal permissioned PR + gates — there is no out-of-band edit to `main`.

To **un-adopt**, set `default: false` again and/or remove it from the
harness(es). Existing installs keep the component until those projects re-resolve
and drop it.

---

## Retire a component: deprecate or yank (lifecycle)

**Who:** a **publisher** (or admin), through the **same permissioned PR + gates**
as any registry change. Capability: `component-lifecycle`.

A published version has a lifecycle state recorded in the catalog and surfaced on
each `versions[]` entry of the component manifest as
`status: active | deprecated | yanked`. The progression is **forward-only**:

```
active ──▶ deprecated ──▶ yanked          (never backwards)
```

### Deprecate — "discouraged, still works"

Use when a version is superseded but you don't want to break anyone.

- Mark the version `status: deprecated` via the gated flow.
- It **remains downloadable and installable**. `fdh` emits a **warning** naming
  the version (and a changelog/replacement pointer when available).
- Constraint resolution **may still pick** a deprecated version if it's the
  highest satisfying a constraint and no active version does — but it warns.

### Yank — "do not use; pulled"

Use when a version is broken or unsafe and must not be installed.

- Mark the version `status: yanked` via the gated flow.
- It is **excluded from constraint resolution** and **not installed by default**.
- Its bundle endpoint responds **`410 Gone`**.
- A consumer whose lock pins a now-yanked version gets a **`fdh doctor`
  warning**.
- An explicit `--allow-yanked` escape hatch can still install a specific yanked
  version (forensics/reproduction), with a prominent warning.

### Rules that bite

- **Forward-only and immutable.** A yanked version **cannot be returned to
  `active`**. Shipping a fix means **publishing a new version string** — published
  content is immutable; you never republish different bytes under the same
  version.
- **Audited.** Every transition records **who** and **when**, consistent with the
  contribution gates.

---

## Release / versioning pipeline

**Who:** the release pipeline runs automatically on merges to `main`; **only a
publisher** merges the resulting release PR (**gate 2**). Capability:
`component-versioning-and-release`.

### Model

- Every component carries a **per-component SemVer `version`** in its entry-file
  frontmatter, starting at `0.1.0`. Versions are **independent** — bumping one
  component never bumps another.
- The affected component is determined by the **conventional-commit scope**:
  `feat(<name>): …`. CI (`commitlint`) **fails** a `feat`/`fix` commit that
  touches a component directory with a scope that doesn't match a real component.
  Housekeeping types (`chore`, `ci`, `build`, `docs`, `test`) and commits
  touching only non-component paths are exempt and trigger no bump.
- **0.x bump semantics:** `fix` → patch, `feat` → minor, and `feat!` /
  `BREAKING CHANGE` → **minor** (not major) while in `0.x`. Promotion to `1.0.0`
  is a **deliberate manual** action, never an automatic consequence of a breaking
  commit.

### Flow

1. Contributions merge to `main` with scoped conventional commits (gate 1
   already satisfied: green CI + non-author CODEOWNERS approval).
2. The release pipeline opens a **release PR** that, per affected component,
   writes the new `version` back into its entry-file frontmatter, appends to its
   changelog, and updates `latest_version` in the catalog.
3. A **publisher merges the release PR**. That merge creates the per-component
   tag **`<kind>/<name>@<semver>`** (e.g. `skills/design-system@0.5.0`) and
   publishes the signed bundle.

### Initial vs. subsequent releases

- A component with **no prior tag** is published at the version declared in its
  frontmatter (`0.1.0` for a new component) — the pipeline does **not** apply a
  conventional-commit bump to a first release.
- A component that **already has a tag** is bumped from its last tag per the 0.x
  semantics above.

### Producer and `hub_version`

The reference producer derives each component's `versions[]` and each version's
`published_at` from the **per-component tags**, not from a catalog-wide number.
`hub_version` in `hub/registry.yaml` is an **informational marker only** and is
not the source of any component's version.

### On-disk layout: source vs published artifacts

Each kind directory holds **two** different kinds of subdirectory — don't
confuse them (this is why you see more folders on disk than the catalog lists):

- **Source** (what you author/edit): `<kind>/<name>/` with the entrypoint file,
  e.g. `skills/design-system/SKILL.md`. **Only these are catalog components** —
  the catalog and the portal list exactly the source dirs declared in
  `hub/registry.yaml` (12 today).
- **Published artifacts** (build output — don't hand-edit): the producer writes
  `<kind>/<owner_team>/<name>/manifest.json` + `versions/<v>/bundle.tar.gz`,
  namespaced by `owner_team` (e.g. `skills/appsec/devsecops/…`). The CLI's
  GitRegistry fetches manifests + bundles from these paths. They are **not**
  extra components — they are the *published form* of the same source
  components.

`tools/validate-registry.py` distinguishes the two: a directory is an "orphan"
only if it looks like a source component (has the entrypoint file) yet is
missing from `hub/registry.yaml`; published-artifact namespace dirs are ignored.

---

## Permissions and CODEOWNERS

**Who:** an **admin** (Admin on the repo) manages CODEOWNERS and branch
protection. Capability: `hub-contribution-policy`.

### CODEOWNERS routing

[`.github/CODEOWNERS`](../.github/CODEOWNERS) routes each component directory to
the GitHub team mapped from its `owner_team`, so review requests resolve to a
**team**, not one person.

- **Target state:** one line per component (or per namespace),
  `skills/<namespace>/* → @askenaz-dev/<team>`, plus an admin-owned block for
  `hub/`, `.github/`, and `tools/`.
- **Transitional state (today):** the org's GitHub teams aren't provisioned yet
  (the EMU CLI auth can't create them — an **org owner** must, via the GitHub web
  UI). Until then a **catch-all** (`* @askenaz`) is the owner so every PR still
  requires a CODEOWNERS review. An individual catch-all is permitted **only** as a
  transient owner for an unprovisioned namespace and **must be replaced** by the
  namespace team once it exists.

When you add a new component, add its CODEOWNERS line mapping its directory to its
`owner_team`'s team (uncomment the per-team block once the teams exist).

### Branch protection (gate 1 + gate 2 enforcement)

Strict protection on `main` is provided **as code** in
[`scripts/setup-branch-protection.sh`](../scripts/setup-branch-protection.sh); an
org/repo **admin** runs it once the CI workflows have run (so the required check
names exist). It enforces:

- Required status checks: **`validate-registry`** and **`commitlint`**.
- **≥ 1 CODEOWNERS approval from a non-author**; stale approvals dismissed.
- **No self-merge**; admin bypass disabled (break-glass is an audited, deliberate
  act).
- **Release-PR merge restricted to the publisher team.**

### Naming coherence

A namespace's GitHub team, its CODEOWNERS owner, and the Keycloak group that maps
to the portal `reviewer` role for that namespace **share a name** (e.g. `appsec`
for the security namespace). No Keycloak↔GitHub federation is required — the
shared name gives the operational benefit without it.

### Public vs. internal/closed deployment

- **Public hub** (`fdh.askenaz.dev`): anonymous `/v1/*` reads; org members with
  Write contribute via branch + PR; external contributors via **fork + PR**.
- **Internal/closed** (corporate self-host): compose **(a)** registry serving with
  `Bearer` / `Basic` / `mTLS` auth on `/v1/*` and **(b)** a restricted
  contribution policy (who may open/merge PRs). The consume side (the `/v1/*` wire
  protocol) stays portable to any static host; the `fdh`-based contribute side
  assumes a GitHub-like host.

---

## Interpreting `scan_status`

**Who:** informational for everyone; produced by the registry build, surfaced by
the portal. Capability: `portal-scan-status`.

The registry producer runs the security scanner (`fdh scan`) over each component
when building the catalog and records the verdict per component/version in the
manifest (memoized by content-hash, so unchanged components aren't re-scanned).
The portal serves that **real** value on every endpoint and the UI renders it as
a labelled badge:

| `scan_status` | Meaning | Portal badge |
|---|---|---|
| `pass` | Scanned, **no blocking** findings | green — "Scanned" |
| `warn` | Scanned, **non-blocking** findings | amber — "Warnings" |
| `fail` | Scanned, **blocking** findings | red — "Failed" |
| `none` | **Not scanned** / no result | neutral — "Unscanned" |

Rules that bite:

- **`fail` is informative in this capability — it does NOT block installation or
  publication.** Gating on scan results is a separate policy decision that lives
  in another capability; today a `fail` component still installs.
- **A scan that errors records `none` and does not abort the catalog build.** So
  `none` means "we have no verdict", not "clean" — the badge says "Unscanned"
  precisely to avoid the old optimistic placeholder that painted `none` green.
- **The verdict applies to the tip version.** Older, un-rescanned versions report
  `none`.
- The portal filter `?scan_status=<value>` filters against the **real** recorded
  value.

A maintainer reviewing the catalog should read `warn`/`fail` as a prompt to look
at the findings before broadening adoption — even though nothing is blocked
automatically.

---

## Quick reference — who does what

| Action | Authorized role | Where |
|---|---|---|
| Open a contribution PR | author | `fdh <kind> share` / fork + PR |
| Approve the contribution PR (gate 1) | reviewer (CODEOWNERS, non-author) | GitHub review |
| Merge the release PR → publish (gate 2) | publisher | release PR |
| Deprecate / yank a version | publisher (or admin) | gated registry PR |
| Set `default` / add to harness (gate 3) | admin | `hub/registry.yaml` / `hub/harnesses.yaml` |
| Edit CODEOWNERS / branch protection | admin | `.github/CODEOWNERS`, `scripts/setup-branch-protection.sh` |
| Break-glass bypass of protection | admin (audited) | GitHub, emergency only |

---

## See also

- [Authoring Guide](./authoring-guide.md) — how authors produce components.
- [Hub Guide](./hub-guide.md) — primitives and consumption.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — the three gates and permission model
  (canonical).
- Source specs (in `forge-specs`): `hub-contribution-policy`,
  `component-lifecycle`, `component-versioning-and-release`,
  `hub-registry-v2`, `portal-scan-status`.
