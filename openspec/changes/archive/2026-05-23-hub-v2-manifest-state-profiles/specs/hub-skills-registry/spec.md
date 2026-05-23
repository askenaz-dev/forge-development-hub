## MODIFIED Requirements

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

### Requirement: Registro inicial contiene al menos un componente de cada kind

Al hacer apply del change `hub-v2-manifest-state-profiles`, el catálogo SHALL contener al menos una entry por cada kind: una entry para `design-system` (skill, existente), una para `no-console-log` (rule, nueva), una para `falabella-pr-writer` (agent, nueva), una para `doctor-on-session-start` (hook, nueva). El profile `minimal` en `hub/profiles.yaml` SHALL referenciar las cuatro.

#### Scenario: Registry inicial post-apply

- **WHEN** el apply del change termina
- **THEN** el catálogo contiene cuatro entries (una por kind) con todos los campos requeridos poblados; cada entry apunta a un `path` que existe; `hub/profiles.yaml` contiene `profiles.minimal` referenciando las cuatro

## ADDED Requirements

### Requirement: Campo `kind` obligatorio en cada entry del catálogo

Toda entry en el catálogo SHALL declarar `kind` con uno de los valores `skill | rule | agent | hook`. Entries sin `kind` SHALL ser rechazadas por la validación; no hay defaulting silencioso a `skill` para forzar la decisión consciente del admin.

#### Scenario: Entry sin kind es rechazada

- **WHEN** un PR introduce una entry sin campo `kind`
- **THEN** la validación falla con error nombrando la entry y exigiendo `kind` explícito
