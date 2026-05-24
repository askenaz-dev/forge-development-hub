# surfaces.md - Superficies 1:1

*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

> Fuentes canonicas: `Surface`, `Card`, `Dialog`, `AlertDialog` y `Popover`.

---

## Componentes

| Componente | Uso | Variantes/partes |
|------------|-----|------------------|
| `Surface` | Contenedor composable | `variant`, `padding`, `radius`, `asChild` |
| `Card` | Card estructurada | `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` |
| `Dialog` | Modal general | `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogFooter` |
| `AlertDialog` | Confirmacion destructiva | `AlertDialogAction`, `AlertDialogCancel` |
| `Popover` | Panel flotante | `PopoverTrigger`, `PopoverContent`, `PopoverAnchor` |

---

## React

```tsx
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Surface,
} from "@forge-enablers-genai/ui";

<Surface variant="default" padding="lg" radius="xl">
  <Card>
    <CardHeader>
      <CardTitle>Resumen</CardTitle>
      <CardDescription>Descripcion breve</CardDescription>
    </CardHeader>
    <CardContent>Contenido</CardContent>
    <CardFooter>Acciones</CardFooter>
  </Card>
</Surface>
```

```tsx
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@forge-enablers-genai/ui";

<Dialog>
  <DialogTrigger asChild>
    <Button>Abrir</Button>
  </DialogTrigger>
  <DialogContent size="md">
    <DialogHeader>
      <DialogTitle>Editar datos</DialogTitle>
      <DialogDescription>Actualiza la informacion principal.</DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="secondary">Cancelar</Button>
      <Button>Guardar</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

---

## Variantes Canonicas

| Componente | Prop | Valores |
|------------|------|---------|
| `Surface` | `variant` | `default`, `subtle`, `elevated`, `interactive`, `ghost` |
| `Surface` | `padding` | `none`, `sm`, `md`, `lg` |
| `Surface` | `radius` | `none`, `lg`, `xl` |
| `DialogContent` | `size` | `sm`, `md`, `lg`, `full` |

---

## Tokens y Utilities

| Uso | Canonico |
|-----|----------|
| Fondo card | `bg-card` / `--color-bg-raised` |
| Fondo popover | `bg-popover` / `--color-bg-overlay` |
| Texto | `text-card-foreground` / `--color-text-primary` |
| Borde | `border-border` / `--color-border-default` |
| Radio | `rounded-lg`, `rounded-xl` / `--radius-lg`, `--radius-xl` |
| Elevacion | `shadow-xs`, `shadow-sm`, `shadow-xl` / `--shadow-*` |
| Focus | `focus-visible:ring-ring-soft` o `--shadow-focus` |

---

## CSS Puro Equivalente

```css
.ds-card {
  background-color: var(--color-bg-raised);
  color: var(--color-text-primary);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-xs);
}

.ds-surface-interactive {
  background-color: var(--color-bg-raised);
  color: var(--color-text-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition-duration: var(--duration-fast);
  transition-property: background-color, box-shadow;
}

.ds-surface-interactive:hover {
  box-shadow: var(--shadow-md);
}

.ds-surface-interactive:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}
```

---

## Reglas

1. Usa `AlertDialog` para confirmaciones destructivas.
2. Usa `Popover` para contenido contextual no modal.
3. No crees un componente local `Panel` si `Surface` o `Card` cubren el caso.
4. No uses colores primitivos en superficies; usa `bg-card`, `bg-popover`, `--color-bg-*`.
