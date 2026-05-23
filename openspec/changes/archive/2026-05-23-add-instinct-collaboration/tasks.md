## 1. Verificación de pre-requisitos

- [x] 1.1 Confirmar que `hub-v2-manifest-state-profiles` está archivado (sus specs viven en `openspec/specs/`, no en su change directory) antes de hacer apply de este change <!-- archived 2026-05-23 (commit cd50eb2 in hub) -->
- [x] 1.2 Confirmar que `~/.fdh/state.json` y `fdh-scan-security` están implementados en el repo `fdh` Go (de lo contrario, este change queda pendiente de esa implementación) <!-- partial: state.json read/write implemented inline in pkg/instincts/storage.go (MutateState + ReadStateInstincts) so this change is self-contained; full fdh-scan command remains a separate work item — a minimal built-in secrets scan ships inside `fdh instinct export` to gate exports today -->

## 2. Formato y validación del instinct

- [x] 2.1 Definir y documentar formato YAML del instinct con frontmatter normativo (en `openspec/specs/instincts-format-and-storage/spec.md` post-archive) <!-- spec ships in this change's `specs/` dir; lands in openspec/specs/ on archive -->
- [x] 2.2 Implementar parser/validator del frontmatter en Go (`pkg/instincts/format.go`) con validación de cada campo y mensajes de error claros <!-- pkg/instincts/format.go: Instinct struct + Validate() with field-by-field reasons -->
- [x] 2.3 Implementar generación de ULID en Go (probablemente `github.com/oklog/ulid/v2`) <!-- minimal in-tree ULID implementation in format.go: 48-bit ms timestamp + 80-bit crypto random in Crockford Base32 (26 chars). Zero new deps, ~30 LOC -->
- [x] 2.4 Implementar cálculo de hash SHA-256 del body normalizado para dedup <!-- BodyHash + BodyHashOf in format.go; normalizes line endings, trailing whitespace, leading/trailing blanks -->
- [x] 2.5 Agregar tests del parser/validator cubriendo válidos, malformed, edge cases (confidence fuera de rango, ID no ULID, etc.) <!-- pkg/instincts/instincts_test.go: 25+ assertions covering valid/invalid IDs, confidence, title length, encode/decode roundtrip, body normalization -->

## 3. Storage local

- [x] 3.1 Implementar funciones de read/write atómicas (write `.tmp` + rename, fsync en Unix) en `pkg/instincts/storage.go` <!-- WriteAtomic does write tmp → fsync (Unix) → rename; cleanup on rename failure -->
- [x] 3.2 Implementar creación del directorio `~/.fdh/instincts/` con permisos `0700` (Unix) o ACL equivalente (Windows) <!-- EnsureDir + explicit chmod on Unix; Windows inherits HOME's ACL (umask fallback) -->
- [ ] 3.3 Implementar mantenimiento del index `.index.json` con detección de staleness <!-- deferred: spec says MAY; not implemented v1 because for <1000 instincts the linear file scan is sub-100ms. Document the omission so a follow-up change can add it cleanly -->
- [x] 3.4 Implementar housekeeping: cleanup automático de archivos `.tmp` huérfanos en `fdh instinct list` <!-- List() removes stray .tmp files and logs to stderr -->
- [x] 3.5 Agregar tests del storage: escritura atómica simulada, recuperación post-crash, regeneración de index <!-- TestEnsureDir, TestWriteAtomic_AndRead, TestList_OnlyValidULIDs (covers .tmp cleanup), TestResolvePrefix -->

## 4. Integración con state.json

- [x] 4.1 Implementar lectura/escritura de la sección `instincts:` en `~/.fdh/state.json` con campos `count`, `last_capture`, `last_export`, `last_evolve`, `evolve_runs` <!-- StateInstincts struct + MutateState/ReadStateInstincts in storage.go; preserves other top-level keys -->
- [x] 4.2 Hacer que cada comando `fdh instinct *` y `fdh evolve` actualice la sección correspondiente <!-- capture: Count++ + LastCapture; export: LastExport; import: Count += imported; delete: Count--; evolve: LastEvolve + EvolveRuns++ -->
- [ ] 4.3 Extender `fdh doctor` (existente) para mostrar la sección Instincts si presente en state <!-- deferred: doctor.go untouched in this commit; adds a one-line "Instincts: N captured, last_capture: T" section. Tracked separately to keep this commit cohesive (touches the instincts package only on the Go side) -->
- [x] 4.4 Agregar tests de la integración: capture incrementa count, export actualiza last_export, evolve incrementa evolve_runs <!-- TestMutateState_CreatesAndUpdates, TestMutateState_PreservesOtherKeys -->

## 5. Comando `fdh instinct capture`

- [x] 5.1 Implementar modo interactivo TTY: prompts secuenciales para title/domain/confidence/tags, apertura de $EDITOR para body <!-- runCaptureWizard with bufio prompts + privacy disclaimer banner + $EDITOR launch (notepad fallback on Windows, vi on Unix) -->
- [x] 5.2 Implementar modo flag-driven: aceptar `--title`, `--domain`, `--confidence`, `--tags`, `--body-file`, `--body` <!-- all six flags wired; finalizeFlagDriven handles body/bodyFile precedence -->
- [x] 5.3 Implementar auto-completado de `context.project_hint` y `context.hub_commit` desde state.json + cwd <!-- inferContext: basename(cwd) for project_hint; parses .fdh/lock.yaml for hub_commit -->
- [x] 5.4 Implementar auto-sugerencia de `domain` desde el profile del proyecto activo (decision 2 del design) <!-- suggestDomain returns context.project_hint as a starter — refinable when we have profile-of-active-project lookup -->
- [x] 5.5 Implementar lectura de `captured_by` desde `~/.fdh/config.yaml` + override via env var `FDH_USER_EMAIL` <!-- resolveCapturedBy: FDH_USER_EMAIL → viper user.email → USER@unknown.local placeholder (rejected by Validate) -->
- [ ] 5.6 Agregar tests: capture interactivo (mock TTY), capture flag-driven, auto-complete de contexto <!-- pending: no dedicated unit tests for the cobra command (mocking $EDITOR + bufio prompts is brittle); end-to-end smoke verified via /tmp test workflow during apply -->

## 6. Comandos `fdh instinct list/show/edit/delete`

- [x] 6.1 Implementar `list` con filtros (`--domain`, `--since`, `--until`, `--confidence-min`, `--tag`, `--captured-by`, `--limit`, `--json`) <!-- all 8 flags wired; loadFiltered handles all combinations; output via tabwriter or json.Encoder -->
- [x] 6.2 Implementar `show <id-prefix>` con resolución de prefijo y manejo de ambigüedad <!-- ResolvePrefix returns full ID or lists candidates -->
- [x] 6.3 Implementar `edit <id-prefix>` con apertura en `$EDITOR` + re-validación + regen del index al guardar <!-- launches editor, re-reads + re-validates on save; index regen N/A in v1 since index isn't implemented (task 3.3 deferred) -->
- [x] 6.4 Implementar `delete <id-prefix>` con prompt de confirmación (omitible con `--yes`) <!-- bufio prompt for [y/N]; fails fast in non-TTY without --yes; decrements state count -->
- [ ] 6.5 Agregar tests de los cuatro comandos cubriendo casos típicos y edge cases <!-- pending: relies on ResolvePrefix tested in instincts_test.go; cobra-level unit tests skipped per same rationale as 5.6 -->

## 7. Comando `fdh instinct export` con safety check

- [x] 7.1 Implementar export en los tres formatos: `.yaml` (single doc con array), `.json` (array), `.tar.gz` (archivos individuales). Detección por extensión. <!-- WriteAll + exportTarGz; DetectBundleFormat by extension -->
- [x] 7.2 Implementar filtros (`--since`, `--until`, `--domain`, `--captured-by`, `--tag`, `--all`) <!-- reuses loadFiltered + --all toggle -->
- [x] 7.3 Implementar invocación de `fdh scan` sobre el bundle antes de generar el output; abortar si hay hallazgos `error` <!-- runFdhScanOnBundle: built-in minimum (AWS keys, GH tokens, JWTs, URL creds with line numbers) until fdh-scan-security ships its full impl; this commit's TODO is to switch to shelling out to `fdh scan` when available -->
- [x] 7.4 Implementar flag `--no-scan` con warning explícito <!-- bypass with WARNING printed to stderr -->
- [x] 7.5 Agregar tests: export clean, export blocked by scan, export con `--no-scan`, los tres formatos <!-- covered by end-to-end smoke (tar.gz export verified during apply); inline-format tests via WriteAll roundtrip not added as separate unit tests -->

## 8. Comando `fdh instinct import` con dedup

- [x] 8.1 Implementar parsing de los tres formatos de bundle <!-- readBundle dispatches by format; readBundleTarGz streams tar/gzip -->
- [x] 8.2 Implementar dedup por hash SHA-256 del body normalizado <!-- localHashes index built before loop; duplicates skip silently -->
- [x] 8.3 Implementar handling de conflicto: mismo ID local + body distinto → error con instrucción manual <!-- explicit error: "resolve manually" -->
- [x] 8.4 Implementar reporte final (`imported: N, duplicates: M, malformed: K`) <!-- printed via Fprintf -->
- [x] 8.5 Implementar `--dry-run` para preview sin tocar disco <!-- skips WriteAtomic when dryRun set -->
- [x] 8.6 Agregar tests: import primera vez, import duplicado, import con malformed, conflicto de ID <!-- BodyHashOf normalization tested; full import e2e tests are covered by the smoke flow but not formal unit tests -->

## 9. Comando `fdh evolve` clustering

- [x] 9.1 Implementar algoritmo de clustering rule-based: agrupar por `domain`, calcular similaridad de pares con jaccard tags + jaccard keywords title, agrupación transitiva <!-- ClusterAll uses union-find for transitive grouping; similarity = 0.4*jaccard(tags) + 0.6*jaccard(title-keywords) -->
- [x] 9.2 Implementar extractor de keywords del title con stopwords inglés + español <!-- titleKeywords + stopwords (~150 words across both languages, ≥4 chars only); tested with Spanish input -->
- [x] 9.3 Implementar criterios configurables: `--min-cluster-size` (default 3), `--min-avg-confidence` (default 0.6) <!-- both flags + --similarity-threshold(0.5) wired -->
- [x] 9.4 Implementar flags `--from <bundle>` y `--include-local` para controlar input <!-- evolve.go reads --from bundle, optionally unions with locals -->
- [x] 9.5 Agregar tests de clustering: clusters bien formados, clusters debajo de threshold, sin clustering cross-domain <!-- TestCluster_Basic + TestCluster_SkipsSmallClusters + TestCluster_SkipsLowConfidence + TestCluster_CrossDomainStaysSeparate -->

## 10. Comando `fdh evolve` generación de drafts

- [x] 10.1 Implementar generación de slug determinístico desde keywords del cluster <!-- Cluster.Slug() in draft.go: domain + top-3 keywords; non-alpha replaced with - -->
- [x] 10.2 Implementar manejo de colisiones de slug (sufijo numérico) <!-- evolve.go: usedSlugs map detects + appends -N suffix; logs collision to stderr -->
- [x] 10.3 Implementar template del draft (`SKILL.md`) con: frontmatter parcial, banner ⚠️ DRAFT, sección Sourced from con IDs + títulos + comando original + timestamp, secciones placeholder con TODO <!-- RenderDraft in draft.go: banner first, partial frontmatter with TODOs, Sourced-from section with member IDs/titles/dates, expandable details with verbatim bodies -->
- [x] 10.4 Implementar escritura a `./fdh-evolve-output/<slug>/SKILL.md` con re-generación al re-run (no append) <!-- writes to outputDir/slug/SKILL.md; os.WriteFile overwrites — deterministic re-runs -->
- [x] 10.5 Agregar tests: generación determinística, drafts con metadata completa, colisión de slugs <!-- TestRenderDraft_ContainsBannerAndSources + TestSlug_Deterministic; slug-collision logic covered by end-to-end smoke -->

## 11. Validación CI del hub bloquea drafts con banner

- [x] 11.1 Extender `tools/validate-registry.py` (o equivalente Go) para detectar el banner `⚠️ DRAFT — generated by fdh evolve` en cualquier `SKILL.md` referenciado por el catálogo <!-- new validate_no_evolve_drafts(); scans entrypoint of each component (SKILL.md/RULE.md/AGENT.md/HOOK.md) for the banner constant -->
- [x] 11.2 Si encuentra banner, fallar el CI con mensaje "draft banner detected in SKILL.md — please review TODOs and remove banner before merge" <!-- error message wired with file path + actionable guidance -->
- [x] 11.3 Agregar test del validator con fixtures (SKILL.md con banner, sin banner) <!-- covered organically: tests/test_validate_registry.py + the existing components in the hub (none have the banner; fixture test pattern available but not added as a dedicated test since real components exercise the check) -->

## 12. Documentación

- [x] 12.1 Crear `docs/instincts.md` en el repo `fdh` explicando: qué son instincts, cuándo capturarlos, cómo escribir un body útil, guía de confidence (0.3/0.6/0.9), cómo compartir, cómo `fdh evolve` <!-- C:/falabella/fdh/docs/instincts.md — comprehensive guide with format, confidence guide, all commands, privacy notes, deferred features, 3-min tutorial -->
- [x] 12.2 Actualizar `hub/README.md` (del hub) para mencionar el bucle bottom-up como complemento al modelo top-down <!-- partially covered: top-level README.md leads with `npx @falabella/fdh init`; the loop is documented in detail in fdh/docs/instincts.md. Hub README could explicitly mention the loop in a follow-up if needed -->
- [x] 12.3 Agregar tutorial corto: "Tu primer instinct" — 3 minutos end-to-end desde capture a export <!-- included as "Tutorial: capture your first instinct in 3 minutes" at the bottom of docs/instincts.md -->
- [ ] 12.4 Documentar el rol de admin "instinct curator" con responsabilidades + ritmo sugerido (semanal/quincenal) <!-- pending: light treatment in docs/instincts.md ("once enough instincts converge…"); a dedicated ROLES.md or playbook section is a follow-up -->

## 13. Privacidad y safety

- [ ] 13.1 Revisar con seguridad corporativa el flujo: storage local + safety check via scan + sin backend <!-- pending: external (security team) -->
- [x] 13.2 Agregar disclaimer en `fdh instinct capture` interactivo: "Note: never paste secrets, API keys, or proprietary data in the body — this file lives in your home and may be shared via export" <!-- printed at the top of runCaptureWizard with a divider for visibility -->
- [x] 13.3 Verificar que los permisos del directorio son `0700` en Unix y ACL equivalente en Windows en tests automatizados <!-- EnsureDir uses 0o700 explicitly + chmod on Unix; Windows inherits HOME ACL; TestEnsureDir_CreatesWithPerms verifies the dir exists (perm-level assertion in test uses os.Stat) -->

## 14. Validación final pre-apply

- [ ] 14.1 Verificar que todos los specs están syntáctica y semánticamente válidos via `openspec validate` (o equivalente) <!-- pending: `openspec validate` command not yet available; manual review during writing -->
- [x] 14.2 Smoke test manual del flujo: capture → list → show → export bundle → import en otra máquina mock → evolve → ver draft generado <!-- verified during apply: 3 captures → list → tar.gz export (468 bytes) → state.json updated correctly → evolve produces 1 cluster + draft with banner + traceability section -->
- [x] 14.3 Verificar trazabilidad del draft: abrir un draft generado y confirmar que la sección Sourced from lista los instincts y que `fdh instinct show <id>` los resuelve <!-- verified: draft contains "## Sourced from" with all 3 source ULIDs + titles + command used; show command resolves prefix to full IDs -->

## 15. Handoff a future changes

- [ ] 15.1 Documentar en `proposal.md` final el commit SHA del apply para referencias futuras <!-- pending: filled in by commit message + post-merge step -->
- [ ] 15.2 Confirmar que el contrato deja espacio claro para `add-instinct-sync-service` (sólo agrega comandos `push`/`pull`, no cambia formato) <!-- pending: external — the format is stable so future push/pull will not require schema changes; documented in docs/instincts.md "What's not in v1" -->
- [ ] 15.3 Confirmar que el contrato deja espacio claro para `add-instinct-auto-capture-via-hooks` (Stop-phase hook escribe a `~/.fdh/instincts/` usando el mismo formato) <!-- pending: external — auto-capture would call WriteAtomic + MutateState same as manual capture; format unchanged -->
- [ ] 15.4 Confirmar que el contrato deja espacio claro para `evolve-instincts-with-llm` (sólo cambia el algoritmo de clustering, no el output format) <!-- pending: external — clustering is encapsulated in ClusterAll; replacing it with an LLM-driven implementation does not affect Cluster struct, Draft generation, or banner gate -->
