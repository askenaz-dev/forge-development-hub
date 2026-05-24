# tokens.md - CSS Custom Properties Canonicas

*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

> Los tokens se generan desde `tokens/tokens.json` y `tokens/semantic/dark.json`.
> Este archivo no copia valores. Solo documenta como consumirlos 1:1.

---

## Imports Publicos

```css
@import "@forge-enablers-genai/ui/tokens.css";
@import "@forge-enablers-genai/ui/styles.css";
```

- `tokens.css` expone `:root` y `.dark`.
- `styles.css` mapea tokens a utilities Tailwind v4 via `@theme`.
- No uses un import separado para dark mode; no es un export publico.
- No apuntes a rutas internas del paquete; usa los exports publicos.

---

## Grupos de Variables

| Grupo | Ejemplos | Fuente |
|-------|----------|--------|
| Color semantico | `--color-text-primary`, `--color-bg-raised`, `--color-border-focus` | `color.*` |
| Color interactivo | `--color-interactive-default`, `--color-interactive-hover`, `--color-interactive-active` | `color.interactive.*` |
| Acentos | `--color-accent-primary`, `--color-accent-secondary`, `--color-accent-tertiary` | `color.accent.*` |
| Espaciado | `--space-1`, `--space-2`, `--space-4`, `--space-6`, `--space-12` | `space.*` |
| Radios | `--radius-base`, `--radius-lg`, `--radius-xl`, `--radius-full` | `radius.*` |
| Sombras | `--shadow-xs`, `--shadow-sm`, `--shadow-md`, `--shadow-focus` | `shadow.*` |
| Tipografia | `--type-body-sm-font-size`, `--type-heading-h2-line-height` | `type.*` |
| Motion | `--duration-fast`, `--duration-normal`, `--duration-slow` | `duration.*` |
| Breakpoints | `--breakpoint-sm`, `--breakpoint-md`, `--breakpoint-lg` | `breakpoint.*` |
| Button | `--button-primary-bg-default`, `--button-secondary-border-hover` | `button.*` |
| Input | `--input-bg-default`, `--input-border-focus`, `--input-text-placeholder` | `input.*` |
| Badge | `--badge-pink-bg`, `--badge-blue-text` | `badge.*` |
| Chart | `--chart-palette-1`, `--chart-axis-label`, `--chart-tooltip-bg` | `chart.*` |

---

## Tailwind v4 Map

`styles.css` convierte tokens en utilities. Usa estas utilities en React siempre que estes siguiendo los componentes del DS.

| Utility | Variable de theme | Token base |
|---------|-------------------|------------|
| `bg-background` | `--color-background` | `--color-bg-page` |
| `text-foreground` | `--color-foreground` | `--color-text-primary` |
| `bg-card` | `--color-card` | `--color-bg-raised` |
| `bg-popover` | `--color-popover` | `--color-bg-overlay` |
| `bg-primary` | `--color-primary` | `--color-interactive-default` |
| `hover:bg-primary-hover` | `--color-primary-hover` | `--color-interactive-hover` |
| `text-primary-foreground` | `--color-primary-foreground` | `--button-primary-text-default` |
| `border-border` | `--color-border` | `--color-border-default` |
| `text-muted-foreground` | `--color-muted-foreground` | `--color-text-secondary` |
| `shadow-xs` | `--shadow-xs` | theme shadow |
| `duration-fast` | `--duration-fast` | `duration.fast` |

---

## CSS Puro

Cuando no uses React, referencia las variables canonicas directamente.

```css
.ds-surface {
  background-color: var(--color-bg-raised);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-xs);
}

.ds-surface:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}
```

Si una variable no existe en `packages/ui/tokens.css` o `packages/ui/styles.css`, no la inventes. Propone un RFC.

---

## Dark Mode

```html
<html class="dark">
  <body>...</body>
</html>
```

Los tokens semanticos cambian por `.dark`. El codigo de UI debe seguir usando el mismo token (`--color-text-primary`, `bg-card`, etc.) en ambos temas.

---

## Checklist Anti-Drift

1. Buscar namespaces paralelos de tokens: debe dar cero resultados.
2. Buscar imports separados de dark mode en docs de consumo: no debe aparecer ninguno.
3. Buscar tokens nuevos: cada `var(--*)` debe existir en `packages/ui/tokens.css` o `packages/ui/styles.css`.
4. Si necesitas un valor que no existe, no uses un raw value silencioso; documenta el gap y propone RFC.
