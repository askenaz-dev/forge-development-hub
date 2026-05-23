# DESIGN.md - Indice 1:1 del Design System

> **Para LLMs:** este archivo es solo una puerta de entrada. La fuente de verdad es el DS original: tokens, componentes y documentacion generada del repo.
> No inventes aliases, namespaces ni valores locales.

---

## Fuente de Verdad

| Necesidad | Fuente canonica |
|-----------|-----------------|
| Decisiones de diseño | [`docs/DESIGN-SYSTEM.md`](docs/DESIGN-SYSTEM.md) |
| Tokens fuente | [`tokens/tokens.json`](tokens/tokens.json) |
| Dark mode | [`tokens/semantic/dark.json`](tokens/semantic/dark.json) |
| CSS generado consumible | [`packages/ui/tokens.css`](packages/ui/tokens.css) |
| Theme Tailwind v4 consumible | [`packages/ui/styles.css`](packages/ui/styles.css) |
| Metadata de componentes | [`components.meta.json`](components.meta.json) |
| Catalogo de componentes | [`COMPONENTS.md`](COMPONENTS.md) |
| Implementacion React | [`packages/ui/src/components/`](packages/ui/src/components) |

---

## Que Necesitas Hacer

| Tarea | Archivo a leer |
|-------|----------------|
| Usar componentes React del DS | [`semantic-design/ds-react.md`](semantic-design/ds-react.md) |
| Usar tokens CSS canonicos | [`semantic-design/tokens.md`](semantic-design/tokens.md) |
| Botones, links, acciones | [`semantic-design/actions.md`](semantic-design/actions.md) |
| Inputs, selects, checkboxes, switches | [`semantic-design/forms.md`](semantic-design/forms.md) |
| Cards, superficies, dialog, popover | [`semantic-design/surfaces.md`](semantic-design/surfaces.md) |
| Badge, status, toast, tooltip | [`semantic-design/feedback.md`](semantic-design/feedback.md) |
| Tabs, menus, sidebar, navegacion | [`semantic-design/navigation.md`](semantic-design/navigation.md) |
| Layout, grids, data table, charts | [`semantic-design/layout.md`](semantic-design/layout.md) |

---

## Stack Canonico

- **Paquete:** `@falabella-enablers-genai/ui`
- **React:** 19+
- **Componentes:** Radix UI + CVA + Tailwind v4
- **Tablas:** `@tanstack/react-table`
- **Charts:** ECharts via `echarts-for-react`
- **Toasts:** `sonner`
- **Command palette:** `cmdk`
- **Iconos:** `lucide-react`

CSS global para consumidores:

```css
@import "@falabella-enablers-genai/ui/tokens.css";
@import "@falabella-enablers-genai/ui/styles.css";
```

`tokens.css` ya incluye `:root` y `.dark`. No existe un subpath publico separado para dark mode.

---

## Reglas 1:1

1. **El DS original manda.** Si este directorio discrepa de `tokens/tokens.json`, `components.meta.json`, `COMPONENTS.md` o `packages/ui/src/components`, corrige este directorio.
2. **No crear tokens paralelos.** Prohibido cualquier namespace o alias local que duplique tokens canonicos.
3. **No copiar valores a mano.** Usa CSS variables generadas (`--color-*`, `--space-*`, `--type-*`, `--button-*`, etc.) o utilities de Tailwind mapeadas por `styles.css`.
4. **No importar rutas internas del paquete.** Consumidores usan solo `@falabella-enablers-genai/ui/tokens.css`, `@falabella-enablers-genai/ui/styles.css` y los exports React del paquete.
5. **Usa componentes existentes primero.** Antes de escribir UI custom, revisa `COMPONENTS.md`.
6. **Dark mode es semantico.** Activa con `.dark` en `<html>`; no codifiques colores por tema en componentes.
7. **Estados obligatorios.** Todo elemento interactivo debe cubrir default, hover, focus-visible, active y disabled.
8. **Accesibilidad base.** WCAG 2.1 AA, HTML semantico, `aria-label` en botones icon-only y touch target minimo 44x44px.

---

## Filosofia

| Principio | Practica |
|-----------|----------|
| Claridad sobre complejidad | Si necesita instrucciones, necesita rediseño |
| Consistencia con proposito | Misma situacion -> mismo patron |
| Accesibilidad como fundamento | WCAG 2.1 AA minimo |
| Token-first | El codigo referencia tokens; el valor vive en el sistema |
| 1:1 con origen | Este indice no redefine el DS, solo apunta al DS original |

---

*Fuentes: `tokens/tokens.json`, `tokens/semantic/dark.json`, `components.meta.json`, `COMPONENTS.md`, `docs/DESIGN-SYSTEM.md` v1.0.0.*
