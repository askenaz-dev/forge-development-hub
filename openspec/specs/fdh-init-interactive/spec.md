# fdh-init-interactive Specification

## Purpose

Wizard TTY de fdh init: detecta agentes, prompt de selección con defaults pre-tildados del catalogo, copia adapters per ecosistema, marcador .skill-version. Modo no-interactivo con --agents/--skills/--no-defaults/--dry-run para CI.

## Requirements

### Requirement: Detección de TTY decide modo wizard vs no interactivo

El comando `fdh init` SHALL evaluar si stdin es un TTY y si se pasaron flags que resuelvan agentes o skills, y SHALL entrar en modo wizard sólo cuando stdin es TTY y no se pasaron `--agents`, `--skills` ni `--non-interactive`; en caso contrario SHALL ejecutar en modo no interactivo.

#### Scenario: TTY sin flags entra a wizard

- **WHEN** un developer ejecuta `fdh init` en una terminal interactiva sin pasar `--agents` ni `--skills`
- **THEN** `fdh init` configura registry+scope+doctor como hasta ahora y luego abre el wizard de selección de agentes/skills

#### Scenario: CI sin TTY usa modo no interactivo

- **WHEN** `fdh init` se invoca con stdin redirigido (pipe, archivo, CI runner sin TTY)
- **THEN** `fdh init` no abre wizard, usa flags pasadas y defaults del catálogo, y termina sin pedir input

#### Scenario: `--non-interactive` fuerza modo no interactivo en TTY

- **WHEN** un developer ejecuta `fdh init --non-interactive` en una terminal interactiva
- **THEN** `fdh init` no abre wizard, usa flags + defaults, y termina sin pedir input

### Requirement: Detección de agentes IA instalados en el host

El wizard SHALL detectar qué agentes IA están instalados en el host (Claude Code, Codex, Copilot, OpenCode) usando las mismas heurísticas que `fdh doctor` y SHALL mostrarlos pre-tildados; los agentes soportados pero no detectados SHALL aparecer en la lista sin pre-tildar.

#### Scenario: Mostrar detectados y no detectados

- **WHEN** el host tiene Claude Code y Copilot instalados, pero no Codex ni OpenCode
- **THEN** el wizard muestra los cuatro agentes; Claude Code y Copilot aparecen pre-tildados (`[x]`), Codex y OpenCode aparecen sin tildar (`[ ]`), y cada línea indica `detected` o `not detected`

#### Scenario: El developer destilda un agente detectado

- **WHEN** un developer destilda un agente pre-tildado (ej.: no quiere instalar nada en Copilot)
- **THEN** ese agente queda excluido del set final y no recibe ninguna copia de skills

#### Scenario: El developer tilda un agente no detectado

- **WHEN** un developer tilda un agente no detectado y confirma
- **THEN** el wizard advierte que el agente no fue detectado y pregunta si continuar; si confirma, se instala igualmente (creando los directorios convencionales)

### Requirement: Selección de skills sobre catálogo del hub con sección de defaults

El wizard SHALL leer `skills/registry.yaml` del hub configurado en `registry.url`, SHALL mostrar dos grupos visualmente separados ("Defaults" y "Extras") donde los skills con `default: true` aparecen pre-tildados en Defaults y los demás aparecen sin tildar en Extras, y SHALL permitir tildar/destildar cualquiera de los dos grupos.

#### Scenario: Defaults pre-tildados

- **WHEN** el wizard carga el catálogo y `registry.yaml` marca `design-system` y `code-review` con `default: true`
- **THEN** el wizard muestra una sección "Defaults" con ambos skills pre-tildados y una sección "Extras" con el resto sin tildar

#### Scenario: Destildar un default

- **WHEN** un developer destilda `code-review` y confirma
- **THEN** `code-review` queda excluido del set final aunque sea default

#### Scenario: Agregar un extra

- **WHEN** un developer tilda `security-owasp` (que es extra) y confirma
- **THEN** `security-owasp` se agrega al set final

#### Scenario: Filtro por agentes seleccionados

- **WHEN** el developer seleccionó sólo Codex y un skill del catálogo declara `agents_supported: [claude-code]`
- **THEN** ese skill no aparece en la lista del wizard (ni en Defaults ni en Extras)

### Requirement: Pantalla de resumen y confirmación antes de copiar

El wizard SHALL mostrar una pantalla de resumen final que liste agentes elegidos, skills elegidas y las rutas destino exactas, y SHALL pedir confirmación `[Y/n]` antes de modificar el filesystem.

#### Scenario: Confirmación afirmativa

- **WHEN** el developer confirma el resumen con `Y` (o Enter)
- **THEN** `fdh init` copia cada skill al directorio target de cada agente y actualiza los marcadores `.skill-version`

#### Scenario: Cancelación

- **WHEN** el developer responde `n` al resumen
- **THEN** `fdh init` sale con código cero sin tocar el filesystem y sin escribir nada más allá del `config.yaml` ya persistido por el flujo init existente

### Requirement: Flags de modo no interactivo

El comando `fdh init` SHALL aceptar las flags `--agents`, `--skills`, `--no-defaults` y `--dry-run` con la siguiente semántica:

- `--agents <csv>` lista de agentes a activar; valor especial `auto` = detectados, `all` = todos los soportados.
- `--skills <csv>` con sintaxis `name`, `+name` (add) o `-name` (remove).
- `--no-defaults` excluye los skills `default: true` del set base.
- `--dry-run` imprime el plan resuelto y sale sin tocar filesystem.

#### Scenario: `--agents` y `--skills` explícitos

- **WHEN** un developer ejecuta `fdh init --agents claude-code --skills design-system,code-review --non-interactive`
- **THEN** se instalan `design-system` y `code-review` en Claude Code únicamente, sin prompt

#### Scenario: `--skills` con add y remove

- **WHEN** se ejecuta `fdh init --skills +security-owasp,-code-review --non-interactive` y los defaults son `design-system` y `code-review`
- **THEN** el set final es `design-system` + `security-owasp` (code-review fue removido)

#### Scenario: `--no-defaults` sin `+skills`

- **WHEN** se ejecuta `fdh init --no-defaults --non-interactive`
- **THEN** `fdh init` no instala ningún skill y termina con código cero y un mensaje claro

#### Scenario: `--dry-run`

- **WHEN** se ejecuta `fdh init --dry-run` con cualquier combinación de flags
- **THEN** se imprime el plan completo (agentes, skills, rutas target, archivos a crear) y `fdh` sale con código cero sin escribir nada al filesystem

### Requirement: Adaptación de SKILL.md per ecosistema target

`fdh init` SHALL copiar `skills/<name>/` al directorio target de cada agente seleccionado aplicando la transformación mínima requerida por el ecosistema: copia literal del directorio para Claude Code y Codex, conversión a `<name>.prompt.md` para Copilot, conversión a `commands/<name>.md` para OpenCode.

#### Scenario: Instalación en Claude Code

- **WHEN** se selecciona `design-system` para Claude Code en scope project
- **THEN** `fdh` copia `skills/design-system/` completo (incluyendo `references/`, `scripts/`, `.ds-version`) a `<cwd>/.claude/skills/design-system/`

#### Scenario: Instalación en Copilot

- **WHEN** se selecciona `design-system` para Copilot en scope project
- **THEN** `fdh` lee `skills/design-system/SKILL.md`, escribe `<cwd>/.github/prompts/design-system.prompt.md` con el cuerpo del SKILL.md adaptado al formato Copilot, e imprime un warning nombrando los sub-recursos no portados (`references/`, `scripts/`)

#### Scenario: Skill con `agents_supported` restringido

- **WHEN** un skill tiene `agents_supported: [claude-code, codex]` y el developer eligió Copilot
- **THEN** ese skill no se instala para Copilot, y `fdh` imprime una nota indicando el skip y la razón

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
