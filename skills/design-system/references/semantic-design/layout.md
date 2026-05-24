# layout.md - Layout, Datos y Charts 1:1

*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

> Fuentes canonicas: `ScrollArea`, `Collapsible`, `DataTable`, componentes de charts y tokens de breakpoint/spacing.

---

## Layout Base

El DS original no exporta un componente `Container` o `Grid`. Usa CSS/Tailwind con tokens canonicos.

```css
.ds-page {
  min-height: 100dvh;
  background-color: var(--color-bg-page);
  color: var(--color-text-primary);
  font-family: var(--type-body-base-font-family);
}

.ds-container {
  width: 100%;
  max-width: var(--breakpoint-xl);
  margin-inline: auto;
  padding-inline: var(--space-4);
}

@media (min-width: 768px) {
  .ds-container {
    padding-inline: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .ds-container {
    padding-inline: var(--space-8);
  }
}
```

Breakpoints canonicos: `--breakpoint-sm`, `--breakpoint-md`, `--breakpoint-lg`, `--breakpoint-xl`, `--breakpoint-2xl`.

---

## ScrollArea y Collapsible

```tsx
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
  ScrollArea,
} from "@forge-enablers-genai/ui";

<ScrollArea className="h-72">
  <div className="space-y-4">Contenido</div>
</ScrollArea>

<Collapsible>
  <CollapsibleTrigger>Ver detalles</CollapsibleTrigger>
  <CollapsibleContent>Contenido expandible</CollapsibleContent>
</Collapsible>
```

---

## DataTable

```tsx
import { DataTable } from "@forge-enablers-genai/ui";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<User>[] = [
  { accessorKey: "name", header: "Nombre" },
  { accessorKey: "email", header: "Correo" },
];

<DataTable columns={columns} data={users} filterKey="name" />;
```

`DataTable` usa `@tanstack/react-table` y depende de `ScrollArea` en el registry del CLI.

---

## Charts

Todos los charts dependen de `Chart` / `chart-core` y de temas ECharts generados desde tokens.

| Componente | Tipo |
|------------|------|
| `BarChart` | Barras verticales/horizontales |
| `LineChart` | Lineas multi-serie |
| `PieChart` | Pie/donut |
| `AreaChart` | Area/stacked area |
| `ScatterChart` | Scatter/bubble |
| `RadarChart` | Radar |
| `GaugeChart` | KPI gauge |
| `TreemapChart` | Jerarquia treemap |
| `HeatmapChart` | Heatmap |
| `FunnelChart` | Funnel |
| `WaterfallChart` | Waterfall |
| `SankeyChart` | Sankey |
| `SunburstChart` | Sunburst |
| `CandlestickChart` | OHLC |
| `BoxPlotChart` | Box plot |
| `ParallelChart` | Coordenadas paralelas |

```tsx
import { LineChart } from "@forge-enablers-genai/ui";

<LineChart
  data={[
    { name: "Ene", value: 12 },
    { name: "Feb", value: 18 },
  ]}
/>;
```

Tokens de charts: `--chart-palette-*`, `--chart-bg`, `--chart-text`, `--chart-axis-*`, `--chart-tooltip-*`, `--chart-legend-text`.

---

## CSS Puro Para Grids

```css
.ds-card-grid {
  display: grid;
  gap: var(--space-6);
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .ds-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .ds-card-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.ds-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.ds-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
```

---

## Reglas

1. Layouts son mobile-first; usa media queries con los breakpoints canonicos.
2. Para tablas interactivas usa `DataTable`; no dupliques sorting/filtering local si el componente cubre el caso.
3. Para visualizacion de datos usa los charts del DS antes de configurar ECharts a mano.
4. No crees tokens de layout locales; usa `--space-*`, `--breakpoint-*` y utilities Tailwind mapeadas.
