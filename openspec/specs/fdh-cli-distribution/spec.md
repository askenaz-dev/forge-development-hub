# fdh-cli-distribution Specification

## Purpose

Canales de distribución del binario `fdh` per-OS, ordenados por adopción: **npm primary** (`@falabella/fdh`) para devs con Node ya instalado (mayoría en 2026), con `install.sh`/`install.ps1`/`.deb`/`.rpm` como fallback Node-less para servers headless y entornos minimal. Homebrew tap interno y winget source interno quedan como canales secundarios/opcionales (no bloquean GA). Manifest público de versiones + endpoint configurable vía `FDH_PKG_HOST`. Firma de binarios deja de bloquear el rollout principal porque el canal npm sidesteps SmartScreen/Gatekeeper. Cierra el gap entre el binario `fdh` y el PATH del developer.

## Requirements

### Requirement: One-liner universal de instalación per-OS

El sistema SHALL proveer scripts oficiales `install.sh` (POSIX) e `install.ps1` (PowerShell) que descarguen el binario `fdh` correcto para el OS/arch del host desde un endpoint interno conocido, verifiquen su integridad por SHA-256, lo extraigan a un directorio per-usuario y lo agreguen al PATH del usuario sin requerir privilegios de administrador.

#### Scenario: Instalación exitosa en macOS

- **WHEN** un developer en macOS ejecuta `curl -fsSL https://${FDH_PKG_HOST}/fdh/install.sh | bash` (con `FDH_PKG_HOST` apuntando al host interno)
- **THEN** el script detecta `darwin/arm64` (o `darwin/amd64`), descarga el tarball correspondiente, valida SHA-256 contra el manifest publicado, extrae `fdh` a `$HOME/.fdh/bin/fdh`, agrega `export PATH="$HOME/.fdh/bin:$PATH"` a `~/.zshrc` (o `~/.bashrc` según `$SHELL`) si aún no está, y deja el binario ejecutable

#### Scenario: Instalación exitosa en Windows

- **WHEN** un developer en Windows ejecuta `iwr -useb https://${env:FDH_PKG_HOST}/fdh/install.ps1 | iex` (con `FDH_PKG_HOST` apuntando al host interno)
- **THEN** el script detecta `windows/amd64`, descarga el zip correspondiente, valida SHA-256, extrae `fdh.exe` a `$env:USERPROFILE\.fdh\bin\fdh.exe`, agrega esa ruta al `Path` de usuario en el registro (`HKCU:\Environment`) si aún no está, y emite un mensaje indicando que debe abrirse una nueva sesión de PowerShell para que el PATH tome efecto

#### Scenario: Verificación de integridad falla

- **WHEN** el SHA-256 del binario descargado no coincide con el SHA-256 publicado en el manifest
- **THEN** el script elimina el archivo descargado, no modifica el PATH, imprime un error con el SHA esperado vs el SHA observado, y sale con código distinto de cero

#### Scenario: Re-ejecución idempotente

- **WHEN** un developer ejecuta el instalador por segunda vez con la misma versión ya presente
- **THEN** el script detecta el binario existente, valida su SHA-256, no re-descarga, no duplica entradas en `~/.zshrc` ni en el registro de Windows, y sale con código cero indicando "ya instalado"

#### Scenario: Shell no reconocido

- **WHEN** el script detecta un `$SHELL` que no maneja (ej.: fish, nushell)
- **THEN** copia el binario a su destino y emite una instrucción accionable: `"detected $SHELL=<value>; please add $HOME/.fdh/bin to your PATH manually"`, saliendo con código cero

### Requirement: Distribución vía Homebrew tap interno

El sistema SHALL publicar una formula Homebrew en un tap interno Falabella (`falabella-internal/tools`) que permita instalar `fdh` con `brew tap falabella-internal/tools && brew install fdh` en macOS y Linux.

#### Scenario: Install vía brew

- **WHEN** un developer ejecuta `brew tap falabella-internal/tools && brew install fdh`
- **THEN** Homebrew descarga el bottle/tarball desde el host interno, lo instala bajo el prefix de brew, hace symlink a `fdh` en `$(brew --prefix)/bin/`, y `fdh --version` responde con la versión instalada sin pasos manuales adicionales

#### Scenario: Upgrade vía brew

- **WHEN** se publica una versión nueva en el tap y el developer ejecuta `brew upgrade fdh`
- **THEN** Homebrew descarga e instala la nueva versión, reemplaza el binario y `fdh --version` reporta la versión nueva

### Requirement: Distribución vía winget source interno

El sistema SHALL publicar manifests winget en un source interno Falabella que permita instalar `fdh` con `winget install Falabella.FDH` tras agregar el source.

#### Scenario: Install vía winget

- **WHEN** un developer con el source interno agregado ejecuta `winget install Falabella.FDH`
- **THEN** winget descarga el instalador desde el source interno, instala el binario en una ruta de usuario, registra `fdh.exe` en el PATH y `fdh --version` responde sin reiniciar la sesión

### Requirement: Paquetes nativos `.deb` y `.rpm` para Linux corporativo

El sistema SHALL proveer paquetes `.deb` (Debian/Ubuntu) y `.rpm` (RHEL/Fedora) en repositorios internos Falabella que instalen `fdh` con el package manager nativo.

#### Scenario: Install vía apt

- **WHEN** un developer con el repo interno configurado ejecuta `sudo apt-get install fdh`
- **THEN** apt instala el binario en `/usr/local/bin/fdh` (o `/usr/bin/fdh`), `fdh --version` responde, y `apt-get remove fdh` lo desinstala limpiamente

#### Scenario: Install vía rpm

- **WHEN** un developer con el repo interno configurado ejecuta `sudo dnf install fdh`
- **THEN** dnf instala el binario en `/usr/local/bin/fdh`, `fdh --version` responde, y `dnf remove fdh` lo desinstala limpiamente

### Requirement: Endpoint de distribución configurable via `FDH_PKG_HOST`

Los scripts `install.sh` y `install.ps1` SHALL leer el host de descarga desde la variable de entorno `FDH_PKG_HOST` (no hardcodearlo), permitiendo que el endpoint corporativo real (Artifactory, Nexus, S3 interno, GitHub Enterprise Releases, etc.) se inyecte sin modificar los scripts. El default placeholder es `pkg.falabella.internal` hasta que el equipo de plataforma confirme el host real.

#### Scenario: Override vía env var

- **WHEN** un developer ejecuta `FDH_PKG_HOST=falabella.jfrog.io/artifactory/fdh-generic-local curl -fsSL https://falabella.jfrog.io/artifactory/fdh-generic-local/fdh/install.sh | bash`
- **THEN** el script usa el host pasado en `FDH_PKG_HOST` para resolver todas las URLs (binario, manifest, SHA-256) sin modificar el script

#### Scenario: Default placeholder cuando env var no está

- **WHEN** un developer ejecuta el one-liner sin setear `FDH_PKG_HOST`
- **THEN** el script usa `pkg.falabella.internal` como default y emite un warning indicando que se está usando el placeholder; si ese host no responde, sale con error accionable nombrando la env var como override

### Requirement: Manifest público de versiones disponibles

El sistema SHALL publicar en `https://${FDH_PKG_HOST}/fdh/manifest.json` un manifest legible por los scripts de instalación que liste para cada versión: tarball/zip URLs per (os, arch), SHA-256, fecha de release y nota de breaking changes si aplica.

#### Scenario: Manifest contiene versión solicitada

- **WHEN** `install.sh` solicita la versión `latest` (default) o una versión específica
- **THEN** el manifest expone esa versión con todos los pares (os, arch) soportados y sus respectivos SHA-256, y el script puede resolver la URL del binario sin scraping

#### Scenario: Manifest indica un breaking change

- **WHEN** un developer instala una versión cuyo manifest tiene `breaking: true`
- **THEN** el instalador imprime un warning con un link a las release notes y pide confirmación interactiva (omitible con `--yes`)

### Requirement: Firma de binarios opcional con warning explícito si está ausente

El sistema MAY distribuir binarios firmados con el certificado corporativo Falabella (Authenticode para Windows, Developer ID + notarization para macOS); cuando la firma no esté disponible y se use el canal fallback (`install.sh`/`install.ps1`/tarball/`.deb`/`.rpm`), el instalador SHALL imprimir un warning visible que nombre la ausencia de firma, confirme la verificación SHA-256, y continúe la instalación sin fallar. Para el canal **primary npm** (`@falabella/fdh`), el binario se ejecuta desde `node_modules/` y Windows SmartScreen / macOS Gatekeeper no disparan los mismos checks, por lo que la firma deja de ser bloqueante para el rollout principal.

#### Scenario: Binario firmado disponible (canal fallback)

- **WHEN** el manifest declara `signed: true` para la versión instalada y el developer usa `install.sh`/`install.ps1`/tarball
- **THEN** el instalador verifica la firma además del SHA-256 antes de mover el binario al destino final; si la firma no valida, aborta sin tocar PATH

#### Scenario: Binario no firmado (canal fallback)

- **WHEN** el manifest declara `signed: false` y el developer usa el canal fallback
- **THEN** el instalador imprime un warning nombrando explícitamente que el binario no está firmado, indica que el SHA-256 fue verificado contra el manifest, sugiere usar el canal npm si su política de seguridad requiere menos warnings, y continúa con código cero

#### Scenario: Canal npm sin warning de signing

- **WHEN** un developer instala vía `npx @falabella/fdh init` o `npm i -g @falabella/fdh` con binario subyacente no firmado
- **THEN** no aparece warning de SmartScreen/Gatekeeper porque el binario se ejecuta desde `node_modules/`; la instalación es transparente

### Requirement: Canal npm como distribución primary

El canal npm (`@falabella/fdh`) SHALL ser el canal primary de distribución del binario `fdh` para devs con Node ya instalado (mayoría en 2026 dada la dependencia de Claude Code, VS Code, frontend toolchain). Toda documentación oficial SHALL presentar `npx @falabella/fdh init` y `npm i -g @falabella/fdh` como comandos canónicos antes que cualquier otra alternativa.

#### Scenario: Quickstart lidera con npm

- **WHEN** un nuevo dev abre `docs/quickstart.md` del repo `fdh`
- **THEN** las primeras dos secciones explican `npx @falabella/fdh init` y `npm i -g @falabella/fdh`; brew/install.sh aparecen después como alternativas para entornos Node-less

#### Scenario: Portal `/install` por defecto

- **WHEN** un usuario abre el portal web `/install` sin un OS particular detectado
- **THEN** la CTA principal es el comando npm; otras opciones aparecen vía tabs/expandables

### Requirement: Canales fallback Node-less se mantienen

Los canales `install.sh`/`install.ps1` y los paquetes nativos `.deb`/`.rpm` SHALL mantenerse para entornos sin Node disponible (servers headless, contenedores minimal, air-gapped, dev VMs corporativas estrictas). El binario subyacente SHALL ser el mismo que el del paquete npm; sólo cambia el medio de entrega.

#### Scenario: Server sin Node usa install.sh

- **WHEN** un server Linux headless sin Node ejecuta `curl -fsSL https://${FDH_PKG_HOST}/fdh/install.sh | bash`
- **THEN** la instalación procede como definido en el spec original (descarga + SHA-256 + extracción + PATH editing), con el mismo binario que entrega el paquete npm

#### Scenario: Server Debian usa apt

- **WHEN** un server Debian con repo interno configurado ejecuta `sudo apt-get install fdh`
- **THEN** apt instala el binario en `/usr/local/bin/fdh` (igual que antes), sin requerir Node

### Requirement: Brew tap y winget source pasan a opcionales/deferred

Los canales brew tap interno y winget source interno SHALL ser opcionales y SHALL NO bloquear GA. Se publican cuando plataforma tenga capacidad de operarlos, no como prerrequisito. La documentación SHALL mencionarlos como "available if your team prefers package managers" en lugar de presentarlos como instalación primaria.

#### Scenario: GA sin brew tap

- **WHEN** la fecha de GA del rollout llega y el tap interno Homebrew aún no está provisionado
- **THEN** el rollout procede usando el canal npm primary; la documentación menciona brew como "coming soon" sin bloquear

#### Scenario: Brew tap publicado posteriormente

- **WHEN** plataforma activa el tap interno semanas después de GA
- **THEN** la documentación se actualiza para listar `brew tap falabella-internal/tools && brew install fdh` como alternativa adicional sin desplazar al canal npm primary
