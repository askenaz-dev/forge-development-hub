*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## ADDED Requirements

### Requirement: Schema version 2 con campo `kind`

El catálogo del hub SHALL declarar `schema_version: 2` y cada entry SHALL incluir un campo obligatorio `kind` con uno de los valores `skill | rule | agent | hook`. Entries sin `kind` explícito SHALL ser rechazadas por la validación; no hay defaulting silencioso.

#### Scenario: Entry válida con kind

- **WHEN** un admin agrega una entry con `kind: rule`, `name: no-console-log`, `path: rules/no-console-log` y demás campos requeridos
- **THEN** la validación del registry acepta la entry como rule

#### Scenario: Entry inválida sin kind

- **WHEN** un admin agrega una entry sin campo `kind`
- **THEN** la validación falla con error nombrando la entry y exigiendo `kind` explícito

#### Scenario: Schema version inválido

- **WHEN** el archivo declara `schema_version: 1` o lo omite
- **THEN** la validación falla con mensaje accionable indicando que la versión soportada es 2 y sugiriendo correr `tools/migrate-registry-v1-v2.py`

### Requirement: Migración tooled e idempotente de v1 a v2

El repo SHALL proveer un script `tools/migrate-registry-v1-v2.py` que tome un archivo v1 y produzca su equivalente v2 agregando `kind: skill` a cada entry existente y bumpeando `schema_version`. La migración SHALL ser idempotente: correrla sobre un archivo v2 SHALL ser no-op con exit code cero.

#### Scenario: Migración de v1 a v2

- **WHEN** el script corre sobre un `skills/registry.yaml` v1 con la entry `design-system`
- **THEN** produce un archivo v2 con la misma entry más `kind: skill` y `schema_version: 2`, preservando comentarios y orden

#### Scenario: Migración idempotente sobre v2

- **WHEN** el script corre sobre un archivo ya v2
- **THEN** detecta que ya está migrado, no modifica el archivo y sale con código cero y mensaje informativo

### Requirement: Catálogo unificado lista las cuatro primitivas

El catálogo v2 SHALL referenciar componentes de las cuatro primitivas mediante el campo `kind`, y SHALL exigir que `path` apunte a `skills/<name>/`, `rules/<name>/`, `agents/<name>/` o `hooks/<name>/` según corresponda al `kind` declarado.

#### Scenario: Coherencia kind ↔ directorio

- **WHEN** una entry declara `kind: rule` pero `path: skills/foo`
- **THEN** la validación falla nombrando la inconsistencia (kind rule debe vivir en `rules/`)

#### Scenario: Catálogo con cuatro kinds

- **WHEN** el catálogo contiene entries de los cuatro kinds y todas con `path` coherente
- **THEN** la validación pasa y `fdh init` puede ofrecer componentes de cualquier kind en el wizard

### Requirement: Validación de directorios huérfanos por kind

La validación del registry SHALL verificar que cada directorio bajo `skills/`, `rules/`, `agents/` y `hooks/` tenga una entry correspondiente en el catálogo con el `kind` correcto; directorios huérfanos SHALL bloquear el merge en CI.

#### Scenario: Directorio sin entry

- **WHEN** existe `rules/orphan-rule/RULE.md` pero no hay entry para `name: orphan-rule, kind: rule` en el catálogo
- **THEN** la validación falla nombrando el directorio huérfano y bloquea el merge

#### Scenario: Entry sin directorio

- **WHEN** el catálogo declara `kind: hook, name: phantom-hook, path: hooks/phantom-hook` pero el directorio no existe
- **THEN** la validación falla nombrando la entry sin path real
