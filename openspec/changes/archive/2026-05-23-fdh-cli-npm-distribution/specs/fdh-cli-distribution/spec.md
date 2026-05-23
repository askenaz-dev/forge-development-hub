## MODIFIED Requirements

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

## ADDED Requirements

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
