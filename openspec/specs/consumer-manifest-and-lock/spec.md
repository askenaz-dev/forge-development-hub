# consumer-manifest-and-lock Specification

## Purpose

Define el contrato declarativo del consumer: `.fdh/manifest.yaml` (committed, editado por humanos, expresa intención —qué profile, qué componentes, qué scope) y `.fdh/lock.yaml` (committed, escrito por `fdh install`, captura la resolución reproducible con `hub_commit` e integrity hashes por componente). Establece el flow `manifest → resolución → lock` análogo a `package.json` + `package-lock.json` del ecosistema npm, incluyendo `fdh install --frozen` para CI, auto-generación del manifest desde estado legacy de los pilots, y la regla de que ambos archivos viven bajo `.fdh/` y SHALL ser committed.

## Requirements

### Requirement: Archivo `.fdh/manifest.yaml` declara intención del consumer

El consumer repo SHALL contener un archivo `.fdh/manifest.yaml` committed que declare la intención del proyecto: qué profile usar (opcional), qué componentes individuales agregar/remover, y el scope (`project` por default, `user` opcional). Schema mínimo: `schema_version: 1`, opcionalmente `profile: <name>`, opcionalmente bloques `skills:`, `rules:`, `agents:`, `hooks:` con listas de `name`, opcionalmente `extends: { add_*, remove_* }`.

#### Scenario: Manifest minimalista con profile

- **WHEN** un admin crea `.fdh/manifest.yaml` con `schema_version: 1` y `profile: minimal`
- **THEN** `fdh install` resuelve los componentes del profile y los registra en `.fdh/lock.yaml`

#### Scenario: Manifest sin profile, sólo componentes explícitos

- **WHEN** `.fdh/manifest.yaml` no declara `profile` pero declara `skills: [{ name: design-system }]`
- **THEN** `fdh install` instala sólo `design-system`

#### Scenario: Manifest inválido

- **WHEN** `.fdh/manifest.yaml` declara `schema_version: 2` (no soportado)
- **THEN** `fdh install` falla con error accionable nombrando la versión soportada

### Requirement: Archivo `.fdh/lock.yaml` registra resolución reproducible

`fdh install` SHALL escribir `.fdh/lock.yaml` después de cada resolución exitosa, conteniendo: `schema_version`, `hub_commit` (SHA del hub al momento de resolver), `resolved_at` (timestamp), `resolved_from_profile` (opcional, informativo) y la lista expandida de componentes agrupada por kind con `name`, `version`, `path` (en el hub) e `integrity` (SHA-256 del contenido).

#### Scenario: Lock generado post-install

- **WHEN** `fdh install` resuelve un manifest con profile `minimal` y termina exitoso
- **THEN** existe `.fdh/lock.yaml` con `hub_commit` poblado y los cuatro componentes del profile listados bajo sus kinds respectivos, cada uno con `version` e `integrity`

#### Scenario: Lock determinista entre máquinas

- **WHEN** dos developers corren `fdh install` sobre el mismo manifest, mismo `registry.url`, y el hub no cambió entre las dos ejecuciones
- **THEN** ambos `.fdh/lock.yaml` son byte-idénticos

### Requirement: `fdh install --frozen` falla si el lock no satisface el manifest

`fdh install` SHALL aceptar un flag `--frozen` (estilo `npm ci`) que NO regenere el lock; si el lock existente no satisface el manifest actual (componente faltante, hub_commit incompatible, integrity mismatch), `fdh install --frozen` SHALL fallar con código distinto de cero sin tocar el filesystem. Sin `--frozen`, `fdh install` regenera el lock cuando es necesario.

#### Scenario: Frozen con lock válido

- **WHEN** se corre `fdh install --frozen` y el lock satisface el manifest
- **THEN** `fdh` materializa según el lock sin regenerarlo y sale con código cero

#### Scenario: Frozen con manifest modificado

- **WHEN** se edita el manifest agregando un skill nuevo y se corre `fdh install --frozen` sin regenerar lock
- **THEN** `fdh install --frozen` falla con error nombrando la divergencia y sugiriendo correr `fdh install` (sin frozen) para regenerar

#### Scenario: Frozen es default en CI

- **WHEN** `fdh install` detecta entorno CI (env var `CI=true` o equivalente) y no se pasó `--no-frozen`
- **THEN** se comporta como si `--frozen` hubiera sido pasado

### Requirement: Auto-generación del manifest desde estado legacy

Si `fdh install` corre en un repo que ya tiene componentes instalados (markers `.fdh-managed.yaml` o `.skill-version` legacy) pero no tiene `.fdh/manifest.yaml`, `fdh` SHALL generar un manifest derivado del estado real, listar los componentes encontrados, e instruir al developer a revisar y commitear el resultado antes de continuar.

#### Scenario: Repo con skills legacy sin manifest

- **WHEN** un dev del pilot corre `fdh install` por primera vez después del upgrade y su repo tiene `.skill-version` legacy en `.claude/skills/design-system/`
- **THEN** `fdh` genera `.fdh/manifest.yaml` con `skills: [{ name: design-system }]`, imprime "Generated manifest from legacy state — please review and commit `.fdh/manifest.yaml` before re-running install" y sale sin modificar más nada

#### Scenario: Repo nuevo sin estado legacy ni manifest

- **WHEN** `fdh install` corre en un repo limpio sin manifest ni estado legacy
- **THEN** `fdh install` imprime un mensaje accionable sugiriendo `fdh init` y sale con código distinto de cero

### Requirement: Tanto manifest como lock viven bajo `.fdh/` y SHALL ser committed

Los archivos `.fdh/manifest.yaml` y `.fdh/lock.yaml` SHALL vivir en el directorio `.fdh/` en la raíz del consumer repo y SHALL ser committed a control de versiones. El directorio `.fdh/` NO SHALL ser ignorado por `.gitignore`; sólo paths managed individuales bajo `.claude/`, `.codex/`, etc., son ignorados.

#### Scenario: .fdh/ no aparece en .gitignore managed block

- **WHEN** se inspecciona el bloque managed de `.gitignore` después de `fdh install`
- **THEN** no contiene `.fdh/`, `.fdh/*`, ni cualquier path que excluya manifest o lock del git

#### Scenario: Manifest está en git tras primer install

- **WHEN** un developer corre `fdh install` por primera vez en un repo nuevo y luego `git status`
- **THEN** `.fdh/manifest.yaml` y `.fdh/lock.yaml` aparecen como archivos modificados/nuevos, listos para `git add`
