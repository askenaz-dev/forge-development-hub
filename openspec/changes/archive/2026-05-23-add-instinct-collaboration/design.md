*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Context

Tras `hub-v2-manifest-state-profiles` (que introduce las 4 primitivas, manifest/lock/state, fdh-scan y profiles), el hub tiene un modelo top-down funcional: equipo plataforma cura skills/rules/agents/hooks → devs los consumen. Lo que falta para escalar a 500 devs sin que plataforma sea bottleneck es un **bucle inverso**: dev genera conocimiento → equipo plataforma cura → se vuelve catálogo formal.

El concepto `continuous-learning-v2` de ECC (https://github.com/affaan-m/ECC) propone instincts: pequeñas notas de dominio que un dev captura sobre la marcha, con confidence scoring y contexto, que pueden compartirse y eventualmente convertirse en skills curados. Este change adopta ese modelo en su variante más simple: **file-based local, sin backend, sin LLM**.

**Stakeholders:**
- Devs Forge: consumen el bucle como flujo opcional para capturar/compartir patrones tribales.
- Admins del hub: corren `fdh evolve` sobre instincts agregados para proponer nuevos skills.
- Equipo seguridad: revisa el modelo de privacidad y el safety-check pre-export.
- Equipo `fdh` Go: implementa los nuevos comandos.

**Constraints duras:**
- DEPENDE de `hub-v2-manifest-state-profiles` aplicado (state.json, fdh-scan, formato de skills).
- Sin backend HTTP en v1 (intercambio manual via archivos `.tar.gz`).
- Sin LLM en v1 (clustering rule-based).
- Privacidad por default — captura nunca incluye contenido del proyecto automáticamente.
- Compat con flujo normal de `fdh` — instincts es opt-in, no afecta `fdh init`/`install`/`update`.

**Sibling/dependent changes:**
- `hub-v2-manifest-state-profiles` (debe aplicarse primero).
- `fdh-cli-npm-distribution` (paralelo, sin acoplamiento).
- Future changes habilitados: `add-instinct-sync-service`, `add-instinct-auto-capture-via-hooks`, `evolve-instincts-with-llm`, `add-instinct-team-curation`, `add-instinct-review-loop`.

## Goals / Non-Goals

**Goals:**

- Permitir captura manual de instincts por dev en archivos locales con formato YAML estructurado.
- Permitir intercambio via export/import de bundles entre devs y equipos.
- Habilitar a admins curar via `fdh evolve` que clusterea y genera drafts de skills.
- Garantizar privacidad por default: cero captura automática de contenido del proyecto + safety check con `fdh scan` pre-export.
- Mantener determinismo total (sin LLM) en v1.
- Diseñar contratos extensibles para que future changes (sync, hooks, LLM) sean additive.

**Non-Goals:**

- **No** backend HTTP para sync entre devs — defer a `add-instinct-sync-service`.
- **No** auto-captura via hooks — defer a `add-instinct-auto-capture-via-hooks`.
- **No** clustering semántico con embeddings — defer a `evolve-instincts-with-llm`.
- **No** review/voting workflow entre devs — defer a `add-instinct-review-loop`.
- **No** encryption at rest de los instincts locales — defer hasta requerimiento explícito de seguridad.
- **No** versionado/historial por instinct — edits son in-place; si se necesita historial, future change.
- **No** instincts como componentes del catálogo del hub — instincts son input al proceso de curación; el output curado son skills (que ya tienen su propio modelo).

## Decisions

### Decision 1: Confidence es input manual del dev en v1

El campo `confidence` (float 0.0-1.0) en el frontmatter del instinct es **input manual** del dev al momento de capture. No se calcula heurísticamente.

**Razones:**
- El dev sabe mejor que ningún algoritmo qué tan seguro está de un patrón.
- Heurísticas (ej. ponderar por frecuencia de patrones similares) requerirían LLM o algoritmos no triviales — fuera de scope v1.
- Mantener el modelo simple y honesto en v1; refinar después con datos reales.

**Default sugerido en el wizard**: `0.5` ("idea preliminar"). El dev sube a `0.7-0.8` si está más confiado.

**Alternativa descartada**: calcular confidence post-captura basado en N (cuántas veces un patrón similar fue capturado). Requiere clustering pre-confidence — circular. Defer a `evolve-instincts-with-llm` cuando haya embeddings.

### Decision 2: Domain auto-sugerido desde state.json del proyecto activo

`fdh instinct capture` SHALL inferir un `domain` sugerido desde el contexto del cwd: si el `cwd` corresponde a un proyecto registrado en `~/.fdh/state.json` bajo `projects:`, lee el `manifest.profile` (si declarado) o un primer tag de los componentes instalados para sugerir un domain. El dev puede aceptar (Enter) o sobreescribir.

**Ejemplos:**
- Cwd es `~/work/checkout-service`, su manifest declara `profile: forge-backend-go` → domain sugerido: `backend-services-go` (o el slug del profile).
- Cwd no está en state → no hay sugerencia, dev escribe libre.

**Razones:**
- Reduce fricción del capture manual sin imponer una taxonomía global.
- Permite normalización gradual: si muchos devs aceptan la sugerencia del profile, los domains terminan alineados naturalmente.

**Alternativa descartada**: domain enforcement contra una taxonomía cerrada. Innecesariamente rígido en v1 cuando aún no sabemos qué domains importan.

### Decision 3: `fdh evolve` opera sobre locales + bundles importados, controlable

`fdh evolve` por default opera sobre `~/.fdh/instincts/` (locales). Con `--from <bundle>` opera sobre el contenido de un bundle importado (sin requerir que los instincts del bundle estén copiados a locales). Con `--include-local` combinable con `--from`, opera sobre la unión.

**Workflow de admin típico:**
1. Recibe bundle de un equipo via Slack / shared drive.
2. `fdh evolve --from team-bundle.tar.gz` para clusterear sólo lo del equipo sin mezclar con sus propios capturados.
3. Si quiere combinar: `fdh evolve --from team-bundle.tar.gz --include-local`.

**Razón**: separar contextos. Un admin puede tener sus propios instincts personales que no quiere mezclar con el análisis de los del equipo.

**Alternativa descartada**: forzar import antes de evolve. Genera deduplicación temporal innecesaria y persiste instincts ajenos en `~/.fdh/instincts/` cuando el admin sólo quería analizarlos efímeramente.

### Decision 4: Review loop entre devs queda fuera de scope

El concepto de que un dev pueda votar/etiquetar instincts de otros como útiles/no-útiles antes de que admin evolve es interesante pero queda para `add-instinct-review-loop` future change.

**Razón**: requiere mecanismo de identidad/propagación de votos que no es trivial sin backend. El admin curador en v1 hace el rol de filtro con su juicio + thresholds de cluster.

### Decision 5: Encryption at rest fuera de scope hasta requerimiento explícito

Los archivos en `~/.fdh/instincts/` NO se cifran en v1. Quedan bajo la protección del home del dev (permisos `0700` del directorio).

**Razones:**
- Captura es manual y el body es lo que el dev escribe — el dev controla qué entra.
- `fdh scan` corre pre-export para evitar exfiltración accidental de secrets.
- Encryption at rest requiere key management (per-user keys, recovery, rotación) que es un proyecto en sí mismo.

**Trigger para reconsiderar**: si seguridad Forge declara los archivos `~/.fdh/instincts/` como "datos clasificados", future change `add-instinct-encryption-at-rest` se prioriza.

### Decision 6: Bundle de export soporta tres formatos según volumen

- **`.yaml`**: single YAML document con array de instincts. Ideal para bundles pequeños (≤20 instincts), legible humano, diff-friendly.
- **`.json`**: single JSON array. Ideal para consumo por scripts/CI, mismo tamaño que YAML.
- **`.tar.gz`**: archivos individuales `<id>.yaml` empaquetados. Ideal para bundles grandes (≥50 instincts), permite extracción parcial.

Detección automática por extensión del output file.

**Razón**: YAML/JSON para legibilidad + small bundles; tar.gz para escalabilidad. Cubre tanto el caso "share with one colleague via email" como "team-wide quarterly dump".

### Decision 7: Stopwords para Jaccard incluyen inglés y español

Para el cálculo de keywords del title en clustering, el filtro de stopwords SHALL incluir las listas estándar de **inglés y español** (Forge es regional LATAM con devs bilingües). Lista hardcodeada en el binario, ~100 palabras por idioma.

**Razón**: instincts pueden escribirse en cualquiera de los dos idiomas. Filtrar sólo inglés deja palabras como "el", "la", "para", "que" como keywords, distorsionando los clusters.

### Decision 8: Conflict handling en import — same id, different body es error

Si un import encuentra un instinct con ID existente local pero body distinto, SHALL fallar con error reportando el conflicto. El dev decide manualmente: keep local, replace con import, o renombrar.

**Razón**: IDs son ULIDs únicos. Mismo ID + body diferente = corrupción o edit divergente. No es safe resolver silenciosamente.

**Alternativa descartada**: auto-replace o auto-keep. Genera surprise comportamiento; mejor fallar y forzar decisión consciente.

### Decision 9: Captured_by se lee de `~/.fdh/config.yaml` con override env var

El campo `captured_by` se persiste auto desde `~/.fdh/config.yaml` (existente, contiene el email/identifier del dev). Si esa config no existe, `fdh instinct capture` falla con instrucción de correr `fdh init` o `fdh config set user.email <...>` primero. Override via env var `FDH_USER_EMAIL` (útil en CI).

**Razón**: identidad debe ser deterministic y trazable; pedir cada vez es fricción innecesaria.

## Risks / Trade-offs

- **Confidence manual genera valores inconsistentes entre devs** → aceptado en v1; mitigable con guía en docs ("0.3 = idea inicial, 0.6 = patrón observado en 3+ ocasiones, 0.9 = regla universal del dominio"). En v2 con embeddings se puede normalizar.

- **Dev olvida correr `fdh instinct capture` cuando descubre algo** → aceptado en v1; mitigado parcialmente por el future change de auto-capture via hooks. La fricción del paso manual es el costo del modelo file-based.

- **Bundles compartidos via Slack/email se vuelven informales** → aceptado en v1; el future change `add-instinct-sync-service` resuelve cuando volumen lo justifique.

- **Rule-based clustering produce clusters de baja calidad para domains con tags inconsistentes** → mitigado por thresholds configurables; `fdh evolve` reporta razones de skip claras para que el admin entienda qué falta.

- **Drafts generados son "casi vacíos" porque tienen muchos TODO placeholders** → aceptado; el banner explícito previene que se publiquen sin curación. El valor está en la trazabilidad a instincts fuente, no en la auto-generación de contenido.

- **`fdh scan` pre-export no detecta todo (false negatives)** → aceptado; el modelo es defense-in-depth. Si scan falla en detectar, el dev sigue siendo responsable. Documentar que `--no-scan` es flag deliberadamente verbose.

- **Edit manual concurrente desde dos terminales corrompe el index** → mitigado por escrituras atómicas + regeneración automática del index al detectar staleness; pero edits concurrentes al mismo instinct desde dos máquinas (HOME compartido) pueden perder cambios. Documentar.

- **Acumulación de instincts viejos sin valor** → mitigado por `--since`/`--until` en list/export; future change `add-instinct-archive` para auto-mover viejos a `~/.fdh/instincts-archive/`.

- **Captura manual no llega a masa crítica → admin nunca corre evolve** → riesgo de adopción real; mitigado parcialmente por evangelización en docs y plantillas. Si después de 3 meses no hay tracción, este change se evalúa para deprecation o pivotaje a auto-capture (que de todas formas era el plan natural).

## Migration Plan

Migración del usuario es no-op porque el feature es opt-in:

1. **Post-apply en hub**: este change agrega los specs y deja documentadas las capabilities. Cero cambios al filesystem del hub.
2. **Implementación en `fdh` Go**: 2-3 sprints. Cada developer adopta cuando quiere.
3. **Primer dev usa `fdh instinct capture`**: se crea `~/.fdh/instincts/` automáticamente, sin acción adicional.
4. **Primer admin corre `fdh evolve`**: produce drafts en `./fdh-evolve-output/`. Si los abre y le gustan, PR al hub.

Rollback: el feature es opt-in. Si se decide remover, `~/.fdh/instincts/` puede borrarse manualmente o vía `fdh instinct delete --all`.

## Open Questions

Resueltas en este design:
- ✅ Confidence: manual v1 con default 0.5 sugerido.
- ✅ Domain auto-inferido: sí, sugerencia desde state.json del proyecto activo.
- ✅ Evolve sobre locales/importados: ambos, controlado por flags `--from`/`--include-local`.
- ✅ Review loop: defer a `add-instinct-review-loop`.
- ✅ Encryption at rest: defer hasta requerimiento explícito.
- ✅ Bundle formats: yaml/json/tar.gz según volumen.
- ✅ Stopwords: inglés + español.
- ✅ Conflict en import: error, decisión manual.
- ✅ Captured_by: de config.yaml + env var override.

Quedan abiertas para apply / changes futuros:
- **¿`fdh evolve` debe sugerir el `agents_supported` del draft basado en los instincts fuente?** Probable yes — si todos los instincts mencionan código Go, sugerir `[claude-code, codex]`. Refinable en apply.
- **¿Garbage collection de bundles `.tar.gz` viejos en algún cache?** Probablemente no — los bundles son del dev, viven donde el dev los puso.
- **¿Profiles del hub deberían tener concepto "encourage instincts from this domain"?** Interesante pero no v1.
- **¿`fdh doctor` debería sugerir "hace N días no capturas un instinct" como reminder?** UX call; probable yes con flag `--silent` para devs que no quieren ese nudge.
