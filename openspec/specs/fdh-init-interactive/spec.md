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

### Requirement: Marcador `.skill-version` en cada skill instalada

Por cada skill copiada a un directorio target, `fdh init` SHALL escribir un archivo `.skill-version` (formato YAML) que registre `name`, `hub_version`, `hub_commit`, `installed_at` e `installed_by_fdh`, suficiente para que `fdh update` pueda detectar drift.

#### Scenario: Marcador escrito al instalar

- **WHEN** `fdh init` copia `design-system` a `.claude/skills/design-system/`
- **THEN** dentro de ese directorio existe `.skill-version` con los cinco campos poblados y valores no vacíos

#### Scenario: Marcador para skill flat (Copilot/OpenCode)

- **WHEN** `fdh init` instala `design-system` en Copilot como `.github/prompts/design-system.prompt.md`
- **THEN** se crea `.github/prompts/.skill-version-design-system` (un archivo de marcador por skill ya que no hay directorio propio) con los mismos campos

### Requirement: Re-ejecución de init detecta skills ya instaladas

Si `fdh init` se vuelve a ejecutar en un host que ya tiene skills instaladas, el wizard SHALL leer los `.skill-version` existentes y pre-tildar esos skills como ya seleccionados, permitiendo al developer agregar o quitar sin perder lo previo.

#### Scenario: Re-init con skills existentes

- **WHEN** un developer ya corrió init y tiene `design-system` y `code-review` instalados, y vuelve a correr `fdh init` en modo wizard
- **THEN** el wizard pre-tilda `design-system` y `code-review` (independiente de su flag `default`), reflejando el estado real del host

### Requirement: Compat con flujo `fdh init` existente

`fdh init` SHALL mantener compatibilidad total con su comportamiento previo: resolución de registry, scope, escritura de `config.yaml` y ejecución de doctor SHALL ocurrir antes del wizard; ninguna flag pre-existente SHALL cambiar de significado; la salida JSON existente (`InitResult`) SHALL extenderse sólo con campos adicionales opcionales.

#### Scenario: Init sin nuevas flags emite JSON compatible

- **WHEN** se ejecuta `fdh init --skip-doctor --json` sin flags nuevas
- **THEN** la salida JSON sigue conteniendo `config_path`, `applied`, `existing`, `doctor_ok`, `doctor_summary` como antes; los campos nuevos (`selected_agents`, `selected_skills`, `installed_skills`) están presentes pero pueden ser vacíos o ausentes según el flujo

#### Scenario: Init con `--registry-url` sigue funcionando

- **WHEN** se ejecuta `fdh init --registry-url https://otro.host/skills.git --skip-doctor --non-interactive`
- **THEN** registry se actualiza al valor pasado y no se invoca wizard, exactamente igual que en el flujo previo
