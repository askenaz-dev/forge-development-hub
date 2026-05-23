## 1. Estructura del hub y schema v2

- [x] 1.1 Crear directorio `hub/` en la raíz del repo
- [x] 1.2 Mover y reescribir `skills/registry.yaml` a `hub/registry.yaml` con `schema_version: 2`, agregando `kind: skill` a la entry `design-system` existente
- [x] 1.3 Crear symlink POSIX `skills/registry.yaml` → `hub/registry.yaml` (en Windows, generar copia via script de CI; documentar en `hub/README.md`)
- [x] 1.4 Crear `hub/profiles.yaml` con `schema_version: 1` y un profile `minimal` (entry vacía por ahora; se puebla en tarea 5.4 cuando las entries reales existan)
- [x] 1.5 Crear `hub/README.md` documentando: nuevo layout, las cuatro primitivas, semántica de profiles, relación con `.fdh/manifest.yaml` del consumer
- [x] 1.6 Actualizar `skills/README.md` para apuntar al nuevo `hub/registry.yaml` y explicar el symlink/redirect de compat

## 2. Tooling de migración

- [x] 2.1 Crear `tools/migrate-registry-v1-v2.py` que tome un `registry.yaml` v1 y produzca v2 (agrega `kind: skill` a cada entry, bumpea `schema_version`)
- [x] 2.2 Hacer la migración idempotente: correr el script sobre un archivo ya v2 sale con código cero sin modificarlo
- [x] 2.3 Agregar tests del script (`tests/test_migrate_registry.py`) cubriendo: migración v1→v2, idempotencia sobre v2, error claro sobre v3 desconocido
- [x] 2.4 Ejecutar el script sobre el catálogo actual para producir `hub/registry.yaml` final (verificación de la tarea 1.2)

## 3. Tooling de validación extendido

- [x] 3.1 Extender `tools/validate-registry.py` para schema v2: validar campo `kind` obligatorio, validar coherencia kind ↔ directorio (`kind: rule` debe estar en `rules/`), validar `agents_supported` no vacío, validar `min_fdh_version` semver válido
- [x] 3.2 Extender `tools/validate-registry.py` para detectar directorios huérfanos en los cuatro dirs (`skills/`, `rules/`, `agents/`, `hooks/`) y entries sin path real
- [x] 3.3 Agregar a `tools/validate-registry.py` validación de `hub/profiles.yaml`: cada profile referencia componentes existentes con el kind correcto
- [x] 3.4 Crear `tools/validate-manifest.py` que valide un `.fdh/manifest.yaml` contra un catálogo del hub (referencias resueltas, schema correcto, profile existente si referenciado)
- [x] 3.5 Agregar tests para `validate-registry.py` cubriendo: registry v2 válido, duplicados por kind, huérfanos, paths inconsistentes con kind, profile con componente inexistente
- [x] 3.6 Agregar tests para `validate-manifest.py` cubriendo: manifest minimal con profile, manifest con extends, manifest con profile inexistente, manifest sin profile y sólo componentes explícitos

## 4. Primera entry real: rule `no-console-log`

- [x] 4.1 Crear directorio `rules/no-console-log/`
- [x] 4.2 Crear `rules/no-console-log/RULE.md` con frontmatter completo (`name: no-console-log`, `kind: rule`, `scope: ["**/*.{ts,tsx,js,jsx}"]`, `severity: warning`, `agents_supported: [claude-code, codex, copilot, opencode]`, `description`, `tags`) y cuerpo markdown explicando la regla + por qué + ejemplo de la alternativa esperada (logger del proyecto)
- [x] 4.3 Agregar entry correspondiente en `hub/registry.yaml`
- [x] 4.4 Verificar que `tools/validate-registry.py` pasa después de la inclusión

## 5. Primera entry real: agent `falabella-pr-writer`

- [x] 5.1 Crear directorio `agents/falabella-pr-writer/`
- [x] 5.2 Crear `agents/falabella-pr-writer/AGENT.md` con frontmatter completo (`name: falabella-pr-writer`, `kind: agent`, `description`, `agents_supported: [claude-code]`, `tools: [Read, Grep, Bash]`) + system prompt describiendo el rol + template con secciones `## What`, `## Why`, `## Test plan`, `## Risk`
- [x] 5.3 Agregar entry correspondiente en `hub/registry.yaml`
- [x] 5.4 Verificar que `tools/validate-registry.py` pasa después de la inclusión

## 6. Primera entry real: hook `doctor-on-session-start`

- [x] 6.1 Crear directorio `hooks/doctor-on-session-start/`
- [x] 6.2 Crear `hooks/doctor-on-session-start/hook.json` con `event: "SessionStart"`, `matcher: "*"`, `command: "fdh doctor --quiet"`, `description: "Run fdh doctor at session start to surface drift early"`, `timeout_seconds: 10`
- [x] 6.3 Crear `hooks/doctor-on-session-start/HOOK.md` documentando propósito, evento, command, agentes soportados, qué hace `fdh doctor --quiet`, cómo modificar
- [x] 6.4 Agregar entry correspondiente en `hub/registry.yaml`
- [x] 6.5 Verificar que `tools/validate-registry.py` pasa después de la inclusión

## 7. Poblar profile `minimal`

- [x] 7.1 Actualizar `hub/profiles.yaml` con el profile `minimal` referenciando los cuatro componentes reales: `skills: [design-system]`, `rules: [no-console-log]`, `agents: [falabella-pr-writer]`, `hooks: [doctor-on-session-start]`
- [x] 7.2 Agregar `description` y `owner_team: dx-platform` al profile
- [x] 7.3 Verificar que `tools/validate-registry.py` pasa después de la inclusión (referencias del profile resuelven correctamente)

## 8. CI updates

- [x] 8.1 Actualizar `.github/workflows/validate-registry.yml` para correr `tools/validate-registry.py` extendido sobre cualquier PR que toque `hub/**`, `skills/**`, `rules/**`, `agents/**`, `hooks/**`
- [x] 8.2 Agregar job al mismo workflow que corra `tools/validate-manifest.py` sobre fixtures de manifests de ejemplo (crear `tests/fixtures/manifests/` con casos válidos e inválidos)
- [x] 8.3 Agregar job que verifique en Linux que `skills/registry.yaml` es symlink válido a `hub/registry.yaml`; en Windows que el contenido es idéntico (copy regenerada)
- [x] 8.4 Documentar en `hub/README.md` cómo correr los validadores localmente antes de PR

## 9. Documentación cross-ecosistema

- [x] 9.1 Actualizar root `CLAUDE.md` (`C:\falabella\falabella-development-hub\CLAUDE.md`) para mencionar el nuevo `hub/` directory, las cuatro primitivas y el modelo manifest/lock/state
- [x] 9.2 Crear `hub/CONSUMER-CONTRACT.md` documentando los schemas de `.fdh/manifest.yaml`, `.fdh/lock.yaml` y `~/.fdh/state.json` (con ejemplos) y los markers `.fdh-managed.yaml` y `.gitignore` sectionado
- [x] 9.3 Verificar que la documentación referencie correctamente los specs nuevos (links a `openspec/specs/<capability>/spec.md`)

## 10. Validación final pre-archive

- [x] 10.1 Correr `tools/validate-registry.py` localmente y verificar exit 0
- [x] 10.2 Correr `tools/validate-manifest.py` sobre las fixtures y verificar comportamiento esperado (válidos pasan, inválidos fallan con mensajes claros)
- [x] 10.3 Verificar que `hub/registry.yaml` contiene exactamente cuatro entries (una por kind), todas con paths existentes
- [x] 10.4 Verificar que `hub/profiles.yaml` contiene el profile `minimal` con las cuatro listas pobladas
- [x] 10.5 Verificar que el symlink/copia de `skills/registry.yaml` funciona (lectura desde la ruta vieja produce el mismo contenido que desde la nueva)
- [ ] 10.6 Verificar que CI workflow corre verde en PR de prueba <!-- pending: needs actual push + PR; workflow YAML syntactically valid + commands smoke-tested locally -->



## 11. Handoff a sibling changes

- [ ] 11.1 Documentar en `proposal.md` (final) el commit SHA del apply para que `fdh-cli-npm-distribution` y `add-instinct-collaboration` puedan referenciarlo <!-- pending: needs git commit to exist; will be filled in by the commit message / post-merge step -->
- [ ] 11.2 Confirmar con equipo `fdh` (repo hermano Go) que los specs nuevos están listos para que arranque su tracking de implementación <!-- pending: external coordination, outside apply scope -->
- [ ] 11.3 Si `fdh-cli-npm-distribution` ya está en apply, coordinar el orden de release del binario `fdh` que implemente este schema <!-- pending: external coordination, outside apply scope -->

