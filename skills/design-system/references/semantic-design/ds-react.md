# ds-react.md - Design System React 1:1

> Referencia rapida del paquete `@falabella-enablers-genai/ui`.
> La API completa vive en [`COMPONENTS.md`](../COMPONENTS.md) y la metadata fuente en [`components.meta.json`](../components.meta.json).

---

## Instalacion

```bash
npm install @falabella-enablers-genai/ui
```

```css
@import "@falabella-enablers-genai/ui/tokens.css";
@import "@falabella-enablers-genai/ui/styles.css";
```

Dark mode se activa con `class="dark"` en `<html>`. `tokens.css` ya incluye los overrides `.dark`.

---

## Stack Interno

| Capa | Tecnologia |
|------|------------|
| React | React 19+ |
| Primitivos UI | Radix UI |
| Variantes | CVA |
| Estilos | Tailwind v4 via `@theme` en `styles.css` |
| Merge de clases | `cn()` |
| Tablas | `@tanstack/react-table` |
| Charts | ECharts + `echarts-for-react` |
| Iconos | `lucide-react` |
| Toasts | `sonner` |
| Command palette | `cmdk` |

---

## Componentes Exportados

Esta tabla debe permanecer sincronizada con `components.meta.json`.

| Grupo | Componentes |
|-------|-------------|
| Acciones | `Button` |
| Tipografia | `Heading`, `Text` |
| Superficies | `Surface`, `Card`, `Dialog`, `AlertDialog`, `Popover` |
| Formularios | `Input`, `Label`, `Checkbox`, `Switch`, `Select` |
| Feedback | `Badge`, `StatusDot`, `StatusBadge`, `StatusIndicator`, `Toaster`, `toast`, `Tooltip` |
| Navegacion | `Tabs`, `DropdownMenu`, `Command`, `Sidebar`, `Avatar`, `ScrollArea`, `Collapsible` |
| Datos | `DataTable` |
| Marca | `Logo` |
| Charts | `Chart`, `BarChart`, `LineChart`, `PieChart`, `AreaChart`, `ScatterChart`, `RadarChart`, `GaugeChart`, `TreemapChart`, `HeatmapChart`, `FunnelChart`, `WaterfallChart`, `SankeyChart`, `SunburstChart`, `CandlestickChart`, `BoxPlotChart`, `ParallelChart` |

---

## Ejemplos Canonicos

### Button

```tsx
import { Button } from "@falabella-enablers-genai/ui";

<Button variant="primary" size="md">Guardar</Button>
<Button variant="secondary" size="sm">Cancelar</Button>
<Button variant="danger">Eliminar</Button>
<Button variant="ghost" size="icon" aria-label="Cerrar">
  <X />
</Button>
<Button variant="link" asChild>
  <a href="/docs">Ver docs</a>
</Button>
```

Variantes: `primary`, `secondary`, `danger`, `ghost`, `link`.
Tamanos: `sm`, `md`, `lg`, `icon`.

### Formularios

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

<Select>
  <SelectTrigger>
    <SelectValue placeholder="Selecciona" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="a">Opcion A</SelectItem>
    <SelectItem value="b">Opcion B</SelectItem>
  </SelectContent>
</Select>

<Checkbox id="terms" />
<Switch size="md" />
```

### Superficies

```tsx
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Surface,
} from "@falabella-enablers-genai/ui";

<Surface variant="interactive" padding="lg">
  <Card>
    <CardHeader>
      <CardTitle>Resumen</CardTitle>
      <CardDescription>Estado general</CardDescription>
    </CardHeader>
    <CardContent>Contenido</CardContent>
  </Card>
</Surface>
```

### Dialog

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
} from "@falabella-enablers-genai/ui";

<Dialog>
  <DialogTrigger asChild>
    <Button>Abrir</Button>
  </DialogTrigger>
  <DialogContent size="md">
    <DialogHeader>
      <DialogTitle>Confirmar accion</DialogTitle>
      <DialogDescription>Esta accion no se puede deshacer.</DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="secondary">Cancelar</Button>
      <Button variant="danger">Eliminar</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

`DialogContent` soporta `size="sm" | "md" | "lg" | "full"`.

### Feedback

```tsx
import { Badge, StatusBadge, Toaster, toast } from "@falabella-enablers-genai/ui";

<Badge variant="success">Activo</Badge>
<Badge variant="warning">Pendiente</Badge>
<Badge variant="error">Error</Badge>
<StatusBadge status="info">Sincronizando</StatusBadge>

<Toaster />
toast.success("Guardado correctamente");
```

### Navegacion

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@falabella-enablers-genai/ui";

<Tabs defaultValue="general">
  <TabsList variant="pills">
    <TabsTrigger variant="pills" value="general">General</TabsTrigger>
    <TabsTrigger variant="pills" value="security">Seguridad</TabsTrigger>
  </TabsList>
  <TabsContent value="general">Contenido general</TabsContent>
  <TabsContent value="security">Contenido seguridad</TabsContent>
</Tabs>
```

`TabsList` y `TabsTrigger` soportan `variant="pills" | "underline"`.

### DataTable

```tsx
import { Badge, DataTable } from "@falabella-enablers-genai/ui";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<User>[] = [
  { accessorKey: "name", header: "Nombre" },
  { accessorKey: "email", header: "Correo" },
  {
    accessorKey: "status",
    header: "Estado",
    cell: ({ row }) => (
      <Badge variant={row.original.status === "active" ? "success" : "muted"}>
        {row.original.status}
      </Badge>
    ),
  },
];

<DataTable columns={columns} data={users} filterKey="name" />;
```

### Charts

```tsx
import { BarChart } from "@falabella-enablers-genai/ui";

<BarChart
  data={[
    { name: "Ene", value: 12 },
    { name: "Feb", value: 18 },
  ]}
/>;
```

Para props completas, lee `COMPONENTS.md` y `packages/ui/src/components/{chart}.tsx`.

---

## Convenciones de Codigo

```tsx
import { cn } from "@falabella-enablers-genai/ui";

<div className={cn("bg-card text-card-foreground", className)} />;
```

- Usa `asChild` cuando un componente de accion debe renderizar un `<a>`.
- Usa `React.forwardRef` y `displayName` si creas wrappers locales.
- Usa utilities mapeadas por `styles.css`: `bg-card`, `text-foreground`, `border-border`, `shadow-xs`, `duration-fast`.
- No uses valores arbitrarios en UI si existe token o utility canonica.
