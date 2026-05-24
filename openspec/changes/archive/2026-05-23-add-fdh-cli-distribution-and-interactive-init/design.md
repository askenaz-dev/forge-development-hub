*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Context

El CLI `fdh` ya existe en el repo hermano `C:/forge/fdh` (Go + cobra + viper). Su comando `init` (ver `internal/cli/init.go`) hoy configura registry + scope y corre `doctor`, pero es **no interactivo y no consume skills** — sólo escribe `<userConfigDir>/fdh/config.yaml`. La detección de agentes IA existe parcialmente dentro de `doctor` (vía `rc.Adapters.DetectAll`), pero no se expone como elección al usuario.

El hub `forge-development-hub` actualmente espeja OpenSpec skills en cuatro ecosistemas (`.claude/`, `.codex/`, `.github/`, `.opencode/`). El change `add-design-system-skill` introdujo un directorio top-level `skills/` con la primera skill canónica (`skills/design-system/`) — pensada explícitamente para que un `fdh init` futuro la copie al ecosistema elegido por el developer. Este change es ese `fdh init` futuro.

Existe ya un snapshot de catálogo en `C:/forge/fdh-registry-snapshot/index.json` generado por `C:/forge/fdh/scripts/build-fixture-registry/main.go` — útil para E2E tests, pero **no autoritativo**. Hoy no hay registry real que un admin pueda editar.

Stakeholders: developers Forge que instalan agentes IA (Claude Code, Codex, Copilot, OpenCode); admins del hub que curan qué skills son base; equipo de plataforma que opera Artifactory/Nexus interno y el repo `fdh`.

Constraints duras:
- Distribución 100% interna: no podemos publicar a Homebrew público, npm público ni Chocolatey Community.
- Firma de binarios Windows y macOS requiere certificado corporativo (proceso que tarda semanas) — el diseño debe degradar limpio si no está disponible aún.
- Compat con `fdh init` existente: el modo actual (no interactivo, flags + env) sigue siendo soportado.
- El idioma de las interacciones CLI es inglés (consistente con `fdh` actual); este spec va en español por consistencia con `add-design-system-skill`.

## Goals / Non-Goals

**Goals:**

- `brew install fdh` (o equivalente per OS) deja a `fdh` en el PATH sin pasos manuales.
- `fdh init` en TTY abre un wizard: detecta agentes → usuario tilda agentes → muestra catálogo del hub con defaults pre-seleccionados → usuario ajusta → copia skills a los directorios target.
- `fdh init` en CI/script (stdin no TTY o flags presentes) corre sin prompts y respeta `--agents`, `--skills`, `--no-defaults`.
- Un admin del hub edita `skills/registry.yaml` y, sin tocar código, cambia qué skills son `default: true` o agrega un skill nuevo al catálogo.
- `fdh update` re-sincroniza skills instaladas contra el hub mostrando diff antes de tocar el filesystem.
- Documentar cómo la implementación Go futura debe atacar la trade-off de firmar binarios cuando el cert corporativo no está listo (degradación a binarios firmados ad-hoc + warning).
- Mantener `fdh init` existente funcionando (no romper pilots actuales).

**Non-Goals:**

- **No** implementar el código Go en el repo `fdh` durante este change — el spec describe el contrato; el apply en el hub crea el `registry.yaml` y los specs, no toca Go.
- **No** publicar a registries externos (Homebrew/Chocolatey/winget public, npm).
- **No** introducir un servidor de registry (HTTP API). El hub sigue siendo un git remote + archivos planos; `fdh` los lee vía clone/pull, como ya hace con `registry.url`.
- **No** soportar skills "privadas por proyecto" en este change — el catálogo es uno solo, global Forge.
- **No** firmar paquetes/binarios en este change. Decisión de firma queda en Decision 6.
- **No** migrar el snapshot `fdh-registry-snapshot/` al hub. Sigue siendo fixture local para tests; el registro autoritativo es `skills/registry.yaml`.
- **No** mirrorear `skills/design-system/` a los 4 ecosistemas en el hub. El mirror lo hace `fdh init` en el proyecto del developer, no en el hub.

## Decisions

### Decision 1: Distribución — `install.sh` / `install.ps1` oficiales + tap interno de Homebrew + paquete winget interno

Tres canales primarios, escalonados por complejidad de adopción:

1. **One-liner universal (entrega inmediata):**
   - macOS/Linux: `curl -fsSL https://${FDH_PKG_HOST}/fdh/install.sh | bash`
   - Windows PowerShell: `iwr -useb https://${env:FDH_PKG_HOST}/fdh/install.ps1 | iex`
   - El host se resuelve vía la env var `FDH_PKG_HOST` (default placeholder `pkg.forge.internal` hasta que plataforma confirme el real). Los scripts detectan OS + arch, descargan el tarball/zip correcto, verifican SHA-256, lo extraen a `$HOME/.fdh/bin/` y agregan ese directorio al `PATH` editando `~/.zshrc` / `~/.bashrc` (Unix) o el `Path` de usuario en el registro (Windows). Idempotente — re-ejecutar actualiza.

2. **Package managers nativos (escala media):**
   - macOS/Linux: tap interno de Homebrew (`brew tap forge-internal/tools && brew install fdh`). Se publica vía repo git interno con formulas Ruby.
   - Windows: paquete winget en source interno (`winget source add forge-internal https://${FDH_PKG_HOST}/winget`). Manifest YAML versionado.

3. **Paquetes nativos (Linux corporativo):**
   - `.deb` y `.rpm` con post-install que crea symlinks en `/usr/local/bin/fdh`.

**Orden de adopción:** entregar (1) primero — desbloquea pilots de inmediato sin tocar infra de package managers. (2) y (3) se publican en paralelo cuando el equipo de plataforma agenda el setup del tap y del source winget.

**Alternativas consideradas:**
- *Sólo tarballs en docs (status quo)* — descartado: es exactamente el problema que estamos resolviendo.
- *Homebrew público + Chocolatey Community* — descartado: el binario es interno; publicar el manifest leak nombres internos y obliga a un release público antes de cada update.
- *MSI con instalador GUI* — descartado por costo de mantenimiento (WiX) y porque devs corporativos prefieren CLI; un MSI silencioso desde MDM se puede agregar después usando el mismo binario que distribuye winget.
- *`go install github.com/forge/fdh/cmd/fdh@latest`* — descartado: requiere Go toolchain en el host del developer y exposición pública del módulo.

### Decision 2: `fdh init` detecta TTY y decide modo interactivo vs flags

`fdh init` evalúa en este orden:

1. Si stdin es TTY **y** no se pasaron `--agents` ni `--skills` ni `--non-interactive` → **modo wizard**.
2. Caso contrario → **modo no interactivo**: usa flags + defaults del catálogo del hub.

El wizard usa una librería TUI estándar de Cobra ecosystem (probablemente `github.com/charmbracelet/huh` o `survey/v2` — decisión final del CLI en el repo `fdh`). El spec no obliga a una librería; obliga al comportamiento.

Wizard steps (UX contract):

```
Step 1/3 — Detected AI coding agents on this machine:
  [x] Claude Code (~/.claude/)         <pre-checked, detected>
  [x] GitHub Copilot (.github/)        <pre-checked, detected>
  [ ] OpenAI Codex (.codex/)           <not detected — listed but unchecked>
  [ ] OpenCode (.opencode/)            <not detected — listed but unchecked>
  Space to toggle, Enter to confirm.

Step 2/3 — Skills available in the Forge hub:
  Defaults (recommended for all developers):
  [x] design-system           Design system rules, tokens, components
  [x] code-review             Standard Forge code review checklist
  Extras:
  [ ] security-owasp          OWASP top-10 review prompts
  [ ] pr-description-writer   Generate PR descriptions from diffs
  Space to toggle, Enter to confirm.

Step 3/3 — Summary:
  Agents:  claude-code, copilot
  Skills:  design-system, code-review
  Targets:
    claude-code → ~/.claude/skills/{design-system,code-review}/
    copilot     → .github/skills/{design-system,code-review}/ (workspace)
  Confirm install? [Y/n]
```

**Alternativas consideradas:**
- *Un único prompt combinado (agents × skills)* — descartado: matriz crece rápido y el usuario se pierde.
- *Sin previa detección, sólo lista todos los agentes* — descartado: pierde la oportunidad de "smart default".
- *Forzar siempre modo no interactivo y solo aceptar flags* — descartado: la UX es exactamente el valor agregado de este change.

### Decision 3: Modo no interactivo — flags explícitas + fallback al catálogo

Flags soportadas (todas opcionales):

- `--agents <comma-list>` (ej.: `--agents claude-code,copilot`). Si se omite, usa todos los agentes detectados. Valor especial `auto` = detectados, `all` = todos los soportados aunque no detectados.
- `--skills <comma-list>` con sintaxis `<name>` o `+<name>` para agregar, `-<name>` para excluir. Si se omite, usa los `default: true` del registry.
- `--no-defaults` (boolean). Si está, ignora `default: true` y sólo instala los nombrados con `+`.
- `--non-interactive` (boolean). Fuerza modo no interactivo aunque stdin sea TTY. Útil para tests del propio fdh.
- `--dry-run` (boolean). Imprime el plan sin tocar filesystem.

Resolución de set final de skills:
```
defaults = registry.skills.filter(s => s.default == true)
adds     = skills.filter(s => s.startsWith("+"))
removes  = skills.filter(s => s.startsWith("-"))
explicit = skills.filter(s => !s.startsWith("+") and !s.startsWith("-"))

if --no-defaults: base = []
else:             base = defaults

if explicit.nonEmpty: base = explicit  // explicit reemplaza defaults
final = (base ∪ adds) \ removes
```

**Alternativas consideradas:**
- *Sintaxis `--skill name` repetible* — descartado: incómodo en YAML/CI; CSV es estándar (cf. `kubectl --selector`).
- *Sin `--no-defaults`, sólo `--skills` exhaustivo* — descartado: pierde el "instálame lo recomendado más estas dos extras".

### Decision 4: `skills/registry.yaml` — esquema autoritativo, formato YAML versionado en el hub

Ubicación: `skills/registry.yaml` en la raíz del hub (mismo nivel que el directorio `skills/<name>/`).

```yaml
schema_version: 1
hub_version: "2026.05"                  # tag semver/calver del hub
skills:
  - name: design-system
    description: "Forge design system rules, tokens, components."
    owner_team: design-platform
    tags: [ui, react, tailwind, accessibility]
    default: true
    min_fdh_version: "0.4.0"
    agents_supported: [claude-code, codex, copilot, opencode]
    path: skills/design-system          # ruta relativa al hub, source de copia
  - name: code-review
    description: "Standard Forge code review checklist."
    owner_team: dx-platform
    tags: [review, quality]
    default: true
    min_fdh_version: "0.4.0"
    agents_supported: [claude-code, codex, copilot, opencode]
    path: skills/code-review
  - name: security-owasp
    description: "OWASP top-10 review prompts."
    owner_team: security
    tags: [security, owasp]
    default: false
    min_fdh_version: "0.4.0"
    agents_supported: [claude-code, copilot]
    path: skills/security-owasp
```

Reglas:
- `name` único, kebab-case, mismo string que el directorio bajo `skills/`.
- `default: true` significa "preseleccionado en `fdh init`"; el admin lo controla.
- `agents_supported` permite filtrar el wizard: un skill que sólo soporta Claude no aparece como opción si el developer eligió sólo Codex.
- `path` es relativa al hub y debe existir; CI del hub valida.
- `min_fdh_version`: `fdh init` rechaza instalar un skill si su CLI es más viejo, sugiriendo `fdh upgrade`.
- Si el frontmatter de `skills/<name>/SKILL.md` declara su propio `default`, **se ignora**. Fuente de verdad = `registry.yaml`. (Sí se respetan otros campos del frontmatter como `triggers`, `description`).

**Alternativas consideradas:**
- *`default` declarado en cada `SKILL.md`* — descartado: cambiar defaults requeriría tocar N archivos; aquí es un commit de 1 línea en `registry.yaml`.
- *JSON en vez de YAML* — descartado: YAML soporta comentarios, los admins editan a mano.
- *TOML* — descartado: menos familiar para el equipo, sin upside.
- *Repo separado para el catálogo* — descartado: scope creep; el hub ya es el repo de skills.

### Decision 5: Adapter de copia por ecosistema — transformación mínima, no transpilación

Por cada (agente, skill) seleccionado, `fdh init` copia `skills/<name>/` del clon local del hub al directorio target del agente. El nombre del directorio target varía:

| Agente | Target (project-scope) | Target (user-scope) |
|---|---|---|
| Claude Code | `.claude/skills/<name>/` | `~/.claude/skills/<name>/` |
| Codex | `.codex/skills/<name>/` | `~/.codex/skills/<name>/` |
| Copilot | `.github/prompts/<name>.prompt.md` (file, no dir) | `~/.config/github-copilot/prompts/<name>.prompt.md` |
| OpenCode | `.opencode/commands/<name>.md` (file, no dir) | `~/.opencode/commands/<name>.md` |

Transformaciones:
- **Claude/Codex:** copia literal del directorio.
- **Copilot:** lee `skills/<name>/SKILL.md` y escribe `<name>.prompt.md` con el cuerpo del SKILL.md sin frontmatter (o con `mode: agent` si Copilot lo requiere — a confirmar en apply).
- **OpenCode:** lee `skills/<name>/SKILL.md` y escribe `commands/<name>.md` con frontmatter mínimo (`description: ...` extraído del SKILL.md).

En todos los casos, `references/`, `scripts/`, `.ds-version` y cualquier directorio adicional se copia tal cual cuando el ecosistema soporta directorios (Claude/Codex). Para Copilot/OpenCode, esos sub-recursos no se copian (no hay convención para ellos en esos ecosistemas) — el skill efectivo es sólo el SKILL.md adaptado, y se anota una warning si el skill original tenía `references/` que se está perdiendo.

**Alternativas consideradas:**
- *Generar un "skill compilado" pre-transformación en CI del hub* — descartado: agrega pipeline en el hub y duplica artifacts; mejor que `fdh` transforme al vuelo, que ya está en el path crítico.
- *Aceptar pérdida silenciosa de `references/`* — descartado: el developer no descubriría que su skill perdió contenido.

### Decision 6: Firma de binarios — cert corporativo deseable, degradación con warning aceptable hoy

**Estado ideal:** binarios firmados con cert corporativo Forge (Authenticode para Windows, Developer ID + notarization para macOS). El install.ps1 y install.sh verifican la firma antes de mover a PATH.

**Estado degradado aceptable (Day 1):** binarios no firmados, install.ps1 hace `Unblock-File`, install.sh verifica sólo SHA-256. Se imprime warning durante install:

```
WARNING: This build of fdh is not yet signed with the Forge corporate certificate.
SHA-256 of the binary has been verified against ${FDH_PKG_HOST}.
If your security policy requires signed binaries, postpone install until
the next signed release. Tracking: <internal-ticket>.
```

**Alternativas consideradas:**
- *Bloquear release hasta tener cert* — descartado: cert corporativo toma semanas/meses y bloquearía el rollout.
- *Self-signed cert* — descartado: peor que no firmar (parece firmado válido cuando no lo es).

### Decision 7: `fdh update` — usa `.skill-version` por skill instalada como marcador

Cada copia que `fdh init` hace en el target del agente incluye un archivo oculto `.skill-version` con:

```yaml
name: design-system
hub_version: "2026.05"           # del registry.yaml en momento de instalación
hub_commit: "abcd1234..."        # SHA del hub en ese momento
installed_at: "2026-05-24T10:15:00Z"
installed_by_fdh: "0.5.2"
```

`fdh update` (sin argumentos) recorre los directorios de cada agente conocido, encuentra los `.skill-version`, hace `git pull` (o equivalente) del hub configurado en `registry.url`, y por cada skill cuyo `hub_commit` cambió:

1. Imprime resumen del cambio (lista de archivos modificados, no diff completo).
2. Pide confirmación (`y/N`) salvo que `--yes`.
3. Aplica la copia (overwrite del directorio) con la misma transformación que `init`.
4. Actualiza `.skill-version`.

Flags:
- `--yes` no pregunta, aplica todo.
- `--dry-run` muestra lo que haría y sale 0.
- `--skill <name>` actualiza sólo uno (puede repetirse).
- `--agent <name>` limita a un agente (puede repetirse).

Si un skill local fue editado a mano por el developer (hash de algún archivo no coincide con lo instalado), `update` imprime warning y skip — el developer debe `--force` para sobreescribir.

**Alternativas consideradas:**
- *Diff completo (archivo por archivo) en vez de resumen* — descartado: ruidoso; los devs miran resumen primero y abren los archivos si quieren.
- *Update automático silencioso* — descartado: rompe confianza; lectura del registry es opt-in via comando.
- *Sin detección de edits manuales* — descartado: hay devs que tweaquean SKILL.md; sobreescribirles silenciosamente es mala UX.

### Decision 8: Compat con `fdh init` actual — el modo wizard es additive

El `fdh init` actual ([`internal/cli/init.go:32`](C:/forge/fdh/internal/cli/init.go)) acepta flags y escribe `config.yaml`. Este change extiende sin romper:

- El "core" actual de init (resolver registry + scope, escribir config, correr doctor) se mantiene textual.
- El wizard de selección de agentes/skills corre **después** de doctor, sólo si doctor pasó y stdin es TTY + sin flags resolvedoras de selección.
- Output JSON existente (`InitResult`) se extiende con campos opcionales: `selected_agents`, `selected_skills`, `installed_skills` (no breaking; campos opcionales).
- Si el usuario ya corrió init antes y vuelve a correrlo, el wizard pre-tilda lo que ya tenía instalado (lee los `.skill-version`).

**Alternativas consideradas:**
- *Comando separado `fdh setup` para el wizard* — descartado: el usuario ya espera "init = todo listo"; agregar otro comando es UX peor.
- *Reescribir `init` desde cero* — descartado: rompe pilots.

## Risks / Trade-offs

- **Cert corporativo no listo al lanzamiento** → mitigado por Decision 6 (degradación con warning + SHA-256 verificado); se promueve cert firmado en la primera release subsiguiente.
- **`registry.yaml` desincronizado con `skills/`** (admin agrega entry pero falta el directorio, o vice versa) → mitigado por validación en CI del hub: pre-merge job verifica que cada `name` en `registry.yaml` exista como `skills/<name>/` y viceversa.
- **Wizard rompe en terminales raros (Windows Terminal viejo, tmux con TERM exótico)** → mitigado por fallback: si la librería TUI falla al inicializar, imprime mensaje "wizard no disponible, usá flags `--agents`/`--skills` o `--non-interactive`" y sale 0 con instrucciones.
- **Pérdida silenciosa de `references/` al instalar en Copilot/OpenCode** → mitigado: warning explícito en el output del install nombrando los archivos que se omiten.
- **Edit manual del developer al SKILL.md instalado** → mitigado por detección de hash en `update` + flag `--force` para overwrite; documentado.
- **PATH editing falla por shell exótico (fish, nushell)** → mitigado: el script imprime instrucción manual si no reconoce el shell (`detected $SHELL=/usr/bin/fish, please add ~/.fdh/bin to PATH yourself`).
- **El hub crece y `git clone` se vuelve lento** → mitigado parcialmente por `fdh` haciendo shallow clone + sparse-checkout de `skills/<name>/` y `registry.yaml` solamente.
- **`registry.yaml` se vuelve fuente de churn** (cada PR de skill nuevo lo toca) → aceptado: es el costo de tener un único archivo autoritativo; la alternativa (un registry distribuido por skill) cambia conflicts por confusión.
- **Skills opt-in que un admin movió a `default: true` no se auto-instalan en máquinas que ya corrieron init** → aceptado: `fdh update` no agrega skills nuevas a menos que el usuario las pida; la promoción a default se comunica en release notes del hub. Alternativa "auto-instalar nuevos defaults" se discute en Open Questions.

## Migration Plan

No hay migración de datos: este change introduce capabilities nuevas y no rompe nada existente.

Secuencia de rollout:
1. **Apply en este hub (corto):** crea `skills/registry.yaml` con `design-system` como primera entrada (depende de que `add-design-system-skill` haya sido al menos propuesto); crea las 4 specs nuevas vía deltas. CI del hub valida `registry.yaml` ↔ `skills/`. No toca código.
2. **Cambio en repo `fdh` (largo, separado):** implementa los comportamientos descritos en specs. Se hace con su propio change OpenSpec dentro del repo `fdh` (si adopta OpenSpec) o como release tradicional. Se publica un binario beta para pilots.
3. **Distribución (paralelo a 2):** plataforma confirma el host real (`FDH_PKG_HOST`), setea tap Homebrew interno, source winget interno, publica `install.sh`/`install.ps1` en `https://${FDH_PKG_HOST}/fdh/`. Documentación de quickstart se actualiza con el host concreto.
4. **Pilot:** 5-10 devs corren `install.sh` + `fdh init` end-to-end. Feedback alimenta refinamiento.
5. **General availability:** anuncio interno, deprecación gradual del flujo manual de tarball.

Rollback (si algo va mal después de GA):
- `install.sh` y `install.ps1` mantienen versiones N-1 disponibles en `${FDH_PKG_HOST}/fdh/<version>/` para downgrade manual.
- `registry.yaml` es sólo lectura para `fdh`; revertir un commit en el hub deshace el cambio sin tocar máquinas instaladas. Las máquinas ya instaladas siguen con la versión que copiaron.
- `fdh update --dry-run` permite a cada dev validar antes de aplicar cambios.

## Open Questions

- **¿`fdh update` debe ofrecer instalar skills nuevamente promovidas a `default: true`?** Hoy el diseño dice "no, sólo refresca lo ya instalado". Argumento contra: silencioso, devs no esperan ver skills nuevas aparecer. Argumento a favor: la única forma de propagar nuevos defaults sin un manual `fdh init --reset`. Decisión diferida — probablemente un flag opt-in `fdh update --include-new-defaults`.
- **¿Soporte para `agents_supported` que combine "user-scope" vs "project-scope"?** Hoy se asume project-scope por default y user-scope con `--scope user`. ¿Algunos skills sólo tienen sentido user-scope (ej.: code review checklist personal)? Decisión diferida hasta tener 5+ skills en el catálogo y ver el patrón real.
- **¿Schema validation de `registry.yaml` en el hub vive en CI del hub o en `fdh validate-registry`?** Probablemente ambos (DRY: el código de validación vive en `fdh`, el CI del hub invoca `fdh validate-registry`). A confirmar en apply.
- **¿El wizard ofrece "install all defaults to all detected agents" como shortcut Ctrl-A?** UX detail; decidir al implementar.
- **¿`fdh init` debe ofrecer instalar el propio `fdh-cli-completion` (autocomplete para zsh/bash/pwsh)?** Fuera del scope estricto de este change, pero natural agregarlo. Open question para alcance de este change vs uno siguiente.
- **¿`registry.yaml` debe versionar el contenido (snapshot por release del hub) o ser siempre HEAD?** Hoy: HEAD del default branch. Si en el futuro el hub corta releases (`hub-2026.05`), `fdh` debería poder pinear a un tag — pero el spec actual no lo exige.
