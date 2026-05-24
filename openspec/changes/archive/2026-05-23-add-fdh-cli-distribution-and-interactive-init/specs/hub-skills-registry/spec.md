*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## ADDED Requirements

### Requirement: Archivo `skills/registry.yaml` como catálogo autoritativo del hub

El hub SHALL contener un único archivo `skills/registry.yaml` en la raíz del directorio `skills/` que liste todos los skills disponibles, declare la metadata curada por el admin y sirva como única fuente de verdad para `fdh init` y `fdh update`.

#### Scenario: Estructura del archivo

- **WHEN** un admin abre `skills/registry.yaml`
- **THEN** encuentra los campos top-level `schema_version` (entero), `hub_version` (string semver/calver) y `skills` (lista), donde cada entry de `skills` tiene como mínimo `name`, `description`, `owner_team`, `tags`, `default`, `min_fdh_version`, `agents_supported` y `path`

#### Scenario: `name` unico y kebab-case

- **WHEN** dos entries en `skills` tienen el mismo `name`
- **THEN** la validación del registry falla con un error que identifica el duplicado por `name`

#### Scenario: `path` debe existir como directorio bajo `skills/`

- **WHEN** un entry declara `path: skills/foo` y el directorio `skills/foo/` no existe
- **THEN** la validación del registry falla nombrando explícitamente la entry y la ruta faltante

#### Scenario: Cada `skills/<name>/` debe tener entry en el registry

- **WHEN** existe `skills/bar/` pero no hay entry con `path: skills/bar` (ni `name: bar`)
- **THEN** la validación del registry falla nombrando el directorio huérfano

### Requirement: Bandera `default` controlada exclusivamente por `registry.yaml`

La bandera `default: true|false` por skill SHALL ser determinada únicamente por `registry.yaml`; cualquier valor `default` declarado en el frontmatter de `skills/<name>/SKILL.md` SHALL ser ignorado por `fdh init` y `fdh update`.

#### Scenario: Default sólo lo decide el admin

- **WHEN** `registry.yaml` declara `design-system` con `default: false` y `skills/design-system/SKILL.md` tiene en frontmatter `default: true`
- **THEN** `fdh init` no pre-tilda `design-system` en el wizard; el frontmatter del SKILL.md no influye

#### Scenario: Cambiar defaults es un commit de una línea

- **WHEN** un admin cambia `default: false` a `default: true` para `security-owasp` en `registry.yaml` y mergea
- **THEN** la próxima ejecución de `fdh init` (modo wizard o no interactivo con defaults) pre-tilda/incluye `security-owasp` sin requerir cambios en `skills/security-owasp/`

### Requirement: `agents_supported` declara compatibilidad por ecosistema

Cada entry en `registry.yaml` SHALL declarar `agents_supported` como una lista no vacía con un subconjunto de `[claude-code, codex, copilot, opencode]`; los agentes no listados SHALL ser excluidos al instalar esa skill.

#### Scenario: Skill compatible con todos

- **WHEN** una entry declara `agents_supported: [claude-code, codex, copilot, opencode]`
- **THEN** `fdh init` ofrece esa skill para los cuatro ecosistemas seleccionados

#### Scenario: Skill compatible parcialmente

- **WHEN** una entry declara `agents_supported: [claude-code, copilot]` y el developer seleccionó OpenCode
- **THEN** esa skill no aparece en el wizard ni se instala vía flag para OpenCode, con un mensaje que explica la razón si fue pedida explícitamente vía `--skills`

#### Scenario: Lista vacía es inválida

- **WHEN** una entry declara `agents_supported: []`
- **THEN** la validación del registry falla pidiendo al menos un agente

### Requirement: `min_fdh_version` valida compatibilidad de CLI

Cada entry SHALL declarar `min_fdh_version` (semver); si la versión instalada de `fdh` es menor, `fdh init` y `fdh update` SHALL rechazar instalar esa skill y SHALL sugerir `fdh upgrade`.

#### Scenario: CLI demasiado viejo

- **WHEN** el developer corre `fdh 0.3.0` y un skill declara `min_fdh_version: 0.4.0`
- **THEN** ese skill no aparece como instalable, y si es default, `fdh` emite warning con el mensaje `"skill <name> requires fdh >= 0.4.0; current is 0.3.0 — run 'fdh upgrade' to enable"`

#### Scenario: CLI compatible

- **WHEN** el developer corre `fdh 0.5.0` y un skill declara `min_fdh_version: 0.4.0`
- **THEN** ese skill es instalable normalmente

### Requirement: Validación en CI del hub bloquea merges con registry inválido

El hub SHALL ejecutar en CI una validación del `registry.yaml` (vía `fdh validate-registry` o equivalente) que bloquee el merge de cualquier PR donde el registry no satisfaga las reglas: nombres únicos, paths existentes, directorios huérfanos detectados, schema_version reconocido, listas no vacías donde corresponde.

#### Scenario: PR con duplicado

- **WHEN** un PR introduce un `registry.yaml` con dos entries con `name: design-system`
- **THEN** el CI del hub falla con un error específico nombrando el duplicado, y el merge queda bloqueado

#### Scenario: PR con directorio huérfano

- **WHEN** un PR agrega `skills/new-skill/` pero olvida agregar el entry correspondiente en `registry.yaml`
- **THEN** el CI del hub falla nombrando el directorio huérfano, y el merge queda bloqueado

#### Scenario: PR con entry sin directorio

- **WHEN** un PR agrega un entry para `name: ghost` pero no crea `skills/ghost/`
- **THEN** el CI del hub falla nombrando la entry sin path real, y el merge queda bloqueado

### Requirement: `registry.yaml` documenta su propio formato vía comentarios

El archivo `skills/registry.yaml` SHALL incluir comentarios YAML al inicio del archivo que documenten brevemente cada campo top-level y cada campo de las entries de `skills`, para que un admin nuevo pueda editar sin documentación externa.

#### Scenario: Admin nuevo abre el registry

- **WHEN** un admin sin contexto previo abre `skills/registry.yaml`
- **THEN** encuentra al inicio del archivo y/o cerca de cada campo, comentarios que explican el propósito de `schema_version`, `hub_version`, `default`, `min_fdh_version`, `agents_supported`, `path` y `owner_team`

### Requirement: Registro inicial contiene al menos `design-system`

Al hacer apply de este change, `skills/registry.yaml` SHALL contener al menos una entry para `design-system` apuntando a `skills/design-system/` (creado por el change `add-design-system-skill`), de modo que el catálogo no esté vacío desde el primer commit.

#### Scenario: Registry inicial post-apply

- **WHEN** el apply de este change termina
- **THEN** `skills/registry.yaml` existe y contiene una entry `design-system` con todos los campos requeridos poblados; el resto del archivo puede contener placeholders comentados para entries futuras
