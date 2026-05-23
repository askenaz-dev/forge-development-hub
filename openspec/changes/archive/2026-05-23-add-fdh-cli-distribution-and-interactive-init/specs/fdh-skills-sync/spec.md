## ADDED Requirements

### Requirement: Comando `fdh update` para sincronizar skills instaladas

El sistema SHALL proveer un comando `fdh update` que recorra los directorios convencionales de cada agente conocido, encuentre los marcadores `.skill-version`, sincronice el hub configurado en `registry.url`, y para cada skill cuyo `hub_commit` cambió, ofrezca actualizar el contenido instalado.

#### Scenario: Update sin cambios

- **WHEN** un developer ejecuta `fdh update` y ninguna skill instalada tiene cambios en el hub respecto al `hub_commit` registrado
- **THEN** `fdh` imprime "all skills up to date" y sale con código cero sin modificar el filesystem

#### Scenario: Update con cambios disponibles

- **WHEN** un developer ejecuta `fdh update` y `design-system` tiene un `hub_commit` distinto al instalado
- **THEN** `fdh` imprime un resumen del cambio (lista de archivos modificados/añadidos/borrados, no diff completo), pide confirmación `[y/N]`, y al confirmar reemplaza el contenido instalado y actualiza `.skill-version`

#### Scenario: Update con `--yes` no pregunta

- **WHEN** se ejecuta `fdh update --yes`
- **THEN** `fdh` aplica todos los cambios disponibles sin preguntar y sale con código cero si todo OK

### Requirement: `--dry-run` muestra plan sin tocar filesystem

`fdh update` SHALL aceptar `--dry-run` que imprima el plan completo (skills con cambios, archivos afectados, rutas target) y salga con código cero sin modificar el filesystem.

#### Scenario: Dry-run con cambios pendientes

- **WHEN** se ejecuta `fdh update --dry-run` y hay dos skills con cambios
- **THEN** `fdh` imprime el plan para ambas, incluyendo el `hub_commit` actual y el nuevo, y sale con código cero sin tocar nada

### Requirement: Filtros `--skill` y `--agent` para update selectivo

`fdh update` SHALL aceptar flags repetibles `--skill <name>` y `--agent <name>` que limiten la sincronización a esas combinaciones; sin flags sincroniza todas las combinaciones detectadas.

#### Scenario: Update sólo de un skill

- **WHEN** se ejecuta `fdh update --skill design-system --yes`
- **THEN** sólo `design-system` se sincroniza (en todos los agentes donde está instalado); las demás skills se ignoran

#### Scenario: Update sólo en un agente

- **WHEN** se ejecuta `fdh update --agent claude-code --yes`
- **THEN** sólo las skills instaladas en `.claude/skills/` se sincronizan; copias en otros agentes (Copilot/OpenCode/Codex) se ignoran

#### Scenario: Combinación de filtros

- **WHEN** se ejecuta `fdh update --skill design-system --agent copilot --yes`
- **THEN** sólo se sincroniza `design-system` en Copilot

### Requirement: Detección de edits manuales del developer

`fdh update` SHALL calcular un hash de los archivos instalados al momento del update y SHALL compararlo contra el hash registrado en `.skill-version`; si no coincide, SHALL emitir un warning y SHALL saltarse esa skill salvo que el developer pase `--force`.

#### Scenario: Edit manual detectado

- **WHEN** un developer editó manualmente `.claude/skills/design-system/SKILL.md` y luego corre `fdh update`
- **THEN** `fdh` imprime warning del tipo `"skill design-system has local modifications (skipping; use --force to overwrite)"`, no toca esa skill, y continúa con el resto

#### Scenario: Force overwrite

- **WHEN** se ejecuta `fdh update --force --skill design-system --yes` y el skill tiene edits locales
- **THEN** `fdh` sobreescribe los archivos locales con la versión del hub, actualiza `.skill-version`, y emite un mensaje confirmando el overwrite

### Requirement: Resumen final con conteo y exit code agregado

`fdh update` SHALL emitir al final un resumen con conteo de skills actualizadas, skills sin cambios, skills saltadas por edits locales y skills con error; el exit code SHALL ser cero si no hubo errores, distinto de cero si alguna actualización falló (no si simplemente fue saltada).

#### Scenario: Mix de resultados

- **WHEN** `fdh update --yes` actualiza 2 skills, encuentra 1 sin cambios, salta 1 por edit local, y otro falla por permisos
- **THEN** `fdh` imprime `"updated: 2, unchanged: 1, skipped: 1, failed: 1"` y sale con código distinto de cero

#### Scenario: Todo OK

- **WHEN** `fdh update --yes` actualiza 3 skills sin errores ni saltadas
- **THEN** `fdh` imprime `"updated: 3, unchanged: 0, skipped: 0, failed: 0"` y sale con código cero

### Requirement: Salida JSON estructurada con `--json`

`fdh update` SHALL aceptar `--json` para emitir el resumen y el plan en formato JSON estructurado adecuado para consumo por scripts y CI.

#### Scenario: Salida JSON

- **WHEN** se ejecuta `fdh update --dry-run --json`
- **THEN** la salida es un único objeto JSON con campos `plan: [...]` (cada entry con `skill`, `agent`, `from_commit`, `to_commit`, `files_changed`), y exit code cero
