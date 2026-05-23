# feedback.md - Feedback 1:1

> Fuentes canonicas: `Badge`, `Status`, `Toaster` y `Tooltip`.

---

## Componentes

| Componente | Import | Uso |
|------------|--------|-----|
| `Badge` | `import { Badge } from "@falabella-enablers-genai/ui"` | Etiquetas compactas |
| `StatusDot` | `import { StatusDot } from "@falabella-enablers-genai/ui"` | Indicador visual puntual |
| `StatusBadge` | `import { StatusBadge } from "@falabella-enablers-genai/ui"` | Estado con pill y dot opcional |
| `StatusIndicator` | `import { StatusIndicator } from "@falabella-enablers-genai/ui"` | Dot + texto inline |
| `Toaster`, `toast` | `import { Toaster, toast } from "@falabella-enablers-genai/ui"` | Notificaciones |
| `Tooltip` | `import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from "@falabella-enablers-genai/ui"` | Ayuda contextual |

No existe `Alert` como componente del DS original. Compone con `Surface` + `Status` o propone RFC si se repite.

---

## Badge

```tsx
import { Badge } from "@falabella-enablers-genai/ui";

<Badge variant="default">Default</Badge>
<Badge variant="muted">Borrador</Badge>
<Badge variant="primary">Nuevo</Badge>
<Badge variant="success">Activo</Badge>
<Badge variant="warning">Pendiente</Badge>
<Badge variant="error">Error</Badge>
<Badge variant="info">Info</Badge>
<Badge variant="pink">Beta</Badge>
<Badge variant="blue">v2</Badge>
```

Variantes canonicas: `default`, `muted`, `primary`, `success`, `warning`, `error`, `info`, `pink`, `blue`.

---

## Status

```tsx
import { StatusBadge, StatusDot, StatusIndicator } from "@falabella-enablers-genai/ui";

<StatusDot status="success" />
<StatusBadge status="warning">Pendiente</StatusBadge>
<StatusIndicator status="error" label="Sin conexion" />
```

Statuses canonicos: `success`, `warning`, `error`, `info`, `neutral`.

---

## Toast

```tsx
import { Toaster, toast } from "@falabella-enablers-genai/ui";

<Toaster />

toast.success("Guardado correctamente");
toast.error("No se pudo guardar");
toast("Mensaje neutro", { description: "Detalle adicional" });
```

`Toaster` viene de `sonner`; no dupliques un sistema de toast local.

---

## Tooltip

```tsx
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@falabella-enablers-genai/ui";

<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Button variant="ghost" size="icon" aria-label="Informacion">
        <InfoIcon />
      </Button>
    </TooltipTrigger>
    <TooltipContent>Texto de ayuda</TooltipContent>
  </Tooltip>
</TooltipProvider>
```

---

## Tokens y Utilities

| Uso | Canonico |
|-----|----------|
| Success | `text-success`, `bg-success-soft`, `--color-text-success` |
| Warning | `text-warning`, `bg-warning-soft`, `--color-text-warning` |
| Error | `text-error`, `bg-error-soft`, `--color-text-error` |
| Info | `text-info`, `bg-info-soft`, `--color-info` |
| Neutral | `text-muted-foreground`, `bg-muted-subtle` |
| Badge marca | `--badge-pink-*`, `--badge-blue-*` |

---

## Reglas

1. Colores de estado solo comunican estado; no son decorativos.
2. Errores importantes usan `role="alert"` en la composicion que los contiene.
3. Tooltips no reemplazan labels ni mensajes de error.
4. Botones que abren tooltips y solo tienen icono necesitan `aria-label`.
