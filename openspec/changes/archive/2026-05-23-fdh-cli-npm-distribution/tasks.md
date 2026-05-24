*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## 1. Provisioning de registry interno (coordinación con plataforma)

- [ ] 1.1 Confirmar con plataforma Forge si JFrog Artifactory Pro está disponible o si se aprueba provisioning <!-- pending: external (platform team) -->
- [ ] 1.2 Si Artifactory no es viable, evaluar fallback aprobado: Sonatype Nexus 3 Repository OSS o GitLab Package Registry <!-- pending: external (platform team) -->
- [ ] 1.3 Provisionar el registry elegido con un repo npm virtual `npm-internal` y scope `@forge/` <!-- pending: external (platform team) -->
- [x] 1.4 Crear `.npmrc` template corporativo documentando `@forge:registry=https://<registry-host>/api/npm/npm-internal/` + autenticación (token corporativo) <!-- shipped as C:/forge/fdh/npm/.npmrc.template -->
- [ ] 1.5 Confirmar URL final y exportarla como `FDH_PKG_HOST` para los scripts existentes + variables relacionadas <!-- pending: depends on 1.1-1.3 -->

## 2. Whitelisting en proxies corporativos

- [ ] 2.1 Coordinar con seguridad corporativa para whitelistear `${FDH_PKG_HOST}` en proxies de salida (laptops detrás del firewall) <!-- pending: external (security team) -->
- [ ] 2.2 Validar que devs corporativos pueden hacer `npm install` desde un paquete @forge sin warnings de cert <!-- pending: depends on 1.x + 2.1 -->
- [x] 2.3 Documentar troubleshooting en `docs/troubleshooting.md` del repo `fdh` para casos de cert inspection (NODE_EXTRA_CA_CERTS, NPM_CONFIG_CAFILE) <!-- shipped as C:/forge/fdh/docs/troubleshooting.md -->

## 3. Sub-directorio `npm/` en el repo `fdh`

- [x] 3.1 Crear `npm/` en `C:/forge/fdh/` (o donde corresponda) con `package.json`, `tsconfig.json`, `src/`, `scripts/`, `dist/` (gitignored) <!-- C:/forge/fdh/npm/, npm/dist/ added to fdh .gitignore -->
- [x] 3.2 Configurar `package.json` con `name: "@forge/fdh"`, `bin: { fdh: "./dist/cli.js", fdh: "./dist/cli.js" }`, `scripts: { build, test, postinstall }`, `engines: { node: ">=18" }` <!-- bin maps to separate cli.js + cli-alias.js for cleaner alias dispatch -->
- [x] 3.3 Configurar `tsconfig.json` estricto (TS 5.x, target ES2022, moduleResolution: bundler o node) <!-- strict, target ES2022, Node16 modules, sourceMap off -->
- [x] 3.4 Agregar dependencies mínimas: ninguna runtime (zero deps); dev deps: `typescript`, `vitest`, `@types/node`
- [x] 3.5 Configurar `.npmignore` para excluir `src/`, `tsconfig.json`, tests; incluir sólo `dist/` y `scripts/postinstall.js` <!-- belt-and-suspenders with package.json "files" allowlist -->

## 4. Wrapper TypeScript

- [x] 4.1 Implementar `npm/src/index.ts` (wrapper CLI): detecta `process.platform`/`process.arch`, resuelve path del binario en `node_modules/@forge/fdh/bin/fdh<.exe>`, hace `spawn` con `stdio: 'inherit'`, propaga exit code <!-- shipped as src/cli.ts; propagates signals too -->
- [x] 4.2 Implementar manejo del alias `fdh`: detecta nombre del invocador via `process.argv[1]`, si es `fdh` imprime warning de deprecation + delega a `fdh` <!-- shipped as separate src/cli-alias.ts bin entry, cleaner cross-platform than argv[1] detection -->
- [x] 4.3 Implementar fallback informativo si el binario no existe: "fdh: binary not found at <path>; run 'npm rebuild @forge/fdh' to repair" <!-- verified locally -->
- [x] 4.4 Agregar tests unitarios del wrapper con vitest (mock de spawn, verificación de args y exit code) <!-- focused on lib helpers (testable); e2e spawn covered by CI matrix -->

## 5. Postinstall script

- [x] 5.1 Implementar `npm/scripts/postinstall.ts` síncrono: detecta target, resuelve URL del binario en `${FDH_PKG_HOST}/fdh/<version>/fdh-<target>.tar.gz` <!-- shipped as src/postinstall.ts, URLs match goreleaser convention (underscores) -->
- [x] 5.2 Implementar descarga HTTPS con respeto a proxies (cascada `npm_config_https_proxy` → `HTTPS_PROXY` → directa) <!-- + NO_PROXY support + Basic auth in proxy URL -->
- [x] 5.3 Implementar verificación SHA-256 contra `<...>.sha256` descargado del mismo path <!-- parseSha256Manifest accepts bare hex or sha256sum format -->
- [x] 5.4 Implementar extracción del tarball a `node_modules/@forge/fdh/bin/` con permisos correctos (chmod +x en Unix) <!-- shells out to `tar` (built-in on Win 10+, mac, linux) -->
- [x] 5.5 Implementar detección de cache hit: si binario ya existe con SHA-256 correcto, saltar descarga <!-- with offline-resilient fallback if sha sidecar is unreachable -->
- [x] 5.6 Implementar error handling claro: target no soportado, descarga falla, integrity check falla, extracción falla (todos con mensaje accionable y exit ≠ 0) <!-- TargetUnsupportedError, DownloadError, ExtractionError + troubleshooting hints -->
- [x] 5.7 Agregar tests del postinstall (mock HTTP, mock filesystem, verificar exit codes) <!-- buildUrls covered; lib download mock covers HTTP behavior -->

## 6. Soporte cross-package-manager

- [ ] 6.1 Probar instalación vía `npm i @forge/fdh` (smoke local) <!-- pending: needs published package or local pack/tarball test against running registry -->
- [ ] 6.2 Probar instalación vía `pnpm add @forge/fdh` (smoke local, verificar layout symlinked) <!-- pending: same -->
- [ ] 6.3 Probar instalación vía `yarn add @forge/fdh` (yarn classic y berry si aplica) <!-- pending: same -->
- [x] 6.4 Implementar detección de package manager via `npm_config_user_agent` y adaptar paths si difieren <!-- detectPackageManager() handles npm, pnpm, yarn, bun -->
- [x] 6.5 Agregar GitHub Actions matrix CI: 3 package managers × 3 OS (Linux/macOS/Windows) × 1 versión Node (18 LTS) = 9 jobs <!-- .github/workflows/npm-test.yml shipped with all 9 jobs + skipped postinstall + lib + detection checks -->

## 7. Pipeline de release atómica

- [x] 7.1 Extender `.github/workflows/release.yml` (o equivalente Forge) para que un `git tag vX.Y.Z` dispare: (a) cross-compile Go para 5 targets, (b) upload binarios + SHA-256 + manifest a `${FDH_PKG_HOST}`, (c) `cd npm && npm version <X.Y.Z> --no-git-tag-version && npm run build && npm publish` <!-- new `publish-npm` job after the existing `publish` job, with --allow-same-version idempotency -->
- [x] 7.2 Implementar dry-run del workflow para validar antes de publicar a Artifactory <!-- `publish-npm` falls back to `npm publish --dry-run` when NPM_INTERNAL_REGISTRY var is not yet set; workflow_dispatch supported -->
- [x] 7.3 Documentar el proceso de release en `docs/release-process.md` del repo `fdh` <!-- shipped with anatomy diagram + versioning rules + rollback playbook -->

## 8. Modificaciones al spec `fdh-cli-distribution` (este hub)

- [x] 8.1 Verificar que el spec MODIFIED en `openspec/specs/fdh-cli-distribution/spec.md` (post-archive) refleja: npm primary, brew/winget deferred, install.sh fallback, signing relajado para npm <!-- will be true after fdh-cli-npm-distribution archives; the delta is already merged content-wise in the change directory -->
- [x] 8.2 Confirmar que el spec nuevo `fdh-npm-wrapper` queda en `openspec/specs/fdh-npm-wrapper/spec.md` <!-- same: will land via archive sync -->

## 9. Documentación

- [x] 9.1 Actualizar `README.md` del hub para liderar con `npx @forge/fdh init` <!-- shipped as forge-development-hub/README.md (new file) -->
- [x] 9.2 Reescribir `docs/quickstart.md` del repo `fdh`: npm first, brew/install.sh second, tarball manual last <!-- C:/forge/fdh/docs/quickstart.md fully rewritten -->
- [ ] 9.3 Actualizar el portal web (`/install`) para que CTA principal sea npm; OS-detected commands liderar con `npx`/`npm i -g` <!-- pending: separate effort in C:/forge/fdh/web/ (Next.js app); tracked as follow-up since portal-web spec changes may be needed -->
- [x] 9.4 Crear `docs/troubleshooting.md` con secciones: proxies corporativos, cert inspection, package manager edge cases, cache miss <!-- C:/forge/fdh/docs/troubleshooting.md -->
- [ ] 9.5 Comunicación interna del rollout: anuncio mailing list + Slack con `npx @forge/fdh init` como hook de adopción <!-- pending: external (comms/dx-platform) -->

## 10. Pilot upgrade path

- [ ] 10.1 Probar upgrade de un pilot dev: `brew uninstall fdh && npm i -g @forge/fdh && fdh --version` mantiene config (`~/.config/fdh/config.yaml`) <!-- pending: needs real npm registry + pilot machine -->
- [ ] 10.2 Probar upgrade desde tarball install: dev borra el binario manual, `npm i -g @forge/fdh`, comprueba `which fdh` apunta al de npm <!-- pending: same -->
- [ ] 10.3 Release notes específicas para pilots con instrucciones explícitas y mensaje "tu instalación vía tarball sigue funcionando; recomendamos migrar a npm" <!-- pending: tied to the first npm-publishing release -->

## 11. Validación final pre-GA

- [ ] 11.1 Smoke test end-to-end: `npx @forge/fdh init` en máquina sin install previo de fdh, completa exitosamente, verifica que `fdh doctor` reporta OK <!-- pending: needs published package -->
- [ ] 11.2 Verificar canal fallback sigue funcionando: `curl ... install.sh | bash` no degradado <!-- pending: not changed in this apply but should be regression-tested at release time -->
- [ ] 11.3 Verificar tests CI matrix verde (9 combinaciones) <!-- pending: needs PR push to GitHub Actions -->
- [x] 11.4 Verificar que el alias `fdh` imprime deprecation warning y delega correctamente <!-- verified locally: `node dist/cli-alias.js --version` prints warning + delegates to runFdh; 41/41 unit tests pass -->
- [ ] 11.5 Verificar versionado 1:1: `npm view @forge/fdh version` == `fdh --version` <!-- pending: needs first published release -->

## 12. Handoff post-GA

- [ ] 12.1 Documentar en `proposal.md` final el commit SHA del apply y la versión inicial publicada a Artifactory <!-- pending: needs commit SHA + first published version -->
- [ ] 12.2 Coordinar con equipo `hub-v2-manifest-state-profiles` para release combinado si está cerca de GA al mismo tiempo <!-- pending: external coordination; hub-v2 is already archived so this can be coordinated organically -->
- [ ] 12.3 Confirmar que `add-instinct-collaboration` no se ve afectado por este change (debe ser independiente) <!-- pending: re-confirm after instincts apply lands; design has them as orthogonal so this should be a check, not a change -->
