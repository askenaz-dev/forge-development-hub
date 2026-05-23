## Why

El plan archivado `add-fdh-cli-distribution-and-interactive-init` definió tres canales paralelos de distribución del binario `fdh` (Go): one-liner `install.sh`/`install.ps1`, tap interno de Homebrew, paquete winget interno. La Decision 6 reconoce que firmar binarios requiere proceso corporativo Falabella (Authenticode + macOS notarization) que tarda semanas a meses y propone degradación con warning como Day 1 aceptable.

Tras revisar el patrón establecido en el ecosistema JavaScript moderno — donde herramientas con core en Go o Rust (esbuild, biome, swc, tailwindcss-cli v4, prisma) shipean su binario nativo **dentro de un paquete npm** que actúa como wrapper de bootstrap — quedan tres ventajas concretas:

1. **`npx @falabella/fdh init` funciona sin install previo.** Una sola línea, sin tap, sin source winget, sin tarball, sin PATH editing manual.
2. **npm sidesteps gran parte del signing pain.** Paquetes npm no son escaneados por Windows SmartScreen ni por Gatekeeper de la misma forma que binarios standalone. El cert corporativo baja de blocker a nice-to-have.
3. **Single artifact en lugar de N binarios por canal.** Una sola release pipeline (build Go → bundle npm → publish a registry interno).

La premisa habilitante: **la mayoría de los devs Falabella ya tienen Node instalado** porque sus herramientas IA lo requieren (Claude Code corre en Node, VS Code embebe Node, frontend toolchain entero es Node). El "requiere Node" deja de ser una barrera real en 2026.

Este change es **independiente** del `hub-v2-manifest-state-profiles`: aquel toca contratos del catálogo y del consumer manifest; este toca cómo se entrega el binario `fdh`. Pueden aplicarse en cualquier orden.

## What Changes

### Nuevo paquete npm `@falabella/fdh`

- Crear paquete TS bajo `npm/` sub-directorio del repo `fdh` Go (pattern esbuild/biome). ~300 LOC TypeScript estricto.
- Wrapper `npm/src/index.ts`: detecta `process.platform`/`process.arch`, resuelve binario, `spawn` con `stdio: 'inherit'`, propaga exit code.
- `package.json` declara `bin: { fdh: "./dist/cli.js", falabella-installer: "./dist/cli.js" }` (mismo wrapper para ambos nombres, simetría con stub de back-compat).

### Postinstall síncrono con verificación de integridad

- Script `npm/scripts/postinstall.ts` ejecuta sincrónico en `npm install`/`npx`/`pnpm`/`yarn add`. Descarga binario desde `${FDH_PKG_HOST}/fdh/<version>/fdh-<platform>-<arch>.tar.gz`, verifica SHA-256, extrae a `node_modules/@falabella/fdh/bin/`.
- Trade-off documentado: install +3-10s, primer comando instantáneo. Lazy descartado por latencia impredecible y falla offline.
- Honra proxies corporativos: lee `npm_config_proxy`/`npm_config_https_proxy` primero, fallback a `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`.

### Provisionar JFrog Artifactory Self-Hosted (Pro) como registry interno

- **Decisión final**: JFrog Artifactory Pro como registry npm interno corporativo Falabella. Razones: polyglot real (npm hoy, futuro Go modules + Docker + Maven + Helm), Xray integrado alineado con `fdh-scan-security`, mejor UX 2026, standard de facto en enterprises del tamaño de Falabella.
- **Fallbacks documentados según budget**: Sonatype Nexus 3 Repository OSS (gratis, polyglot, mature) o GitLab Package Registry (si Falabella ya tiene GitLab Enterprise).
- **Provisioning es dependencia bloqueante** de este change. Si no existe, plataforma lo levanta en paralelo a la implementación del wrapper.
- Scope npm: `@falabella/`. Config vía `.npmrc` corporativo apuntando a `https://artifactory.falabella.internal/api/npm/npm-internal/`.

### Versionado 1:1 con binario Go

- Versión del paquete npm == versión del CLI Go == versión del release del repo `fdh`. Sin cycles independientes. Un solo tag dispara build Go + build TS + publish a Artifactory en pipeline atómica.

### Canales de distribución reordenados

- **Primary**: `npx @falabella/fdh init` (zero-install) + `npm i -g @falabella/fdh` (persistent).
- **Secondary** (fallback Node-less): `install.sh`/`install.ps1`, paquetes `.deb`/`.rpm`.
- **Deferred**: brew tap interno + winget source interno se vuelven opcionales — no bloquean GA.
- **Signing**: deseable para fallback install.sh, ya no bloquea rollout principal.

### Documentación y comunicación

- README del hub: lead con `npx @falabella/fdh init` como ejemplo primario.
- `docs/quickstart.md` del repo `fdh`: reordenar (npm first, brew/install.sh second, tarball manual last).
- Portal web `/install`: OS-detected install commands liderar con npm; mantener tabs para alternativas.

## Capabilities

### New Capabilities

- `fdh-npm-wrapper`: contrato del paquete `@falabella/fdh` — qué hace el wrapper, postinstall síncrono con verificación SHA-256, manejo de proxies, soporte cross-package-manager (npm/pnpm/yarn), alias `falabella-installer`, comportamiento offline (cache hit).

### Modified Capabilities

- `fdh-cli-distribution`: reordenamiento de canales — npm primary, brew/winget deferred, install.sh/.deb/.rpm como fallback Node-less. Reescritura de la sección de signing para reflejar el riesgo reducido.

## Impact

### Stack del repo `fdh`

- Sub-directorio `npm/` (~300 LOC TS) convive con el código Go existente. No reemplaza nada.
- Build pipeline: agrega `npm run build` + `npm publish` además del cross-compile Go.
- Tests: smoke test del wrapper que valida descarga + spawn en mock harness.
- CI: nueva job que publica a Artifactory en cada tag de release.

### Plataforma Falabella

- **Dependencia bloqueante**: provisioning de Artifactory (o fallback Nexus 3 OSS / GitLab Package Registry). Coordinación con plataforma necesaria pre-GA.
- **Whitelist en proxies corporativos**: la URL de descarga del binario (`${FDH_PKG_HOST}/fdh/<version>/...`) debe estar accesible desde laptops detrás del firewall.
- **Coordinación con seguridad**: revisión del flujo postinstall (descarga + verificación) antes del rollout.

### Pilot devs existentes

- Upgrade suave: próximo release publica a Artifactory. Pilot puede `npm i -g @falabella/fdh` y reemplazar binario tarball/brew sin perder config (`~/.config/fdh/config.yaml` se mantiene).
- Release notes explícitas: "tu instalación vía tarball sigue funcionando; recomendamos migrar a npm cuando puedas".

### Sets up future changes

- `fdh-upgrade-command`: `fdh upgrade` puede ser simplemente `npm update -g @falabella/fdh`, sin lógica custom.
- `fdh-completion-via-npm-postinstall`: postinstall genera autocompletes zsh/bash/pwsh automáticamente.
- `multi-platform-binary-tests`: wrapper TS habilita matrix tests cross-platform via GitHub Actions sin runners self-hosted.
