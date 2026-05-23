## 1. Provisioning de registry interno (coordinación con plataforma)

- [ ] 1.1 Confirmar con plataforma Falabella si JFrog Artifactory Pro está disponible o si se aprueba provisioning
- [ ] 1.2 Si Artifactory no es viable, evaluar fallback aprobado: Sonatype Nexus 3 Repository OSS o GitLab Package Registry
- [ ] 1.3 Provisionar el registry elegido con un repo npm virtual `npm-internal` y scope `@falabella/`
- [ ] 1.4 Crear `.npmrc` template corporativo documentando `@falabella:registry=https://<registry-host>/api/npm/npm-internal/` + autenticación (token corporativo)
- [ ] 1.5 Confirmar URL final y exportarla como `FDH_PKG_HOST` para los scripts existentes + variables relacionadas

## 2. Whitelisting en proxies corporativos

- [ ] 2.1 Coordinar con seguridad corporativa para whitelistear `${FDH_PKG_HOST}` en proxies de salida (laptops detrás del firewall)
- [ ] 2.2 Validar que devs corporativos pueden hacer `npm install` desde un paquete @falabella sin warnings de cert
- [ ] 2.3 Documentar troubleshooting en `docs/troubleshooting.md` del repo `fdh` para casos de cert inspection (NODE_EXTRA_CA_CERTS, NPM_CONFIG_CAFILE)

## 3. Sub-directorio `npm/` en el repo `fdh`

- [ ] 3.1 Crear `npm/` en `C:/falabella/fdh/` (o donde corresponda) con `package.json`, `tsconfig.json`, `src/`, `scripts/`, `dist/` (gitignored)
- [ ] 3.2 Configurar `package.json` con `name: "@falabella/fdh"`, `bin: { fdh: "./dist/cli.js", falabella-installer: "./dist/cli.js" }`, `scripts: { build, test, postinstall }`, `engines: { node: ">=18" }`
- [ ] 3.3 Configurar `tsconfig.json` estricto (TS 5.x, target ES2022, moduleResolution: bundler o node)
- [ ] 3.4 Agregar dependencies mínimas: ninguna runtime (zero deps); dev deps: `typescript`, `vitest`, `@types/node`
- [ ] 3.5 Configurar `.npmignore` para excluir `src/`, `tsconfig.json`, tests; incluir sólo `dist/` y `scripts/postinstall.js`

## 4. Wrapper TypeScript

- [ ] 4.1 Implementar `npm/src/index.ts` (wrapper CLI): detecta `process.platform`/`process.arch`, resuelve path del binario en `node_modules/@falabella/fdh/bin/fdh<.exe>`, hace `spawn` con `stdio: 'inherit'`, propaga exit code
- [ ] 4.2 Implementar manejo del alias `falabella-installer`: detecta nombre del invocador via `process.argv[1]`, si es `falabella-installer` imprime warning de deprecation + delega a `fdh`
- [ ] 4.3 Implementar fallback informativo si el binario no existe: "fdh: binary not found at <path>; run 'npm rebuild @falabella/fdh' to repair"
- [ ] 4.4 Agregar tests unitarios del wrapper con vitest (mock de spawn, verificación de args y exit code)

## 5. Postinstall script

- [ ] 5.1 Implementar `npm/scripts/postinstall.ts` síncrono: detecta target, resuelve URL del binario en `${FDH_PKG_HOST}/fdh/<version>/fdh-<target>.tar.gz`
- [ ] 5.2 Implementar descarga HTTPS con respeto a proxies (cascada `npm_config_https_proxy` → `HTTPS_PROXY` → directa)
- [ ] 5.3 Implementar verificación SHA-256 contra `<...>.sha256` descargado del mismo path
- [ ] 5.4 Implementar extracción del tarball a `node_modules/@falabella/fdh/bin/` con permisos correctos (chmod +x en Unix)
- [ ] 5.5 Implementar detección de cache hit: si binario ya existe con SHA-256 correcto, saltar descarga
- [ ] 5.6 Implementar error handling claro: target no soportado, descarga falla, integrity check falla, extracción falla (todos con mensaje accionable y exit ≠ 0)
- [ ] 5.7 Agregar tests del postinstall (mock HTTP, mock filesystem, verificar exit codes)

## 6. Soporte cross-package-manager

- [ ] 6.1 Probar instalación vía `npm i @falabella/fdh` (smoke local)
- [ ] 6.2 Probar instalación vía `pnpm add @falabella/fdh` (smoke local, verificar layout symlinked)
- [ ] 6.3 Probar instalación vía `yarn add @falabella/fdh` (yarn classic y berry si aplica)
- [ ] 6.4 Implementar detección de package manager via `npm_config_user_agent` y adaptar paths si difieren
- [ ] 6.5 Agregar GitHub Actions matrix CI: 3 package managers × 3 OS (Linux/macOS/Windows) × 1 versión Node (18 LTS) = 9 jobs

## 7. Pipeline de release atómica

- [ ] 7.1 Extender `.github/workflows/release.yml` (o equivalente Falabella) para que un `git tag vX.Y.Z` dispare: (a) cross-compile Go para 5 targets, (b) upload binarios + SHA-256 + manifest a `${FDH_PKG_HOST}`, (c) `cd npm && npm version <X.Y.Z> --no-git-tag-version && npm run build && npm publish`
- [ ] 7.2 Implementar dry-run del workflow para validar antes de publicar a Artifactory
- [ ] 7.3 Documentar el proceso de release en `docs/release-process.md` del repo `fdh`

## 8. Modificaciones al spec `fdh-cli-distribution` (este hub)

- [ ] 8.1 Verificar que el spec MODIFIED en `openspec/specs/fdh-cli-distribution/spec.md` (post-archive) refleja: npm primary, brew/winget deferred, install.sh fallback, signing relajado para npm
- [ ] 8.2 Confirmar que el spec nuevo `fdh-npm-wrapper` queda en `openspec/specs/fdh-npm-wrapper/spec.md`

## 9. Documentación

- [ ] 9.1 Actualizar `README.md` del hub para liderar con `npx @falabella/fdh init`
- [ ] 9.2 Reescribir `docs/quickstart.md` del repo `fdh`: npm first, brew/install.sh second, tarball manual last
- [ ] 9.3 Actualizar el portal web (`/install`) para que CTA principal sea npm; OS-detected commands liderar con `npx`/`npm i -g`
- [ ] 9.4 Crear `docs/troubleshooting.md` con secciones: proxies corporativos, cert inspection, package manager edge cases, cache miss
- [ ] 9.5 Comunicación interna del rollout: anuncio mailing list + Slack con `npx @falabella/fdh init` como hook de adopción

## 10. Pilot upgrade path

- [ ] 10.1 Probar upgrade de un pilot dev: `brew uninstall fdh && npm i -g @falabella/fdh && fdh --version` mantiene config (`~/.config/fdh/config.yaml`)
- [ ] 10.2 Probar upgrade desde tarball install: dev borra el binario manual, `npm i -g @falabella/fdh`, comprueba `which fdh` apunta al de npm
- [ ] 10.3 Release notes específicas para pilots con instrucciones explícitas y mensaje "tu instalación vía tarball sigue funcionando; recomendamos migrar a npm"

## 11. Validación final pre-GA

- [ ] 11.1 Smoke test end-to-end: `npx @falabella/fdh init` en máquina sin install previo de fdh, completa exitosamente, verifica que `fdh doctor` reporta OK
- [ ] 11.2 Verificar canal fallback sigue funcionando: `curl ... install.sh | bash` no degradado
- [ ] 11.3 Verificar tests CI matrix verde (9 combinaciones)
- [ ] 11.4 Verificar que el alias `falabella-installer` imprime deprecation warning y delega correctamente
- [ ] 11.5 Verificar versionado 1:1: `npm view @falabella/fdh version` == `fdh --version`

## 12. Handoff post-GA

- [ ] 12.1 Documentar en `proposal.md` final el commit SHA del apply y la versión inicial publicada a Artifactory
- [ ] 12.2 Coordinar con equipo `hub-v2-manifest-state-profiles` para release combinado si está cerca de GA al mismo tiempo
- [ ] 12.3 Confirmar que `add-instinct-collaboration` no se ve afectado por este change (debe ser independiente)
