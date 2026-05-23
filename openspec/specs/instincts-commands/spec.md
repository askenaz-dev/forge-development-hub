# instincts-commands Specification

## Purpose

Defines the `fdh instinct *` CLI surface that lets a developer capture, browse, edit, share, and ingest tribal knowledge as file-based instincts without standing up any backend. `capture` runs interactively against a TTY or in flag-driven mode for CI, auto-filling `captured_by` and `context.*` from `~/.fdh/config.yaml` and the active project's `state.json`; `list/show/edit/delete` operate on ULID prefixes with confirmation guards and index refresh; `export` produces YAML / JSON / tar.gz bundles only after `fdh scan` clears the contents of secrets (privacy-by-default, with an explicit `--no-scan` override); and `import` deduplicates by SHA-256 of the normalized body so the same bundle can be re-imported safely. Together these commands make manual peer-to-peer instinct exchange via files the v1 transport while a future sync service is still out of scope.

## Requirements

### Requirement: Comando `fdh instinct capture` con modo interactivo y flag-driven

`fdh` SHALL proveer el comando `fdh instinct capture` con dos modos. Modo interactivo (default cuando stdin es TTY y no se pasaron flags resolvedoras): el comando pregunta secuencialmente `title`, `domain`, `confidence`, `tags`, y abre `$EDITOR` para el body. Modo flag-driven (cuando stdin no es TTY o se pasan flags): acepta `--title <s>`, `--domain <s>`, `--confidence <f>`, `--tags <csv>`, `--body-file <path>` (o `--body <s>` para inline corto). En ambos modos SHALL auto-rellenar `captured_by` desde `~/.fdh/config.yaml`, `captured_at` con `time.Now()`, e inferir `context.project_hint`, `context.hub_commit` desde `~/.fdh/state.json` del proyecto activo (`cwd`).

#### Scenario: Capture interactivo TTY

- **WHEN** un developer ejecuta `fdh instinct capture` en TTY sin flags
- **THEN** el comando pregunta title → domain → confidence → tags secuencialmente, abre `$EDITOR` para el body, valida y persiste a `~/.fdh/instincts/<id>.yaml`

#### Scenario: Capture flag-driven en CI

- **WHEN** se ejecuta `fdh instinct capture --title "..." --domain "..." --confidence 0.7 --tags go,observability --body-file body.md` con stdin redirigido
- **THEN** el comando persiste el instinct sin prompts y sale con código cero

#### Scenario: Auto-completar context desde state

- **WHEN** `fdh instinct capture` corre en un proyecto registrado en `~/.fdh/state.json`
- **THEN** el `context.project_hint` se infiere como basename del cwd y `context.hub_commit` se lee del lock.yaml del proyecto si existe

### Requirement: Comando `fdh instinct list` con filtros

`fdh` SHALL proveer `fdh instinct list` que muestre una tabla legible con `id` (truncado a 8 chars), `title` (truncado a 60 chars), `domain`, `confidence`, `captured_at`. SHALL aceptar flags `--domain <s>`, `--since <date>`, `--until <date>`, `--confidence-min <f>`, `--tag <s>` (repetible), `--captured-by <s>`, `--limit <n>`, `--json` (output estructurado).

#### Scenario: List sin filtros

- **WHEN** un developer corre `fdh instinct list` con 30 instincts capturados
- **THEN** la salida muestra los 30 ordenados por `captured_at` descendente con columnas truncadas para legibilidad

#### Scenario: List con filtro de dominio

- **WHEN** se ejecuta `fdh instinct list --domain backend-services-go --confidence-min 0.5`
- **THEN** la salida muestra sólo instincts con ese domain y confidence ≥ 0.5

#### Scenario: List JSON output

- **WHEN** se ejecuta `fdh instinct list --json`
- **THEN** la salida es un único array JSON con un objeto por instinct (campos completos del frontmatter), parseable por scripts

### Requirement: Comandos `show`, `edit`, `delete` por ID

- `fdh instinct show <id-prefix>` SHALL aceptar un prefijo del ULID y SHALL imprimir el archivo YAML completo si hay match único, o listar candidatos si el prefijo matchea varios.
- `fdh instinct edit <id-prefix>` SHALL abrir el archivo en `$EDITOR`; al guardar SHALL re-validar el formato y SHALL regenerar el index.
- `fdh instinct delete <id-prefix>` SHALL pedir confirmación `[y/N]` salvo que se pase `--yes`, y SHALL borrar el archivo + actualizar el index.

#### Scenario: Show con prefijo ambiguo

- **WHEN** un developer ejecuta `fdh instinct show 01HX` y existen dos instincts cuyo ID empieza con `01HX`
- **THEN** el comando imprime "ambiguous prefix; matches: <list>" y sale con código distinto de cero

#### Scenario: Edit refresca index

- **WHEN** un developer hace `fdh instinct edit <id>` y cambia el `title` y `tags`, luego guarda y cierra el editor
- **THEN** el archivo YAML refleja los cambios, el `.index.json` se regenera con los valores nuevos, y un subsiguiente `fdh instinct list` muestra los valores actualizados

#### Scenario: Delete con confirmación

- **WHEN** se ejecuta `fdh instinct delete <id>` sin `--yes`
- **THEN** el comando pregunta `Delete instinct "..."? [y/N]`; sólo borra si la respuesta es `y`/`Y`

### Requirement: Comando `fdh instinct export` con safety check via `fdh scan`

`fdh instinct export <output-file>` SHALL generar un bundle con los instincts seleccionados. Formatos soportados: `.yaml` (single YAML doc con lista), `.json` (single JSON array), `.tar.gz` (archivos individuales). Filtros: `--since`, `--until`, `--domain`, `--captured-by`, `--tag` (repetibles), `--all` (sin filtros). Antes de generar el output, `fdh export` SHALL ejecutar `fdh scan` sobre el contenido del bundle; si scan reporta hallazgos `error`, el export SHALL abortar con código distinto de cero y mensaje accionable identificando qué instinct y qué línea dispara el hallazgo.

#### Scenario: Export con scan limpio

- **WHEN** un developer ejecuta `fdh instinct export bundle.tar.gz --domain backend` y los instincts no contienen secrets/info sensible
- **THEN** el archivo `bundle.tar.gz` se genera, scan reporta "no findings", y el comando sale con código cero indicando cuántos instincts se exportaron

#### Scenario: Export bloqueado por scan

- **WHEN** un developer ejecuta `fdh instinct export bundle.tar.gz` y uno de los instincts contiene una API key en el body
- **THEN** el export aborta antes de generar el archivo, imprime "export blocked by scan: instinct <id> line N contains <rule>", y sale con código distinto de cero

#### Scenario: Export con `--no-scan` bypass

- **WHEN** un developer ejecuta `fdh instinct export bundle.tar.gz --no-scan` (flag explícito de override)
- **THEN** el export procede sin scan; imprime warning "skipped scan: this bundle may contain sensitive data"

### Requirement: Comando `fdh instinct import` con dedup automático

`fdh instinct import <file>` SHALL aceptar bundles en los tres formatos soportados (`.yaml`, `.json`, `.tar.gz`). Para cada instinct en el bundle, SHALL calcular hash SHA-256 del body normalizado (whitespace trimmed, line endings normalizadas a `\n`) y compararlo contra el hash de los instincts locales; si ya existe, SHALL saltarlo silenciosamente (cuenta como duplicado). Al final SHALL reportar: `imported: N, duplicates: M, malformed: K`. Aplica `--dry-run` para preview sin tocar disco.

#### Scenario: Import primera vez

- **WHEN** un developer importa un bundle de 5 instincts y no tenía ninguno local con el mismo body
- **THEN** los 5 se persisten, el reporte muestra `imported: 5, duplicates: 0, malformed: 0`

#### Scenario: Import con duplicados

- **WHEN** un developer importa el mismo bundle por segunda vez
- **THEN** ningún instinct se persiste de nuevo, el reporte muestra `imported: 0, duplicates: 5, malformed: 0`

#### Scenario: Import con malformed

- **WHEN** un bundle contiene 5 instincts de los cuales 1 tiene frontmatter inválido
- **THEN** los 4 válidos se importan, el malformed se reporta con su index/nombre, y el reporte muestra `imported: 4, duplicates: 0, malformed: 1`; exit code es 0 si hay al menos uno importado (warning si todos malformed)
