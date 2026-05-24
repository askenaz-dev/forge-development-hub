*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Why

Forge tiene el CLI `fdh` (repo `fdh`) y un hub de skills (`forge-development-hub`) que ya saben hablar entre sí mediante `fdh init` + `registry.url`, pero el flujo end-to-end del developer todavía tiene tres huecos críticos: (1) instalar `fdh` requiere bajar un tarball y mover el binario al PATH a mano por OS (ver `C:/forge/fdh/docs/quickstart.md`), (2) `fdh init` no es interactivo y no permite que el developer elija qué agentes IA activar ni qué skills traer más allá de lo que el config tenga seteado, y (3) no existe un mecanismo de catálogo donde un admin del hub marque qué skills son "base" recomendadas vs opcionales, ni un comando `fdh update` que sincronice las skills ya instaladas cuando el hub publica versiones nuevas. El cambio `add-design-system-skill` ya deja `skills/design-system/` lista como fuente; este change cierra el resto del ciclo para que un developer pueda hacer `brew install fdh && fdh init` y terminar con sus agentes elegidos y sus skills base operativas.

## What Changes

- **Distribución per-OS del binario `fdh` con PATH automático**: wrappers de package manager (`brew install fdh` para macOS/Linux, `choco install fdh` y `winget install Forge.FDH` para Windows, paquetes `.deb`/`.rpm` para Linux corporativo) y scripts one-liner (`install.sh` / `install.ps1`) que detectan OS, descargan el binario y lo agregan al PATH del usuario. Reemplaza el flujo manual actual de tarball + mover binario a `C:\Tools\` o `~/bin`.
- **`fdh init` interactivo con selección de agentes**: detección automática de agentes IA presentes en el host (extiende lo que ya hace `fdh doctor`) + prompt TTY que muestra los agentes detectados con checkboxes para activar/desactivar. Bandera `--agents <list>` para modo no interactivo en CI.
- **`fdh init` interactivo con selección de skills sobre catálogo del hub**: tras elegir agentes, segundo prompt con el catálogo de skills disponibles en el hub. Los skills marcados `default: true` por el admin aparecen pre-seleccionados; el developer puede destildarlos. El catálogo entero está disponible para opt-in de extras. Banderas `--skills <list>` y `--no-defaults` para modo no interactivo.
- **`fdh init` copia skills del hub al directorio de cada agente elegido**: por cada (agente × skill) seleccionado, copia `skills/<name>/` del hub al directorio convencional del agente (`.claude/skills/`, `.codex/skills/`, `.github/skills/` o `.opencode/skills/`). Aplica la transformación mínima de formato que cada ecosistema requiera (Copilot espera `*.prompt.md`, OpenCode espera `commands/*.md`).
- **Nuevo comando `fdh update`**: compara la versión instalada de cada skill (vía un marcador tipo `.skill-version` en el directorio destino) contra la versión publicada en el hub y aplica re-pull selectivo solo de los que cambiaron. Imprime un diff resumido antes de actuar; bandera `--yes` para automatizar y `--dry-run` para previsualizar.
- **Catálogo del hub con metadata de admin (`skills/registry.yaml`)**: nuevo archivo top-level en el hub donde el admin declara para cada skill: `name`, `description`, `owner_team`, `tags`, `default: true|false`, `min_fdh_version` y `agents_supported`. Inspirado en el formato de `C:/forge/fdh-registry-snapshot/index.json`, pero versionado en el hub y autoritativo. `fdh init` y `fdh update` lo leen vía `registry.url`.
- **Bandera `default: true|false` propagada al skill**: `skills/<name>/SKILL.md` puede declarar su default en su frontmatter como hint, pero la decisión autoritativa la toma `skills/registry.yaml`. Esto permite al admin cambiar defaults sin modificar cada skill.

## Capabilities

### New Capabilities

- `fdh-cli-distribution`: empaquetado del binario `fdh` y configuración de PATH per-OS vía package managers y scripts de instalación oficiales.
- `fdh-init-interactive`: flujo TTY de `fdh init` que detecta agentes, ofrece selección de agentes y skills, y materializa la elección en la copia inicial desde el hub.
- `fdh-skills-sync`: comando `fdh update` para sincronizar skills ya instaladas contra el hub con diff previo y modos `--yes` / `--dry-run`.
- `hub-skills-registry`: catálogo `skills/registry.yaml` en el hub con metadata de admin (defaults, owner, tags, compatibilidad) que `fdh` consume.

### Modified Capabilities

<!-- No existing specs are being modified by this change. -->

## Impact

- **Nuevo archivo:** `skills/registry.yaml` en la raíz del hub (catálogo autoritativo).
- **Nuevas specs:** `openspec/specs/fdh-cli-distribution/spec.md`, `openspec/specs/fdh-init-interactive/spec.md`, `openspec/specs/fdh-skills-sync/spec.md`, `openspec/specs/hub-skills-registry/spec.md` (vía deltas en este change).
- **Dependencia de upstream:** `add-design-system-skill` debe estar al menos en estado proposal antes de hacer apply de este change, porque su `skills/design-system/` es la primera entrada esperada del `skills/registry.yaml`.
- **Repo `fdh` (hermano):** la implementación de los cuatro nuevos comportamientos (distribución, init interactivo, update, lectura de registry.yaml) se hará allá cuando este change pase a apply. Este change deja sólo el contrato.
- **Sin cambios** en `openspec/`, en los 4 directorios espejo (`.claude/`, `.codex/`, `.github/`, `.opencode/`), ni en el código de `fdh` durante el apply en este hub. La implementación Go vivirá en `fdh` y se trackeará por separado.
- **Cero publicación a registries externos:** todos los canales de distribución son internos Forge (Artifactory/Nexus/etc para los binarios; nada se publica a npm, GitHub Packages públicos, ni Homebrew público).
- **Compat con configuración existente:** `fdh init` actual (no interactivo, ver `C:/forge/fdh/internal/cli/init.go`) sigue funcionando con flags; el modo interactivo se activa cuando stdin es TTY y no se pasan flags que ya resuelvan agentes/skills.
- **Riesgo de drift de `registry.yaml`:** si el admin agrega un skill al catálogo pero olvida crear `skills/<name>/`, el `fdh init` debe fallar limpio con mensaje accionable. El spec define ese contrato.
- **Riesgo en distribución:** firmar el binario para Windows (Authenticode) y macOS (notarization) probablemente requiere proceso corporativo Forge. El design.md cubre la trade-off.
