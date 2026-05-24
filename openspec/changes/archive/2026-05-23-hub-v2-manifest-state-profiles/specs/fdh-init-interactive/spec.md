*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## MODIFIED Requirements

### Requirement: Marcador `.fdh-managed.yaml` en cada componente instalado

Por cada componente copiado a un directorio target, `fdh init` (y `fdh install`) SHALL escribir un archivo `.fdh-managed.yaml` (formato YAML) que registre `name`, `kind`, `version`, `hub_commit`, `installed_at`, `installed_by_fdh` y `source_path`, suficiente para que `fdh update`, `fdh doctor` y `fdh repair` puedan detectar drift. Para componentes materializados como archivo único (Copilot prompts, OpenCode commands, agent files), el marker se escribe como `<file>.fdh-managed.yaml` sibling. Este marker REEMPLAZA al `.skill-version` legacy.

#### Scenario: Marker escrito al instalar (directorio)

- **WHEN** `fdh init` copia `design-system` a `.claude/skills/design-system/`
- **THEN** dentro de ese directorio existe `.fdh-managed.yaml` con los siete campos poblados y valores no vacíos

#### Scenario: Marker para componente flat

- **WHEN** `fdh init` instala una rule en Copilot como `.github/rules/no-console-log.md`
- **THEN** se crea `.github/rules/no-console-log.md.fdh-managed.yaml` sibling, con los mismos campos

#### Scenario: Migración silenciosa desde legacy `.skill-version`

- **WHEN** un dev del pilot tiene `.claude/skills/design-system/.skill-version` legacy y corre `fdh init` o `fdh install`
- **THEN** el comando migra el marker a `.fdh-managed.yaml` preservando los campos comunes y agregando `kind: skill` + `source_path: skills/design-system`; el archivo `.skill-version` queda removido

### Requirement: Re-ejecución de init lee del manifest, no de markers

Si `fdh init` se vuelve a ejecutar en un repo que ya tiene `.fdh/manifest.yaml`, el wizard SHALL leer el manifest como fuente de verdad y SHALL pre-tildar los componentes ya declarados ahí; los markers `.fdh-managed.yaml` en disco se usan sólo para drift detection en `fdh doctor`, no para repoblar la selección del wizard.

#### Scenario: Re-init con manifest existente

- **WHEN** un developer ya corrió init y tiene `.fdh/manifest.yaml` declarando `profile: minimal` + `extends: { add_skills: [i18n-helper] }`, y vuelve a correr `fdh init` en modo wizard
- **THEN** el wizard pre-tilda el profile `minimal` + agrega `i18n-helper` como ya seleccionado, reflejando exactamente lo que el manifest declara; cualquier divergencia entre manifest y markers se reporta como warning con sugerencia de `fdh doctor`

#### Scenario: Re-init sin manifest pero con markers legacy

- **WHEN** un developer tiene markers (legacy o nuevos) pero no tiene `.fdh/manifest.yaml`
- **THEN** `fdh init` infiere el manifest desde los markers, lo presenta como propuesta para confirmación, escribe `.fdh/manifest.yaml` y `.fdh/lock.yaml`, y a partir de ahí trata el manifest como fuente de verdad

### Requirement: Compat con flujo `fdh init` existente extendido para manifest/lock/state

`fdh init` SHALL mantener compatibilidad total con su comportamiento previo: resolución de registry, scope, escritura de `config.yaml` y ejecución de doctor SHALL ocurrir antes del wizard; ninguna flag pre-existente SHALL cambiar de significado; la salida JSON existente (`InitResult`) SHALL extenderse con campos opcionales `manifest_path`, `lock_path`, `state_path` y `selected_components` (agrupado por kind). Adicionalmente `fdh init` SHALL escribir/actualizar `.fdh/manifest.yaml`, disparar la resolución que produce `.fdh/lock.yaml`, y registrar/actualizar la entry del proyecto en `~/.fdh/state.json`.

#### Scenario: Init sin nuevas flags emite JSON compatible

- **WHEN** se ejecuta `fdh init --skip-doctor --json` sin flags nuevas
- **THEN** la salida JSON sigue conteniendo `config_path`, `applied`, `existing`, `doctor_ok`, `doctor_summary` como antes; los campos nuevos (`manifest_path`, `lock_path`, `state_path`, `selected_components`) están presentes con valores poblados o vacíos según el flujo

#### Scenario: Init persiste manifest, lock y state

- **WHEN** un developer completa exitosamente `fdh init` con selección de profile `minimal`
- **THEN** después del comando existen `.fdh/manifest.yaml` (con `profile: minimal`), `.fdh/lock.yaml` (con la lista expandida resuelta) y `~/.fdh/state.json` (con la entry del proyecto actual bajo `projects:`)

## ADDED Requirements

### Requirement: Wizard ofrece selección de profile además de componentes individuales

El wizard SHALL ofrecer como primer step de selección (después de detección de agentes) la elección de un profile del hub (`hub/profiles.yaml`), con opciones `(none)` (selección 100% manual), `minimal` y demás profiles disponibles. Tras elegir profile, los steps siguientes SHALL presentar los componentes del profile pre-tildados + lista de extras desplegable agrupada por kind (`Skills`, `Rules`, `Agents`, `Hooks`).

#### Scenario: Selección con profile

- **WHEN** el developer elige `profile: minimal` y confirma sin agregar extras ni remover nada
- **THEN** el manifest resultante declara `profile: minimal` sin bloque `extends`

#### Scenario: Selección con profile + extras

- **WHEN** el developer elige `profile: minimal`, agrega un skill `i18n-helper` desde Extras, y destilda la rule `no-console-log`
- **THEN** el manifest resultante declara `profile: minimal` + `extends: { add_skills: [i18n-helper], remove_rules: [no-console-log] }`

#### Scenario: Selección sin profile

- **WHEN** el developer elige `(none)` y arma su lista a mano (selección de componentes individuales)
- **THEN** el manifest resultante NO declara `profile:` y en su lugar lista explícitamente `skills:`, `rules:`, etc., según selección
