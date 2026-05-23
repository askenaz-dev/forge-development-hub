> **NOTA — BORRADOR (no es un change formal todavía).**
> Este archivo vive bajo `openspec/changes/_drafts/` para revisión humana antes de
> ejecutar `/opsx:propose`. Cuando se apruebe, el contenido se mueve al directorio
> oficial del change generado por `openspec new change "hub-v2-manifest-state-profiles"`.

## Why

El hub publica hoy una sola primitiva ("skill") y un solo archivo de catálogo (`skills/registry.yaml` v1, una entrada: `design-system`). El plan ya proyecta crecimiento: el `add-fdh-cli-distribution-and-interactive-init` archivado contempla un catálogo de skills, `fdh init` interactivo y `fdh update`, pero apoyado en un único marker `.skill-version` por directorio instalado y sin contrato declarativo en el repo del consumidor.

Mirando ECC (https://github.com/affaan-m/ECC) — el ecosistema cross-harness más maduro del espacio — quedan claras cinco brechas que se vuelven caras cuanto más grande sea el catálogo:

1. **No hay separación entre rules y skills.** El `skills/design-system/SKILL.md` mezcla 20 reglas siempre-encendidas con workflows on-demand. Cambiarlo después de tener 50 skills es refactor masivo; cambiarlo hoy con 1 skill es cosmético.
2. **No hay primitivas para agents ni hooks.** Falabella ya tiene patrones tribales ("cómo escribir un PR description", "qué chequear en una migration Postgres") que naturalmente serían agents distribuibles. Hoy se forzarían como "skills raros".
3. **No hay manifest committeado en el consumidor.** Reproducibilidad entre developers depende de correr `fdh init` con los mismos flags. Equivalente conceptual: no tener `package.json`.
4. **No hay lockfile.** Versionado del hub avanza, pero cada `fdh install` puede resolver distinto. Equivalente conceptual: no tener `package-lock.json`.
5. **No hay ledger per-máquina.** `fdh list-installed`, `fdh repair`, `fdh uninstall --dry-run` no son posibles sin un inventario global del usuario.

Adicionalmente, falta una capability concreta de seguridad: validar que un skill/agent/hook publicado al hub no fugue secretos, no inyecte comandos en hooks, y no abra MCPs riesgosos. Es prerequisito para que seguridad corporativa apruebe el rollout a 500 devs.

Este change introduce las primitivas, los contratos declarativos y la capability de scan **antes** de que el catálogo crezca, siguiendo el patrón establecido del ecosistema JavaScript (npm/yarn/pnpm: manifest + lock + cache global).

## What Changes

### Schema y catálogo del hub

- **BREAKING — bump `skills/registry.yaml` a `schema_version: 2`** con campo nuevo `kind: skill | rule | agent | hook` (default `skill` para compat). Migración automática vía `tools/migrate-registry-v1-v2.py`.
- **Reorganización del root del hub:** además de `skills/`, agregar `rules/`, `agents/`, `hooks/` como directorios paralelos. Cada uno alberga `<name>/` con su propio archivo principal (`RULE.md`, `AGENT.md`, `HOOK.md`).
- **Renombrar `skills/registry.yaml` a `hub/registry.yaml`** (o equivalente que refleje que ya no es sólo de skills). A confirmar en design — alternativa: mantener nombre y tratarlo como catálogo unificado.
- **Nuevo archivo `hub/profiles.yaml`** con bundles curados. Estructura:
  ```yaml
  profiles:
    falabella-frontend:
      description: "Starter pack para devs frontend"
      skills: [design-system, code-review]
      rules:  [no-console-log]
      agents: [pr-writer]
      hooks:  [pre-commit-typecheck]
  ```

### Contrato del consumidor — manifest + lock + state

- **`.fdh/manifest.yaml` en consumer repo** (committed, editado por humanos). Declara intención: qué profile usar, qué extender, qué excluir, scope (project vs user). Schema documentado.
- **`.fdh/lock.yaml` en consumer repo** (committed, escrito por `fdh install`). Snapshot reproducible: hub_commit, lista expandida de componentes con versiones e integrity hashes.
- **`~/.fdh/state.json` en HOME** (NO committed, escrito por todos los comandos `fdh`). Inventario per-máquina:
  - Mínimo v1: user_scope_installs + hub_cache metadata.
  - Estructura extensible para `projects: { <path>: { lock_hash, managed_paths, ... } }` a llenar bajo demanda.

### Gestión de paths managed vs user-owned

- **Marker `.fdh-managed.yaml`** dentro de cada directorio instalado por `fdh`. Contiene `name`, `kind`, `version`, `hub_commit`, `installed_at`, `installed_by_fdh`. Permite a `fdh doctor`/`repair` discernir lo managed de lo escrito a mano.
- **Gestión de `.gitignore` sectionada e idempotente:**
  ```
  # >>> fdh:managed-paths >>>
  .claude/skills/design-system/
  .codex/skills/design-system/
  # <<< fdh:managed-paths <<<
  ```
- **Bloque managed dentro de `.claude/settings.json`** para hooks: cada entry FDH lleva marker `_fdh_managed: <name>`. `fdh uninstall` los remueve sin tocar los del developer.

### Primeras entries reales de cada primitiva (camino hecho, modificables)

Cada una de las tres primitivas nuevas ship con **al menos una entry real y funcional** — no stubs ni placeholders. Son ejemplos minimalistas pero ejecutables, que sirven como referencia para futuras entries y son seguras de remover/modificar:

- **`rules/no-console-log/RULE.md`** — regla simple, alto valor: prohibe `console.log()` en código committed. Scope: `*.{ts,tsx,js,jsx}`. Real, materializable a `.claude/rules/no-console-log.md` (y target equivalentes en otros agentes), referenciable desde el profile `minimal`.
- **`agents/falabella-pr-writer/AGENT.md`** — agent simple: genera descripciones de PR en formato Falabella (template + tono). System prompt corto, herramientas mínimas (`Read`, `Grep`, `Bash`). Real, materializable a `.claude/agents/falabella-pr-writer.md`.
- **`hooks/doctor-on-session-start/HOOK.md` + `hook.json`** — hook simple, demuestra el flujo end-to-end: evento `SessionStart`, comando `fdh doctor --quiet`. Real, materializable como bloque managed en `.claude/settings.json`. La ejecución del hook es responsabilidad del agente (Claude Code lo invoca al iniciar sesión); FDH sólo lo instala.

**Importante sobre runtime**: estos tres primitivos no requieren runtime FDH propio porque los agentes (Claude Code, Codex, etc.) ya tienen su mecanismo nativo para ejecutar/cargar rules, agents y hooks. FDH escribe los archivos en los paths que cada agente espera; el agente hace el resto. Esto es coherente con cómo funciona ya el primitivo `skill`.

### Nueva capability: `fdh-scan`

- Comando `fdh scan` que audita componentes (skills/rules/agents/hooks) antes de publicar al hub o instalar en una máquina:
  - Detección de secrets (patterns comunes: API keys, AWS, GitHub tokens, JWTs).
  - Validación de hooks contra inyección de comandos.
  - Perfilado de riesgo de MCPs declarados.
  - Auditoría de permisos en agent configs.
- Implementación inicial: rule-based deterministic. Pipeline adversarial multi-agente (estilo AgentShield de ECC) queda como evolución futura.

### Validación y CI

- `tools/validate-registry.py` extendido para schema v2 (validar `kind`, validar profiles, validar consistencia entre `registry.yaml` y los directorios `skills/`/`rules/`/`agents/`/`hooks/`).
- Nuevo `tools/validate-manifest.py` (también future-Go `fdh validate-manifest`) que valida `.fdh/manifest.yaml` contra el catálogo del hub.
- CI del hub corre `fdh scan` (cuando esté implementado) sobre cada PR que toque `skills/`/`rules/`/`agents/`/`hooks/`.

## Capabilities

### New Capabilities

- `hub-registry-v2`: schema v2 del catálogo unificado, con `kind` y los cuatro tipos de primitivas. Reglas de migración desde v1.
- `hub-profiles`: bundles curados en `hub/profiles.yaml`, semántica de referencia desde el manifest y extension/override en el consumer.
- `consumer-manifest-and-lock`: schemas y semántica de `.fdh/manifest.yaml` y `.fdh/lock.yaml`. Relación entre intención (manifest) y resolución (lock). Reglas de regeneración.
- `installation-state-ledger`: schema y semántica de `~/.fdh/state.json`. Comandos `fdh list-installed`, `fdh repair`, `fdh uninstall --dry-run`. Distinción minimal v1 vs full.
- `consumer-managed-paths`: contrato de `.fdh-managed.yaml`, gestión de `.gitignore` sectionada, bloque managed en `.claude/settings.json` para hooks. Detección de drift.
- `hub-rules-primitive`: contrato de rules como primitiva separada de skills. Formato, scope por glob, materialización per-agente. **Ship con 1 entry real funcional** (`rules/no-console-log/`).
- `hub-agents-primitive`: contrato de agents como primitiva. Formato, target dirs per-agente. **Ship con 1 entry real funcional** (`agents/falabella-pr-writer/`).
- `hub-hooks-primitive`: contrato de hooks como primitiva. Formato, matchers, profiles. **Ship con 1 entry real funcional** (`hooks/doctor-on-session-start/`).
- `fdh-scan-security`: comando `fdh scan` con detección rule-based de secrets, command injection en hooks, riesgo de MCPs, permisos de agents.

### Modified Capabilities

- `hub-skills-registry`: el catálogo deja de ser exclusivo de skills. Si se mantiene el nombre `registry.yaml`, ahora indexa las cuatro primitivas via `kind`. Si se renombra a `hub/registry.yaml`, queda redirect/symlink durante una ventana de migración.
- `fdh-init-interactive`: el wizard ahora persiste sus decisiones en `.fdh/manifest.yaml` (intención) y dispara `fdh install` que escribe `.fdh/lock.yaml` y actualiza `~/.fdh/state.json`. Pre-rellena el wizard leyendo el manifest existente si re-corrés `init`.
- `fdh-skills-sync`: `fdh update` ahora compara contra `lock.yaml` como fuente de verdad, no contra `.skill-version` distribuido. El marker se rebautiza a `.fdh-managed.yaml` y se vuelve cache local + self-describing, no source of truth.

## Impact

### Schema migration

- `skills/registry.yaml` v1 (actual, 1 entrada) → schema v2. Migración tooled, idempotente. CI valida que no haya archivos v1 al merge.
- Posible rename del archivo (`skills/registry.yaml` → `hub/registry.yaml`). Decisión a finalizar en design.md. Si se renombra, redirect/symlink durante 60 días.

### Estructura del hub

- **Nuevos directorios root con su primera entry real:**
  - `rules/no-console-log/` (RULE.md + frontmatter completo)
  - `agents/falabella-pr-writer/` (AGENT.md + frontmatter + system prompt + template)
  - `hooks/doctor-on-session-start/` (HOOK.md + hook.json)
- `hub/profiles.yaml` nuevo. Mínimo: 1 profile `minimal` que ejercita las 4 primitivas (incluye `design-system` skill + `no-console-log` rule + `falabella-pr-writer` agent + `doctor-on-session-start` hook). Sirve como ejemplo end-to-end de cómo se compone un profile.
- `skills/design-system/` queda igual; sólo gana `kind: skill` en su entrada del registry.

### Consumer repos

- Repos que ya tienen skills instalados (los 30 del pilot) **no se rompen**: el próximo `fdh install` detecta ausencia de `.fdh/manifest.yaml` y lo genera a partir del estado real (introspection del `.fdh-managed.yaml` o `.skill-version` legacy). El developer revisa y commitea.
- `.gitignore` se modifica automáticamente la primera vez. Si el dev ya tenía `.gitignore` con sus propias entries, FDH agrega su sección sin tocar las del dev.
- `.claude/settings.json` se modifica in-place añadiendo marker `_fdh_managed` a los hooks que FDH inyecte (none en este change, todo es stub).

### Repo `fdh` (hermano, Go)

- Implementación de manifest/lock parsing, state.json management, gestión de `.gitignore`, `fdh scan` rule-based. ~2-4 sprints estimado (no en scope de este change del hub).
- Tracking: change separado dentro del repo `fdh` (si adopta OpenSpec) o release plan tradicional.

### Scope explícitamente NO incluido (tracking separado)

- **Wrapping `fdh` en paquete npm**: lo cubre el change paralelo `fdh-cli-npm-distribution`. Independiente de hub-v2.
- **Instincts / continuous learning** (concepto ECC `continuous-learning-v2`): lo cubre el change paralelo `add-instinct-collaboration` (drafteado junto a este, queda listo para `/opsx:propose` apenas hub-v2 termine apply). Razón de separación: requiere su propia storage layer (`~/.fdh/instincts/`) y comandos propios; meterlo aquí infla el alcance.
- **`fdh scan` con pipeline adversarial multi-agente**: v1 en este change es rule-based deterministic. La evolución a 3-agent red-team/defender/auditor queda como change futuro `evolve-scan-to-adversarial`.

### Sets up future changes

- `add-more-rules`: catálogo de rules adicionales (`prefer-named-exports`, `use-ds-button`, `no-fmt-print` para Go, etc.). El camino ya está hecho con `no-console-log` como referencia.
- `add-more-agents`: agents adicionales (`falabella-security-auditor`, `falabella-postgres-dba`, `falabella-i18n-reviewer`). Mismo patrón.
- `add-more-hooks`: hooks adicionales con eventos PreToolUse/PostToolUse/Stop. La pieza de SessionStart ya está demostrada.
- `evolve-scan-to-adversarial`: `fdh scan` pasa de rule-based a pipeline 3-agente.
- `add-instinct-sync-service`: backend de sincronización de instincts entre devs (parte 2 de `add-instinct-collaboration`).

### Open questions (a resolver en design.md, no bloquean este proposal)

- ¿Renombrar `skills/registry.yaml` a `hub/registry.yaml` o mantener nombre y cambiar contenido?
- ¿`state.json` mínimo v1 (sólo user_scope + cache) o full v1 (incluye `projects:`)?
- ¿`hub/profiles.yaml` archivo separado o sección dentro del registry?
- ¿`fdh install --frozen` (no actualiza lock, falla si manifest cambió) como en `npm ci`?
- ¿Cómo se sincroniza `~/.fdh/state.json` cuando dos máquinas comparten HOME (NFS, dev containers)?
