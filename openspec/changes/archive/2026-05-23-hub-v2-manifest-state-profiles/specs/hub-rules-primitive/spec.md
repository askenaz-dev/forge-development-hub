*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## ADDED Requirements

### Requirement: Formato de `rules/<name>/RULE.md` con frontmatter normativo

El hub SHALL distribuir rules como directorios `rules/<name>/` cuyo archivo entrypoint es `RULE.md` con frontmatter YAML que declare: `name` (kebab-case), `kind: rule`, `scope` (lista de globs), `severity` (`info | warning | error`), `agents_supported` (subset de `[claude-code, codex, copilot, opencode]`), y opcionalmente `description` y `tags`.

#### Scenario: RULE.md válido

- **WHEN** un admin abre `rules/no-console-log/RULE.md`
- **THEN** encuentra frontmatter con `name: no-console-log`, `kind: rule`, `scope: ["**/*.{ts,tsx,js,jsx}"]`, `severity: warning`, `agents_supported: [claude-code, codex, copilot, opencode]` y un cuerpo markdown que describe la regla

#### Scenario: Severity inválido

- **WHEN** un RULE.md declara `severity: critical`
- **THEN** la validación falla nombrando el archivo y los valores permitidos (`info | warning | error`)

### Requirement: Materialización per-agente de rules

`fdh install` SHALL materializar cada rule seleccionada en el directorio que cada agente target espera: `.claude/rules/<name>.md` para Claude Code, `.codex/rules/<name>.md` para Codex, `.github/rules/<name>.md` para Copilot, `.opencode/rules/<name>.md` para OpenCode. La materialización SHALL preservar el cuerpo markdown y SHALL transformar el frontmatter al formato esperado por cada ecosistema.

#### Scenario: Materialización en Claude Code

- **WHEN** `fdh install` materializa `no-console-log` para Claude Code en scope project
- **THEN** existe `<cwd>/.claude/rules/no-console-log.md` con el cuerpo de `rules/no-console-log/RULE.md` y un marker `.fdh-managed.yaml` en el directorio padre o como sibling

#### Scenario: Agente no soportado se omite

- **WHEN** una rule declara `agents_supported: [claude-code]` y el manifest del consumer apunta a Codex
- **THEN** la rule no se materializa para Codex y `fdh install` imprime una línea informativa explicando el skip

### Requirement: Primera entry real `rules/no-console-log/`

Como parte del apply de este change, el hub SHALL contener `rules/no-console-log/RULE.md` con frontmatter completo y un cuerpo que prohíba el uso de `console.log()` (y equivalentes triviales) en código committed, sugiriendo el logger del proyecto como alternativa.

#### Scenario: Rule shipped post-apply

- **WHEN** termina el apply del change
- **THEN** existe `rules/no-console-log/RULE.md` con `name: no-console-log`, `kind: rule`, `scope: ["**/*.{ts,tsx,js,jsx}"]`, `severity: warning` y un cuerpo que explica la regla, el por qué, y un ejemplo de la alternativa esperada

#### Scenario: Rule referenciada desde profile minimal

- **WHEN** se inspecciona `hub/profiles.yaml` después del apply
- **THEN** el profile `minimal` incluye `rules: [no-console-log]`
