# fdh-npm-wrapper Specification

## Purpose

Define el contrato del paquete `@askenaz-dev/fdh` publicado al registry npm interno: shipea el binario Go vía un wrapper TypeScript de zero runtime deps, descarga el binario correcto para el OS/arch del host en `postinstall` síncrono con verificación SHA-256, honra proxies corporativos en cascada (npm_config → env vars → NO_PROXY), soporta los tres principales package managers (npm/pnpm/yarn) incluyendo cache hit offline, y propaga args/exit code sin transformación. La versión del paquete npm SHALL ser 1:1 con la del binario Go (sin cycles independientes). Ningún binario alias `forge-installer` ni paquete `@askenaz-dev/fdh` se publica.
## Requirements
### Requirement: Paquete `@askenaz-dev/fdh` distribuye el binario Go vía npm

El sistema SHALL publicar un paquete npm `@askenaz-dev/fdh` al registry interno (JFrog Artifactory Pro o fallback aprobado) cuyo contenido es un wrapper TypeScript + un script postinstall que descarga el binario `fdh` Go correcto para el OS/arch del host. El paquete SHALL declarar `bin: { fdh }` apuntando al wrapper, para que el nombre `fdh` quede disponible en PATH tras `npm i -g` o vía `npx`. El paquete NO declara ningún alias `forge-installer` ni `@askenaz-dev/fdh`.

#### Scenario: Install global con npm

- **WHEN** un developer ejecuta `npm i -g @askenaz-dev/fdh`
- **THEN** después del comando, el binario `fdh` está en PATH y `fdh --version` responde con la versión del paquete instalado; ningún binario llamado `forge-installer` queda registrado

#### Scenario: Zero-install con npx

- **WHEN** un developer ejecuta `npx @askenaz-dev/fdh init` sin install previo
- **THEN** npx descarga el paquete, corre el postinstall síncrono, ejecuta el wrapper que invoca el binario subyacente y termina con el exit code de `fdh init`

#### Scenario: Versión del paquete = versión del binario

- **WHEN** se publica `@askenaz-dev/fdh@0.7.2` al registry interno
- **THEN** el binario `fdh` que el postinstall descarga es exactamente la versión 0.7.2 del release Go (sin cycles de versionado independientes)

### Requirement: Postinstall síncrono con verificación de integridad

El script `postinstall` SHALL ejecutar sincrónico (bloqueando `npm install`/`npx`/`pnpm add`/`yarn add`) y SHALL: (a) detectar `process.platform` y `process.arch` para resolver el target (`darwin-arm64`, `darwin-amd64`, `linux-arm64`, `linux-amd64`, `windows-amd64`), (b) descargar `${FDH_RELEASES_BASE}/fdh/<version>/fdh-<target>.tar.gz` y `<...>.sha256`, (c) verificar SHA-256, (d) extraer a `node_modules/@askenaz-dev/fdh/bin/`. Si cualquier paso falla, el postinstall SHALL fallar con código distinto de cero y mensaje accionable.

#### Scenario: Postinstall exitoso

- **WHEN** un developer corre `npm i @askenaz-dev/fdh` en darwin-arm64 con conectividad al registry
- **THEN** el postinstall descarga `fdh-darwin-arm64.tar.gz`, verifica SHA-256, extrae el binario, deja el wrapper listo para spawnearlo, y `npm install` reporta exit 0

#### Scenario: SHA-256 mismatch

- **WHEN** el binario descargado no coincide con el SHA-256 esperado
- **THEN** el postinstall elimina el archivo descargado, imprime "fdh: integrity check failed (expected <X>, got <Y>) — re-run with --verbose for details", y sale con código distinto de cero; `npm install` falla

#### Scenario: Target no soportado

- **WHEN** el postinstall corre en `freebsd-amd64` (no en la matriz soportada)
- **THEN** imprime "fdh: no prebuilt binary for freebsd-amd64; supported targets: [darwin-arm64, darwin-amd64, linux-arm64, linux-amd64, windows-amd64]" y sale con código distinto de cero

### Requirement: Honrar proxies corporativos

El postinstall SHALL leer la configuración de proxy en este orden de precedencia: primero `npm_config_https_proxy`/`npm_config_proxy` (lo que npm pasa), luego `HTTPS_PROXY`/`HTTP_PROXY` del entorno, luego `NO_PROXY` para excluir hosts. Si ninguna está seteada, SHALL hacer requests directas. Documentación SHALL explicitar esto.

#### Scenario: Proxy seteado vía npm config

- **WHEN** el developer corre `npm i @askenaz-dev/fdh` con `npm_config_https_proxy=http://corp-proxy:8080` heredado
- **THEN** el postinstall enruta la descarga del binario por ese proxy

#### Scenario: NO_PROXY excluye el host interno

- **WHEN** `NO_PROXY=*.askenaz.dev` y `${FDH_RELEASES_BASE}=artifactory.askenaz.dev/...`
- **THEN** el postinstall hace request directa (no por proxy) al host interno

### Requirement: Soporte cross-package-manager (npm, pnpm, yarn)

El paquete SHALL funcionar correctamente cuando se instala vía npm, pnpm o yarn. El postinstall SHALL detectar el package manager activo (vía `npm_config_user_agent`) y SHALL adaptar paths de instalación si difieren (por ejemplo, pnpm usa `node_modules/.pnpm/<hash>/` symlinkeado).

#### Scenario: Install vía pnpm

- **WHEN** un developer ejecuta `pnpm add -g @askenaz-dev/fdh`
- **THEN** el postinstall completa exitosamente, el binario queda accesible vía PATH (pnpm linkea), y `fdh --version` responde

#### Scenario: Install vía yarn classic

- **WHEN** un developer ejecuta `yarn global add @askenaz-dev/fdh`
- **THEN** el postinstall completa exitosamente y el binario queda accesible vía `$(yarn global bin)/fdh`

### Requirement: Comportamiento offline con cache hit

Si el binario ya está extraído en `node_modules/@askenaz-dev/fdh/bin/` con un SHA-256 que coincide con el esperado para la versión instalada, el postinstall SHALL detectarlo y SHALL saltar la descarga (cache hit). Esto permite re-ejecuciones offline después del primer install exitoso.

#### Scenario: Cache hit en re-install

- **WHEN** el binario ya existe con SHA-256 correcto y se re-ejecuta `npm i @askenaz-dev/fdh`
- **THEN** el postinstall imprime "fdh: binary already present (cache hit)", no descarga, y sale con código cero

#### Scenario: Cache miss por mismatch

- **WHEN** el binario existe pero el SHA-256 no coincide con el esperado (corrupción, versión vieja)
- **THEN** el postinstall lo trata como cache miss, descarga la versión correcta y la reemplaza

### Requirement: Wrapper propaga args y exit code

El wrapper TypeScript SHALL spawnear el binario subyacente con `stdio: 'inherit'`, SHALL pasar `process.argv.slice(2)` como args sin transformación, y SHALL propagar el exit code del binario al proceso Node padre. Errores de spawn (binario faltante, permisos) SHALL emitir un mensaje accionable y SHALL salir con código distinto de cero.

#### Scenario: Exit code propagado

- **WHEN** un developer ejecuta `fdh doctor` y el comando Go retorna exit 1
- **THEN** el proceso Node padre termina con exit 1

#### Scenario: Binario faltante

- **WHEN** el wrapper intenta spawnear el binario pero el archivo no existe (postinstall falló o fue limpiado)
- **THEN** el wrapper imprime "fdh: binary not found at <path>; run 'npm rebuild @askenaz-dev/fdh' to repair" y sale con código distinto de cero

### Requirement: Documentación de instalación lidera con npm

La documentación oficial (`README.md` del hub, `docs/quickstart.md` del repo `fdh`, portal web `/install`) SHALL presentar `npx @askenaz-dev/fdh init` como comando primario para el primer install, con `npm i -g @askenaz-dev/fdh` como alternativa persistente. Otros canales (brew/install.sh/.deb/.rpm) SHALL aparecer como alternativas en secciones secundarias.

#### Scenario: README del hub

- **WHEN** un nuevo dev lee `README.md` del hub
- **THEN** encuentra `npx @askenaz-dev/fdh init` como ejemplo primario en la sección de instalación, antes de mencionar brew/tarball; ninguna referencia a `@askenaz-dev/fdh` queda visible

#### Scenario: Portal `/install` por defecto

- **WHEN** un usuario sin OS detectado abre `/install` en el portal web
- **THEN** ve el comando `npx @askenaz-dev/fdh init` como CTA principal, con tabs/expandables para alternativas

