# hub-profiles Specification

## Purpose

Define el archivo `hub/profiles.yaml` con bundles curados que referencian componentes del catálogo del hub agrupados por kind (`skills`, `rules`, `agents`, `hooks`), y especifica la semántica de cómo un consumer manifest los referencia, extiende y resuelve. El profile `minimal` ship as parte del apply de este change ejercita las cuatro primitivas end-to-end; el lock del consumer registra la lista expandida resuelta —no la referencia al profile— para garantizar reproducibilidad aunque el profile cambie en el hub.

## Requirements

### Requirement: Archivo `hub/profiles.yaml` declara bundles curados

El hub SHALL contener un archivo `hub/profiles.yaml` (ubicación final confirmada en design) que defina bundles curados ("profiles") referenciando componentes del catálogo. Cada profile SHALL listar componentes por su `kind` (`skills:`, `rules:`, `agents:`, `hooks:`) con sus `name` y SHALL declarar `description` y `owner_team`.

#### Scenario: Estructura mínima de un profile

- **WHEN** un admin abre `hub/profiles.yaml`
- **THEN** encuentra una clave top-level `profiles:` cuyo contenido es un mapa `<profile-name>: { description, owner_team, skills?, rules?, agents?, hooks? }`, donde al menos una de las listas de componentes es no vacía

#### Scenario: Profile referencia componentes válidos

- **WHEN** un profile lista `rules: [no-console-log]` y el catálogo del hub contiene una entry `kind: rule, name: no-console-log`
- **THEN** la validación acepta el profile

#### Scenario: Profile referencia componente inexistente

- **WHEN** un profile lista `skills: [phantom-skill]` pero el catálogo no tiene esa entry
- **THEN** la validación falla nombrando el profile, el componente faltante y el kind esperado

### Requirement: Profile `minimal` ejercita las cuatro primitivas

Como parte del apply de este change, `hub/profiles.yaml` SHALL contener un profile llamado `minimal` que referencie al menos un componente de cada primitiva (`skills: [design-system]`, `rules: [no-console-log]`, `agents: [falabella-pr-writer]`, `hooks: [doctor-on-session-start]`), sirviendo como ejemplo end-to-end y caso de prueba del schema.

#### Scenario: Profile minimal completo post-apply

- **WHEN** termina el apply del change
- **THEN** existe `profiles.minimal` con las cuatro listas pobladas con al menos un componente cada una

### Requirement: Consumer manifest referencia un profile por nombre

El `.fdh/manifest.yaml` del consumer SHALL permitir referenciar un profile mediante el campo `profile: <name>`; al instalar, `fdh` SHALL resolver el profile expandiendo la lista de componentes desde `hub/profiles.yaml` y registrando el resultado expandido en `.fdh/lock.yaml`.

#### Scenario: Manifest con profile

- **WHEN** el manifest declara `profile: minimal` y nada más
- **THEN** `fdh install` resuelve los cuatro componentes del profile `minimal` y los registra en el lock

#### Scenario: Profile inexistente

- **WHEN** el manifest declara `profile: not-defined` y el hub no tiene ese profile
- **THEN** `fdh install` falla con error accionable nombrando el profile faltante y listando los profiles disponibles

### Requirement: Extension y override del profile desde el manifest

El manifest SHALL permitir extender o restringir un profile vía la clave `extends:` con sub-campos `add_skills`, `add_rules`, `add_agents`, `add_hooks`, `remove_skills`, `remove_rules`, `remove_agents`, `remove_hooks`. El resultado expandido SHALL aplicar primero el profile, luego los `add_*`, luego los `remove_*`.

#### Scenario: Manifest extiende con add y remove

- **WHEN** el manifest declara `profile: minimal` + `extends: { add_skills: [i18n-helper], remove_rules: [no-console-log] }`
- **THEN** el lock incluye `skills: [design-system, i18n-helper]`, `rules: []`, `agents: [falabella-pr-writer]`, `hooks: [doctor-on-session-start]`

#### Scenario: Remove de algo que no estaba

- **WHEN** el manifest declara `remove_skills: [not-in-profile]` y el profile no incluía ese skill
- **THEN** `fdh install` emite warning informativo (no falla) y continúa

### Requirement: Lock registra resolución expandida, no referencia al profile

El `.fdh/lock.yaml` SHALL registrar la lista expandida final de componentes con sus versiones e integrity hashes; SHALL incluir un campo `resolved_from_profile: <name>` informativo, pero la fuente de verdad para reproducibilidad SHALL ser la lista expandida, no la referencia al profile.

#### Scenario: Profile cambia después del install

- **WHEN** un admin del hub cambia la definición del profile `minimal` (agrega un nuevo agent) y otra dev tiene un lock generado antes del cambio
- **THEN** correr `fdh install` (sin `fdh update`) reproduce exactamente lo que estaba en el lock, ignorando el cambio del profile en el hub
