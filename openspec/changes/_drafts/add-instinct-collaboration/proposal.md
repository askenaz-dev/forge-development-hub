*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

> **NOTA — BORRADOR (no es un change formal todavía).**
> Este archivo vive bajo `openspec/changes/_drafts/` para revisión humana antes de
> ejecutar `/opsx:propose`.
>
> **Dependencia explícita: este change asume que `hub-v2-manifest-state-profiles`
> ya hizo apply.** Se beneficia de `~/.fdh/state.json` y del contrato de `~/.fdh/`
> como home del CLI. Diseñado para correr inmediatamente después de hub-v2.

## Why

`hub-v2-manifest-state-profiles` deja al hub con 4 primitivas distribuibles (skills, rules, agents, hooks) y al consumidor con un contrato declarativo (manifest + lock + state). Pero el **flujo de conocimiento sigue siendo top-down**: equipo plataforma escribe → devs consumen. A escala de 500 devs Forge, esto convierte al equipo plataforma en bottleneck eterno de curación, y desperdicia el conocimiento tribal que cada dev genera cada día en sesiones con su agente IA.

El concepto `continuous-learning-v2` de ECC (ver `https://github.com/affaan-m/ECC`) introduce un **bucle bottom-up de aprendizaje**:

```
┌──────────────────────────────────────────────────────────────────┐
│  Dev codeando con su agente IA                                    │
│           │                                                        │
│           ▼                                                        │
│  fdh instinct capture                                              │
│  (manual v1; auto via Stop-phase hook en future change)           │
│           │                                                        │
│           ▼                                                        │
│  ~/.fdh/instincts/<id>.yaml                                        │
│  (storage local, confidence score, contexto, dominio)             │
│           │                                                        │
│           ▼                                                        │
│  fdh instinct export bundle.tar.gz                                 │
│  fdh instinct import (otro dev del equipo)                         │
│  (intercambio manual v1; servicio sync en future change)          │
│           │                                                        │
│           ▼                                                        │
│  Admin: fdh evolve                                                 │
│  (clusterea instincts importados → propone borrador de SKILL.md)  │
│           │                                                        │
│           ▼                                                        │
│  PR al hub agregando el skill curado                               │
└──────────────────────────────────────────────────────────────────┘
```

El valor para Forge: el conocimiento de los devs senior del equipo de fulfillment sobre integración SAP (o el del equipo de pricing sobre los corner cases de descuentos, o el del equipo de checkout sobre los timeouts de pasarelas) deja de ser tribal y se vuelve un input al catálogo que cura plataforma. Sin este bucle, el catálogo crece lineal con la capacidad de plataforma; con el bucle, crece exponencial con el uso.

Este change introduce **la versión file-based del bucle** (sin backend, intercambio manual via archivos). El backend HTTP para sync automático entre devs queda como future change `add-instinct-sync-service` cuando volumen lo justifique.

## What Changes

### Formato del instinct

Cada instinct es un archivo YAML con frontmatter estructurado + body markdown:

```yaml
---
id: 01HXY7K2QZ3M5R9TPVNBJ8D6F4         # ULID
title: "Al refactorizar services Go, verificar IDs de traza OTel"
confidence: 0.8                          # 0.0-1.0, manual en v1
domain: backend-services-go              # taxonomía libre, normalizable después
captured_by: guillmar.ortiz@forge.com  # del ~/.fdh/config.yaml
captured_at: 2026-05-24T10:15:00Z
context:
  project_hint: "checkout-service"       # path-agnostic, hash del cwd opcional
  hub_commit: abc123def
  triggers:
    - "user prompt mentioned 'refactor' AND 'service'"
    - "file modified matches **/*.go"
tags: [go, observability, refactor]
related_skills: [code-review]            # opcional, cross-ref a skills del hub
---

Cuerpo libre en markdown. Explica el patrón, el "por qué", contraejemplos.

## Contexto
Esto pasó después de unificar dos services que tenían sus propios spans...

## La idea
Antes de mergear refactors de services, correr...

## Cuándo NO aplicar
Si el service no participa en flows distribuidos...
```

### Storage local

- **Layout**: `~/.fdh/instincts/<id>.yaml` (un archivo por instinct, ID es ULID lexicográficamente ordenable).
- **Index opcional**: `~/.fdh/instincts/.index.json` con metadata cacheada (title, domain, confidence, tags) para listings rápidos sin parsear cada YAML.
- **Dedup**: por hash SHA-256 del body normalizado (whitespace trimmed). `fdh instinct import` salta los que ya existen.
- **Versionado**: ninguno en v1. Si un instinct se edita, el archivo cambia in-place (no historial). Si se quiere historial, future change.

### Comandos `fdh instinct *`

- `fdh instinct capture` — modo interactivo: pregunta title, domain, confidence, tags, abre $EDITOR para el body. Auto-rellena `context` desde el `state.json` y `cwd`.
- `fdh instinct capture --title "..." --domain "..." --body-file body.md` — modo no interactivo (CI / scripts).
- `fdh instinct list` — tabla con id, title, domain, confidence, captured_at. Filtros: `--domain`, `--since`, `--until`, `--confidence-min`, `--tag`, `--captured-by`.
- `fdh instinct show <id>` — imprime el archivo completo.
- `fdh instinct edit <id>` — abre en $EDITOR. Re-genera index al guardar.
- `fdh instinct delete <id>` — confirma y borra.
- `fdh instinct export <file>` — bundle todos (o filtrados) a YAML/JSON/tar.gz para compartir. Soporta `--since`, `--domain`, `--captured-by`.
- `fdh instinct import <file>` — carga desde archivo. Hace dedup automático. Reporta cuántos nuevos, cuántos duplicados.

### Comando admin `fdh evolve`

- `fdh evolve` — sobre el contenido actual de `~/.fdh/instincts/` (o sobre un bundle importado vía `--from <file>`):
  1. Clusterea instincts por **similaridad rule-based** (mismo domain + overlap de tags + Jaccard sobre keywords del title).
  2. Para cada cluster con N≥3 instincts y confidence promedio ≥ 0.6, genera un **draft de `skills/<slug>/SKILL.md`** bajo `./fdh-evolve-output/` (no toca el hub directamente).
  3. El draft tiene placeholders TODO marcados claramente y referencia los instincts fuente (por ID).
  4. El admin revisa el draft, lo refina, lo agrega al hub via PR normal.
- v1 explícitamente **NO usa LLM** para clustering — es rule-based deterministic. La evolución a clustering semántico via embeddings queda como future change `evolve-instincts-with-llm`.

### Privacidad y filtrado

- **Captura nunca incluye contenido del proyecto automáticamente.** El body es lo que el dev escribe; los `context.triggers` son metadata sintética. Los paths se reducen a `project_hint` (basename del cwd) por default.
- **`fdh instinct export` corre `fdh scan` (introducido en hub-v2) sobre el bundle** antes de generar el archivo. Si detecta secrets o info sensible, aborta con error y señala qué instinct + qué línea.
- **Encryption at rest queda fuera de scope v1** — los `~/.fdh/instincts/` están en el home del dev, sujetos a la misma protección que el resto de `~/.fdh/`. Si plataforma security exige cifrado, future change.

## Capabilities

### New Capabilities

- `instincts-format-and-storage`: formato YAML del instinct, layout en `~/.fdh/instincts/`, generación de ULID, dedup por hash, index cache opcional. Privacidad por default.
- `instincts-commands`: comandos `capture | list | show | edit | delete | export | import` con sus contratos de input/output, filtros, modos interactivo vs flag-driven.
- `instincts-evolution`: comando admin `fdh evolve` con clustering rule-based, generación de drafts de skills, referencia trazable a instincts fuente.

### Modified Capabilities

- `fdh-scan-security` (introducido en hub-v2): se extiende para soportar input desde un bundle de instincts (`fdh scan --instincts-bundle <file>`). El contrato de detección no cambia, sólo agrega un input source.
- `installation-state-ledger` (introducido en hub-v2): el `~/.fdh/state.json` agrega una sección `instincts: { count, last_capture, last_export }` para que `fdh doctor` muestre el estado del bucle. Cambio mínimo.

## Impact

### Filesystem

- Nuevo directorio per-usuario: `~/.fdh/instincts/<id>.yaml` + opcional `.index.json`.
- Sin archivos nuevos en el repo del hub (los instincts viven en máquinas de devs; el hub sólo recibe los skills resultado de `fdh evolve`).
- Sin archivos nuevos en consumer repos (los instincts no son project-bound).

### Repo `fdh` (Go, hermano)

- Implementación de `fdh instinct *` commands y `fdh evolve`. Estimado: 2-3 sprints.
- Dependencia interna: el código necesita leer/escribir `~/.fdh/` (ya cubierto por hub-v2 implementation).
- Dependencia interna: `fdh evolve` reusa el código de `fdh scan` para el screening pre-export.

### Sin dependencias externas en v1

- No requiere Artifactory (es file-based local).
- No requiere backend Forge (intercambio es manual via archivos `.tar.gz`).
- No requiere LLM (clustering rule-based).
- No requiere hook runtime (captura es manual).

### Habilita pero no requiere

- Auto-captura via Stop-phase hook (future change `add-instinct-auto-capture-via-hooks`): la captura manual de v1 ya valida el flujo; agregar auto-capture después es additive.
- Sync server entre devs (future change `add-instinct-sync-service`): el export/import manual ya valida la mecánica; un servicio HTTP que automatice push/pull es additive.
- Clustering semántico con LLM (future change `evolve-instincts-with-llm`): el clustering rule-based de v1 ya entrega valor; subir el techo con embeddings es additive.

### Sets up future changes

- `add-instinct-sync-service`: backend HTTP Forge para sync automático push/pull entre devs. Resuelve la fricción del intercambio manual cuando el volumen lo justifique.
- `add-instinct-auto-capture-via-hooks`: integración con Stop-phase hooks para captura automática al finalizar sesiones. Depende de que hooks tengan un mecanismo más rico de event payload.
- `evolve-instincts-with-llm`: `fdh evolve` pasa de clustering rule-based a semántico via embeddings. Mejora calidad de los drafts generados.
- `add-instinct-team-curation`: workflows de revisión multi-stakeholder para instincts antes de proponerse como skills. Útil cuando varios equipos contribuyen al mismo dominio.

### Open questions (a resolver en design.md, no bloquean este proposal)

- ¿Confidence score es input manual o se calcula heurísticamente desde algo? v1 manual; v2 podría ponderar por frecuencia de patrones similares.
- ¿`fdh instinct capture` puede inferir el dominio automáticamente desde el cwd o el state.json? Probablemente sí — si `state.json` registra projects, el dominio puede sugerirse desde el manifest del proyecto activo.
- ¿`fdh evolve` corre sólo sobre instincts locales o también sobre bundles importados de otros equipos? Probable: ambos via `--from <file>` y `--include-local`.
- ¿Hay un comando `fdh instinct review` para que un dev marque instincts de otros como útiles/no-útiles antes de que admin haga evolve? Puede ser future change `add-instinct-review-loop`.
- ¿Encryption at rest en `~/.fdh/instincts/` requerido por security Forge? Defer hasta tener requerimiento explícito.
