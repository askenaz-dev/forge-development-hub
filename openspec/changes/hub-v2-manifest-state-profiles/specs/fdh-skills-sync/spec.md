## MODIFIED Requirements

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

## ADDED Requirements

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
