# hub-agents-primitive Specification

## Purpose

Introduce `agent` como primitiva del hub distinta de `skill` y `rule`, materializada como directorios `agents/<name>/AGENT.md` con frontmatter normativo (`name`, `kind: agent`, `description`, `agents_supported`, `tools` non-vacío) y un cuerpo que contiene system prompt + template. Define la materialización per-agente —al momento de este change sólo Claude Code soporta agents distribuibles, `.claude/agents/<name>.md`— con skip informativo en ecosistemas que aún no lo soportan. Ship con la primera entry real `agents/falabella-pr-writer/`, lista para generar descripciones de PR en formato Falabella.

## Requirements

### Requirement: Formato de `agents/<name>/AGENT.md` con frontmatter normativo

El hub SHALL distribuir agents como directorios `agents/<name>/` cuyo archivo entrypoint es `AGENT.md` con frontmatter YAML que declare: `name` (kebab-case), `kind: agent`, `description` (one-liner), `agents_supported`, `tools` (lista de tools que el agente puede usar, ej. `[Read, Grep, Bash]`), y opcionalmente `tags`, `owner_team` y `model_preference`.

#### Scenario: AGENT.md válido

- **WHEN** un admin abre `agents/falabella-pr-writer/AGENT.md`
- **THEN** encuentra frontmatter con `name: falabella-pr-writer`, `kind: agent`, `description`, `agents_supported: [claude-code]`, `tools: [Read, Grep, Bash]`, y un cuerpo markdown que contiene el system prompt + template

#### Scenario: Tools vacío es inválido

- **WHEN** un AGENT.md declara `tools: []`
- **THEN** la validación falla pidiendo al menos un tool (un agente sin tools no puede actuar)

### Requirement: Materialización per-agente

`fdh install` SHALL materializar cada agent seleccionado al path que cada agente target espera: `.claude/agents/<name>.md` para Claude Code. Para ecosistemas que aún no soportan agents distribuibles (Codex, Copilot, OpenCode al momento de este change), `fdh install` SHALL omitir la materialización con un mensaje informativo en lugar de fallar.

#### Scenario: Materialización en Claude Code

- **WHEN** `fdh install` materializa `falabella-pr-writer` para Claude Code en scope project
- **THEN** existe `<cwd>/.claude/agents/falabella-pr-writer.md` con el contenido completo del `AGENT.md` y la entrada correspondiente en `.gitignore` managed

#### Scenario: Agente target sin soporte para agents

- **WHEN** un agent declara `agents_supported: [claude-code]` y el manifest selecciona también Codex
- **THEN** la materialización ocurre sólo para Claude Code; `fdh install` imprime una nota informativa sobre Codex

### Requirement: Primera entry real `agents/falabella-pr-writer/`

Como parte del apply de este change, el hub SHALL contener `agents/falabella-pr-writer/AGENT.md` con frontmatter completo, un system prompt que describa el rol ("genera descripciones de PR en formato Falabella"), y un template que defina las secciones esperadas (`## What`, `## Why`, `## Test plan`, `## Risk`).

#### Scenario: Agent shipped post-apply

- **WHEN** termina el apply del change
- **THEN** existe `agents/falabella-pr-writer/AGENT.md` con `name: falabella-pr-writer`, `kind: agent`, `agents_supported: [claude-code]`, `tools: [Read, Grep, Bash]`, system prompt + template, listo para ser materializado por `fdh install`

#### Scenario: Agent referenciado desde profile minimal

- **WHEN** se inspecciona `hub/profiles.yaml` después del apply
- **THEN** el profile `minimal` incluye `agents: [falabella-pr-writer]`
