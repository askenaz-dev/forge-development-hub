## ADDED Requirements

### Requirement: Formato de `hooks/<name>/HOOK.md` + `hook.json`

El hub SHALL distribuir hooks como directorios `hooks/<name>/` que contengan dos archivos: `HOOK.md` con documentación humana del propósito + cuándo aplicar + ejemplo, y `hook.json` con la configuración ejecutable que `fdh install` materializa al settings del agente. El `hook.json` SHALL declarar al menos `event`, `matcher` (string o regex), `command`, y opcionalmente `profile`, `timeout_seconds` y `description`.

#### Scenario: hook.json válido

- **WHEN** un admin abre `hooks/doctor-on-session-start/hook.json`
- **THEN** encuentra `event: "SessionStart"`, `matcher: "*"`, `command: "fdh doctor --quiet"`, `description: "..."`

#### Scenario: Event inválido

- **WHEN** un `hook.json` declara `event: "OnFileSave"` (no en la lista soportada)
- **THEN** la validación falla nombrando los eventos soportados (`SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`)

### Requirement: Materialización como bloque managed en `settings.json` del agente

`fdh install` SHALL materializar cada hook seleccionado escribiéndolo como entry dentro de la sección apropiada de `.claude/settings.json` (o equivalente per-agente cuando soporten hooks), agregando el marker `_fdh_managed: <name>` a la entry para permitir uninstall selectivo. `fdh install` SHALL preservar entries pre-existentes del developer en el mismo archivo.

#### Scenario: Hook agregado a settings.json existente

- **WHEN** el developer tiene `.claude/settings.json` con su propio hook PreToolUse, y `fdh install` materializa `doctor-on-session-start`
- **THEN** el archivo final contiene tanto el hook pre-existente del developer como una entry SessionStart con `_fdh_managed: "doctor-on-session-start"`, sin perder ninguno

#### Scenario: Settings.json no existe

- **WHEN** `fdh install` materializa un hook y `.claude/settings.json` no existe
- **THEN** `fdh` crea el archivo con la estructura mínima necesaria y la entry managed

#### Scenario: Uninstall selectivo

- **WHEN** `fdh uninstall doctor-on-session-start` corre y settings.json contiene entries managed + entries del developer
- **THEN** sólo se remueven las entries con marker `_fdh_managed: "doctor-on-session-start"`; entries del developer quedan intactas

### Requirement: Primera entry real `hooks/doctor-on-session-start/`

Como parte del apply de este change, el hub SHALL contener `hooks/doctor-on-session-start/` con `HOOK.md` (documentando propósito y configuración) y `hook.json` con `event: "SessionStart"`, `matcher: "*"`, `command: "fdh doctor --quiet"`, listo para ser materializado por `fdh install`.

#### Scenario: Hook shipped post-apply

- **WHEN** termina el apply del change
- **THEN** existen `hooks/doctor-on-session-start/HOOK.md` y `hooks/doctor-on-session-start/hook.json` con los valores mencionados, y el catálogo registra una entry con `kind: hook, name: doctor-on-session-start`

#### Scenario: Hook referenciado desde profile minimal

- **WHEN** se inspecciona `hub/profiles.yaml` después del apply
- **THEN** el profile `minimal` incluye `hooks: [doctor-on-session-start]`

### Requirement: La ejecución del hook es responsabilidad del agente, no de FDH

`fdh install` SHALL únicamente materializar la configuración del hook en el settings del agente; la ejecución del comando configurado SHALL ser disparada por el agente (Claude Code, etc.) en el evento correspondiente. FDH NO SHALL implementar un runtime propio de hooks en este change.

#### Scenario: Hook ejecutado por Claude Code

- **WHEN** un developer abre Claude Code en un proyecto con `doctor-on-session-start` instalado
- **THEN** Claude Code lee su `settings.json`, detecta el hook `SessionStart`, y ejecuta `fdh doctor --quiet` al iniciar la sesión, sin involucramiento de `fdh` en el disparo
