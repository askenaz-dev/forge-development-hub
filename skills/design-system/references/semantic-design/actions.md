# actions.md - Acciones Clicables 1:1

> Fuente canonica: [`packages/ui/src/components/button.tsx`](../packages/ui/src/components/button.tsx) y tokens `button.*`.

---

## React Primero

```tsx
import { Button } from "@falabella-enablers-genai/ui";

<Button variant="primary" size="md">Guardar</Button>
<Button variant="secondary" size="sm">Cancelar</Button>
<Button variant="danger">Eliminar</Button>
<Button variant="ghost">Mas opciones</Button>
<Button variant="link" asChild>
  <a href="/docs">Ver docs</a>
</Button>
<Button variant="ghost" size="icon" aria-label="Cerrar">
  <X />
</Button>
```

| Prop | Valores canonicos |
|------|-------------------|
| `variant` | `primary`, `secondary`, `danger`, `ghost`, `link` |
| `size` | `sm`, `md`, `lg`, `icon` |
| `asChild` | `boolean` |

---

## Tokens Canonicos

| Variante | Tokens principales |
|----------|--------------------|
| Primary | `--button-primary-bg-default`, `--button-primary-bg-hover`, `--button-primary-bg-active`, `--button-primary-text-default` |
| Secondary | `--button-secondary-bg-default`, `--button-secondary-bg-hover`, `--button-secondary-bg-active`, `--button-secondary-text-default`, `--button-secondary-border-default` |
| Danger | `--button-danger-bg-default`, `--button-danger-bg-hover`, `--button-danger-text-default` |
| Shared | `--button-border-radius`, `--button-padding-x-*`, `--button-padding-y-*`, `--duration-fast`, `--shadow-focus` |

`ghost` y `link` usan los tokens semanticos mapeados en `styles.css` (`text-muted-foreground`, `text-link`, `bg-secondary`, etc.).

---

## CSS Puro Equivalente

Usa esto solo fuera de React. En React, usa `Button`.

```css
.ds-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: var(--space-12);
  padding-inline: var(--button-padding-x-md);
  border-radius: var(--button-border-radius);
  font-family: var(--type-body-sm-font-family);
  font-size: var(--type-body-sm-font-size);
  font-weight: var(--type-body-sm-font-weight);
  line-height: 1;
  text-decoration: none;
  border: 1px solid transparent;
  cursor: pointer;
  transition-duration: var(--duration-fast);
  transition-property: color, background-color, border-color, box-shadow;
}

.ds-action:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.ds-action:disabled,
.ds-action[aria-disabled="true"] {
  pointer-events: none;
  opacity: 0.5;
}

.ds-action-primary {
  background-color: var(--button-primary-bg-default);
  color: var(--button-primary-text-default);
  box-shadow: var(--shadow-sm);
}

.ds-action-primary:hover {
  background-color: var(--button-primary-bg-hover);
  box-shadow: var(--shadow-md);
}

.ds-action-primary:active {
  background-color: var(--button-primary-bg-active);
  box-shadow: var(--shadow-sm);
}

.ds-action-secondary {
  background-color: var(--button-secondary-bg-default);
  color: var(--button-secondary-text-default);
  border-color: var(--button-secondary-border-default);
  box-shadow: var(--shadow-xs);
}

.ds-action-secondary:hover {
  background-color: var(--button-secondary-bg-hover);
  border-color: var(--button-secondary-border-hover);
  box-shadow: var(--shadow-sm);
}

.ds-action-secondary:active {
  background-color: var(--button-secondary-bg-active);
}

.ds-action-danger {
  background-color: var(--button-danger-bg-default);
  color: var(--button-danger-text-default);
  box-shadow: var(--shadow-sm);
}

.ds-action-danger:hover,
.ds-action-danger:active {
  background-color: var(--button-danger-bg-hover);
}
```

---

## Icon-only buttons

Misma `Button`, sin texto. Siempre con `aria-label`.

```tsx
<Button variant="ghost" size="icon" aria-label="Cerrar">
  <X />
</Button>
```

Combinaciones canonicas (no son props nuevas, son guias de uso):

| Rol semantico       | Combinacion recomendada                                                |
|---------------------|------------------------------------------------------------------------|
| Header / toolbar    | `variant="ghost" size="icon"`                                          |
| Acción destructiva  | `variant="ghost" size="icon"` + tooltip; usa `<DropdownMenu>` para confirmacion |
| CTA flotante (FAB)  | `variant="primary" size="icon"`                                        |

Reglas adicionales:

1. `aria-label` obligatorio.
2. No mezcles texto e icono en `size="icon"`. Si necesitas texto, usa `sm/md/lg`.
3. El SVG hereda tamaño desde el variant (`[&_svg]:size-4`); no fijes `h-4 w-4` manualmente.

---

## Reglas

1. Botones con solo icono siempre llevan `aria-label`.
2. Usa `asChild` para renderizar un link con apariencia de boton.
3. No crees variantes visuales nuevas sin RFC.
4. No uses tokens primitivos de color (`--color-blue-*`, `--color-gray-*`) en UI.
5. Si necesitas un estado no cubierto por los tokens de componente, usa la implementacion React o propone el token faltante.
