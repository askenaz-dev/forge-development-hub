# instincts-format-and-storage Specification

## Purpose

Defines the file-based contract for storing developer-captured "instincts" on the local machine: each instinct is a single YAML document (frontmatter + markdown body) with a ULID identifier, persisted as `~/.fdh/instincts/<id>.yaml` under a `0700` directory, written atomically via `.tmp + rename`. An optional `.index.json` cache speeds up listings without becoming the source of truth, and a dedicated `instincts:` section in `~/.fdh/state.json` (additive, never destructive) exposes summary stats to `fdh doctor`. This capability is the foundation for the bottom-up knowledge loop that lets tribal domain expertise from 500 Falabella devs become input to the hub catalog without standing up any backend.

## Requirements

### Requirement: Formato YAML del instinct

Un instinct SHALL ser un archivo YAML con frontmatter delimitado por `---` y body markdown. El frontmatter SHALL declarar al menos: `id` (ULID, 26 chars, lexicográficamente ordenable), `title` (one-liner ≤120 chars), `confidence` (float 0.0-1.0), `domain` (string libre kebab-case), `captured_by` (identificador del dev, normalmente email), `captured_at` (ISO 8601 con timezone), `context` (objeto con `project_hint`, `hub_commit`, `triggers`), opcionalmente `tags` (lista de strings) y `related_skills` (lista de nombres de skills del hub). El body es markdown libre.

#### Scenario: Instinct válido

- **WHEN** un developer abre un archivo `~/.fdh/instincts/01HXY7K2QZ3M5R9TPVNBJ8D6F4.yaml`
- **THEN** encuentra frontmatter con los 7 campos requeridos y un body markdown libre

#### Scenario: Instinct inválido

- **WHEN** un archivo en `~/.fdh/instincts/` no parsea como YAML válido o le falta `id`/`title`/`confidence`
- **THEN** `fdh instinct list` lo reporta como "malformed" sin abortar el listado del resto

#### Scenario: Confidence fuera de rango

- **WHEN** un instinct declara `confidence: 1.5` o `confidence: -0.1`
- **THEN** las herramientas (`list`, `evolve`, `export`) lo tratan como inválido y lo reportan en stderr

### Requirement: ID es ULID, no UUID

Cada instinct SHALL tener `id` que sea un ULID válido (26 caracteres Crockford Base32). NO se SHALL aceptar UUIDs. Razones del diseño: ULIDs son lexicográficamente ordenables por timestamp, más cortos en filenames, sin guiones intermedios.

#### Scenario: Generación de ULID en capture

- **WHEN** `fdh instinct capture` genera un nuevo instinct
- **THEN** el ID generado matchea regex `^[0-9A-HJKMNP-TV-Z]{26}$` y es lexicográficamente posterior a IDs previamente generados en la misma máquina

#### Scenario: ULID inválido es rechazado

- **WHEN** un archivo en `~/.fdh/instincts/` tiene un nombre que no es ULID válido (ej. `not-a-ulid.yaml`)
- **THEN** las herramientas lo ignoran y reportan en stderr "skipping <file>: not a valid ULID filename"

### Requirement: Storage local en `~/.fdh/instincts/`

`fdh` SHALL almacenar instincts como archivos individuales en `~/.fdh/instincts/<id>.yaml`. Un archivo por instinct (no un único YAML grande). El directorio SHALL crearse automáticamente cuando el primer instinct se captura. Permisos del directorio SHALL ser `0700` (sólo el dueño puede leer/escribir).

#### Scenario: Layout file-per-instinct

- **WHEN** un developer tiene 12 instincts capturados
- **THEN** existen 12 archivos `<id>.yaml` en `~/.fdh/instincts/` y nada más (excepto el opcional `.index.json`)

#### Scenario: Permisos restrictivos

- **WHEN** `fdh instinct capture` crea por primera vez `~/.fdh/instincts/`
- **THEN** el directorio tiene permisos `0700` en sistemas Unix; en Windows usa la ACL equivalente que limita acceso al usuario actual

### Requirement: Escrituras atómicas para evitar corrupción

`fdh` SHALL escribir cualquier instinct usando el patrón "write `.tmp` + rename": primero escribe `<id>.yaml.tmp`, fsync (en Unix), luego `rename(<id>.yaml.tmp, <id>.yaml)`. Esto garantiza que un crash a mitad de escritura no deja un archivo corrupto.

#### Scenario: Crash durante escritura

- **WHEN** `fdh instinct capture` es interrumpido (Ctrl-C, kill -9) después de escribir `.tmp` pero antes del rename
- **THEN** `~/.fdh/instincts/` contiene a lo sumo un archivo `.tmp` (limpiable manualmente o por `fdh instinct list`) y nunca un `<id>.yaml` parcial

#### Scenario: Cleanup de tmp files

- **WHEN** `fdh instinct list` corre y encuentra archivos `<id>.yaml.tmp`
- **THEN** los reporta en stderr y los borra (limpieza housekeeping); el listado de instincts no incluye los `.tmp`

### Requirement: Index opcional `.index.json` para listings rápidos

`fdh` MAY mantener un archivo `~/.fdh/instincts/.index.json` con metadata cacheada (id, title, domain, confidence, tags, captured_at) para que `fdh instinct list` no tenga que parsear cada YAML. El index SHALL regenerarse automáticamente si está stale (timestamp del directorio > timestamp del index) o ausente. NO SHALL ser source of truth — los YAMLs lo son.

#### Scenario: Index regenerado tras edit

- **WHEN** un developer hace `fdh instinct edit <id>` que modifica el título de un instinct, y luego corre `fdh instinct list`
- **THEN** el index se detecta stale, se regenera, y el listing muestra el título nuevo

#### Scenario: Index corrupto cae a fallback

- **WHEN** `.index.json` es manualmente corrompido (JSON inválido)
- **THEN** `fdh instinct list` ignora el index, parsea los YAMLs directamente, y regenera el index al terminar

### Requirement: Sección `instincts:` en `~/.fdh/state.json`

Cualquier comando `fdh instinct *` o `fdh evolve` SHALL actualizar la sección `instincts:` en `~/.fdh/state.json` con: `count` (entero, número de instincts locales), `last_capture` (ISO 8601 del último capture), `last_export` (ISO 8601 del último export), `last_evolve` (ISO 8601 del último evolve), `evolve_runs` (entero, contador acumulado). La sección es additive — no remueve ni modifica otras secciones del state.

#### Scenario: State actualizado tras capture

- **WHEN** un developer corre `fdh instinct capture` exitosamente
- **THEN** `~/.fdh/state.json` tiene `instincts.count` incrementado y `instincts.last_capture` actualizado al timestamp del momento

#### Scenario: State leído por `fdh doctor`

- **WHEN** `fdh doctor` corre y existe la sección `instincts:` en el state
- **THEN** la salida de `doctor` muestra una sección "Instincts" con los contadores y los timestamps

#### Scenario: Sección ausente si nunca se usaron instincts

- **WHEN** un developer nunca corrió un comando `fdh instinct *`
- **THEN** `~/.fdh/state.json` NO tiene la clave `instincts:`; `fdh doctor` no muestra esa sección
