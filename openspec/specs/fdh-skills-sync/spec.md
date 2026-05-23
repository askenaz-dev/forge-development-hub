# fdh-skills-sync Specification

## Purpose

Comando fdh update para sincronizar skills instaladas contra el hub: diff resumido, filtros --skill/--agent, detección de edits locales por hash, --force opcional, salida JSON estable.

## Requirements

### Requirement: Comando `fdh update` para sincronizar componentes instalados

El sistema SHALL proveer un comando `fdh update` que lea `.fdh/lock.yaml` (o `~/.fdh/state.json` para componentes user-scope) como fuente de verdad sobre qué componentes están instalados y sus versiones esperadas, sincronice el hub configurado en `registry.url`, y para cada componente cuyo `hub_commit` (o `integrity`) cambió en el hub, ofrezca actualizar el contenido instalado y refrescar el lock. Aplica a las cuatro primitivas (skills, rules, agents, hooks), no sólo a skills.

#### Scenario: Update sin cambios

- **WHEN** un developer ejecuta `fdh update` y ningún componente del lock tiene cambios en el hub respecto al `hub_commit`/`integrity` registrado
- **THEN** `fdh` imprime "all components up to date" y sale con código cero sin modificar el filesystem ni el lock

#### Scenario: Update con cambios disponibles

- **WHEN** un developer ejecuta `fdh update` y `design-system` tiene un `integrity` distinto al lockfile
- **THEN** `fdh` imprime un resumen del cambio (lista de archivos modificados/añadidos/borrados, no diff completo), pide confirmación `[y/N]`, y al confirmar reemplaza el contenido instalado, refresca el marker `.fdh-managed.yaml` y actualiza el lock

#### Scenario: Update con `--yes` no pregunta

- **WHEN** se ejecuta `fdh update --yes`
- **THEN** `fdh` aplica todos los cambios disponibles sin preguntar, refresca lock y markers, y sale con código cero si todo OK

#### Scenario: Update cubre las cuatro primitivas

- **WHEN** se ejecuta `fdh update` en un proyecto con skill, rule, agent y hook instalados, y los cuatro tienen cambios en el hub
- **THEN** `fdh` propone actualizar los cuatro, agrupados por kind en el output

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

`fdh update` SHALL calcular un hash del contenido instalado al momento del update y SHALL compararlo contra el hash registrado en `.fdh-managed.yaml`; si no coincide, SHALL emitir un warning y SHALL saltarse ese componente salvo que el developer pase `--force`. Aplica a las cuatro primitivas.

#### Scenario: Edit manual detectado

- **WHEN** un developer editó manualmente `.claude/skills/design-system/SKILL.md` y luego corre `fdh update`
- **THEN** `fdh` imprime warning del tipo `"skill design-system has local modifications (skipping; use --force to overwrite)"`, no toca ese componente, y continúa con el resto

#### Scenario: Force overwrite

- **WHEN** se ejecuta `fdh update --force --skill design-system --yes` y el componente tiene edits locales
- **THEN** `fdh` sobreescribe los archivos locales con la versión del hub, refresca `.fdh-managed.yaml`, refresca el lock, y emite un mensaje confirmando el overwrite

#### Scenario: Edit manual en hook dentro de settings.json

- **WHEN** un developer editó la entry managed dentro de `.claude/settings.json` (cambió el `command` o el `matcher`)
- **THEN** `fdh update` detecta la divergencia comparando el hash de la entry contra el registrado en el `.fdh-managed.yaml` sibling y aplica la misma lógica de skip/--force

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

### Requirement: Filtro `--kind` para sincronización selectiva por primitiva

`fdh update` SHALL aceptar el flag repetible `--kind <skill|rule|agent|hook>` que limite la sincronización a los componentes del kind indicado; combinable con `--skill <name>`/`--agent <agent-name>`. Sin flag, sincroniza componentes de todos los kinds.

#### Scenario: Update sólo de rules

- **WHEN** se ejecuta `fdh update --kind rule --yes`
- **THEN** sólo se sincronizan componentes con `kind: rule` registrados en el lock; skills, agents y hooks se ignoran

#### Scenario: Combinación de filtros

- **WHEN** se ejecuta `fdh update --kind rule --kind hook --yes`
- **THEN** se sincronizan componentes con `kind: rule` o `kind: hook`; skills y agents se ignoran

### Requirement: Update sincroniza también el lock

`fdh update` SHALL escribir un `.fdh/lock.yaml` actualizado después de cada operación exitosa (no sólo refresca markers); el nuevo lock SHALL reflejar el `hub_commit` actual y los `integrity` hashes nuevos. Si todos los componentes se saltaron por `--dry-run` o por edits locales, el lock no se modifica.

#### Scenario: Lock refrescado tras update exitoso

- **WHEN** `fdh update --yes` actualiza exitosamente `design-system` y `no-console-log`
- **THEN** `.fdh/lock.yaml` se reescribe con el nuevo `hub_commit` y los `integrity` actualizados para ambos; el resto de entries del lock permanece igual

#### Scenario: Lock intacto en dry-run

- **WHEN** `fdh update --dry-run` lista cambios disponibles
- **THEN** `.fdh/lock.yaml` permanece byte-idéntico al estado pre-comando
