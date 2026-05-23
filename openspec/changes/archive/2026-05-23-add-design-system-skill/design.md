## Context

`falabella-development-hub` es un workflow hub que actualmente espeja skills de OpenSpec en cuatro ecosistemas de coding agents (`.claude/`, `.codex/`, `.github/`, `.opencode/`). El design system de la compañía vive en un repo separado (`falabella-enablers-genai/FTI00575-design-system`, monorepo privado) y ya publica documentación pensada para LLMs:

- `AGENTS.md` — 20 reglas no-negociables agrupadas en Tokens / Colors / Typography / Spacing / Components / Accessibility / Responsive.
- `COMPONENTS.md` — catálogo LLM-optimizado de 43 componentes (26 UI + 17 chart) sobre Radix + CVA + Tailwind 4.
- `DESIGN.md` + `semantic-design/*.md` — índice 1:1 que enruta a tokens canónicos.
- `components.meta.json` — single source of truth de metadata.

A pesar de eso, los agentes que generan UI en proyectos consumidores no leen estos archivos por defecto: el contexto se carga sólo si el agente tropieza con ellos. El consumo del DS además requiere setup no trivial: `.npmrc` con scope `@falabella-enablers-genai`, `GITHUB_PKG_TOKEN` con `read:packages`, y elegir entre el CLI `genai-ds` (copia código fuente al proyecto) o el package `@falabella-enablers-genai/ui` (import directo). Pedirle al developer que cargue manualmente `AGENTS.md` en cada sesión escala mal.

El usuario tiene en mente un CLI futuro `fdh init/update` que permitirá al developer elegir agentes y skills, y que excluirá los directorios de skills del control de versiones del proyecto consumidor (se regeneran on-demand). Este change deja la **fuente del skill** lista para ese consumidor futuro, sin construir el CLI todavía.

## Goals / Non-Goals

**Goals:**

- Entregar un skill canónico instalable que cualquier coding agent compatible cargue por auto-detección al generar UI, con las reglas no-negociables del DS pre-cargadas en contexto.
- Mantener una sola fuente de verdad para las reglas del DS: el repo `FTI00575-design-system`. El skill *apunta*; no *re-define*.
- Permitir uso del skill **hoy** vía copia manual del directorio al ecosistema elegido, sin esperar al CLI `fdh init`.
- Versionar el contenido del skill contra una versión específica del DS (pinning) para que el agente sepa qué snapshot está leyendo y pueda detectar drift.
- Diseñar el directorio `skills/design-system/` de forma agnóstica al ecosistema target, de modo que `fdh init` (change futuro) lo pueda copiar sin transformación a `.claude/skills/`, `.codex/skills/`, `.github/skills/` u `.opencode/skills/`.

**Non-Goals:**

- **No** implementar el CLI `fdh init/update` — es un change separado que el usuario propondrá después.
- **No** mirrorear el skill a los cuatro ecosistemas en este change. El skill vive sólo en `skills/design-system/` hasta que `fdh init` decida copiarlo.
- **No** publicar nada a GitHub Packages, npm, ni a un registry externo.
- **No** modificar el repo `FTI00575-design-system`. La sincronización es unidireccional (DS → skill).
- **No** crear nuevos tokens, componentes ni reglas. El skill es lectura.
- **No** soportar design systems distintos al de Falabella en este change (extensibilidad futura).

## Decisions

### Decision 1: Ubicación canónica del skill — `skills/design-system/` (top-level, fuera de los espejos)

Se crea un nuevo directorio top-level `skills/` en la raíz del hub. La estructura interna del skill es:

```
skills/design-system/
├── SKILL.md                # entrypoint con frontmatter agente-agnóstico
├── README.md               # cómo instalar manualmente (pre-fdh-init)
├── references/             # snapshot versionado del DS
│   ├── AGENTS.md
│   ├── COMPONENTS.md
│   ├── DESIGN.md
│   ├── components.meta.json
│   └── semantic-design/
│       ├── ds-react.md
│       ├── tokens.md
│       ├── actions.md
│       ├── forms.md
│       ├── surfaces.md
│       ├── feedback.md
│       ├── navigation.md
│       └── layout.md
├── scripts/
│   └── sync.mjs            # sincroniza references/ desde el DS upstream
└── .ds-version             # versión del DS contra la que se sincronizó
```

**Alternativas consideradas:**
- *Mirrorear en los cuatro espejos desde el comienzo* — descartado: contradice la visión `fdh init` del usuario y duplica contenido innecesariamente.
- *Colocar en `openspec/skills/`* — descartado: confunde el skill con el dominio OpenSpec; los OpenSpec skills viven en los espejos por convención del hub.
- *Repo separado para el registro de skills* — descartado para este change: el usuario quiere que el hub mismo sea el registro central, y crear un repo nuevo es scope creep.

### Decision 2: SKILL.md frontmatter agente-agnóstico, traducible al formato de cada ecosistema

`SKILL.md` usa frontmatter YAML con campos comunes (`name`, `description`, `version`, `ds-version`, `triggers`) más una sección de cuerpo en Markdown plano. Cada ecosistema target tiene convenciones distintas (Claude Code usa frontmatter con `description` para auto-trigger; Copilot usa `*.prompt.md`; OpenCode usa `commands/*.md`). Para minimizar transformación en `fdh init`, este change adopta el formato Claude Code (más cercano al estándar) como base, y deja documentado en `README.md` cómo el CLI futuro lo adaptará a los otros tres.

**Alternativas consideradas:**
- *Generar 4 variantes desde el inicio* — descartado: scope creep, y el CLI `fdh init` es quien debería hacer la adaptación.
- *Inventar un formato neutro propio* — descartado: agrega capa de complejidad sin beneficio en este punto.

### Decision 3: Auto-detección por triggers explícitos en `description`

El campo `description` del frontmatter se redacta para que el modelo lo cargue cuando detecte intención de generar UI. Triggers nucleares (versión final se ajustará en apply):

> Use when the user wants to build, design, style, or modify any UI: React/Next/Vue components, screens, forms, buttons, layouts, dashboards, charts, modals, tables, navigation; or when the user mentions Tailwind, CSS, dark mode, accessibility, design tokens, colors, typography, spacing, or any Falabella visual identity. ALWAYS load this skill BEFORE writing UI code so design system rules, tokens, and the component catalog are in context.

**Alternativas consideradas:**
- *Activación explícita vía slash command* — descartado: el usuario eligió auto-detección y es el patrón con mayor recall.
- *Activación híbrida (auto + slash)* — descartado para este change; se puede agregar después sin breaking changes.

### Decision 4: Reglas no-negociables embebidas; resto por referencia

`SKILL.md` embebe **sólo** las 20 reglas no-negociables de `AGENTS.md` (tokens, contraste WCAG, type scale, spacing scale, estados obligatorios, focus ring, semantic HTML, prefers-reduced-motion, touch targets 44×44, mobile-first, breakpoints) y la decision tree "¿crear componente nuevo?". El resto (APIs específicas de componentes, ejemplos extensos, governance) queda como referencias en `references/` con instrucciones al agente de leerlas según necesite.

**Por qué embebido + referencia y no todo embebido:** mantener `SKILL.md` chico (< 8 KB) maximiza la probabilidad de carga completa en context window. Las APIs por componente (>20 KB en `COMPONENTS.md`) se leen on-demand cuando el agente está por usar un componente específico.

**Por qué embebido + referencia y no todo por referencia:** las 20 reglas son lo suficientemente compactas y lo suficientemente críticas (afectan cada línea de UI generada) como para forzar su presencia en contexto desde el momento del trigger.

### Decision 5: Snapshot de `references/` versionado contra `.ds-version`

`references/` contiene copias literales de los archivos del DS upstream al momento de la última sincronización. El archivo `.ds-version` registra la versión exacta (commit SHA + tag semver) del DS contra la que se sincronizó. `SKILL.md` instruye al agente: si la `.ds-version` registrada es más vieja que `N` meses, advertir al usuario y sugerir `fdh update` (cuando exista) o ejecutar `scripts/sync.mjs` manualmente.

**Alternativas consideradas:**
- *Sin snapshot, sólo URLs* — descartado: depende de conectividad y permisos GitHub en cada sesión; el agente fuera de red queda sin acceso.
- *Submódulo git al DS* — descartado: el DS es un monorepo grande (>20 MB con turbo cache, lockfile, etc.) y el skill sólo necesita un puñado de archivos doc.
- *Sync automático en cada uso* — descartado: agrega latencia y dependencia de red en runtime del agente.

### Decision 6: `scripts/sync.mjs` lee desde un clon local del DS (no clona él mismo)

El script de sincronización toma una ruta a un clon local del DS (default: `../FTI00575-design-system` o el path pasado por flag/env). Copia archivos selectos a `references/` y actualiza `.ds-version` con el SHA + tag del HEAD del clon.

**Por qué no clonar dentro del script:** evita acoplarse a auth de GitHub (PAT, SSH, etc.), funciona offline si el DS ya está clonado, y es el patrón que `fdh init/update` (change futuro) generalizará.

### Decision 7: Setup helper en `SKILL.md` orientado al CLI `genai-ds`

La sección "Setup en un proyecto consumidor" del SKILL.md prioriza la ruta CLI (`npx @falabella-enablers-genai/cli init` + `add`) porque le da source ownership al consumidor (componentes copiados al proyecto, no dependencia de runtime), que es la ruta recomendada por el README del DS. Documenta la alternativa npm package en segundo plano.

### Decision 8: Instalación manual documentada en `README.md` (puente hasta `fdh init`)

Mientras no exista `fdh init`, el `README.md` del skill describe los pasos manuales:

1. Clonar este hub: `git clone <hub-url>`
2. Copiar el directorio: `cp -r skills/design-system <target-project>/.claude/skills/design-system`
3. (Opcional) Agregar `.claude/skills/` al `.gitignore` del proyecto consumidor.
4. Verificar carga en Claude Code: el skill aparece en la lista del `/skills`.

Para otros agentes (Codex/Copilot/OpenCode), documenta la ruta target equivalente con una nota: "adaptación automatizada vendrá con `fdh init`".

## Risks / Trade-offs

- **Drift del snapshot vs DS upstream** → mitigado por `.ds-version`, `scripts/sync.mjs`, y una instrucción explícita al agente de releer si `.ds-version` está stale (> 60 días) o si el usuario menciona un componente que no aparece en `references/COMPONENTS.md`.
- **Auto-detección sobre-dispara fuera de contextos UI** (ej.: el usuario menciona "Tailwind" en una conversación de configuración) → mitigado redactando triggers verbo-orientados ("build/design/style UI") en lugar de sustantivos solos, y validando empíricamente en la fase apply contra prompts de control.
- **`SKILL.md` se vuelve obsoleto si el DS añade reglas nuevas** → el script `sync.mjs` debe extender un check de hash sobre `AGENTS.md`: si cambia, advierte al maintainer que las reglas embebidas necesitan revisión humana (no auto-sobreescribir, porque embebidas son un subset curado).
- **Fricción de setup en consumidores nuevos** (`.npmrc` + PAT con `read:packages`) → el SKILL.md incluye los pasos exactos con copy-paste blocks; no hay forma de evitar el PAT mientras el registro siga siendo privado.
- **El skill se acopla al formato de un ecosistema (Claude Code)** → aceptado: el costo de soportar los 4 desde el día 1 sin un CLI que los unifique es mayor que el costo de adaptar después.
- **Sin tests automatizados del skill en este change** → aceptado: validación en la fase apply será manual (carga el skill en un proyecto de prueba, pídele al agente que genere un Button, verifica que use `var(--button-primary-bg-default)` o equivalente). Tests automatizados son trabajo futuro.

## Migration Plan

No hay migración: es contenido nuevo. No se borra ni se cambia nada existente. Rollback es `rm -rf skills/design-system` + revertir entradas de `CLAUDE.md` si se actualiza.

## Open Questions

- ¿La versión del DS a pinear es `1.0.1` (la del `package.json` del monorepo) o la del package `@falabella-enablers-genai/ui` específicamente? Resolverlo en apply leyendo `packages/ui/package.json`.
- ¿`scripts/sync.mjs` debe correr en CI del hub cuando el DS publica un nuevo tag? Decisión diferida — fuera del scope de este change.
- ¿El `README.md` del skill debe incluir instrucciones para los 4 ecosistemas, o sólo Claude Code y referir a `fdh init` para los otros? Decisión: Claude Code completo + nota corta para los otros tres con TODO explícito.
