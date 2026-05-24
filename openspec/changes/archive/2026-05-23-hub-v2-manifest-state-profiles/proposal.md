*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Why

El hub publica hoy una sola primitiva (`skill`) y un único archivo de catálogo (`skills/registry.yaml` v1, una entrada: `design-system`). El plan ya proyecta crecimiento: `add-fdh-cli-distribution-and-interactive-init` (archivado) contempla catálogo de skills, `fdh init` interactivo y `fdh update`, pero apoyado en un único marker `.skill-version` por directorio instalado y sin contrato declarativo en el repo del consumidor.

Mirando ECC (https://github.com/affaan-m/ECC), el ecosistema cross-harness más maduro del espacio, quedan claras cinco brechas que se vuelven caras cuanto más grande sea el catálogo: (1) no hay separación entre `rule` siempre-encendido y `skill` on-demand; (2) no hay primitivas para `agent` ni `hook`; (3) no hay manifest committeado en el consumidor (equivalente a no tener `package.json`); (4) no hay lockfile (equivalente a no tener `package-lock.json`); (5) no hay ledger per-máquina, lo que impide `fdh list-installed`, `fdh repair`, `fdh uninstall --dry-run`. Adicionalmente falta una capability concreta de seguridad para validar componentes antes de publicarlos al hub.

Este change introduce las primitivas, los contratos declarativos y la capability de scan **antes** de que el catálogo crezca, siguiendo el patrón establecido del ecosistema JavaScript (npm/yarn/pnpm: manifest + lock + cache global).

## What Changes

### Schema y catálogo del hub

- **BREAKING — bump del catálogo a `schema_version: 2`** con campo nuevo `kind: skill | rule | agent | hook` (default `skill` para compat). Migración tooled e idempotente.
- **Reorganización del root del hub:** además de `skills/`, agregar `rules/`, `agents/`, `hooks/` como directorios paralelos. Cada uno alberga `<name>/` con su archivo principal (`RULE.md`, `AGENT.md`, `HOOK.md`).
- **Decisión de ubicación del catálogo** (`skills/registry.yaml` actual vs `hub/registry.yaml` nuevo) se resuelve en `design.md`.
- **Nuevo `hub/profiles.yaml`** con bundles curados que referencian componentes de las cuatro primitivas. Ship con al menos un profile `minimal` ejercitando las cuatro.

### Contrato del consumidor — manifest + lock + state

- **`.fdh/manifest.yaml`** en consumer repo (committed, editado por humanos): declara intención — qué profile usar, qué extender, qué excluir, scope.
- **`.fdh/lock.yaml`** en consumer repo (committed, escrito por `fdh install`): snapshot reproducible con `hub_commit`, lista expandida de componentes con versiones e integrity hashes.
- **`~/.fdh/state.json`** en HOME (NO committed, escrito por todos los comandos `fdh`): inventario per-máquina. Diseño minimal-vs-full resuelto en `design.md`.

### Gestión de paths managed vs user-owned

- **Marker `.fdh-managed.yaml`** dentro de cada directorio instalado por `fdh` con `name`, `kind`, `version`, `hub_commit`, `installed_at`, `installed_by_fdh`. Permite detección de drift.
- **`.gitignore` sectionado e idempotente** entre markers `# >>> fdh:managed-paths >>>` y `# <<< fdh:managed-paths <<<`. FDH sólo modifica su sección.
- **Bloque managed en `.claude/settings.json`** para hooks: cada entry FDH lleva marker `_fdh_managed: <name>` para `fdh uninstall` selectivo.

### Primeras entries reales de cada primitiva (camino hecho, modificables)

Cada primitiva nueva ship con una entry real funcional — no stubs:

- **`rules/no-console-log/RULE.md`** — prohibe `console.log()` en TypeScript/JavaScript committed. Scope `*.{ts,tsx,js,jsx}`.
- **`agents/forge-pr-writer/AGENT.md`** — genera descripciones de PR en formato Forge (template + tono).
- **`hooks/doctor-on-session-start/HOOK.md` + `hook.json`** — evento `SessionStart`, comando `fdh doctor --quiet`.

Las tres entries no requieren runtime FDH propio: los agentes (Claude Code, etc.) ya tienen su mecanismo nativo para ejecutar/cargar rules/agents/hooks. FDH sólo materializa los archivos en los paths que cada agente espera.

### Nueva capability `fdh-scan`

- Comando `fdh scan` audita componentes (skills/rules/agents/hooks) antes de publicar o instalar: detección de secrets, validación de hooks contra inyección de comandos, perfilado de riesgo de MCPs, auditoría de permisos en agent configs.
- Implementación rule-based deterministic. Pipeline adversarial multi-agente queda como evolución futura.

### Validación y CI

- `tools/validate-registry.py` extendido para schema v2 (validar `kind`, profiles, consistencia entre catálogo y directorios).
- Nuevo `tools/validate-manifest.py` valida `.fdh/manifest.yaml` contra el catálogo del hub.
- CI corre `fdh scan` sobre cada PR que toque `skills/`/`rules/`/`agents/`/`hooks/`.

## Capabilities

### New Capabilities

- `hub-registry-v2`: schema v2 del catálogo unificado con `kind` y las cuatro primitivas. Reglas de migración desde v1.
- `hub-profiles`: bundles curados en `hub/profiles.yaml`, semántica de referencia desde el manifest y extension/override en el consumer.
- `consumer-manifest-and-lock`: schemas y semántica de `.fdh/manifest.yaml` y `.fdh/lock.yaml`. Relación intención → resolución. Reglas de regeneración.
- `installation-state-ledger`: schema y semántica de `~/.fdh/state.json`. Comandos `fdh list-installed`, `fdh repair`, `fdh uninstall --dry-run`.
- `consumer-managed-paths`: contrato de `.fdh-managed.yaml`, `.gitignore` sectionado, bloque managed en `.claude/settings.json`. Detección de drift.
- `hub-rules-primitive`: contrato de rules como primitiva separada de skills. Formato, scope por glob, materialización per-agente. Ship con `rules/no-console-log/`.
- `hub-agents-primitive`: contrato de agents como primitiva. Formato, target dirs per-agente. Ship con `agents/forge-pr-writer/`.
- `hub-hooks-primitive`: contrato de hooks como primitiva. Formato, matchers, profiles. Ship con `hooks/doctor-on-session-start/`.
- `fdh-scan-security`: comando `fdh scan` con detección rule-based de secrets, command injection en hooks, riesgo de MCPs, permisos de agents.

### Modified Capabilities

- `hub-skills-registry`: el catálogo deja de ser exclusivo de skills; ahora indexa las cuatro primitivas via `kind`. Schema v1 → v2 con regla de migración.
- `fdh-init-interactive`: el wizard persiste sus decisiones en `.fdh/manifest.yaml` y dispara `fdh install` que escribe `.fdh/lock.yaml` + actualiza `~/.fdh/state.json`. Pre-rellena el wizard desde el manifest existente si re-corrés `init`.
- `fdh-skills-sync`: `fdh update` compara contra `lock.yaml` como fuente de verdad, no contra `.skill-version` distribuido. Marker rebautizado a `.fdh-managed.yaml`, cache local self-describing.

## Impact

### Schema migration

- `skills/registry.yaml` v1 (1 entrada) → schema v2 tooled e idempotente. CI valida ausencia de archivos v1 al merge.
- Decisión de rename de archivo se finaliza en `design.md` (impacto principal: docs + un tool `tools/migrate-registry-v1-v2.py`).

### Estructura del hub (post-apply)

- Nuevos directorios root con su primera entry real: `rules/no-console-log/`, `agents/forge-pr-writer/`, `hooks/doctor-on-session-start/`.
- `hub/profiles.yaml` con profile `minimal` que ejercita las cuatro primitivas end-to-end.
- `skills/design-system/` queda igual; sólo gana `kind: skill` en su entrada del registry.

### Consumer repos

- Los 30 pilots no se rompen: próximo `fdh install` detecta ausencia de `.fdh/manifest.yaml` y lo genera por introspección del `.fdh-managed.yaml`/`.skill-version` legacy. Developer revisa y commitea.
- `.gitignore` modificado automáticamente con sección propia, sin tocar entries pre-existentes.
- `.claude/settings.json` modificado in-place sólo si se instala el hook real (`doctor-on-session-start`).

### Repo `fdh` (hermano, Go)

- Implementación de manifest/lock parsing, state.json management, gestión de `.gitignore` y de bloque settings.json, comandos `fdh list-installed/repair/uninstall/scan`. Estimado 2-4 sprints (no en scope de este change del hub).

### Scope explícitamente NO incluido

- Wrapping `fdh` en paquete npm → change paralelo `fdh-cli-npm-distribution`.
- Instincts / continuous learning → change post-hub-v2 `add-instinct-collaboration`.
- `fdh scan` con pipeline adversarial multi-agente → future change `evolve-scan-to-adversarial`.

### Sets up future changes

- `add-more-rules`, `add-more-agents`, `add-more-hooks`: catálogo poblándose con el patrón ya establecido.
- `evolve-scan-to-adversarial`: `fdh scan` pasa de rule-based a pipeline multi-agente.
- `add-instinct-sync-service`: backend de sincronización de instincts (parte 2 de `add-instinct-collaboration`).
