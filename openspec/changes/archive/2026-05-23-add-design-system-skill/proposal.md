*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Why

Forge ya tiene un design system maduro (`FTI00575-design-system`) con `AGENTS.md`, `COMPONENTS.md` y reglas de tokens estrictas, pero los agentes de codificación AI (Claude Code, Codex, Copilot, OpenCode) no las cargan automáticamente cuando generan UI en proyectos consumidores: terminan inventando colores, espaciados y componentes ad-hoc que rompen consistencia visual y accesibilidad. Necesitamos un *skill* instalable que cualquier agente cargue por auto-detección al generar UI, de modo que las reglas del DS, los tokens y el catálogo de 43 componentes sean contexto obligatorio antes de escribir una línea de código de interfaz.

## What Changes

- Nuevo skill canónico `design-system` con `SKILL.md` que se activa por auto-detección ante triggers de generación de UI (palabras como "componente", "pantalla", "formulario", "botón", "estilo", "React", "Tailwind", etc.).
- El skill *no duplica* el contenido del DS: embebe únicamente las reglas no-negociables de `AGENTS.md` (tokens semánticos, WCAG 2.1 AA, estados obligatorios, dark mode, mobile-first) y *apunta* al resto vía rutas/URLs canónicas en el repo `FTI00575-design-system`.
- Helper de setup: el skill guía la configuración del consumidor (`.npmrc` con scope `@forge-enablers-genai`, `GITHUB_PKG_TOKEN`, `npm install @forge-enablers-genai/ui` o `npx @forge-enablers-genai/cli init`).
- Ubicación canónica del skill: nuevo directorio top-level `skills/design-system/` en este hub, fuera de los cuatro espejos por ecosistema (`.claude/`, `.codex/`, `.github/`, `.opencode/`). Este directorio es la fuente que el futuro `fdh init` (change separado) leerá para copiar al ecosistema elegido por el developer.
- Snapshot versionado del DS bajo `skills/design-system/references/` (copia parcial de `AGENTS.md`, `COMPONENTS.md`, `DESIGN.md`, `semantic-design/*.md` y `components.meta.json`) con un script de sincronización para refrescar contra el repo origen.
- README del skill con instrucciones de uso manual hasta que exista `fdh init` (copiar el directorio a `.claude/skills/design-system/` del proyecto consumidor).

## Capabilities

### New Capabilities

- `design-system-skill`: skill instalable, auto-detectable y agente-agnóstico que carga las reglas, tokens y catálogo de componentes del design system Forge en cualquier sesión de coding agent que genere UI, apuntando al repo canónico `FTI00575-design-system` como fuente de verdad.

### Modified Capabilities

<!-- No existing specs are being modified by this change. -->

## Impact

- **Nuevo directorio:** `skills/design-system/` en la raíz del hub (canónico, no mirroreado por ahora a los cuatro ecosistemas).
- **Nueva spec:** `openspec/specs/design-system-skill/spec.md` describe el contrato del skill (triggers, contenido mínimo, mecanismo de referencia al DS, modo de instalación manual).
- **Dependencia operativa:** lectura del repo `forge-enablers-genai/FTI00575-design-system` en fase apply para extraer las reglas y el catálogo. Requiere acceso GitHub (vía clone local o `gh`).
- **Sin cambios** en `openspec/`, en los directorios espejo (`.claude/`, `.codex/`, `.github/`, `.opencode/`) ni en el CLI `openspec`. Tampoco se publica nada a GitHub Packages.
- **Futuro `fdh init`** (change separado): consumirá `skills/design-system/` como entrada de su registro de skills. Este change deja la fuente lista pero no implementa el CLI.
- **Riesgo de drift:** el snapshot bajo `references/` puede desincronizarse con el DS origen. Mitigado por (a) script `sync.mjs`, (b) marca de versión del DS en `SKILL.md`, (c) instrucción explícita al agente de releer si hay duda.
