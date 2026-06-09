# Privacy and Telemetry Policy

This document is the **canonical reference** for what the Forge Development Hub
(`fdh`) collects, what it deliberately does **not** collect, and how you stay in
control. It covers the optional usage telemetry emitted by the `fdh` CLI and the
events the portal records.

If you operate `fdh`, read [Opt in / opt out](#opt-in--opt-out) and
[Right to be forgotten](#right-to-be-forgotten-salt-rotation). If you are
evaluating whether telemetry is safe to enable, the short version is:

- **Telemetry is OFF by default.** Nothing is sent unless you explicitly opt in.
- **It is pseudonymous.** No username, email, hostname, IP, repository path, or
  file content ever leaves your machine.
- **It is forgettable.** A single command rotates your identifier to a fresh,
  uncorrelatable one.
- **It never bridges to your identity.** The telemetry stream is a *parallel
  surface*; it is never joined to your portal login or your GitHub account.

---

## What this is for

The platform wants honest usage signal — what gets installed, downloaded, and
resolved, whether onboarding converts, and which components are healthy and
adopted — plus a feedback channel. That signal is genuinely *data*, not *code*,
so it may live in a store. The hard constraint is doing it **privacy-first**: the
platform is developer-facing, and trust is the product.

Telemetry never changes the catalog. It never writes `hub/registry.yaml`,
`hub/harnesses.yaml`, or any component. "Code is the source of truth" stays
intact — the catalog changes only through the GitHub-PR flow.

---

## What is collected

When — and **only** when — you have opted in, the `fdh` CLI emits a structured
event for each `install`, `download`, and `resolve` operation. Each event
contains exactly these fields, and nothing else:

| Field          | Example                                  | Notes |
|----------------|------------------------------------------|-------|
| `event`        | `install`                                | One of `install`, `download`, `resolve`, `activation`, `feedback`. |
| `kind`         | `skill`                                   | The component primitive: `skill`, `rule`, `agent`, or `hook`. |
| `namespace`    | `forge`                                   | The component namespace from the catalog. |
| `name`         | `design-system`                           | The component name from the catalog. |
| `version`      | `1.4.0`                                    | The resolved component version. |
| `content_hash` | `sha256:…`                                | Integrity hash of the materialized content. |
| `scope`        | `project`                                  | Install scope: `project` or `user`. |
| `registry`     | `hub`                                      | The registry the component came from. |
| `os`           | `darwin`                                   | **Coarse only** — one of `darwin`, `linux`, `windows`. No architecture, kernel, or OS-version detail. |
| `locale`       | `en`                                       | One of `es` or `en`. |
| `install_id`   | `9f1c…` (64-hex)                          | A **pseudonymous, rotating, salted hash** (see below). |
| `timestamp`    | `2026-06-08T14:32:05Z`                     | RFC 3339, UTC. |

These are exactly the fields the CLI already produces when it resolves and
installs a component (`kind` / `namespace` / `name` / `version` / `content_hash`
/ `scope` / `registry`), plus a coarse `os`, your `locale`, the pseudonymous
`install_id`, and a timestamp.

The ingest endpoint **strict-decodes** every event against this closed schema. An
event carrying any field not in the list above is rejected outright — it is never
stored. This is a structural guarantee that the field set cannot silently grow to
include something identifying.

### Activation events

The onboarding wizard records **activation** events as you move through it. These
carry the same minimal shape plus a `step` and an anonymous `wizard_session_id`
(a per-session token, not tied to your identity) and your `locale` / `os`. They
let the platform measure the onboarding funnel — how far people get — without
knowing who anyone is.

### Feedback events

When you submit feedback (`fdh feedback`, or the feedback form in the portal),
the event additionally carries a `rating`, a `category`, and the free-text
`text` you wrote. Feedback is submitted anonymously and is **content you chose to
write** — please do not include personal information in the free-text field.

---

## What is NOT collected

There is no field, anywhere in the schema, for any of the following. They are not
collected, not transmitted, and not stored:

- **No username** and **no email address**.
- **No hostname** or machine name.
- **No IP-derived identity** — the ingest endpoint records no IP-based fingerprint.
- **No repository path, working-directory path, or any filesystem path.**
- **No file contents** of any kind.
- **No account, login, or OIDC subject** — telemetry carries no portal or GitHub
  identity.
- **No fine-grained device detail** — `os` is coarse (`darwin` / `linux` /
  `windows`) with no architecture, kernel, or version.
- **No third-party analytics SDK or tracker.** Events are first-party only, sent
  to a first-party store. Nothing is shared with an external analytics vendor.

If you ever see a field that is not in the [What is collected](#what-is-collected)
table being sent, that is a bug — please report it.

---

## Opt in / opt out

**Default state is OFF.** With no configuration and no consent answer on record,
`fdh` emits no events, makes no telemetry network call, and sends no
`install_id`.

You can turn telemetry **on** in any of these ways:

- Answer **yes** to the one-time first-run consent prompt (interactive sessions
  only — see below).
- Set the config key: `fdh config set telemetry.enabled true` (persisted to
  `<config-dir>/fdh/config.yaml`).
- Set the environment override for a single invocation:
  `FDH_TELEMETRY=1 fdh install …` (does not modify your config).

You can turn telemetry **off** in any of these ways:

- `fdh telemetry disable` — durable; subsequent commands emit nothing until you
  explicitly re-enable.
- Set `telemetry.enabled: false` in config.
- Set `DO_NOT_TRACK=1` (or any non-empty `DO_NOT_TRACK`) in the environment.

### `DO_NOT_TRACK` is absolute

`DO_NOT_TRACK` is honored as an **absolute opt-out** that overrides every opt-in
signal. The precedence the CLI applies is:

```
DO_NOT_TRACK  >  FDH_TELEMETRY  >  telemetry.enabled (config)  >  consent answer  >  default OFF
```

So a machine with `telemetry.enabled: true` in config will still emit **nothing**
for any command run with `DO_NOT_TRACK=1` in the environment.

### The first-run consent prompt

On the first command that *would* emit telemetry, an **interactive** CLI shows a
one-time consent prompt. It summarizes what is and is not collected, **defaults to
declining**, and links back to this policy. Your answer is persisted so the prompt
never recurs.

In a **non-interactive** context — no TTY, or CI — the CLI never prompts. Absence
of an explicit opt-in is treated as **declined**, and telemetry stays off.

### Emission never blocks your command

When telemetry is enabled, emission is **batched, asynchronous, time-boxed, and
best-effort**. The success, exit status, output, and latency of any `fdh` command
never depend on whether telemetry was sent or whether the ingest endpoint was
reachable. Network or store errors are swallowed silently. If the endpoint is
down, your command still succeeds with its normal exit code.

---

## Pseudonymity: the `install_id`

Telemetry is **pseudonymous**, not anonymous: events from the same machine carry
a stable `install_id` so the platform can count distinct installs without knowing
who you are.

The `install_id` is a **salted hash**. The salt is generated locally and stored
under your `fdh` config directory (`<config-dir>/fdh`). The identifier:

- is **not derived from**, and **not reversible to**, any stable hardware id,
  account, or identity value;
- is a 64-hex string that reveals nothing about you or your machine;
- changes completely whenever the salt is rotated (see below).

Because the only inputs are a locally-held random salt and a non-identifying base,
nobody — including the platform — can reverse an `install_id` back to a person, a
machine, or an account.

---

## Right to be forgotten: salt rotation

Your **right to be forgotten** is implemented as **salt rotation**. Rotating the
salt produces a brand-new `install_id` that is **not correlatable** to the prior
one. After rotation, future events are pseudonymous under a fresh identifier, and
the old identifier can no longer be associated with your machine.

- **On demand:** run `fdh telemetry rotate` at any time. The next event carries a
  new `install_id`, and nothing stored locally or transmitted links the new id to
  the old one.
- **Automatically:** the salt **auto-rotates every 90 days** by default, to bound
  how long any single identifier can be linked across time.

There is no need to contact anyone to be forgotten — rotation is entirely
local and immediate.

---

## Retention

- **Raw events** are retained for a bounded window — **180 days** by default —
  after which they are pruned by an in-process retention job.
- **Aggregates** (rollups such as top components, install trends, and the
  onboarding funnel) are **long-lived**. They are derived from pseudonymous data
  and contain no per-user-identity row.

The retention job deletes raw rows past the window while their already-computed
contribution to the aggregates remains. The UI is driven by aggregates, not raw
rows.

---

## No identity federation

This is a guarantee, not a default you can lose:

- The telemetry subsystem **never establishes a mapping** from an `install_id` to
  a portal OIDC subject or a GitHub account. The pseudonymous stream and your
  login are **parallel surfaces** that are never joined.
- Admin analytics return **aggregates only** — never a row that maps an
  `install_id` to an identity, and never a raw `install_id` tied to a person.
- The **one** exception is fully under your control: if you *voluntarily claim* a
  machine's install activity into your profile, those installs appear in your own
  activity feed. Absent that explicit, user-initiated claim, install activity is
  never attributed to you, and the system never reverses an unclaimed
  `install_id` to your identity.

In short: enabling telemetry does **not** connect your usage to your identity. The
only thing that ever does is an action you take yourself, on your own profile.

---

## Where to find this

This document is the canonical privacy and telemetry policy referenced by:

- the **CLI first-run consent prompt**, which links here before you decide; and
- the **portal**, which points users here for the full policy.

Cross-link target: `docs/privacy.md` in the `forge-development-hub` repository —
<https://github.com/askenaz-dev/forge-development-hub/blob/main/docs/privacy.md>.

Related reading: the [Hub Guide](./hub-guide.md) for what the platform is, and the
[`fdh` CLI](https://github.com/askenaz-dev/forge-development-hub-cli) for the
commands referenced above (`fdh telemetry status|enable|disable|rotate`,
`fdh feedback`).
