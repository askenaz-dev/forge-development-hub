# forms.md - Formularios 1:1

> Fuentes canonicas: `Input`, `Label`, `Checkbox`, `Switch` y `Select` en `packages/ui/src/components/`.

---

## Componentes Disponibles

| Componente | Import | Props/partes clave |
|------------|--------|--------------------|
| `Input` | `import { Input } from "@falabella-enablers-genai/ui"` | `size="sm" | "md" | "lg"`, `error?: boolean` |
| `Label` | `import { Label } from "@falabella-enablers-genai/ui"` | `required?: boolean` |
| `Checkbox` | `import { Checkbox } from "@falabella-enablers-genai/ui"` | `size="sm" | "md"` |
| `Switch` | `import { Switch } from "@falabella-enablers-genai/ui"` | `size="sm" | "md"` |
| `Select` | `import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@falabella-enablers-genai/ui"` | `error?: boolean` en `SelectTrigger` |

No existe `Radio` como componente del DS original. Si se repite en tres contextos, propone RFC.

---

## React

```tsx
import {
  Checkbox,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
} from "@falabella-enablers-genai/ui";

<div className="flex flex-col gap-2">
  <Label htmlFor="email" required>Correo</Label>
  <Input id="email" type="email" placeholder="tu@correo.com" />
</div>

<div className="flex flex-col gap-2">
  <Label htmlFor="country">Pais</Label>
  <Select>
    <SelectTrigger id="country">
      <SelectValue placeholder="Selecciona" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="cl">Chile</SelectItem>
      <SelectItem value="pe">Peru</SelectItem>
    </SelectContent>
  </Select>
</div>

<Label className="flex items-center gap-3">
  <Checkbox id="terms" />
  Acepto los terminos
</Label>

<Switch aria-label="Activar notificaciones" />
```

---

## Tokens Canonicos

| Uso | Tokens |
|-----|--------|
| Campo | `--input-bg-default`, `--input-text-default`, `--input-text-placeholder` |
| Borde | `--input-border-default`, `--input-border-hover`, `--input-border-focus`, `--input-border-error` |
| Disabled | `--input-bg-disabled`, `--input-text-disabled` |
| Dimension | `--input-border-radius`, `--input-padding-x`, `--input-padding-y`, `--space-*` |
| Tipografia | `--type-body-sm-*`, `--type-body-base-*` |
| Focus | `--shadow-focus` o ring utilities mapeadas en `styles.css` |

---

## CSS Puro Equivalente

Usa esto solo cuando no puedas usar React.

```css
.ds-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.ds-label {
  color: var(--color-text-primary);
  font-family: var(--type-body-sm-font-family);
  font-size: var(--type-body-sm-font-size);
  font-weight: var(--type-body-sm-font-weight);
  line-height: var(--type-body-sm-line-height);
}

.ds-input {
  width: 100%;
  min-height: var(--space-12);
  padding-inline: var(--input-padding-x);
  color: var(--input-text-default);
  background-color: var(--input-bg-default);
  border: 1px solid var(--input-border-default);
  border-radius: var(--input-border-radius);
  font-family: var(--type-body-sm-font-family);
  font-size: var(--type-body-sm-font-size);
  transition-duration: var(--duration-fast);
  transition-property: border-color, box-shadow, background-color;
}

.ds-input::placeholder {
  color: var(--input-text-placeholder);
}

.ds-input:hover {
  border-color: var(--input-border-hover);
  box-shadow: var(--shadow-sm);
}

.ds-input:focus-visible {
  outline: none;
  background-color: var(--color-bg-page);
  border-color: var(--input-border-focus);
  box-shadow: var(--shadow-focus);
}

.ds-input[aria-invalid="true"] {
  border-color: var(--input-border-error);
  background-color: var(--color-bg-error);
}

.ds-input:disabled {
  cursor: not-allowed;
  color: var(--input-text-disabled);
  background-color: var(--input-bg-disabled);
  opacity: 0.5;
}
```

---

## Reglas

1. Labels visibles siempre; el placeholder no reemplaza al label.
2. Errores inline debajo del campo y conectados con `aria-describedby`.
3. Usa `error` en `Input` y `SelectTrigger` para el estado visual.
4. `Checkbox` y `Switch` son Radix; no reemplaces su semantica con `div`.
5. Cualquier control interactivo mantiene focus visible y target minimo 44x44px.
