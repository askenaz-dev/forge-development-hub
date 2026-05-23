## Context

El binario `fdh` existe hoy en `C:/falabella/fdh` como CLI Go de ~13k LOC + portal HTTP API. El plan archivado `add-fdh-cli-distribution-and-interactive-init` definió distribución vía tres canales (one-liner install.sh/ps1 + brew tap interno + winget source interno) con `FDH_PKG_HOST` como variable de entorno para apuntar al endpoint corporativo. La Decision 6 del archive aceptó binarios sin firmar Day 1 con warnings, dado que el cert corporativo Falabella toma semanas/meses de gestión.

El ecosistema JavaScript moderno convergió en un patrón para herramientas con core Go/Rust: distribuir el binario nativo dentro de un paquete npm wrapper. Ejemplos en producción: esbuild (Go), biome (Rust), swc (Rust), tailwindcss-cli v4 (Rust), prisma (TS + Rust engines), vscode-ripgrep (Rust). Este change adopta ese patrón para `fdh`.

**Premisa clave**: la mayoría de devs Falabella ya tiene Node instalado porque Claude Code corre en Node, VS Code embebe Node, y el frontend toolchain entero es Node. "Requiere Node" deja de ser barrera real en 2026.

**Stakeholders:**
- Devs Falabella adoptando `fdh` (pilot 30 → target 500).
- Equipo plataforma operando Artifactory (o fallback aprobado).
- Equipo seguridad revisando flujo postinstall.
- Equipo `fdh` Go que implementará el wrapper y actualizará la pipeline de release.

**Constraints duras:**
- Distribución 100% interna (sin npm público, sin Homebrew público, sin Chocolatey public).
- Cero firma de binarios bloqueando GA — debe degradarse limpio.
- Compatibilidad con 30 pilots existentes que usan tarball/brew.
- Binario underlying es el mismo que el del canal install.sh — un solo build, dos rutas de entrega.

**Sibling change:**
- `hub-v2-manifest-state-profiles` (paralelo, independiente): toca contratos del catálogo y consumer manifest; no afecta este change y viceversa.

## Goals / Non-Goals

**Goals:**

- Habilitar `npx @falabella/fdh init` como camino de adopción cero-fricción.
- Habilitar `npm i -g @falabella/fdh` como instalación persistente, con `fdh upgrade` trivial (`npm update -g`).
- Sidestep del signing pain para el canal primary (npm).
- Honrar proxies corporativos en el postinstall sin código custom.
- Soportar npm/pnpm/yarn sin matrices de testing exponenciales.
- Preservar canales fallback (`install.sh`/`.deb`/`.rpm`) para entornos Node-less.
- Versionado 1:1 atómico entre binario Go y paquete npm.

**Non-Goals:**

- **No** reescribir `fdh` Go a TypeScript — sólo agregamos un wrapper TS. El core Go permanece intacto.
- **No** publicar a npm público — sólo a registry interno Falabella.
- **No** soportar el modelo "lazy install" (descargar binario en primer uso) — descartado por latencia impredecible y falla offline.
- **No** implementar el registry interno en este change — Artifactory provisioning es coordinación con plataforma.
- **No** generar autocompletes shell en este change — defer a `fdh-completion-via-npm-postinstall`.
- **No** automatizar `fdh upgrade` como comando custom — el modelo npm lo cubre nativamente.

## Decisions

### Decision 1: JFrog Artifactory Pro como registry interno con fallbacks documentados

**Primary recommendation**: JFrog Artifactory Self-Hosted Pro.

Razones:
- **Polyglot real**: npm hoy, futuro Go modules + Docker + Helm + PyPI + Maven en un solo sistema. Evita N registries paralelos.
- **JFrog Xray integrado**: security scanning de paquetes alineado con `fdh-scan-security` (change hub-v2).
- **Mejor UX/UI 2026** + REST APIs maduras + build promotion (dev → staging → prod) + federación multi-DC.
- **Standard de facto** en retailers/enterprises del tamaño de Falabella.

**Fallback budget-conscious documentado**: Sonatype Nexus 3 Repository OSS — gratis, polyglot (npm + Maven + Docker + PyPI + Helm + Go + RubyGems + APT/YUM + NuGet + Conan + R), mature, miles de enterprises usándolo. Si plataforma rechaza costo de Artifactory Pro, fallback a Nexus 3 OSS NO cambia el contrato de este change.

**Tercera opción si aplica**: GitLab Package Registry si Falabella ya tiene GitLab Enterprise (incluido sin costo extra, soporta npm).

**Alternativas descartadas:**
- *Verdaccio*: liviano y open source, pero sólo npm. Falabella va a necesitar más registries pronto; mejor empezar con polyglot.
- *Cloudsmith / Bytesafe SaaS*: descartado por restricción interna (no SaaS externo).
- *GitHub Packages*: depende de licencias enterprise que no se confirma que existan.

### Decision 2: Sub-directorio `npm/` del repo `fdh`, no repo separado

El código TS del wrapper vive en `C:/falabella/fdh/npm/` como sub-directorio del repo Go existente.

**Razones:**
- **Versionado trivialmente sincronizado**: un solo `git tag` dispara build Go + build TS + publish.
- **PR único** para cambios que tocan ambos lados.
- **Pattern establecido**: esbuild (`esbuild/npm/`), biome (`biome/packages/...`), tailwindcss-cli adoptan exactamente este layout.
- **CI más simple**: una sola pipeline coordina ambos builds.

**Trade-offs aceptados:**
- El repo `fdh` deja de ser "puramente Go" — gana un sub-tree TypeScript. Aceptable: el sub-tree es chico (~300 LOC) y co-located.
- CI cross-language ligeramente más complejo. Aceptable: gana mucho en simplicidad de release.

**Alternativas descartadas:**
- *Repo separado `@falabella/fdh-npm`*: descartado por overhead de sincronización de versiones y posibilidad de drift.
- *Mono-repo nuevo*: descartado, scope creep.

### Decision 3: Postinstall síncrono, no lazy

El postinstall descarga el binario sincrónico durante `npm install`/`npx`/`pnpm add`. Bloquea el install hasta que el binario está listo.

**Trade-off**: install +3-10s según red. Aceptable porque:
- Primer comando `fdh ...` ejecuta instantáneo sin sorpresa de latencia.
- Funciona offline después del primer install (cache hit).
- El comportamiento es predecible: o el install funciona y el binario está, o el install falla y queda claro por qué.

**Alternativa lazy descartada**: descargar binario en primer uso introduce latencia impredecible (`fdh init` tarda 5+s la primera vez), falla offline si el primer comando es local, y rompe expectativas de "está instalado, debe funcionar".

### Decision 4: Versionado 1:1 atómico binario Go ↔ paquete npm

Un solo `git tag v0.7.2` en el repo `fdh` dispara una pipeline atómica que:
1. Cross-compila el binario Go para los 5 targets soportados.
2. Sube binarios + SHA-256 + manifest a `${FDH_PKG_HOST}/fdh/0.7.2/`.
3. Builda el paquete TS bajo `npm/`, bumpea `package.json` a `0.7.2`, runea tests.
4. Publica `@falabella/fdh@0.7.2` a Artifactory.

**Ventajas:**
- Imposible que el wrapper npm apunte a una versión del binario que no existe.
- Cero confusión "¿qué versión tengo realmente?" — siempre la misma.
- Release notes únicas, no duplicadas.

**Alternativa descartada**: cycles de versionado independientes (wrapper TS y binario Go bumpean separados). Genera matriz de compatibilidad que nadie va a mantener.

### Decision 5: Honra proxies con cascada de fuentes

El postinstall lee proxy config en este orden:
1. `npm_config_https_proxy` / `npm_config_proxy` (lo que npm/pnpm/yarn ya parsearon de `.npmrc`).
2. `HTTPS_PROXY` / `HTTP_PROXY` del entorno.
3. `NO_PROXY` para excluir hosts.
4. Sin proxy si nada está seteado.

**Razón**: cubre el 99% de configuraciones corporativas sin código custom. `.npmrc` corporativo ya tiene la config — el postinstall la hereda.

**Alternativas descartadas:**
- *Sólo env vars*: ignora la convención `.npmrc` que muchos corporativos usan.
- *Config propia `FDH_PROXY`*: redundante, npm ya resuelve.

### Decision 6: Soporte cross-package-manager (npm + pnpm + yarn)

Tests del wrapper SHALL pasar con los tres package managers. El postinstall detecta el package manager activo vía `npm_config_user_agent` y adapta paths cuando difieren (pnpm symlinks, yarn classic vs yarn berry).

**Razón**: cualquiera de los tres puede ser el preferido del dev. pnpm en particular gana adopción en frontend Falabella (probable).

**Trade-off**: matriz de CI crece 3x. Aceptable porque el smoke test es rápido (<10s).

### Decision 7: Alias `falabella-installer` en el mismo paquete

`package.json` declara `bin: { fdh, falabella-installer }` apuntando al mismo wrapper. `falabella-installer` imprime one-liner de deprecation y delega a `fdh`.

**Razón**: simetría con el stub `cmd/falabella-installer-stub` del repo Go (introducido por `dev-portal` para 90 días). Mantener el alias en el paquete npm previene rupturas en scripts/docs que aún referencien el nombre viejo.

**Alternativa descartada**: paquete separado `@falabella/falabella-installer-stub`. Overhead de mantener dos paquetes para básicamente la misma cosa.

### Decision 8: Cache del binario en `node_modules/`, no en `~/.cache/fdh-npm/`

El postinstall extrae el binario a `node_modules/@falabella/fdh/bin/`. NO usa un cache global per-user.

**Razón:**
- Filesystem layout estándar de npm — herramientas existentes (npm rebuild, npm uninstall) funcionan sin tratamiento especial.
- Cache hit funciona por proyecto (npm cache de tarballs + integrity check del binario en node_modules).
- Limpiar un install corrupto es `rm -rf node_modules && npm install` — workflow conocido.

**Alternativa descartada**: cache global compartido entre proyectos (`~/.cache/fdh-npm/<version>/`). Complica la lógica, requiere garbage collection custom, no es lo que el ecosistema espera.

### Decision 9: Matriz de targets pre-built

Soporte oficial:
- `darwin-arm64`, `darwin-amd64`, `linux-arm64`, `linux-amd64`, `windows-amd64`.

No soportados (fallan con error accionable):
- `freebsd-*`, `linux-mips*`, `windows-arm64` (a evaluar si demanda corporativa lo justifica).

**Razón**: cubre 99%+ de laptops/servers Falabella. Targets exóticos pueden compilar desde source vía Go toolchain.

## Risks / Trade-offs

- **Artifactory provisioning bloquea GA** → mitigado documentando fallbacks (Nexus 3 OSS, GitLab Package Registry); el contrato no cambia con cualquiera de los tres.

- **Postinstall síncrono frustrar a devs con red lenta** → mitigado por cache hit en re-ejecuciones; documentado en quickstart que primera vez tarda 3-10s.

- **Proxies corporativos con cert inspection rompen la descarga** → mitigado por respeto a `NODE_EXTRA_CA_CERTS` y `NPM_CONFIG_CAFILE`; documentado en troubleshooting; si falla, devs usan canal `install.sh` con cert custom.

- **pnpm cambia su layout interno en major version y rompe la detección** → riesgo aceptable; tests cross-package-manager en CI lo detectan; podríamos pinear versiones probadas en docs.

- **Versionado 1:1 obliga a re-publicar npm package por cada fix de binario** → aceptado, es el costo de la atomicidad; en práctica no se hacen fixes de binario sin bump de versión.

- **Devs sin Node en entornos restrictivos** → no afecta — usan canal fallback `install.sh` o `.deb`/`.rpm`. Documentado.

- **Cert corporativo Falabella eventualmente disponible pero binario subyacente sigue sin firmar** → aceptado, canal npm sidesteps; canal fallback usa firma cuando esté.

- **npm package privado en Artifactory requiere autenticación que el dev no tiene configurada** → mitigado documentando `.npmrc` corporativo template + `fdh doctor` que detecta y reporta auth faltante.

- **Whitelist en proxies corporativos para `${FDH_PKG_HOST}` no está hecha al GA** → bloqueante real; coordinación con seguridad corporativa pre-GA es task explícita.

## Migration Plan

Pre-GA:
1. **Plataforma**: provisionar Artifactory Pro (o fallback aprobado). Crear repo virtual npm `npm-internal` con scope `@falabella/`.
2. **Seguridad**: whitelist en proxies corporativos para `${FDH_PKG_HOST}`. Revisión del flujo postinstall.
3. **Repo `fdh`**: implementar `npm/` sub-directorio + extender CI pipeline.
4. **Tests**: smoke test cross-package-manager (npm/pnpm/yarn) cross-OS (Linux/macOS/Windows).
5. **Documentación**: `README.md` del hub, `docs/quickstart.md`, portal `/install` updated.

GA:
1. Publicar primer release atómico (binario Go + paquete npm).
2. Comunicación interna anunciando `npx @falabella/fdh init` como camino primario.
3. Release notes claros: pilot existentes pueden migrar con `npm i -g @falabella/fdh`; tarball install sigue funcionando.

Rollback (si npm causa problemas inesperados):
- El paquete npm es independiente del binario Go publicado. Si hay bug en el wrapper, `npm unpublish` (en Artifactory) lo remueve sin afectar canales fallback.
- Devs revertir manualmente con tarball install (que sigue funcionando).

## Open Questions

Resueltas en este design:
- ✅ Registry interno: JFrog Artifactory Pro (con Nexus 3 OSS / GitLab Package Registry como fallbacks documentados).
- ✅ Ubicación del código TS: sub-directorio `npm/` del repo `fdh`.
- ✅ Postinstall síncrono vs lazy: síncrono.
- ✅ Versionado: 1:1 atómico.
- ✅ Proxies: cascada npm_config → env vars → NO_PROXY.
- ✅ Cross-package-manager: npm + pnpm + yarn soportados.
- ✅ Alias `falabella-installer`: mismo paquete con deprecation warning.
- ✅ Cache: en `node_modules/`, no global.
- ✅ Matriz de targets: 5 combos (darwin/linux arm64+amd64, windows amd64).

Quedan abiertas para apply / changes futuros:
- **¿`NPM_CONFIG_CAFILE` y `NODE_EXTRA_CA_CERTS` son suficientes para proxies con cert inspection corporativo?** A confirmar con seguridad durante implementation.
- **¿windows-arm64 entra en la matriz oficial o queda excluido por demanda baja?** A confirmar con base de hardware del pilot.
- **¿El `fdh doctor` extendido reporta `npm` vs `install.sh` como método de instalación?** Útil para soporte; refinable en apply.
- **¿Auto-update de `@falabella/fdh` se ofrece via comando custom o se confía 100% en `npm update -g`?** Defer a `fdh-upgrade-command` future change.
