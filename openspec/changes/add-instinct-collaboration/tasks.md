## 1. Verificación de pre-requisitos

- [ ] 1.1 Confirmar que `hub-v2-manifest-state-profiles` está archivado (sus specs viven en `openspec/specs/`, no en su change directory) antes de hacer apply de este change
- [ ] 1.2 Confirmar que `~/.fdh/state.json` y `fdh-scan-security` están implementados en el repo `fdh` Go (de lo contrario, este change queda pendiente de esa implementación)

## 2. Formato y validación del instinct

- [ ] 2.1 Definir y documentar formato YAML del instinct con frontmatter normativo (en `openspec/specs/instincts-format-and-storage/spec.md` post-archive)
- [ ] 2.2 Implementar parser/validator del frontmatter en Go (`pkg/instincts/format.go`) con validación de cada campo y mensajes de error claros
- [ ] 2.3 Implementar generación de ULID en Go (probablemente `github.com/oklog/ulid/v2`)
- [ ] 2.4 Implementar cálculo de hash SHA-256 del body normalizado para dedup
- [ ] 2.5 Agregar tests del parser/validator cubriendo válidos, malformed, edge cases (confidence fuera de rango, ID no ULID, etc.)

## 3. Storage local

- [ ] 3.1 Implementar funciones de read/write atómicas (write `.tmp` + rename, fsync en Unix) en `pkg/instincts/storage.go`
- [ ] 3.2 Implementar creación del directorio `~/.fdh/instincts/` con permisos `0700` (Unix) o ACL equivalente (Windows)
- [ ] 3.3 Implementar mantenimiento del index `.index.json` con detección de staleness
- [ ] 3.4 Implementar housekeeping: cleanup automático de archivos `.tmp` huérfanos en `fdh instinct list`
- [ ] 3.5 Agregar tests del storage: escritura atómica simulada, recuperación post-crash, regeneración de index

## 4. Integración con state.json

- [ ] 4.1 Implementar lectura/escritura de la sección `instincts:` en `~/.fdh/state.json` con campos `count`, `last_capture`, `last_export`, `last_evolve`, `evolve_runs`
- [ ] 4.2 Hacer que cada comando `fdh instinct *` y `fdh evolve` actualice la sección correspondiente
- [ ] 4.3 Extender `fdh doctor` (existente) para mostrar la sección Instincts si presente en state
- [ ] 4.4 Agregar tests de la integración: capture incrementa count, export actualiza last_export, evolve incrementa evolve_runs

## 5. Comando `fdh instinct capture`

- [ ] 5.1 Implementar modo interactivo TTY: prompts secuenciales para title/domain/confidence/tags, apertura de $EDITOR para body
- [ ] 5.2 Implementar modo flag-driven: aceptar `--title`, `--domain`, `--confidence`, `--tags`, `--body-file`, `--body`
- [ ] 5.3 Implementar auto-completado de `context.project_hint` y `context.hub_commit` desde state.json + cwd
- [ ] 5.4 Implementar auto-sugerencia de `domain` desde el profile del proyecto activo (decision 2 del design)
- [ ] 5.5 Implementar lectura de `captured_by` desde `~/.fdh/config.yaml` + override via env var `FDH_USER_EMAIL`
- [ ] 5.6 Agregar tests: capture interactivo (mock TTY), capture flag-driven, auto-complete de contexto

## 6. Comandos `fdh instinct list/show/edit/delete`

- [ ] 6.1 Implementar `list` con filtros (`--domain`, `--since`, `--until`, `--confidence-min`, `--tag`, `--captured-by`, `--limit`, `--json`)
- [ ] 6.2 Implementar `show <id-prefix>` con resolución de prefijo y manejo de ambigüedad
- [ ] 6.3 Implementar `edit <id-prefix>` con apertura en `$EDITOR` + re-validación + regen del index al guardar
- [ ] 6.4 Implementar `delete <id-prefix>` con prompt de confirmación (omitible con `--yes`)
- [ ] 6.5 Agregar tests de los cuatro comandos cubriendo casos típicos y edge cases

## 7. Comando `fdh instinct export` con safety check

- [ ] 7.1 Implementar export en los tres formatos: `.yaml` (single doc con array), `.json` (array), `.tar.gz` (archivos individuales). Detección por extensión.
- [ ] 7.2 Implementar filtros (`--since`, `--until`, `--domain`, `--captured-by`, `--tag`, `--all`)
- [ ] 7.3 Implementar invocación de `fdh scan` sobre el bundle antes de generar el output; abortar si hay hallazgos `error`
- [ ] 7.4 Implementar flag `--no-scan` con warning explícito
- [ ] 7.5 Agregar tests: export clean, export blocked by scan, export con `--no-scan`, los tres formatos

## 8. Comando `fdh instinct import` con dedup

- [ ] 8.1 Implementar parsing de los tres formatos de bundle
- [ ] 8.2 Implementar dedup por hash SHA-256 del body normalizado
- [ ] 8.3 Implementar handling de conflicto: mismo ID local + body distinto → error con instrucción manual
- [ ] 8.4 Implementar reporte final (`imported: N, duplicates: M, malformed: K`)
- [ ] 8.5 Implementar `--dry-run` para preview sin tocar disco
- [ ] 8.6 Agregar tests: import primera vez, import duplicado, import con malformed, conflicto de ID

## 9. Comando `fdh evolve` clustering

- [ ] 9.1 Implementar algoritmo de clustering rule-based: agrupar por `domain`, calcular similaridad de pares con jaccard tags + jaccard keywords title, agrupación transitiva
- [ ] 9.2 Implementar extractor de keywords del title con stopwords inglés + español
- [ ] 9.3 Implementar criterios configurables: `--min-cluster-size` (default 3), `--min-avg-confidence` (default 0.6)
- [ ] 9.4 Implementar flags `--from <bundle>` y `--include-local` para controlar input
- [ ] 9.5 Agregar tests de clustering: clusters bien formados, clusters debajo de threshold, sin clustering cross-domain

## 10. Comando `fdh evolve` generación de drafts

- [ ] 10.1 Implementar generación de slug determinístico desde keywords del cluster
- [ ] 10.2 Implementar manejo de colisiones de slug (sufijo numérico)
- [ ] 10.3 Implementar template del draft (`SKILL.md`) con: frontmatter parcial, banner ⚠️ DRAFT, sección Sourced from con IDs + títulos + comando original + timestamp, secciones placeholder con TODO
- [ ] 10.4 Implementar escritura a `./fdh-evolve-output/<slug>/SKILL.md` con re-generación al re-run (no append)
- [ ] 10.5 Agregar tests: generación determinística, drafts con metadata completa, colisión de slugs

## 11. Validación CI del hub bloquea drafts con banner

- [ ] 11.1 Extender `tools/validate-registry.py` (o equivalente Go) para detectar el banner `⚠️ DRAFT — generated by fdh evolve` en cualquier `SKILL.md` referenciado por el catálogo
- [ ] 11.2 Si encuentra banner, fallar el CI con mensaje "draft banner detected in SKILL.md — please review TODOs and remove banner before merge"
- [ ] 11.3 Agregar test del validator con fixtures (SKILL.md con banner, sin banner)

## 12. Documentación

- [ ] 12.1 Crear `docs/instincts.md` en el repo `fdh` explicando: qué son instincts, cuándo capturarlos, cómo escribir un body útil, guía de confidence (0.3/0.6/0.9), cómo compartir, cómo `fdh evolve`
- [ ] 12.2 Actualizar `hub/README.md` (del hub) para mencionar el bucle bottom-up como complemento al modelo top-down
- [ ] 12.3 Agregar tutorial corto: "Tu primer instinct" — 3 minutos end-to-end desde capture a export
- [ ] 12.4 Documentar el rol de admin "instinct curator" con responsabilidades + ritmo sugerido (semanal/quincenal)

## 13. Privacidad y safety

- [ ] 13.1 Revisar con seguridad corporativa el flujo: storage local + safety check via scan + sin backend
- [ ] 13.2 Agregar disclaimer en `fdh instinct capture` interactivo: "Note: never paste secrets, API keys, or proprietary data in the body — this file lives in your home and may be shared via export"
- [ ] 13.3 Verificar que los permisos del directorio son `0700` en Unix y ACL equivalente en Windows en tests automatizados

## 14. Validación final pre-apply

- [ ] 14.1 Verificar que todos los specs están syntáctica y semánticamente válidos via `openspec validate` (o equivalente)
- [ ] 14.2 Smoke test manual del flujo: capture → list → show → export bundle → import en otra máquina mock → evolve → ver draft generado
- [ ] 14.3 Verificar trazabilidad del draft: abrir un draft generado y confirmar que la sección Sourced from lista los instincts y que `fdh instinct show <id>` los resuelve

## 15. Handoff a future changes

- [ ] 15.1 Documentar en `proposal.md` final el commit SHA del apply para referencias futuras
- [ ] 15.2 Confirmar que el contrato deja espacio claro para `add-instinct-sync-service` (sólo agrega comandos `push`/`pull`, no cambia formato)
- [ ] 15.3 Confirmar que el contrato deja espacio claro para `add-instinct-auto-capture-via-hooks` (Stop-phase hook escribe a `~/.fdh/instincts/` usando el mismo formato)
- [ ] 15.4 Confirmar que el contrato deja espacio claro para `evolve-instincts-with-llm` (sólo cambia el algoritmo de clustering, no el output format)
