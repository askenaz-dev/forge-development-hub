## Why

`hub-v2-manifest-state-profiles` deja al hub con 4 primitivas distribuibles (skills, rules, agents, hooks) y al consumidor con un contrato declarativo (manifest + lock + state). Pero el flujo de conocimiento sigue siendo top-down: equipo plataforma escribe → devs consumen. A escala de 500 devs Falabella, esto convierte al equipo plataforma en bottleneck eterno de curación y desperdicia el conocimiento tribal que cada dev genera cada día en sesiones con su agente IA.

El concepto `continuous-learning-v2` de ECC (https://github.com/affaan-m/ECC) introduce un bucle bottom-up de aprendizaje: cada sesión de dev captura "instincts" (patrones de dominio con confidence scoring), pueden compartirse via export/import, y un admin los "evoluciona" en skills formales con `fdh evolve`. Para Falabella, esto significa que el conocimiento de devs senior de fulfillment sobre integración SAP (o del equipo de pricing sobre corner cases de descuentos, o del checkout sobre timeouts de pasarelas) deja de ser tribal y se vuelve input al catálogo. Sin este bucle, el catálogo crece lineal con la capacidad de plataforma; con el bucle, crece exponencial con el uso.

**Dependencia**: este change asume que `hub-v2-manifest-state-profiles` ya hizo apply. Se beneficia de `~/.fdh/state.json` y del contrato de `~/.fdh/` como home del CLI. Diseñado para correr inmediatamente después de hub-v2.

Este change introduce **la versión file-based del bucle** (sin backend, intercambio manual via archivos). Backend HTTP para sync automático queda como future change `add-instinct-sync-service`; auto-capture via hooks como `add-instinct-auto-capture-via-hooks`; clustering semántico via LLM como `evolve-instincts-with-llm`.

## What Changes

### Formato y storage del instinct

- Cada instinct es un archivo YAML en `~/.fdh/instincts/<id>.yaml` con frontmatter estructurado (`id` ULID, `title`, `confidence`, `domain`, `captured_by`, `captured_at`, `context`, `tags`, `related_skills`) + body markdown libre.
- ID es ULID lexicográficamente ordenable (no UUID — sortable + shorter).
- Index opcional `~/.fdh/instincts/.index.json` con metadata cacheada para listings rápidos.
- Dedup por hash SHA-256 del body normalizado en import.
- Escrituras atómicas (write `.tmp` + rename).

### Comandos `fdh instinct *`

- `capture` (interactivo y flag-driven), `list` (con filtros), `show`, `edit` (en $EDITOR), `delete`, `export` (a YAML/JSON/tar.gz con filtros), `import` (con dedup automático).
- Auto-completar `context` desde `~/.fdh/state.json` del proyecto activo.

### Comando admin `fdh evolve`

- Clusterea instincts por similaridad rule-based (mismo domain + overlap de tags + Jaccard sobre keywords del title). Sin LLM en v1.
- Para cada cluster con N≥3 instincts y `confidence` promedio ≥ 0.6, genera draft de `skills/<slug>/SKILL.md` bajo `./fdh-evolve-output/` para review humano antes de PR al hub.
- Soporta `--from <bundle>` para clusterear desde un bundle importado, además del contenido local.

### Privacidad por default

- Captura nunca incluye contenido del proyecto automáticamente — el body es lo que el dev escribe.
- `fdh instinct export` corre `fdh scan` (de `hub-v2`) sobre el bundle antes de generarlo; aborta si detecta secrets/info sensible.
- Encryption at rest queda fuera de scope v1 — los `~/.fdh/instincts/` quedan bajo la protección del home del dev.

### Integración con state.json

- `~/.fdh/state.json` gana una sección `instincts: { count, last_capture, last_export, evolve_runs }` actualizada por los comandos. Permite a `fdh doctor` mostrar el estado del bucle. Es agregación; no duplica datos.

## Capabilities

### New Capabilities

- `instincts-format-and-storage`: formato YAML del instinct (frontmatter + body), layout en `~/.fdh/instincts/`, generación de ULID, dedup por hash, index cache opcional, escrituras atómicas, integración con `~/.fdh/state.json` para summary stats.
- `instincts-commands`: contratos de los comandos `capture | list | show | edit | delete | export | import`, modos interactivo vs flag-driven, formato del bundle de export, dedup en import, integración con `fdh scan` para pre-export safety check.
- `instincts-evolution`: comando admin `fdh evolve` con clustering rule-based (domain + tags + Jaccard), criterios de cluster (N≥3, confidence ≥ 0.6), generación de drafts de skills en `./fdh-evolve-output/`, trazabilidad a instincts fuente.

### Modified Capabilities

Sin modificaciones a specs existentes. Las extensiones de `fdh-scan-security` (uso desde export) y `installation-state-ledger` (sección `instincts:`) se modelan como requirements **dentro de las nuevas capabilities**, no como deltas a las introducidas por hub-v2. Esto evita coupling temporal entre changes (hub-v2 debe estar archivado primero) y mantiene cada capability self-contained.

## Impact

### Filesystem

- Nuevo directorio per-usuario: `~/.fdh/instincts/<id>.yaml` + opcional `.index.json`.
- Sin archivos nuevos en el repo del hub durante apply (los instincts viven en máquinas de devs; el hub sólo recibe skills resultado de `fdh evolve` curados por admins).
- Sin archivos nuevos en consumer repos (los instincts no son project-bound).

### Repo `fdh` (Go, hermano)

- Implementación de `fdh instinct *` commands y `fdh evolve`. Estimado 2-3 sprints.
- Reusa código de `fdh scan` (de hub-v2) para el screening pre-export.
- Reusa código de lectura/escritura de `~/.fdh/` (también de hub-v2).

### Sin dependencias externas en v1

- No requiere Artifactory (file-based local).
- No requiere backend Falabella (intercambio manual via archivos `.tar.gz`).
- No requiere LLM (clustering rule-based).
- No requiere hook runtime (captura es manual).

### Habilita future changes

- `add-instinct-sync-service`: backend HTTP Falabella para sync automático push/pull entre devs.
- `add-instinct-auto-capture-via-hooks`: integración con Stop-phase hooks para captura automática al finalizar sesiones.
- `evolve-instincts-with-llm`: `fdh evolve` pasa de clustering rule-based a semántico via embeddings.
- `add-instinct-team-curation`: workflows de revisión multi-stakeholder antes de proponerse como skills.
- `add-instinct-review-loop`: comando `fdh instinct review` para devs voten utilidad de instincts ajenos.
