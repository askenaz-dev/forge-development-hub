*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Context

El hub publica hoy una única primitiva (`skill`) con un único archivo de catálogo (`skills/registry.yaml` schema v1, 1 entrada: `design-system`). El plan archivado `add-fdh-cli-distribution-and-interactive-init` definió `fdh init` interactivo, `fdh update` y el concepto de catálogo via `registry.yaml`, pero apoyado en un único marker `.skill-version` por directorio instalado y sin contrato declarativo en el consumer repo.

Tras revisar ECC (https://github.com/affaan-m/ECC) — el ecosistema cross-harness más maduro del espacio — se identificaron cinco brechas estructurales (descritas en `proposal.md`) que se vuelven costosas cuanto más grande es el catálogo. Este design resuelve las decisiones de implementación clave que el proposal dejó abiertas.

**Stakeholders:**
- Devs Forge consumiendo el hub (pilot actual: 30; target: 500).
- Admins del hub curando catálogo y profiles.
- Equipo plataforma operando registry interno y CI del hub.
- Seguridad corporativa aprobando rollout (requirente de `fdh scan`).

**Constraints duras:**
- CLI `fdh` existente en Go (`C:/forge/fdh`, 13k LOC, portal API incluido). Cambios al CLI tracking separado.
- Distribución 100% interna (sin npm/Homebrew público). Internal npm registry (Artifactory) provisioning es change paralelo `fdh-cli-npm-distribution`.
- Compatibilidad con pilot existente: migración automática sin reinstalls manuales.
- Cuatro ecosistemas espejo (`.claude/`, `.codex/`, `.github/`, `.opencode/`) actualizados en lockstep.

**Sibling changes:**
- `fdh-cli-npm-distribution` (paralelo): wrap del binario Go en npm package.
- `add-instinct-collaboration` (depende de éste): bucle bottom-up de aprendizaje.

## Goals / Non-Goals

**Goals:**

- Definir schema v2 del catálogo con `kind` como primitiva paralela y migración tooled desde v1.
- Definir contrato `manifest + lock + state` análogo al modelo npm/yarn/pnpm.
- Habilitar `fdh list-installed`, `fdh repair`, `fdh uninstall --dry-run` via state ledger.
- Distribuir las primeras entries reales de `rule`, `agent` y `hook` (camino hecho, modificables).
- Habilitar `fdh scan` rule-based para auditoría de componentes pre-publicación.
- Permitir profiles curados que un consumer manifest pueda referenciar + extender.
- No romper el pilot de 30 devs durante el upgrade.

**Non-Goals:**

- **No** implementar el código Go en el repo `fdh` durante este change — el spec describe contratos; la implementación es tracking separado.
- **No** implementar runtime FDH de hooks/rules/agents — los ejecutan los agentes nativos (Claude Code, etc.), `fdh` sólo materializa archivos.
- **No** levantar Artifactory ni publicar a npm — lo cubre `fdh-cli-npm-distribution`.
- **No** introducir instincts / continuous learning — lo cubre `add-instinct-collaboration`.
- **No** pipeline adversarial multi-agente para `fdh scan` — v1 es rule-based; evolución en `evolve-scan-to-adversarial`.
- **No** soportar más primitivas además de las cuatro (`skill`, `rule`, `agent`, `hook`). Nuevas primitivas requerirían un schema v3.
- **No** migrar agentes que no soporten una primitiva dada — si Codex no soporta `agent` distribuible, `fdh install` simplemente omite con mensaje informativo.

## Decisions

### Decision 1: Renombrar `skills/registry.yaml` → `hub/registry.yaml`

El archivo deja de ser exclusivo de skills. Mantener el nombre actual confunde semánticamente; renombrarlo refleja la realidad del catálogo unificado.

**Ubicación final**: `hub/registry.yaml` en la raíz del repo. El directorio `hub/` también aloja `hub/profiles.yaml` (Decision 3).

**Ventana de migración**: durante 60 días post-apply, `skills/registry.yaml` SHALL ser un symlink (POSIX) o copia generada por CI (Windows) apuntando a `hub/registry.yaml`. Esto permite a herramientas externas que pinearon la ruta vieja seguir funcionando mientras se actualizan. Después de 60 días el symlink se remueve en un change cleanup.

**Alternativas consideradas:**
- *Mantener `skills/registry.yaml` con contenido v2*: descartado, confunde nombre vs contenido y dificulta search en el repo ("¿dónde están los rules?").
- *Renombrar a `catalog.yaml` o `manifest.yaml`*: descartado, "manifest" choca con `.fdh/manifest.yaml` del consumer; "catalog" no comunica que es del hub.
- *Múltiples archivos por kind* (`skills.yaml`, `rules.yaml`, etc.): descartado, fragmenta validación cross-kind (orphans, profiles) y multiplica boilerplate.

### Decision 2: `state.json` schema minimal v1 con `projects:` opcional extensible

El schema v1 SHALL definir las tres secciones (`user_scope_installs`, `hub_cache`, `projects`), pero la sección `projects:` SHALL ser opcional (default vacío) y SHALL poblarse bajo demanda en cada `fdh install` que corra en un proyecto. Esto da estructura para `fdh repair --orphans` y `fdh list-installed --projects` sin requerir backfill masivo.

```json
{
  "schema_version": 1,
  "user_scope_installs": { "skills": [], "rules": [], "agents": [], "hooks": [] },
  "hub_cache": { "url": "...", "last_pulled": "...", "commit": "..." },
  "projects": {}   // opcional, se llena lazily
}
```

**Alternativas consideradas:**
- *Schema v1 sin `projects`* (full minimal): descartado, agregar `projects` después requeriría schema v2 o detectar formato dinámicamente.
- *Schema v1 con `projects` obligatorio y backfill al primer comando*: descartado, costo de I/O en primer comando proporcional al número de proyectos del usuario.
- *State distribuido (un archivo por proyecto en `~/.fdh/projects/<hash>.json`)*: descartado, complica `fdh list-installed --global` y dispara muchas operaciones de filesystem.

### Decision 3: `hub/profiles.yaml` como archivo separado del registry

Mantener profiles en un archivo dedicado en lugar de una sección dentro del registry.

**Razones:**
- **Separación de ownership**: el equipo plataforma cura profiles; los owners de skills/rules/agents/hooks editan el registry. Archivos separados → permisos separados, PRs separados.
- **Schema más simple**: el registry queda como "catálogo plano de componentes"; profiles agrega complejidad (extends, references). No mezclar concerns.
- **Visualización**: revisar todos los profiles disponibles es `cat hub/profiles.yaml` directo.

**Alternativas consideradas:**
- *Sección `profiles:` dentro del registry*: descartado, mezcla concerns y hace el registry más grande/más difícil de revisar.
- *Profiles en repos separados por team*: descartado, scope creep; un solo lugar canonical es mejor para discoverability.

### Decision 4: `fdh install --frozen` shippea en este change, auto-enable en CI

`--frozen` (semántica de `npm ci`) NO regenera el lock y falla si el lock no satisface el manifest. Crítico para reproducibilidad en CI.

**Auto-enable**: si `fdh install` detecta env var `CI=true` (convención cross-CI) o `FDH_FROZEN=true`, se comporta como si `--frozen` hubiera sido pasado, salvo que el usuario explícitamente pase `--no-frozen`. Esto previene que CI builds regeneren locks silenciosamente.

**Alternativas consideradas:**
- *Comando separado `fdh ci`*: descartado, complica la matriz de comandos sin ganancia clara; `--frozen` es flag canónico en el ecosistema.
- *Frozen siempre default*: descartado, romp el flujo dev local donde `fdh install` debe poder resolver versiones nuevas tras edits del manifest.
- *Diferir `--frozen` a un change posterior*: descartado, sin él la reproducibilidad entre máquinas no está garantizada — derrota el punto del lockfile.

### Decision 5: State.json per-host con namespacing por hostname

Para soportar usuarios con HOME compartido (NFS, dev containers, máquinas multi-arranque), `state.json` SHALL vivir en `~/.fdh/state.<hostname>.json` en lugar de `~/.fdh/state.json` cuando se detecte un HOME compartido. La detección puede ser opt-in vía `FDH_HOSTNAME_NAMESPACED=true` env var (default: archivo plano).

**Comportamiento por defecto**: `~/.fdh/state.json` único per-HOME. Suficiente para la gran mayoría de devs (laptop personal con disco local).

**Comportamiento opt-in para HOMEs compartidos**: archivo per-hostname. `fdh doctor` puede sugerir la opción si detecta múltiples binarios `fdh` en lugares no estándar o si el HOME está en NFS.

**Alternativas consideradas:**
- *Siempre per-hostname*: descartado, fragmenta innecesariamente para 95% de casos donde el HOME es local.
- *Detección automática siempre*: descartado, detectar NFS confiable es difícil cross-platform.
- *Ignorar el caso* (un solo `state.json` siempre): descartado, dev containers compartidos son cada vez más comunes y producirían corrupción concurrente.

### Decision 6: `kind` no defaultea a `skill` — debe ser explícito

Aunque sería tentador defaultear `kind: skill` para preservar compat con v1, este design lo prohíbe: cada entry SHALL declarar `kind` explícitamente. Razón: forzar la decisión consciente del admin al agregar una entry nueva, especialmente importante porque el directorio target depende del kind.

La migración v1 → v2 vía `tools/migrate-registry-v1-v2.py` agrega `kind: skill` a todas las entries v1 automáticamente, así que la rigidez no afecta el upgrade del pilot.

### Decision 7: Adapter de hooks usa marker `_fdh_managed` dentro de settings.json

Hooks viven en `.claude/settings.json` (no en archivos propios). Como el archivo es de ownership mixto (dev tiene sus propios hooks ahí), `fdh install` SHALL agregar el campo `_fdh_managed: <component-name>` a cada entry FDH dentro del `settings.json`. `fdh uninstall` filtra entries por ese marker.

**Implicación**: el `settings.json` queda ligeramente "polucionado" con campos no estándar `_fdh_managed`. Esto es aceptable porque (a) Claude Code ignora campos desconocidos, (b) los markers son cortos y autoexplicativos, (c) es la única forma de identificar entries managed sin un archivo paralelo. El convenio `_*` para campos privados es estándar en JSON.

### Decision 8: Tooling de validación queda en Python interim, migra a Go cuando `fdh` lo implemente

`tools/validate-registry.py` y `tools/validate-manifest.py` se mantienen en Python durante este change para minimizar fricción al apply. Cuando el repo `fdh` implemente `fdh validate-registry` y `fdh validate-manifest` (tracking separado), CI cambia de invocar Python a invocar el binario Go. Los scripts Python quedan como fallback for development local hasta que `fdh` esté en cada laptop.

### Decision 9: `hub/profiles.yaml` SHALL incluir al menos profile `minimal` post-apply

Ship con un profile real ejercita el schema end-to-end y da ejemplo concreto a futuros curadores. `minimal` referencia las cuatro primitivas (skill `design-system`, rule `no-console-log`, agent `forge-pr-writer`, hook `doctor-on-session-start`), todas las cuales también shippea este change como entries reales.

## Risks / Trade-offs

- **Repo `fdh` (Go) atrasado en implementar las specs nuevas** → mitigado: contratos en specs son verificables sin código (validación de archivos YAML/JSON); CI puede usar el Python tooling interim. El binario Go puede tardar 2-4 sprints sin bloquear este change.

- **Pilot devs no migran su `.skill-version` legacy** → mitigado: `fdh install` y `fdh update` detectan el marker viejo y migran silenciosamente al nuevo. Cero acción del developer.

- **Profile `minimal` se desactualiza si el catálogo crece** → mitigado: CI del hub valida que cada componente referenciado por cada profile existe; PRs que rompan referencias quedan bloqueados.

- **`.gitignore` modificado automáticamente sorprende al developer** → mitigado: la sección managed está claramente delimitada con markers; `fdh init` imprime "modified .gitignore: see managed section" como primer output después de install.

- **`settings.json` con marker `_fdh_managed` puede confundir herramientas third-party** → aceptado: el campo `_*` es convención estándar para metadata privada en JSON; documentado en el spec.

- **CI auto-enable de `--frozen` rompe flujos locales que setean `CI=true`** → mitigado: el override `--no-frozen` está disponible; documentado en `fdh install --help`.

- **Symlink de compat `skills/registry.yaml` → `hub/registry.yaml` no funciona en Windows sin permisos especiales** → mitigado: en Windows, CI genera una copia regenerada (no symlink) y la commitea como parte del workflow. El comportamiento de redirect/read es transparente.

- **HOME compartido (NFS, dev containers) corrompe `state.json` concurrente** → mitigado parcialmente por Decision 5 (namespacing opt-in por hostname). Aceptado el riesgo en el caso default; documentado.

- **Devs con muchos proyectos acumulan entries `projects:` huge en `state.json`** → aceptado, mitigado por `fdh repair --orphans` para limpieza periódica; en práctica un dev con 50 proyectos representa <50KB de JSON.

- **`kind` obligatorio rompe scripts externos que generan entries** → aceptado, scripts externos no son use case soportado; la migración tooled cubre el caso pilot.

## Migration Plan

Migración interna al repo del hub (no afecta consumers en este change):

1. **Pre-apply**: snapshot del estado actual (`skills/registry.yaml` v1 con 1 entrada + `tools/validate-registry.py` v1).
2. **Apply de este change**:
   - Crear directorios nuevos `rules/no-console-log/`, `agents/forge-pr-writer/`, `hooks/doctor-on-session-start/`.
   - Crear `hub/` con `registry.yaml` (v2, 4 entries) y `profiles.yaml` (1 profile `minimal`).
   - Generar symlink/redirect `skills/registry.yaml` → `hub/registry.yaml`.
   - Extender `tools/validate-registry.py` para schema v2 + cuatro dirs.
   - Crear `tools/validate-manifest.py`.
   - Actualizar CI del hub para correr ambos.
   - Actualizar `skills/README.md` y agregar `hub/README.md` documentando el nuevo layout.
3. **Post-apply en consumers (pilot 30 devs)**: ninguna acción inmediata; al próximo `fdh install` (cuando esté disponible la versión Go que soporte este schema), el manifest se auto-genera por introspección del estado legacy.
4. **Día 60**: cleanup change remueve symlink `skills/registry.yaml` y deja sólo `hub/registry.yaml`.

**Rollback** (si algo va mal post-apply): revert del commit del apply restaura `skills/registry.yaml` v1 y elimina los nuevos directorios. Pilot no afectado porque no se tocó código del CLI Go.

## Open Questions

Resueltas en este design:
- ✅ Rename de `skills/registry.yaml` → `hub/registry.yaml` (Decision 1).
- ✅ State.json minimal v1 con `projects:` opcional (Decision 2).
- ✅ Profiles como archivo separado (Decision 3).
- ✅ `--frozen` ship + auto-enable en CI (Decision 4).
- ✅ HOME compartido vía namespace opt-in por hostname (Decision 5).

Quedan abiertas para el apply / changes futuros:
- **¿Qué CI pipeline ejecuta `fdh scan` post-implementación Go?** Probablemente GitHub Actions / equivalente Forge. A confirmar en apply una vez `fdh scan` esté implementado.
- **¿La migración de `.skill-version` legacy genera notificación al developer o es completamente silenciosa?** Hoy spec dice silenciosa; podríamos agregar one-liner informativo. Refinable en apply.
- **¿`hub/profiles.yaml` soporta herencia entre profiles (`extends: another-profile`)?** No en v1. Defer hasta tener >5 profiles y ver patrón real.
- **¿Notificación push cuando admin cambia un profile que un consumer usa?** Hoy no — el consumer ve el cambio al correr `fdh update`. Posible enhancement futuro con webhooks.
