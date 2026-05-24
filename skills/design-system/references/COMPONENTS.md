# GenAI UI — Component Reference

*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

> Machine-readable component catalog for AI agents.
> Auto-generated from components.meta.json — do not edit manually.

---

## Summary

| Component | Status | Import |
|-----------|--------|--------|
| [Button](#button) | stable | `import { Button } from '@forge-enablers-genai/ui'` |
| [Badge](#badge) | stable | `import { Badge } from '@forge-enablers-genai/ui'` |
| [Heading](#heading) | stable | `import { Heading } from '@forge-enablers-genai/ui'` |
| [Surface](#surface) | stable | `import { Surface } from '@forge-enablers-genai/ui'` |
| [Card](#card) | stable | `import { Card } from '@forge-enablers-genai/ui'` |
| [Text](#text) | stable | `import { Text } from '@forge-enablers-genai/ui'` |
| [Input](#input) | stable | `import { Input } from '@forge-enablers-genai/ui'` |
| [Label](#label) | stable | `import { Label } from '@forge-enablers-genai/ui'` |
| [Checkbox](#checkbox) | stable | `import { Checkbox } from '@forge-enablers-genai/ui'` |
| [Switch](#switch) | stable | `import { Switch } from '@forge-enablers-genai/ui'` |
| [Select](#select) | stable | `import { Select } from '@forge-enablers-genai/ui'` |
| [Dialog](#dialog) | stable | `import { Dialog } from '@forge-enablers-genai/ui'` |
| [AlertDialog](#alert-dialog) | stable | `import { AlertDialog } from '@forge-enablers-genai/ui'` |
| [DropdownMenu](#dropdown-menu) | stable | `import { DropdownMenu } from '@forge-enablers-genai/ui'` |
| [Popover](#popover) | stable | `import { Popover } from '@forge-enablers-genai/ui'` |
| [Tooltip](#tooltip) | stable | `import { TooltipProvider } from '@forge-enablers-genai/ui'` |
| [Tabs](#tabs) | stable | `import { Tabs } from '@forge-enablers-genai/ui'` |
| [Avatar](#avatar) | stable | `import { Avatar } from '@forge-enablers-genai/ui'` |
| [ScrollArea](#scroll-area) | stable | `import { ScrollArea } from '@forge-enablers-genai/ui'` |
| [Collapsible](#collapsible) | stable | `import { Collapsible } from '@forge-enablers-genai/ui'` |
| [Toaster](#toast) | stable | `import { Toaster } from '@forge-enablers-genai/ui'` |
| [Command](#command) | stable | `import { Command } from '@forge-enablers-genai/ui'` |
| [DataTable](#data-table) | stable | `import { DataTable } from '@forge-enablers-genai/ui'` |
| [Sidebar](#sidebar) | stable | `import { SidebarProvider } from '@forge-enablers-genai/ui'` |
| [ChartCore](#chart-core) | stable | `import { Chart } from '@forge-enablers-genai/ui'` |
| [BarChart](#bar-chart) | stable | `import { BarChart } from '@forge-enablers-genai/ui'` |
| [LineChart](#line-chart) | stable | `import { LineChart } from '@forge-enablers-genai/ui'` |
| [PieChart](#pie-chart) | stable | `import { PieChart } from '@forge-enablers-genai/ui'` |
| [AreaChart](#area-chart) | stable | `import { AreaChart } from '@forge-enablers-genai/ui'` |
| [ScatterChart](#scatter-chart) | stable | `import { ScatterChart } from '@forge-enablers-genai/ui'` |
| [RadarChart](#radar-chart) | stable | `import { RadarChart } from '@forge-enablers-genai/ui'` |
| [GaugeChart](#gauge-chart) | stable | `import { GaugeChart } from '@forge-enablers-genai/ui'` |
| [TreemapChart](#treemap-chart) | stable | `import { TreemapChart } from '@forge-enablers-genai/ui'` |
| [HeatmapChart](#heatmap-chart) | stable | `import { HeatmapChart } from '@forge-enablers-genai/ui'` |
| [FunnelChart](#funnel-chart) | stable | `import { FunnelChart } from '@forge-enablers-genai/ui'` |
| [WaterfallChart](#waterfall-chart) | stable | `import { WaterfallChart } from '@forge-enablers-genai/ui'` |
| [SankeyChart](#sankey-chart) | stable | `import { SankeyChart } from '@forge-enablers-genai/ui'` |
| [SunburstChart](#sunburst-chart) | stable | `import { SunburstChart } from '@forge-enablers-genai/ui'` |
| [CandlestickChart](#candlestick-chart) | stable | `import { CandlestickChart } from '@forge-enablers-genai/ui'` |
| [BoxPlotChart](#boxplot-chart) | stable | `import { BoxPlotChart } from '@forge-enablers-genai/ui'` |
| [ParallelChart](#parallel-chart) | stable | `import { ParallelChart } from '@forge-enablers-genai/ui'` |
| [Logo](#logo) | stable | `import { Logo } from '@forge-enablers-genai/ui'` |
| [Status](#status) | stable | `import { StatusDot } from '@forge-enablers-genai/ui'` |

---

## Button

**Status:** `stable`

**Import:** `import { Button, buttonVariants } from '@forge-enablers-genai/ui'`

**Description:** Interactive button with primary, secondary, and danger variants.

**Exports:** `Button`, `buttonVariants`, `ButtonProps`

**Dependencies:** `@radix-ui/react-slot`

---

## Badge

**Status:** `stable`

**Import:** `import { Badge } from '@forge-enablers-genai/ui'`

**Description:** Compact status pill for short labels and metadata.

**Exports:** `Badge`, `badgeVariants`, `BadgeProps`

**Dependencies:** `@radix-ui/react-slot`

---

## Heading

**Status:** `stable`

**Import:** `import { Heading } from '@forge-enablers-genai/ui'`

**Description:** Typography primitive for semantic page and section headings.

**Exports:** `Heading`, `headingVariants`, `HeadingProps`

---

## Surface

**Status:** `stable`

**Import:** `import { Surface } from '@forge-enablers-genai/ui'`

**Description:** Composable surface primitive for cards, panels, and interactive containers.

**Exports:** `Surface`, `surfaceVariants`, `SurfaceProps`

**Dependencies:** `@radix-ui/react-slot`

---

## Card

**Status:** `stable`

**Import:** `import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@forge-enablers-genai/ui'`

**Description:** Structured card with header, content, and footer sections.

**Exports:** `Card`, `CardHeader`, `CardFooter`, `CardTitle`, `CardDescription`, `CardContent`

---

## Text

**Status:** `stable`

**Import:** `import { Text } from '@forge-enablers-genai/ui'`

**Description:** Body text primitive with semantic tones and sizes.

**Exports:** `Text`, `textVariants`, `TextProps`

---

## Input

**Status:** `stable`

**Import:** `import { Input, inputVariants } from '@forge-enablers-genai/ui'`

**Description:** Text input with validation states.

**Exports:** `Input`, `inputVariants`, `InputProps`

**Depends on:** label

---

## Label

**Status:** `stable`

**Import:** `import { Label } from '@forge-enablers-genai/ui'`

**Description:** Accessible form label.

**Exports:** `Label`, `LabelProps`

**Dependencies:** `@radix-ui/react-label`

---

## Checkbox

**Status:** `stable`

**Import:** `import { Checkbox, checkboxVariants } from '@forge-enablers-genai/ui'`

**Description:** Checkbox with checked, unchecked, and indeterminate states.

**Exports:** `Checkbox`, `checkboxVariants`, `CheckboxProps`

**Dependencies:** `@radix-ui/react-checkbox`, `lucide-react`

---

## Switch

**Status:** `stable`

**Import:** `import { Switch } from '@forge-enablers-genai/ui'`

**Description:** Toggle switch control.

**Exports:** `Switch`, `SwitchProps`

**Dependencies:** `@radix-ui/react-switch`

---

## Select

**Status:** `stable`

**Import:** `import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@forge-enablers-genai/ui'`

**Description:** Dropdown select with grouped options.

**Exports:** `Select`, `SelectGroup`, `SelectValue`, `SelectTrigger`, `SelectContent`, `SelectLabel`, `SelectItem`, `SelectSeparator`, `SelectScrollUpButton`, `SelectScrollDownButton`

**Dependencies:** `@radix-ui/react-select`, `lucide-react`

---

## Dialog

**Status:** `stable`

**Import:** `import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '@forge-enablers-genai/ui'`

**Description:** Modal dialog with overlay.

**Exports:** `Dialog`, `DialogTrigger`, `DialogPortal`, `DialogOverlay`, `DialogContent`, `DialogHeader`, `DialogFooter`, `DialogTitle`, `DialogDescription`, `DialogClose`, `DialogContentProps`

**Dependencies:** `@radix-ui/react-dialog`, `lucide-react`

---

## AlertDialog

**Status:** `stable`

**Import:** `import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogAction, AlertDialogCancel } from '@forge-enablers-genai/ui'`

**Description:** Confirmation dialog for destructive actions.

**Exports:** `AlertDialog`, `AlertDialogTrigger`, `AlertDialogPortal`, `AlertDialogOverlay`, `AlertDialogContent`, `AlertDialogHeader`, `AlertDialogFooter`, `AlertDialogTitle`, `AlertDialogDescription`, `AlertDialogAction`, `AlertDialogCancel`

**Dependencies:** `@radix-ui/react-alert-dialog`

**Depends on:** button

---

## DropdownMenu

**Status:** `stable`

**Import:** `import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@forge-enablers-genai/ui'`

**Description:** Dropdown menu with items, separators, and sub-menus.

**Exports:** `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuGroup`, `DropdownMenuPortal`, `DropdownMenuSub`, `DropdownMenuSubTrigger`, `DropdownMenuSubContent`, `DropdownMenuRadioGroup`, `DropdownMenuItem`, `DropdownMenuCheckboxItem`, `DropdownMenuRadioItem`, `DropdownMenuLabel`, `DropdownMenuSeparator`, `DropdownMenuShortcut`

**Dependencies:** `@radix-ui/react-dropdown-menu`, `lucide-react`

---

## Popover

**Status:** `stable`

**Import:** `import { Popover, PopoverTrigger, PopoverContent } from '@forge-enablers-genai/ui'`

**Description:** Floating popover panel.

**Exports:** `Popover`, `PopoverTrigger`, `PopoverContent`, `PopoverAnchor`

**Dependencies:** `@radix-ui/react-popover`

---

## Tooltip

**Status:** `stable`

**Import:** `import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from '@forge-enablers-genai/ui'`

**Description:** Hover tooltip for additional context.

**Exports:** `TooltipProvider`, `Tooltip`, `TooltipTrigger`, `TooltipContent`

**Dependencies:** `@radix-ui/react-tooltip`

---

## Tabs

**Status:** `stable`

**Import:** `import { Tabs, TabsList, TabsTrigger, TabsContent } from '@forge-enablers-genai/ui'`

**Description:** Tabbed navigation with underline and pills variants.

**Exports:** `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`, `TabsListProps`, `TabsTriggerProps`

**Dependencies:** `@radix-ui/react-tabs`

---

## Avatar

**Status:** `stable`

**Import:** `import { Avatar, AvatarImage, AvatarFallback } from '@forge-enablers-genai/ui'`

**Description:** User avatar with image and fallback.

**Exports:** `Avatar`, `AvatarImage`, `AvatarFallback`, `avatarVariants`, `AvatarProps`

**Dependencies:** `@radix-ui/react-avatar`

---

## ScrollArea

**Status:** `stable`

**Import:** `import { ScrollArea, ScrollBar } from '@forge-enablers-genai/ui'`

**Description:** Custom scrollbar container.

**Exports:** `ScrollArea`, `ScrollBar`, `ScrollBarThumb`

**Dependencies:** `@radix-ui/react-scroll-area`

---

## Collapsible

**Status:** `stable`

**Import:** `import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@forge-enablers-genai/ui'`

**Description:** Expandable/collapsible content section.

**Exports:** `Collapsible`, `CollapsibleTrigger`, `CollapsibleContent`

**Dependencies:** `@radix-ui/react-collapsible`

---

## Toaster

**Status:** `stable`

**Import:** `import { Toaster, toast } from '@forge-enablers-genai/ui'`

**Description:** Toast notification system.

**Exports:** `Toaster`, `toast`, `ToasterProps`

**Dependencies:** `sonner`

---

## Command

**Status:** `stable`

**Import:** `import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from '@forge-enablers-genai/ui'`

**Description:** Command palette with search.

**Exports:** `Command`, `CommandInput`, `CommandList`, `CommandEmpty`, `CommandGroup`, `CommandItem`, `CommandSeparator`, `CommandShortcut`, `CommandDialog`

**Dependencies:** `cmdk`, `lucide-react`

**Depends on:** dialog

---

## DataTable

**Status:** `stable`

**Import:** `import { DataTable } from '@forge-enablers-genai/ui'`

**Description:** Data table with sorting, filtering, and pagination.

**Exports:** `DataTable`, `DataTableProps`

**Dependencies:** `@tanstack/react-table`

**Depends on:** scroll-area

---

## Sidebar

**Status:** `stable`

**Import:** `import { SidebarProvider, Sidebar, SidebarHeader, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupLabel, SidebarGroupContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarTrigger } from '@forge-enablers-genai/ui'`

**Description:** Responsive sidebar with collapsible groups, keyboard shortcuts, and mobile support.

**Exports:** `SidebarProvider`, `Sidebar`, `SidebarTrigger`, `SidebarRail`, `SidebarHeader`, `SidebarFooter`, `SidebarContent`, `SidebarSeparator`, `SidebarGroup`, `SidebarGroupLabel`, `SidebarGroupContent`, `SidebarMenu`, `SidebarMenuItem`, `SidebarMenuButton`, `sidebarMenuButtonVariants`, `SidebarMenuSub`, `SidebarMenuSubItem`, `SidebarMenuSubButton`, `SidebarMenuBadge`, `useSidebar`, `SidebarProps`, `SidebarProviderProps`, `SidebarMenuButtonProps`

**Dependencies:** `@radix-ui/react-slot`, `lucide-react`

---

## ChartCore

**Status:** `stable`

**Import:** `import { Chart } from '@forge-enablers-genai/ui'`

**Description:** Shared ECharts infrastructure: module registration, theme binding, base Chart wrapper, and chart utilities. Required dependency for all individual chart components.

**Exports:** `Chart`, `useResolvedTheme`, `useChartPalette`, `lightenHex`, `chartTitle`, `ChartProps`

**Dependencies:** `echarts`, `echarts-for-react`

---

## BarChart

**Status:** `stable`

**Import:** `import { BarChart } from '@forge-enablers-genai/ui'`

**Description:** Bar chart with vertical and horizontal orientations.

**Exports:** `BarChart`, `BarChartProps`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## LineChart

**Status:** `stable`

**Import:** `import { LineChart } from '@forge-enablers-genai/ui'`

**Description:** Line chart with multi-series, smooth curves, and optional area fill.

**Exports:** `LineChart`, `LineChartProps`, `LineChartSeries`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## PieChart

**Status:** `stable`

**Import:** `import { PieChart } from '@forge-enablers-genai/ui'`

**Description:** Pie chart with optional donut mode.

**Exports:** `PieChart`, `PieChartProps`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## AreaChart

**Status:** `stable`

**Import:** `import { AreaChart } from '@forge-enablers-genai/ui'`

**Description:** Area chart with stacking and smooth curve support.

**Exports:** `AreaChart`, `AreaChartProps`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## ScatterChart

**Status:** `stable`

**Import:** `import { ScatterChart } from '@forge-enablers-genai/ui'`

**Description:** Scatter plot with multi-series and axis labels.

**Exports:** `ScatterChart`, `ScatterChartProps`, `ScatterChartSeriesData`, `ScatterChartDataPoint`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## RadarChart

**Status:** `stable`

**Import:** `import { RadarChart } from '@forge-enablers-genai/ui'`

**Description:** Radar/spider chart with multi-series overlay.

**Exports:** `RadarChart`, `RadarChartProps`, `RadarIndicator`, `RadarSeriesData`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## GaugeChart

**Status:** `stable`

**Import:** `import { GaugeChart } from '@forge-enablers-genai/ui'`

**Description:** Gauge chart for single-value KPI display.

**Exports:** `GaugeChart`, `GaugeChartProps`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## TreemapChart

**Status:** `stable`

**Import:** `import { TreemapChart } from '@forge-enablers-genai/ui'`

**Description:** Treemap chart for hierarchical data visualization.

**Exports:** `TreemapChart`, `TreemapChartProps`, `TreemapNode`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## HeatmapChart

**Status:** `stable`

**Import:** `import { HeatmapChart } from '@forge-enablers-genai/ui'`

**Description:** Heatmap chart with theme-aware gradient colors.

**Exports:** `HeatmapChart`, `HeatmapChartProps`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## FunnelChart

**Status:** `stable`

**Import:** `import { FunnelChart } from '@forge-enablers-genai/ui'`

**Description:** Funnel chart with ascending, descending, and none sort modes.

**Exports:** `FunnelChart`, `FunnelChartProps`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## WaterfallChart

**Status:** `stable`

**Import:** `import { WaterfallChart } from '@forge-enablers-genai/ui'`

**Description:** Waterfall chart with cumulative increase/decrease visualization.

**Exports:** `WaterfallChart`, `WaterfallChartProps`, `WaterfallChartItem`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## SankeyChart

**Status:** `stable`

**Import:** `import { SankeyChart } from '@forge-enablers-genai/ui'`

**Description:** Sankey diagram for flow and relationship visualization.

**Exports:** `SankeyChart`, `SankeyChartProps`, `SankeyNode`, `SankeyLink`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## SunburstChart

**Status:** `stable`

**Import:** `import { SunburstChart } from '@forge-enablers-genai/ui'`

**Description:** Sunburst chart for multi-level hierarchical data.

**Exports:** `SunburstChart`, `SunburstChartProps`, `SunburstNode`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## CandlestickChart

**Status:** `stable`

**Import:** `import { CandlestickChart } from '@forge-enablers-genai/ui'`

**Description:** Candlestick chart for financial OHLC data.

**Exports:** `CandlestickChart`, `CandlestickChartProps`, `CandlestickDataPoint`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## BoxPlotChart

**Status:** `stable`

**Import:** `import { BoxPlotChart } from '@forge-enablers-genai/ui'`

**Description:** Box plot chart for statistical distribution visualization.

**Exports:** `BoxPlotChart`, `BoxPlotChartProps`, `BoxPlotSeriesData`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## ParallelChart

**Status:** `stable`

**Import:** `import { ParallelChart } from '@forge-enablers-genai/ui'`

**Description:** Parallel coordinates chart for multi-dimensional data comparison.

**Exports:** `ParallelChart`, `ParallelChartProps`, `ParallelDimension`

**Dependencies:** `echarts`, `echarts-for-react`

**Depends on:** chart-core

---

## Logo

**Status:** `stable`

**Import:** `import { Logo } from '@forge-enablers-genai/ui'`

**Description:** Forge Tecnología official logo with full, mark, and text variants.

**Exports:** `Logo`, `LogoProps`

---

## Status

**Status:** `stable`

**Import:** `import { StatusDot, StatusBadge, StatusIndicator } from '@forge-enablers-genai/ui'`

**Description:** Status indicators: dot, badge pill, and inline dot+text variants for success, warning, error, info, and neutral states.

**Exports:** `StatusDot`, `StatusBadge`, `StatusIndicator`, `statusDotVariants`, `statusBadgeVariants`, `StatusDotProps`, `StatusBadgeProps`, `StatusIndicatorProps`

---
