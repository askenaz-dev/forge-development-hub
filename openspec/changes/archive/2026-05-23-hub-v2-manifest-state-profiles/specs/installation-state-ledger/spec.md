## ADDED Requirements

### Requirement: Archivo `~/.fdh/state.json` registra inventario per-máquina

`fdh` SHALL mantener un archivo `~/.fdh/state.json` (en el home del usuario, no committed a ningún repo) que registre el inventario de instalaciones en la máquina actual. Schema mínimo v1 SHALL incluir: `schema_version: 1`, `user_scope_installs: { skills, rules, agents, hooks }` (listas de objetos con `name`, `version`, `installed_at`, `path`), y `hub_cache: { last_pulled, commit, url }`.

#### Scenario: State.json creado en primer comando fdh

- **WHEN** un usuario nuevo corre cualquier comando `fdh` por primera vez
- **THEN** se crea `~/.fdh/state.json` con `schema_version: 1`, secciones vacías de `user_scope_installs` y `hub_cache` inicializado al primer pull

#### Scenario: State.json no se committea a ningún repo

- **WHEN** un developer mira el `.gitignore` de cualquier repo donde corre fdh
- **THEN** no encuentra entries que protejan `~/.fdh/state.json` porque vive fuera del repo, en `$HOME`

### Requirement: Sección `projects:` extensible de bajo costo

El schema v1 de `state.json` SHALL permitir una sección opcional `projects: { <absolute_path>: { lock_hash, managed_paths, last_install_at } }` que se llena bajo demanda; comandos `fdh install` corriendo en un proyecto SHALL registrar/actualizar la entry correspondiente. La ausencia de la sección o de entries individuales NO SHALL ser error.

#### Scenario: Primera instalación en un proyecto

- **WHEN** `fdh install` corre por primera vez en `/home/dev/work/checkout-service`
- **THEN** `state.json` gana una entry bajo `projects` con la key `/home/dev/work/checkout-service` y los valores correspondientes

#### Scenario: Segunda instalación actualiza la entry

- **WHEN** `fdh install` corre por segunda vez en el mismo proyecto después de un edit del manifest
- **THEN** la entry existente se actualiza (mismo path, nuevos `lock_hash`, `managed_paths`, `last_install_at`)

### Requirement: Comando `fdh list-installed` lee del state.json

`fdh` SHALL proveer un comando `fdh list-installed` que lea `state.json` y muestre un resumen legible de componentes instalados: por defecto sólo user-scope, con flags `--projects` (incluye registrados en `projects:`), `--all`, `--kind <skill|rule|agent|hook>`, y `--json`.

#### Scenario: list-installed por default

- **WHEN** un developer corre `fdh list-installed` sin flags y tiene 2 skills user-scope y 3 proyectos registrados
- **THEN** la salida muestra sólo los 2 skills user-scope; los proyectos no aparecen salvo que se pase `--projects`

#### Scenario: list-installed --all --json

- **WHEN** se corre `fdh list-installed --all --json`
- **THEN** la salida es un único objeto JSON con `user_scope_installs` y `projects`, parseable por scripts

### Requirement: Comando `fdh repair` reconcilia state contra disco

`fdh` SHALL proveer un comando `fdh repair` que para cada proyecto registrado en `state.json` verifique que los `managed_paths` existen físicamente; SHALL ofrecer opciones para (a) re-instalar paths faltantes leyendo el lock del proyecto, (b) limpiar entries del state que apunten a proyectos borrados, (c) reportar drift sin actuar (`--dry-run`).

#### Scenario: Repair detecta path faltante

- **WHEN** `fdh repair` corre y encuentra que `~/work/checkout-service/.claude/skills/design-system/` está registrado en state pero no existe en disco
- **THEN** `fdh` imprime la divergencia y ofrece `[r]e-install / [s]kip / [u]nregister`

#### Scenario: Repair --orphans limpia proyectos borrados

- **WHEN** `fdh repair --orphans` corre y un proyecto registrado en state no existe como directorio
- **THEN** `fdh` remueve esa entry del state después de confirmación y reporta cuántas entries limpió

#### Scenario: Repair --dry-run

- **WHEN** `fdh repair --dry-run` corre con varios casos de drift
- **THEN** `fdh` lista todas las divergencias detectadas y sale con código cero sin tocar nada

### Requirement: Comando `fdh uninstall --dry-run` previsualiza con state

`fdh uninstall <component>` SHALL aceptar `--dry-run` que liste exactamente qué paths serían removidos (consultando `state.json` + markers `.fdh-managed.yaml` en disco) sin modificar filesystem ni state.

#### Scenario: Uninstall dry-run multi-agent

- **WHEN** `design-system` está instalado en Claude Code y Copilot en el proyecto actual, y se corre `fdh uninstall design-system --dry-run`
- **THEN** la salida lista los dos paths (`.claude/skills/design-system/`, `.github/prompts/design-system.prompt.md`) más las entries que se removerían de `.gitignore`, sin tocar nada
