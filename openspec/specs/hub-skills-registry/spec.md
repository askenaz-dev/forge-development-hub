# hub-skills-registry Specification

## Purpose

Catálogo autoritativo del hub (hub/registry.yaml, schema v2) listando componentes de las cuatro primitivas (skills, rules, agents, hooks) discriminados por `kind`. Cubre: schema y campos requeridos, validación en CI (kind ↔ directorio, paths existentes, huérfanos, profiles), default flag controlado por admin, agents_supported, min_fdh_version, registro inicial mínimo, obligatoriedad de `kind`. El archivo legacy `skills/registry.yaml` se mantiene como mirror generado por 60 días post `hub-v2-manifest-state-profiles`.

## Requirements

### Requirement: Archivo `skills/registry.yaml` como catálogo autoritativo del hub

El hub SHALL contener un único archivo de catálogo en la raíz que liste todos los componentes distribuibles (skills, rules, agents, hooks), declare la metadata curada por el admin y sirva como única fuente de verdad para `fdh init`, `fdh install` y `fdh update`. La ubicación final del archivo (`skills/registry.yaml` actual vs `hub/registry.yaml` nuevo) se determina en `design.md` del change `hub-v2-manifest-state-profiles`; ambas ubicaciones SHALL ser soportadas durante una ventana de migración con redirect/symlink.

#### Scenario: Estructura del archivo v2

- **WHEN** un admin abre el catálogo del hub
- **THEN** encuentra los campos top-level `schema_version: 2`, `hub_version` (string semver/calver) y una lista de entries donde cada entry tiene como mínimo `name`, `kind` (`skill | rule | agent | hook`), `description`, `owner_team`, `tags`, `default`, `min_fdh_version`, `agents_supported` y `path`

#### Scenario: `name` único dentro del mismo `kind`

- **WHEN** dos entries en el catálogo tienen el mismo `name` y el mismo `kind`
- **THEN** la validación del registry falla con un error que identifica el duplicado por `<kind>:<name>`

#### Scenario: `path` debe existir como directorio bajo el dir correcto del kind

- **WHEN** un entry declara `kind: rule, name: foo, path: rules/foo` y el directorio `rules/foo/` no existe
- **THEN** la validación del registry falla nombrando explícitamente la entry y la ruta faltante

#### Scenario: Cada `<kind-dir>/<name>/` debe tener entry en el registry

- **WHEN** existe `rules/bar/` pero no hay entry con `kind: rule, path: rules/bar`
- **THEN** la validación del registry falla nombrando el directorio huérfano y su kind esperado

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

El hub SHALL ejecutar en CI una validación del catálogo (vía `fdh validate-registry` o `tools/validate-registry.py` durante migración) que bloquee el merge de cualquier PR donde el catálogo no satisfaga las reglas: nombres únicos por kind, paths existentes y coherentes con el kind, directorios huérfanos detectados en los cuatro dirs (`skills/`, `rules/`, `agents/`, `hooks/`), `schema_version` reconocido, listas no vacías donde corresponde, y validez de profiles referenciados desde `hub/profiles.yaml`.

#### Scenario: PR con duplicado dentro de un kind

- **WHEN** un PR introduce un catálogo con dos entries `kind: skill, name: design-system`
- **THEN** el CI del hub falla con un error específico nombrando el duplicado `skill:design-system`, y el merge queda bloqueado

#### Scenario: PR con directorio huérfano en cualquiera de los 4 dirs

- **WHEN** un PR agrega `hooks/orphan/` pero olvida agregar el entry correspondiente en el catálogo
- **THEN** el CI del hub falla nombrando el directorio huérfano y su kind esperado (`hook`), y el merge queda bloqueado

#### Scenario: PR con entry sin directorio

- **WHEN** un PR agrega un entry `kind: agent, name: ghost, path: agents/ghost` pero no crea `agents/ghost/`
- **THEN** el CI del hub falla nombrando la entry sin path real, y el merge queda bloqueado

#### Scenario: PR con profile referenciando componente inexistente

- **WHEN** un PR agrega un profile que referencia `rules: [phantom]` pero no existe esa rule
- **THEN** el CI del hub falla nombrando el profile, el componente faltante y el kind esperado

### Requirement: `registry.yaml` documenta su propio formato vía comentarios

El archivo `skills/registry.yaml` SHALL incluir comentarios YAML al inicio del archivo que documenten brevemente cada campo top-level y cada campo de las entries de `skills`, para que un admin nuevo pueda editar sin documentación externa.

#### Scenario: Admin nuevo abre el registry

- **WHEN** un admin sin contexto previo abre `skills/registry.yaml`
- **THEN** encuentra al inicio del archivo y/o cerca de cada campo, comentarios que explican el propósito de `schema_version`, `hub_version`, `default`, `min_fdh_version`, `agents_supported`, `path` y `owner_team`

### Requirement: Registro inicial contiene al menos un componente de cada kind

Al hacer apply del change `hub-v2-manifest-state-profiles`, el catálogo SHALL contener al menos una entry por cada kind: una entry para `design-system` (skill, existente), una para `no-console-log` (rule, nueva), una para `falabella-pr-writer` (agent, nueva), una para `doctor-on-session-start` (hook, nueva). El profile `minimal` en `hub/profiles.yaml` SHALL referenciar las cuatro.

#### Scenario: Registry inicial post-apply

- **WHEN** el apply del change termina
- **THEN** el catálogo contiene cuatro entries (una por kind) con todos los campos requeridos poblados; cada entry apunta a un `path` que existe; `hub/profiles.yaml` contiene `profiles.minimal` referenciando las cuatro

### Requirement: Campo `kind` obligatorio en cada entry del catálogo

Toda entry en el catálogo SHALL declarar `kind` con uno de los valores `skill | rule | agent | hook`. Entries sin `kind` SHALL ser rechazadas por la validación; no hay defaulting silencioso a `skill` para forzar la decisión consciente del admin.

#### Scenario: Entry sin kind es rechazada

- **WHEN** un PR introduce una entry sin campo `kind`
- **THEN** la validación falla con error nombrando la entry y exigiendo `kind` explícito
