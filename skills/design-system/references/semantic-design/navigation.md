# navigation.md - Navegacion 1:1

> Fuentes canonicas: `Tabs`, `DropdownMenu`, `Command`, `Sidebar`, `Avatar`, `ScrollArea` y `Collapsible`.

---

## Componentes

| Componente | Uso |
|------------|-----|
| `Tabs` | Navegacion entre secciones relacionadas |
| `DropdownMenu` | Menu de acciones o seleccion contextual |
| `Command` / `CommandDialog` | Paleta de comandos y busqueda |
| `Sidebar` | Navegacion lateral compleja |
| `Avatar` | Identidad de usuario |
| `ScrollArea` | Contenedores con scroll custom |
| `Collapsible` | Secciones expandibles |

No existe `Breadcrumb` como componente del DS original. Si hace falta, compone HTML semantico con tokens canonicos o propone RFC.

---

## Tabs

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@falabella-enablers-genai/ui";

<Tabs defaultValue="general">
  <TabsList variant="underline">
    <TabsTrigger variant="underline" value="general">General</TabsTrigger>
    <TabsTrigger variant="underline" value="security">Seguridad</TabsTrigger>
  </TabsList>
  <TabsContent value="general">Contenido general</TabsContent>
  <TabsContent value="security">Contenido seguridad</TabsContent>
</Tabs>
```

Variantes canonicas de `TabsList` y `TabsTrigger`: `pills`, `underline`.

---

## Dropdown Menu

```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@falabella-enablers-genai/ui";

<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost">Acciones</Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuItem>Editar</DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem className="text-error">Eliminar</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

---

## Command

```tsx
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@falabella-enablers-genai/ui";

<Command>
  <CommandInput placeholder="Buscar..." />
  <CommandList>
    <CommandEmpty>Sin resultados</CommandEmpty>
    <CommandGroup heading="Acciones">
      <CommandItem>Crear proyecto</CommandItem>
    </CommandGroup>
  </CommandList>
</Command>
```

---

## Sidebar

```tsx
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@falabella-enablers-genai/ui";

<SidebarProvider>
  <Sidebar>
    <SidebarContent>
      <SidebarGroup>
        <SidebarGroupLabel>Principal</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild isActive>
                <a href="/dashboard">Dashboard</a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
  </Sidebar>
  <SidebarTrigger />
</SidebarProvider>
```

---

## Avatar

```tsx
import { Avatar, AvatarFallback, AvatarImage } from "@falabella-enablers-genai/ui";

<Avatar size="md">
  <AvatarImage src="/user.png" alt="Usuario" />
  <AvatarFallback>US</AvatarFallback>
</Avatar>
```

Tamanos canonicos: `sm`, `md`, `lg`.

---

## Tokens y Utilities

| Uso | Canonico |
|-----|----------|
| Fondo nav/sidebar | `bg-sidebar`, `--color-bg-secondary` |
| Item activo | `bg-card`, `text-foreground`, `shadow-xs` |
| Hover | `bg-muted-subtle`, `text-foreground` |
| Indicador activo | `text-primary`, `--color-interactive-default` |
| Borde | `border-border`, `--color-border-default` |
| Focus | `focus-visible:ring-ring-soft`, `--shadow-focus` |

---

## Reglas

1. Navegacion actual usa `aria-current="page"` o prop equivalente (`isActive` en `SidebarMenuButton`).
2. Menus se implementan con Radix (`DropdownMenu`) o `Command`; no con `div` clicables.
3. Evita mezclar navegacion primaria y acciones destructivas en el mismo grupo visual.
4. Si necesitas breadcrumb reutilizable, documenta el gap y propone RFC.
