## ADDED Requirements

### Requirement: Marker `.fdh-managed.yaml` por directorio instalado

Por cada componente instalado en un directorio target, `fdh install` SHALL escribir un archivo `.fdh-managed.yaml` dentro del directorio con campos: `name`, `kind`, `version`, `hub_commit`, `installed_at`, `installed_by_fdh`, `source_path` (path del componente en el hub). Para componentes que se materializan como archivo único (no directorio), el marker SHALL escribirse como `<file>.fdh-managed.yaml` sibling.

#### Scenario: Marker en directorio managed

- **WHEN** `fdh install` materializa `design-system` en `.claude/skills/design-system/`
- **THEN** existe `.claude/skills/design-system/.fdh-managed.yaml` con los siete campos poblados

#### Scenario: Marker para archivo único

- **WHEN** `fdh install` materializa una rule en Copilot como `.github/rules/no-console-log.md`
- **THEN** existe `.github/rules/no-console-log.md.fdh-managed.yaml` con los mismos campos

### Requirement: Marker rebautiza al `.skill-version` legacy

`fdh` SHALL reconocer el marker legacy `.skill-version` (introducido por `add-fdh-cli-distribution-and-interactive-init`) como equivalente al nuevo `.fdh-managed.yaml` durante una ventana de migración. La primera ejecución de `fdh install` o `fdh update` sobre un directorio con marker legacy SHALL migrarlo al formato nuevo preservando los valores.

#### Scenario: Migración silenciosa del marker legacy

- **WHEN** un dev del pilot tiene `.claude/skills/design-system/.skill-version` y corre `fdh install`
- **THEN** después de la operación existe `.fdh-managed.yaml` con campos equivalentes (más `kind: skill`, `source_path: skills/design-system`) y el `.skill-version` ha sido removido

### Requirement: `.gitignore` sectionado e idempotente

`fdh install` SHALL gestionar una sección del `.gitignore` del consumer delimitada por markers `# >>> fdh:managed-paths >>>` y `# <<< fdh:managed-paths <<<`; SHALL listar dentro de esa sección únicamente los paths managed por fdh; SHALL preservar todo contenido fuera de la sección sin modificar; SHALL ser idempotente (re-ejecuciones producen el mismo resultado).

#### Scenario: Primera ejecución crea la sección

- **WHEN** un repo sin sección managed corre `fdh install` por primera vez
- **THEN** el `.gitignore` final contiene los markers de apertura/cierre, las rutas managed listadas, y el resto del archivo (entries del developer) intacto

#### Scenario: Re-ejecución preserva entries externas

- **WHEN** el developer agregó manualmente `dist/` y `node_modules/` fuera de la sección managed y luego corre `fdh install` de nuevo
- **THEN** la sección managed se actualiza si hay cambios, pero `dist/` y `node_modules/` permanecen sin modificar

#### Scenario: Sin .gitignore previo

- **WHEN** `fdh install` corre en un repo sin `.gitignore`
- **THEN** se crea el archivo con sólo la sección managed

#### Scenario: Uninstall remueve entries de la sección

- **WHEN** `fdh uninstall design-system` se ejecuta
- **THEN** las entries correspondientes a `design-system` desaparecen de la sección managed; si la sección queda vacía, los markers también se remueven

### Requirement: Detección de drift entre state, marker y disco

`fdh doctor` SHALL reportar drift entre las tres fuentes de verdad sobre componentes instalados: (a) `state.json` dice que está instalado pero falta el directorio o el marker; (b) marker existe pero no está en state; (c) directorio existe sin marker (instalado a mano); (d) hash del marker no coincide con el contenido (edits manuales).

#### Scenario: State dice instalado, disco no

- **WHEN** `state.json` referencia `~/work/x/.claude/skills/design-system/` pero el directorio no existe
- **THEN** `fdh doctor` reporta "state references missing path" con la ruta y sugiere `fdh repair`

#### Scenario: Directorio sin marker

- **WHEN** existe `.claude/skills/handwritten/` sin `.fdh-managed.yaml`
- **THEN** `fdh doctor` lo lista como "user-managed (not touched by fdh)" — informativo, no error

#### Scenario: Edit manual detectado

- **WHEN** el contenido del directorio managed cambió desde el install (hash recalculado ≠ hash registrado)
- **THEN** `fdh doctor` reporta "local modifications detected" con la lista de archivos modificados; `fdh update` sin `--force` salta este componente

### Requirement: Componentes manualmente escritos por el developer son intocables

`fdh` SHALL nunca modificar directorios o archivos bajo `.claude/`, `.codex/`, `.github/`, `.opencode/` que no tengan un marker `.fdh-managed.yaml` propio. La ausencia del marker SHALL ser tratada como propiedad del developer.

#### Scenario: Skill handwritten coexiste con managed

- **WHEN** el developer tiene `.claude/skills/my-personal/SKILL.md` (sin marker) y `fdh install` materializa `design-system` (con marker)
- **THEN** `my-personal/` permanece intacto; `fdh update` y `fdh uninstall` jamás lo tocan
