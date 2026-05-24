*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

> **NOTA — BORRADOR (no es un change formal todavía).**
> Este archivo vive bajo `openspec/changes/_drafts/` para revisión humana antes de
> ejecutar `/opsx:propose`. Cuando se apruebe, el contenido se mueve al directorio
> oficial del change generado por `openspec new change "fdh-cli-npm-distribution"`.

## Why

El plan archivado `add-fdh-cli-distribution-and-interactive-init` definió tres canales paralelos de distribución del binario `fdh` (Go): one-liner `install.sh`/`install.ps1`, tap interno de Homebrew, paquete winget interno. La Decision 6 reconoce que firmar los binarios requiere proceso corporativo Forge (Authenticode + macOS notarization) que tarda **semanas a meses**, y propone degradación con warning como Day 1 aceptable.

Después de revisar el patrón establecido en el ecosistema JavaScript moderno — donde herramientas con core en Go o Rust (esbuild, biome, swc, tailwindcss-cli v4, prisma) shipean su binario nativo **dentro de un paquete npm** que actúa como wrapper de bootstrap — quedan tres ventajas concretas:

1. **`npx @askenaz-dev/fdh init` funciona sin install previo.** Una sola línea, sin tap, sin source winget, sin tarball, sin PATH editing manual. El primer dev que prueba FDH no tiene fricción.
2. **npm sidesteps gran parte del signing pain.** Paquetes npm no son escaneados por Windows SmartScreen ni por Gatekeeper de la misma forma que binarios standalone. El cert corporativo (Decision 6) baja de "blocker" a "nice-to-have".
3. **Single artifact en lugar de N binarios por canal.** Una sola release pipeline (build Go → bundle en npm package → publish a registry interno) en lugar de mantener brew formula + winget manifest + deb/rpm + install.sh.

La premisa que habilita el cambio: **la mayoría de los devs Forge ya tienen Node instalado** porque sus herramientas IA lo requieren (Claude Code corre en Node, VS Code embebe Node, frontend toolchain entero es Node). El "requiere Node" deja de ser una barrera real en 2026.

Este change es **independiente** del `hub-v2-manifest-state-profiles`: aquel toca contratos del catálogo y del consumer manifest; este toca cómo se entrega el binario `fdh`. Pueden aplicarse en cualquier orden.

## What Changes

### Nuevo paquete npm `@askenaz-dev/fdh`

- **Crear el paquete TS** en el repo `fdh` Go (probablemente bajo `./npm/` como sub-directorio nuevo) o como repo hermano dedicado. ~300 LOC de TypeScript estricto.
- **Wrapper en `npm/src/index.ts`** hace exactamente cuatro cosas:
  1. Detecta `process.platform` + `process.arch` → resuelve target (`darwin-arm64`, `linux-amd64`, `windows-amd64`, etc.).
  2. Resuelve la ruta del binario (descargado en postinstall o on-demand si lazy).
  3. `spawn(binary, process.argv.slice(2), { stdio: 'inherit' })`.
  4. Propaga exit code.
- **Script postinstall síncrono** (`npm/scripts/postinstall.ts`) descarga el binario correcto desde `${FDH_RELEASES_BASE}/fdh/<version>/fdh-<platform>-<arch>.tar.gz`, verifica SHA-256 contra `<...>.sha256`, extrae a `node_modules/@askenaz-dev/fdh/bin/`. Idempotente. **Síncrono por decisión consciente** — el `npm install` (o `npx`) bloquea hasta que el binario está listo. Trade-off: install más lento (~3-10s adicionales según red), pero el primer `fdh <comando>` ejecuta instantáneo sin sorpresas. La alternativa lazy (descargar al primer uso) se descartó porque introduce latencia impredecible y falla si el primer comando es offline-only.
- **`package.json`** declara `bin: { fdh: "./dist/cli.js" }` apuntando al wrapper. Después de `npm i -g @askenaz-dev/fdh` o `npx @askenaz-dev/fdh`, el binario `fdh` aparece en PATH (gestionado por npm).

### Publicación a registry npm interno

- **Provisionar JFrog Artifactory Self-Hosted (Pro)** como registry interno Forge. Decisión basada en:
  - **Polyglot real**: npm hoy, pero futuro Go modules, Docker images, Helm charts, PyPI, Maven — todo en un solo registry. Evita tener N sistemas paralelos.
  - **JFrog Xray integrado**: security scanning de paquetes alineado con la filosofía de `fdh-scan-security`.
  - **Mejor UX/UI de la categoría en 2026** + REST APIs maduras + build promotion (dev → staging → prod) + federación multi-DC.
  - **Standard de facto** en retailers/enterprises del tamaño de Forge.
  - **Alternativa budget-conscious documentada**: Sonatype Nexus 3 Repository OSS es la opción gratuita comparable (polyglot, mature). Si plataforma rechaza el costo de Artifactory Pro, fallback a Nexus 3 OSS no cambia el contrato de este change.
  - **GitLab Package Registry** como tercera opción si Forge ya tiene GitLab Enterprise (incluido sin costo extra).
- **Scope npm**: `@askenaz-dev/` para distinguir de paquetes públicos. Configurable vía `.npmrc` corporativo que apunta `@forge:registry=https://artifactory.askenaz.dev/api/npm/npm-internal/`.
- **Versionado 1:1 con el binario Go siempre**: versión del paquete npm == versión del CLI == versión del release del repo `fdh`. Nada de cycles de versionado independientes — un solo tag de release dispara build Go + build TS + publish a Artifactory en una pipeline atómica.
- **Provisioning de Artifactory** se eleva como dependencia bloqueante de este change. Si no existe, plataforma debe levantar la instancia en paralelo a la implementación del wrapper.

### Canales de distribución reordenados

- **Primary**: `npx @askenaz-dev/fdh init` (zero-install) y `npm i -g @askenaz-dev/fdh` (persistent). Documentación de quickstart lidera con esto.
- **Secondary**: `install.sh` y `install.ps1` se mantienen como fallback para entornos sin Node (servers headless, contenedores minimal, air-gapped).
- **Deferred**: brew tap interno y winget source interno se vuelven opcionales — agendables cuando plataforma tenga capacidad, no bloquean GA.
- **Mantenido**: `.deb` / `.rpm` para servidores Linux corporativos sin Node, mismo binario underlying.

### Impacto en signing (Decision 6 archivada)

- **Antes**: bloqueante para GA. Devs Windows verían SmartScreen al instalar; devs macOS verían Gatekeeper. Workaround = warning explícito + verificación SHA-256.
- **Después**: para el canal npm, el binario se ejecuta desde `node_modules/` y npm no dispara los mismos checks. El warning de SmartScreen/Gatekeeper aparece sólo si el dev usa el canal install.sh/tarball.
- **Sigue siendo deseable** firmar para casos enterprise estrictos y para el fallback install.sh, pero deja de bloquear el rollout principal.

### Back-compat del nombre `fdh`

- El stub `cmd/fdh-stub` del repo `fdh` (introducido por `dev-portal` para 90 días de deprecation) se mantiene tal cual.
- Adicionalmente: el paquete npm puede shipear un binario alias `fdh` que también apunta al wrapper, por simetría. A confirmar en design.md.

### Documentación

- `README.md` del hub: lead con `npx @askenaz-dev/fdh init` como ejemplo primario.
- `docs/quickstart.md` del repo `fdh`: reordenar secciones — npm first, brew/install.sh second, tarball manual last.
- Portal web (`/install`): los OS-detected install commands liderar con npm, mantener tabs para alternativas.
- Comunicación interna del rollout: enfatizar `npx` como hook de adopción.

## Capabilities

### New Capabilities

- `fdh-npm-wrapper`: el contrato del paquete `@askenaz-dev/fdh` — qué hace el wrapper, cómo descarga el binario, cómo lo verifica, cómo propaga args y exit codes, qué pasa si la descarga falla, comportamiento offline (cache hit), versionado.

### Modified Capabilities

- `fdh-cli-distribution`: el spec ya archivado se modifica para reflejar el reordenamiento de canales. npm pasa a ser primary; brew tap y winget source pasan a secondary/optional; install.sh/install.ps1 quedan como fallback Node-less; tarballs `.deb`/`.rpm` se mantienen para servidores Linux. Sección de signing se reescribe para reflejar el nuevo riesgo reducido.

## Impact

### Stack del repo `fdh`

- Agrega un sub-directorio TS (~300 LOC) al repo Go. Convive, no reemplaza. Build pipeline crece: ahora también corre `npm run build` y `npm publish` además del cross-compile Go.
- Test pipeline: agrega tests del wrapper (smoke test que valida descarga + spawn en un mock harness).
- CI: nueva job que publica a Verdaccio interno en cada tag de release.

### Plataforma Forge

- **Dependencia confirmable**: existencia (o provisioning) de registry npm interno. Si Verdaccio/Nexus npm-proxy ya están operativos, integración es trivial. Si no, este change los eleva como prerrequisito.
- Coordinación con seguridad: la URL de descarga del binario (`${FDH_RELEASES_BASE}/fdh/<version>/...`) debe ser whitelisteada en proxies corporativos para que el postinstall funcione desde laptops detrás del firewall.

### Pilot devs existentes

- Camino de upgrade suave: el próximo release publica al npm registry. Los pilot devs pueden hacer `npm i -g @askenaz-dev/fdh` y reemplazar el binario instalado vía tarball/brew sin perder config (`~/.config/fdh/config.yaml` se mantiene).
- Mensaje de release notes explícito: "tu instalación vía tarball sigue funcionando; recomendamos migrar a npm cuando puedas porque permite `fdh upgrade` trivial".

### Decisión técnica: dónde vive el código TS

A confirmar en design.md, dos opciones reales:

- **Opción 1 — sub-directorio del repo Go** (`fdh/npm/`): co-located con el código que envuelve. Sincronización trivial de versión. Cross-cutting CI más complejo.
- **Opción 2 — repo separado `@askenaz-dev/fdh-npm`**: separación limpia de toolchain. Versión sincronizada a mano (o vía bot). Más overhead organizacional.

Recomendación tentativa: Opción 1 (sub-directorio), siguiendo el pattern de esbuild y biome.

### Sets up future changes

- `fdh-upgrade-command`: `fdh upgrade` puede ahora simplemente `npm update -g @askenaz-dev/fdh`, sin lógica custom de auto-update. Mucho más simple que en el modelo brew/tarball.
- `fdh-completion-via-npm-postinstall`: el postinstall del paquete npm puede generar autocompletes para zsh/bash/pwsh automáticamente.
- `multi-platform-binary-tests`: el wrapper TS habilita tests cross-platform vía GitHub Actions matrix sin necesitar runners self-hosted Forge.

### Decisiones resueltas (cerradas)

- **Registry**: JFrog Artifactory Self-Hosted Pro (con Nexus 3 OSS y GitLab Package Registry como fallbacks documentados según budget).
- **Postinstall**: síncrono (bloquea install hasta tener binario listo).
- **Versionado**: 1:1 con el binario Go siempre, una sola pipeline de release.

### Open questions (a resolver en design.md, no bloquean este proposal)

- ¿Manejo de proxies corporativos en el postinstall — usar `npm_config_proxy`, leer `HTTP_PROXY`/`HTTPS_PROXY`, o ambos?
- ¿Soportar `pnpm` y `yarn` además de `npm` (todos hacen el postinstall igual, pero edge cases existen)?
- ¿El binario alias `fdh` se shipea desde el mismo paquete o desde un `@askenaz-dev/fdh-stub` separado?
- ¿Sub-directorio del repo `fdh` (`fdh/npm/`) o repo separado para el wrapper TS?
