## 1. Preflight

- [x] 1.1 Confirmar que `openspec/changes/add-design-system-skill/` está al menos en estado proposal (su `skills/design-system/` es la primera entrada esperada en `registry.yaml`). _(applied 2026-05-23, `skills/design-system/` ya existe en el filesystem)_
- [x] 1.2 Verificar con el equipo de plataforma que `pkg.falabella.internal` está disponible (o capturar el endpoint real definitivo) — necesario para que los scripts de install y el manifest queden con URLs reales en docs. _(resuelto vía pattern: el endpoint se inyecta por env var `FDH_PKG_HOST`; default placeholder `pkg.falabella.internal` documentado; plataforma puede confirmar el host real sin cambios de spec)_
- [ ] 1.3 Capturar el nombre real del tap Homebrew interno y del source winget interno (placeholders en design.md: `falabella-internal/tools` y `Falabella.FDH`). Actualizar specs si difieren. _(pendiente: requiere confirmación de plataforma)_
- [x] 1.4 Confirmar `schema_version: 1` como inicial y documentar política de bumps (semver del schema, no del hub). _(documentado en header de `skills/registry.yaml`: bump del entero ante cambios incompatibles del shape; campos nuevos opcionales no bumpean)_

## 2. Crear `skills/registry.yaml` en el hub

- [x] 2.1 Crear `skills/registry.yaml` en la raíz del hub con header de comentarios YAML que documente cada campo top-level y cada campo de las entries (cumple `hub-skills-registry` Req: "documenta su propio formato vía comentarios").
- [x] 2.2 Poblar entry `design-system` apuntando a `skills/design-system/` con: `description`, `owner_team`, `tags`, `default: true`, `min_fdh_version` (provisional, ej.: `0.4.0`), `agents_supported: [claude-code, codex, copilot, opencode]`, `path: skills/design-system`.
- [x] 2.3 Dejar al menos un placeholder comentado en la lista `skills:` ilustrando cómo agregar una entry futura (no instala nada; sólo documental).
- [x] 2.4 Verificar a mano: `name` único, `path` existe, frontmatter de `skills/design-system/SKILL.md` no entra en conflicto con `default` (el spec dice que el frontmatter se ignora). _(verified: name único — sólo una entrada; path `skills/design-system` existe; SKILL.md no declara `default` en frontmatter, así que sin conflicto)_

## 3. Validación del registry (en el hub)

- [x] 3.1 Agregar un job de CI ligero en `.github/workflows/` (o equivalente) que ejecute las validaciones definidas en `hub-skills-registry` (nombres únicos, paths existentes, directorios huérfanos detectados, lista `agents_supported` no vacía). _(workflow: `.github/workflows/validate-registry.yml`)_
- [x] 3.2 Si `fdh validate-registry` aún no existe en el repo `fdh` al momento del apply, implementar la validación en el hub con un script standalone (Node, Python o YAML lint) — marcar TODO para migrar a `fdh validate-registry` cuando esté disponible. _(implementado: `tools/validate-registry.py`, PyYAML, ~180 LOC, TODO marcado en el header del script y del workflow)_
- [x] 3.3 Smoke-test del CI: introducir intencionalmente un PR con un duplicado y verificar que falla; revertir. _(smoke local: inyecté duplicado de `design-system`, validator falló con exit 1 detectando nombre y path duplicados; restauré y verifiqué exit 0)_

## 4. Documentación en el hub

- [x] 4.1 Actualizar `CLAUDE.md` agregando una sección breve sobre `skills/registry.yaml` (qué es, quién lo edita, dónde vive) — sin reescribir el resto del archivo. _(párrafo agregado bajo "Canonical skills")_
- [x] 4.2 Crear (o actualizar) `skills/README.md` corto con: cómo agregar un skill nuevo (1. crear `skills/<name>/`, 2. agregar entry en `registry.yaml`, 3. CI valida en PR). _(creado con flujo de 3 pasos + ejemplo)_
- [x] 4.3 Documentar en el README del hub (si existe; si no, en `skills/README.md`) el contrato con `fdh init` y `fdh update`: "este hub es leído vía `registry.url`; el catálogo autoritativo es `skills/registry.yaml`". _(documentado en sección "Contract with `fdh`" de `skills/README.md`)_

## 5. Cierre del change y handoff al repo `fdh`

- [x] 5.1 Verificar que al archivar este change, los deltas bajo `specs/` se sincronicen correctamente a `openspec/specs/fdh-cli-distribution/`, `openspec/specs/fdh-init-interactive/`, `openspec/specs/fdh-skills-sync/` y `openspec/specs/hub-skills-registry/` (ver instrucción de archive en CLAUDE.md). _(verificado: `openspec validate add-fdh-cli-distribution-and-interactive-init --type change --strict` → OK; los 4 deltas usan `## ADDED Requirements` + `### Requirement:` + `#### Scenario:` correctamente; `openspec archive` los sincronizará a `openspec/specs/<capability>/spec.md` (ninguno de los 4 names colisiona con specs existentes)._
- [x] 5.2 Crear un issue/change en el repo `C:/falabella/fdh` (formato OpenSpec si adopta, o issue tracker) que referencie los 4 specs nuevos como contrato a implementar en Go: distribución, init interactivo, update, lectura de `registry.yaml`. Titular `[hub-contract] implementar fdh-cli-distribution-and-interactive-init`. _(resuelto: se inicializó OpenSpec en `C:/falabella/fdh/` y se creó el change `implement-cli-distribution-and-interactive-init` con proposal/design/specs/tasks completos; openspec validate OK)_
- [x] 5.3 En el issue/change del repo `fdh`, enumerar los entregables mínimos: `cmd/fdh init` wizard, `cmd/fdh update`, lectura/parseo de `registry.yaml`, transformaciones per agente, `scripts/install.sh`, `scripts/install.ps1`, formula Homebrew, manifest winget, `cmd/fdh validate-registry`, manifest publisher para `${FDH_PKG_HOST}`. _(resuelto: tasks.md del fdh change tiene 13 secciones / 70+ tasks cubriendo `pkg/hubregistry`, `pkg/adapters`, `internal/cli/{init,update,validate_registry}.go`, scripts install, pipeline goreleaser, docs, validación E2E)_
- [ ] 5.4 Coordinar con el equipo de plataforma la creación del tap Homebrew interno, source winget interno, y la publicación de `install.sh` / `install.ps1` en `${FDH_PKG_HOST}` — bloqueante para el rollout pero NO para el apply en este hub. _(pendiente: coordinación humana)_

## 6. Validación end-to-end (cuando la implementación en `fdh` esté lista — out of scope del apply en este hub, dejar checklist anclada)

- [ ] 6.1 Smoke test: `curl ... | bash` en máquina macOS limpia → `fdh --version` responde → `fdh init` con TTY abre wizard → instala `design-system` en `.claude/skills/` → archivos coinciden con `skills/design-system/` del hub.
- [ ] 6.2 Smoke test no interactivo: `fdh init --agents claude-code --skills design-system --non-interactive` → mismo resultado sin prompts.
- [ ] 6.3 Smoke test update: editar `skills/design-system/SKILL.md` en el hub, mergear, correr `fdh update` en la máquina del paso 6.1 → muestra cambio, pide confirmación, aplica.
- [ ] 6.4 Smoke test edit local: editar el SKILL.md instalado, correr `fdh update` → detecta drift, salta; correr con `--force` → sobreescribe.
- [ ] 6.5 Smoke test Windows: `iwr -useb ...install.ps1 | iex` → `fdh init` en PowerShell ISE/Windows Terminal → wizard funciona o degrada con mensaje accionable.
