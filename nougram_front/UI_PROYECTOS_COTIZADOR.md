# Plan de Implementación: Frontend para Creación de Cotización Paso a Paso

**Fecha:** 2026-02-08  
**Base:** `PLAN_TRABAJO_COTIZACION_BACKEND.md` (Backend)  
**Arquitectura:** Next.js 14+ (App Router), React, TypeScript, Tailwind CSS, Framer Motion  
**Ubicación:** `frontend/src/`

---

## 🎯 Resumen Ejecutivo

Implementar el frontend del flujo de creación de cotización paso a paso con estilo Apple, integrando con los nuevos endpoints del backend:

- **Búsqueda de clientes:** Autocompletado inteligente con debounce
- **Resumen ejecutivo con IA:** Generación automática con loading states y manejo de errores
- **Flujo paso a paso:** Navegación fluida con animaciones Framer Motion
- **Diseño premium:** Glassmorphism, Bento Grid, animaciones spring
- **Cálculos en tiempo real:** Actualización automática de márgenes y totales

**Endpoints Backend a Integrar:**

1. ✅ `GET /api/v1/projects/clients/search` - Búsqueda de clientes
2. ✅ `POST /api/v1/ai/generate-executive-summary` - Resumen ejecutivo con IA
3. ✅ `POST /api/v1/projects/` - Crear proyecto (existente)
4. ✅ `POST /api/v1/quotes/calculate` - Calcular cotización (existente)
5. ✅ `GET /api/v1/services/` - Listar servicios (existente)

**Tecnologías:**

- Next.js 14+ (App Router)
- React 18+
- TypeScript
- Tailwind CSS
- Framer Motion
- TanStack Query (React Query)
- Zustand (para estado global del flujo)
- Shadcn/ui (componentes base)

---

## 📊 Análisis de Estado Actual

### Estructura Existente

#### 1. Página Actual de Creación (`frontend/src/app/(app)/projects/new/page.tsx`)

- **Estado:** Monolítico, todo en un solo componente
- **Problemas:**
  - No tiene flujo paso a paso
  - No tiene búsqueda de clientes
  - No tiene generación de resumen ejecutivo
  - UI básica sin animaciones
  - No sigue principios de diseño Apple

#### 2. Hooks Existentes (`frontend/src/lib/queries/`)

- ✅ `useGetServices()` - Listar servicios
- ✅ `useCreateProject()` - Crear proyecto
- ✅ `useCalculateQuote()` - Calcular cotización
- ❌ **Falta:** `useSearchClients()` - Búsqueda de clientes
- ❌ **Falta:** `useGenerateExecutiveSummary()` - Resumen ejecutivo

#### 3. Componentes UI Existentes (`frontend/src/components/ui/`)

- ✅ Componentes Shadcn/ui base (Button, Input, Card, etc.)
- ✅ Slider, Select, Textarea
- ❌ **Falta:** Componente de autocompletado (Combobox)
- ❌ **Falta:** Componente de Bento Grid
- ❌ **Falta:** Componente de contador numérico animado

---

## 📋 Componentes a Implementar

### 1. ✅ Hooks: Búsqueda de Clientes (`frontend/src/lib/queries/projects.ts`)

**Estado:** ⚠️ Necesita nuevo hook

**Hook Nuevo Requerido:**

```typescript
// Agregar al final de frontend/src/lib/queries/projects.ts

export interface ClientSearchResult {
  name: string;
  email?: string;
  project_count: number;
  last_project_date?: string;
}

export interface ClientSearchResponse {
  clients: ClientSearchResult[];
  total: number;
}

/**
 * Hook para búsqueda de clientes existentes
 * Usa debounce automático para evitar demasiadas requests
 */
export function useSearchClients(searchQuery: string, limit: number = 10) {
  return useQuery({
    queryKey: [...queryKeys.projects, 'clients', 'search', searchQuery, limit],
    queryFn: async (): Promise<ClientSearchResponse> => {
      if (!searchQuery || searchQuery.length < 2) {
        return { clients: [], total: 0 };
      }
      
      const response = await apiRequest<ClientSearchResponse>(
        `/projects/clients/search?q=${encodeURIComponent(searchQuery)}&limit=${limit}`
      );
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      return response.data!;
    },
    enabled: searchQuery.length >= 2, // Solo buscar si hay al menos 2 caracteres
    staleTime: 30 * 1000, // Cache por 30 segundos
    retry: false,
  });
}
```

**Nota:** Agregar `'clients'` a `queryKeys.projects` si es necesario para mejor organización.

---

### 2. ✅ Hooks: Generación de Resumen Ejecutivo (`frontend/src/lib/queries/ai.ts`)

**Estado:** ⚠️ Necesita nuevo hook

**Hook Nuevo Requerido:**

```typescript
// Agregar al final de frontend/src/lib/queries/ai.ts

export interface ExecutiveSummaryService {
  service_id: number;
  service_name: string;
  estimated_hours?: number;
  client_price: string; // Decimal as string
}

export interface ExecutiveSummaryRequest {
  project_name: string;
  client_name: string;
  client_sector?: string;
  services: ExecutiveSummaryService[];
  total_price: string; // Decimal as string
  currency: string;
  language?: 'es' | 'en';
}

export interface ExecutiveSummaryResponse {
  summary: string;
  provider: string;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
    estimated_cost?: number;
  };
}

/**
 * Hook para generar resumen ejecutivo con IA
 */
export function useGenerateExecutiveSummary() {
  return useMutation({
    mutationFn: async (request: ExecutiveSummaryRequest): Promise<ExecutiveSummaryResponse> => {
      const response = await apiRequest<ExecutiveSummaryResponse>('/ai/generate-executive-summary', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data!;
    },
    onError: (error) => {
      console.error('Error generating executive summary:', error);
    },
  });
}
```

**Nota:** Agregar `executiveSummary: () => ['ai', 'executive-summary']` a `queryKeys.ai` si se necesita cache.

---

### 3. ✅ Store Zustand: Estado del Flujo (`frontend/src/stores/quote-creation-store.ts`)

**Estado:** ⚠️ Archivo nuevo

**Store Nuevo Requerido:**

```typescript
// Crear archivo frontend/src/stores/quote-creation-store.ts

import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

export interface QuoteService {
  service_id: number;
  service_name: string;
  estimated_hours?: number;
  pricing_type?: 'hourly' | 'fixed' | 'recurring' | 'project_value';
  fixed_price?: number;
  quantity?: number;
  recurring_price?: number;
  billing_frequency?: string;
  project_value?: number;
  client_price?: number; // Calculado
  internal_cost?: number; // Calculado
  margin_percentage?: number; // Calculado
}

export interface QuoteCreationState {
  // Paso 1: Información del Proyecto
  currentStep: number;
  projectName: string;
  clientName: string;
  clientEmail: string;
  clientSector?: string;
  currency: string;
  selectedTaxIds: number[];
  
  // Paso 2: Selección de Servicios
  selectedServices: QuoteService[];
  
  // Paso 3: Configuración de Recursos
  resourceAllocations: Record<number, {
    hours?: number;
    quantity?: number;
    customPrice?: number;
  }>;
  
  // Paso 4: Resumen y Ajustes
  executiveSummary?: string;
  executiveSummaryLoading: boolean;
  executiveSummaryError?: string;
  notes: string;
  targetMargin: number;
  
  // Cálculos
  calculatedQuote?: {
    total_internal_cost: number;
    total_client_price: number;
    margin_percentage: number;
    items: Array<{
      service_id: number;
      service_name: string;
      internal_cost: number;
      client_price: number;
      margin_percentage: number;
    }>;
  };
  
  // Actions
  setCurrentStep: (step: number) => void;
  setProjectName: (name: string) => void;
  setClientName: (name: string) => void;
  setClientEmail: (email: string) => void;
  setClientSector: (sector: string) => void;
  setCurrency: (currency: string) => void;
  setSelectedTaxIds: (ids: number[]) => void;
  addService: (service: QuoteService) => void;
  removeService: (serviceId: number) => void;
  updateService: (serviceId: number, updates: Partial<QuoteService>) => void;
  setResourceAllocation: (serviceId: number, allocation: QuoteService['resourceAllocations']) => void;
  setExecutiveSummary: (summary: string) => void;
  setExecutiveSummaryLoading: (loading: boolean) => void;
  setExecutiveSummaryError: (error?: string) => void;
  setNotes: (notes: string) => void;
  setTargetMargin: (margin: number) => void;
  setCalculatedQuote: (quote: QuoteCreationState['calculatedQuote']) => void;
  reset: () => void;
}

const initialState: Omit<QuoteCreationState, keyof {
  setCurrentStep: never;
  setProjectName: never;
  setClientName: never;
  setClientEmail: never;
  setClientSector: never;
  setCurrency: never;
  setSelectedTaxIds: never;
  addService: never;
  removeService: never;
  updateService: never;
  setResourceAllocation: never;
  setExecutiveSummary: never;
  setExecutiveSummaryLoading: never;
  setExecutiveSummaryError: never;
  setNotes: never;
  setTargetMargin: never;
  setCalculatedQuote: never;
  reset: never;
}> = {
  currentStep: 1,
  projectName: '',
  clientName: '',
  clientEmail: '',
  clientSector: undefined,
  currency: 'USD',
  selectedTaxIds: [],
  selectedServices: [],
  resourceAllocations: {},
  executiveSummary: undefined,
  executiveSummaryLoading: false,
  executiveSummaryError: undefined,
  notes: '',
  targetMargin: 0.40, // 40%
  calculatedQuote: undefined,
};

export const useQuoteCreationStore = create<QuoteCreationState>()(
  immer((set) => ({
    ...initialState,
    
    setCurrentStep: (step) => set({ currentStep: step }),
    
    setProjectName: (name) => set({ projectName: name }),
    setClientName: (name) => set({ clientName: name }),
    setClientEmail: (email) => set({ clientEmail: email }),
    setClientSector: (sector) => set({ clientSector: sector }),
    setCurrency: (currency) => set({ currency }),
    setSelectedTaxIds: (ids) => set({ selectedTaxIds: ids }),
    
    addService: (service) => set((state) => {
      if (!state.selectedServices.find(s => s.service_id === service.service_id)) {
        state.selectedServices.push(service);
      }
    }),
    
    removeService: (serviceId) => set((state) => {
      state.selectedServices = state.selectedServices.filter(s => s.service_id !== serviceId);
      delete state.resourceAllocations[serviceId];
    }),
    
    updateService: (serviceId, updates) => set((state) => {
      const service = state.selectedServices.find(s => s.service_id === serviceId);
      if (service) {
        Object.assign(service, updates);
      }
    }),
    
    setResourceAllocation: (serviceId, allocation) => set((state) => {
      state.resourceAllocations[serviceId] = allocation;
    }),
    
    setExecutiveSummary: (summary) => set({ executiveSummary: summary }),
    setExecutiveSummaryLoading: (loading) => set({ executiveSummaryLoading: loading }),
    setExecutiveSummaryError: (error) => set({ executiveSummaryError: error }),
    setNotes: (notes) => set({ notes }),
    setTargetMargin: (margin) => set({ targetMargin: margin }),
    setCalculatedQuote: (quote) => set({ calculatedQuote: quote }),
    
    reset: () => set(initialState),
  }))
);
```

**Nota:** Instalar `zustand` y `immer` si no están instalados:

```bash
npm install zustand immer
```

---

### 4. ✅ Hook Personalizado: Calculadora de Cotización (`frontend/src/hooks/useQuotationCalculator.ts`)

**Estado:** ⚠️ Archivo nuevo

**Hook Nuevo Requerido:**

```typescript
// Crear archivo frontend/src/hooks/useQuotationCalculator.ts

import { useEffect, useCallback } from 'react';
import { useCalculateQuote } from '@/lib/queries';
import { useQuoteCreationStore } from '@/stores/quote-creation-store';

/**
 * Hook personalizado para calcular cotización en tiempo real
 * Maneja debounce y actualización automática del store
 */
export function useQuotationCalculator() {
  const {
    selectedServices,
    resourceAllocations,
    selectedTaxIds,
    targetMargin,
    setCalculatedQuote,
  } = useQuoteCreationStore();
  
  const calculateQuoteMutation = useCalculateQuote();
  
  const calculateQuote = useCallback(async () => {
    if (selectedServices.length === 0) {
      setCalculatedQuote(undefined);
      return;
    }
    
    // Construir items para el cálculo
    const items = selectedServices.map(service => {
      const allocation = resourceAllocations[service.service_id] || {};
      
      return {
        service_id: service.service_id,
        estimated_hours: allocation.hours || service.estimated_hours,
        pricing_type: service.pricing_type,
        fixed_price: service.fixed_price || allocation.customPrice,
        quantity: allocation.quantity || service.quantity || 1,
        recurring_price: service.recurring_price,
        billing_frequency: service.billing_frequency,
        project_value: service.project_value,
      };
    });
    
    try {
      const result = await calculateQuoteMutation.mutateAsync({
        items,
        tax_ids: selectedTaxIds,
        target_margin_percentage: targetMargin,
      });
      
      setCalculatedQuote(result as any);
    } catch (error) {
      console.error('Error calculating quote:', error);
      setCalculatedQuote(undefined);
    }
  }, [selectedServices, resourceAllocations, selectedTaxIds, targetMargin, calculateQuoteMutation, setCalculatedQuote]);
  
  // Auto-calcular cuando cambien los datos relevantes
  useEffect(() => {
    const timer = setTimeout(() => {
      calculateQuote();
    }, 500); // Debounce de 500ms
    
    return () => clearTimeout(timer);
  }, [calculateQuote]);
  
  return {
    calculateQuote,
    isCalculating: calculateQuoteMutation.isPending,
  };
}
```

---

### 5. ✅ Componente: Autocompletado de Clientes (`frontend/src/components/quotes/client-autocomplete.tsx`)

**Estado:** ⚠️ Componente nuevo

**Componente Nuevo Requerido:**

```typescript
// Crear archivo frontend/src/components/quotes/client-autocomplete.tsx

"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchClients } from "@/lib/queries/projects"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Check, Loader2, Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"

interface ClientAutocompleteProps {
  value: string
  onChange: (value: string) => void
  onSelect?: (client: { name: string; email?: string }) => void
  className?: string
  placeholder?: string
}

export function ClientAutocomplete({
  value,
  onChange,
  onSelect,
  className,
  placeholder = "Buscar cliente..."
}: ClientAutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [debouncedQuery, setDebouncedQuery] = useState(value)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  
  // Debounce del query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(value)
    }, 300)
    
    return () => clearTimeout(timer)
  }, [value])
  
  // Buscar clientes
  const { data, isLoading } = useSearchClients(debouncedQuery, 10)
  
  // Cerrar al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  const handleSelect = (client: { name: string; email?: string }) => {
    onChange(client.name)
    onSelect?.(client)
    setIsOpen(false)
  }
  
  const showResults = isOpen && debouncedQuery.length >= 2 && (data?.clients.length || 0) > 0
  
  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          ref={inputRef}
          value={value}
          onChange={(e) => {
            onChange(e.target.value)
            setIsOpen(true)
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="pl-9"
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
        )}
      </div>
      
      <AnimatePresence>
        {showResults && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute z-50 w-full mt-2 bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg border border-white/20 overflow-hidden"
          >
            <div className="max-h-60 overflow-y-auto">
              {data?.clients.map((client, index) => (
                <motion.button
                  key={`${client.name}-${index}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => handleSelect(client)}
                  className="w-full px-4 py-3 text-left hover:bg-white/50 transition-colors flex items-center justify-between group"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm text-gray-900 truncate">
                      {client.name}
                    </p>
                    {client.email && (
                      <p className="text-xs text-muted-foreground truncate mt-0.5">
                        {client.email}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      {client.project_count} proyecto{client.project_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <Check className="h-4 w-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
```

---

### 6. ✅ Componente: Bento Grid de Servicios (`frontend/src/components/quotes/service-bento-grid.tsx`)

**Estado:** ⚠️ Componente nuevo

**Componente Nuevo Requerido:**

```typescript
// Crear archivo frontend/src/components/quotes/service-bento-grid.tsx

"use client"

import { motion } from "framer-motion"
import { Check, Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { useQuoteCreationStore } from "@/stores/quote-creation-store"

interface Service {
  id: number
  name: string
  description?: string
  pricing_type?: 'hourly' | 'fixed' | 'recurring' | 'project_value'
  default_margin_target: number
}

interface ServiceBentoGridProps {
  services: Service[]
  onServiceSelect?: (service: Service) => void
  className?: string
}

export function ServiceBentoGrid({ services, onServiceSelect, className }: ServiceBentoGridProps) {
  const { selectedServices, addService, removeService } = useQuoteCreationStore()
  
  const handleToggle = (service: Service) => {
    const isSelected = selectedServices.some(s => s.service_id === service.id)
    
    if (isSelected) {
      removeService(service.id)
    } else {
      addService({
        service_id: service.id,
        service_name: service.name,
        pricing_type: service.pricing_type || 'hourly',
      })
    }
    
    onServiceSelect?.(service)
  }
  
  // Layout Bento Grid (configurable)
  const gridLayout = [
    { colSpan: 2, rowSpan: 1 }, // Grande
    { colSpan: 1, rowSpan: 1 }, // Pequeño
    { colSpan: 1, rowSpan: 1 }, // Pequeño
    { colSpan: 1, rowSpan: 2 }, // Alto
    { colSpan: 2, rowSpan: 1 }, // Grande
    { colSpan: 1, rowSpan: 1 }, // Pequeño
  ]
  
  return (
    <div className={cn("grid grid-cols-3 gap-4", className)}>
      {services.slice(0, 6).map((service, index) => {
        const isSelected = selectedServices.some(s => s.service_id === service.id)
        const layout = gridLayout[index % gridLayout.length]
        
        return (
          <motion.button
            key={service.id}
            layout
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            onClick={() => handleToggle(service)}
            className={cn(
              "relative group bg-white/70 backdrop-blur-xl rounded-3xl p-6",
              "border-2 transition-all duration-300",
              "hover:shadow-xl hover:border-primary/50",
              isSelected 
                ? "border-primary bg-primary/5 shadow-lg" 
                : "border-white/20 hover:border-white/40",
              layout.colSpan === 2 && "col-span-2",
              layout.rowSpan === 2 && "row-span-2"
            )}
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-semibold text-lg text-gray-900 group-hover:text-primary transition-colors">
                {service.name}
              </h3>
              <motion.div
                animate={{ scale: isSelected ? 1 : 0 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center",
                  isSelected ? "bg-primary text-white" : "bg-gray-200"
                )}
              >
                {isSelected ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Plus className="h-4 w-4 text-gray-400" />
                )}
              </motion.div>
            </div>
            
            {service.description && (
              <p className="text-sm text-muted-foreground line-clamp-3">
                {service.description}
              </p>
            )}
            
            {/* Overlay hover effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/0 to-primary/0 group-hover:from-primary/5 group-hover:to-transparent rounded-3xl transition-all duration-300" />
          </motion.button>
        )
      })}
    </div>
  )
}
```

---

### 7. ✅ Componente: Contador Numérico Animado (`frontend/src/components/common/animated-counter.tsx`)

**Estado:** ⚠️ Componente nuevo

**Componente Nuevo Requerido:**

```typescript
// Crear archivo frontend/src/components/common/animated-counter.tsx

"use client"

import { useEffect, useRef } from "react"
import { motion, useSpring, useTransform } from "framer-motion"
import { formatCurrency } from "@/lib/currency"

interface AnimatedCounterProps {
  value: number
  currency?: string
  className?: string
  duration?: number
}

export function AnimatedCounter({ 
  value, 
  currency = "USD", 
  className,
  duration = 1 
}: AnimatedCounterProps) {
  const spring = useSpring(0, { stiffness: 100, damping: 30 })
  const display = useTransform(spring, (current) => 
    Math.round(current)
  )
  
  useEffect(() => {
    spring.set(value)
  }, [spring, value])
  
  return (
    <motion.span className={className}>
      {formatCurrency(display.get(), currency)}
    </motion.span>
  )
}
```

**Nota:** Este componente necesita mejoras para manejar números decimales y animaciones más suaves. Se puede mejorar después.

---

### 8. ✅ Componente: Indicador de Margen con Color (`frontend/src/components/quotes/margin-indicator.tsx`)

**Estado:** ⚠️ Componente nuevo

**Componente Nuevo Requerido:**

```typescript
// Crear archivo frontend/src/components/quotes/margin-indicator.tsx

"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { AnimatedCounter } from "@/components/common/animated-counter"

interface MarginIndicatorProps {
  margin: number // 0-1 (ej: 0.40 = 40%)
  currency?: string
  className?: string
}

export function MarginIndicator({ margin, currency = "USD", className }: MarginIndicatorProps) {
  const percentage = margin * 100
  const colorClass = 
    percentage >= 40 ? "text-blue-600" :
    percentage >= 25 ? "text-amber-600" :
    "text-red-600"
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className={cn("flex items-center gap-2", className)}
    >
      <span className={cn("text-2xl font-bold", colorClass)}>
        {percentage.toFixed(1)}%
      </span>
      <div className="h-2 w-24 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, type: "spring" }}
          className={cn(
            "h-full rounded-full",
            percentage >= 40 ? "bg-blue-500" :
            percentage >= 25 ? "bg-amber-500" :
            "bg-red-500"
          )}
        />
      </div>
    </motion.div>
  )
}
```

---

### 9. ✅ Componente: Slider de Recursos (`frontend/src/components/quotes/resource-slider.tsx`)

**Estado:** ⚠️ Componente nuevo

**Componente Nuevo Requerido:**

```typescript
// Crear archivo frontend/src/components/quotes/resource-slider.tsx

"use client"

import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { motion } from "framer-motion"
import { useQuoteCreationStore } from "@/stores/quote-creation-store"

interface ResourceSliderProps {
  serviceId: number
  serviceName: string
  min?: number
  max?: number
  step?: number
  unit?: string
  className?: string
}

export function ResourceSlider({
  serviceId,
  serviceName,
  min = 0,
  max = 200,
  step = 1,
  unit = "horas",
  className
}: ResourceSliderProps) {
  const { resourceAllocations, setResourceAllocation } = useQuoteCreationStore()
  
  const allocation = resourceAllocations[serviceId] || {}
  const value = allocation.hours || 0
  
  const handleChange = (newValue: number[]) => {
    setResourceAllocation(serviceId, { ...allocation, hours: newValue[0] })
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={className}
    >
      <div className="flex items-center justify-between mb-2">
        <Label className="text-sm font-medium">{serviceName}</Label>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            value={value}
            onChange={(e) => {
              const numValue = Math.max(min, Math.min(max, Number(e.target.value)))
              handleChange([numValue])
            }}
            className="w-20 h-8 text-sm"
            min={min}
            max={max}
            step={step}
          />
          <span className="text-xs text-muted-foreground">{unit}</span>
        </div>
      </div>
      <Slider
        value={[value]}
        onValueChange={handleChange}
        min={min}
        max={max}
        step={step}
        className="w-full"
      />
    </motion.div>
  )
}
```

---

### 10. ✅ Página Principal: Flujo Paso a Paso (`frontend/src/app/(app)/projects/new-stepped/page.tsx`)

**Estado:** ⚠️ Archivo nuevo (nueva ruta)

**Estructura del Componente Principal:**

```typescript
// Crear archivo frontend/src/app/(app)/projects/new-stepped/page.tsx

"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { useQuoteCreationStore } from "@/stores/quote-creation-store"
import { useQuotationCalculator } from "@/hooks/useQuotationCalculator"
import { useGetServices } from "@/lib/queries"
import { useCreateProject } from "@/lib/queries/projects"
import { useGenerateExecutiveSummary } from "@/lib/queries/ai"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react"

// Importar componentes de pasos
import { Step1ProjectInfo } from "@/components/quotes/steps/step1-project-info"
import { Step2ServiceSelection } from "@/components/quotes/steps/step2-service-selection"
import { Step3ResourceConfiguration } from "@/components/quotes/steps/step3-resource-configuration"
import { Step4Summary } from "@/components/quotes/steps/step4-summary"

const STEPS = [
  { id: 1, title: "Información del Proyecto", component: Step1ProjectInfo },
  { id: 2, title: "Selección de Servicios", component: Step2ServiceSelection },
  { id: 3, title: "Configuración de Recursos", component: Step3ResourceConfiguration },
  { id: 4, title: "Resumen y Ajustes", component: Step4Summary },
]

export default function NewQuoteSteppedPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { currentStep, reset } = useQuoteCreationStore()
  const { data: servicesData } = useGetServices()
  const createProjectMutation = useCreateProject()
  const generateSummaryMutation = useGenerateExecutiveSummary()
  
  useQuotationCalculator() // Auto-calcular cotización
  
  const services = servicesData?.items || []
  
  const handleNext = () => {
    // Validaciones por paso
    // ...
    useQuoteCreationStore.getState().setCurrentStep(currentStep + 1)
  }
  
  const handleBack = () => {
    useQuoteCreationStore.getState().setCurrentStep(currentStep - 1)
  }
  
  const handleSubmit = async () => {
    // Crear proyecto con cotización
    // ...
  }
  
  const CurrentStepComponent = STEPS[currentStep - 1]?.component
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header con progreso */}
      <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-xl border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          {/* Progress bar */}
          <div className="flex items-center justify-between mb-4">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                {/* Step indicator */}
                <div className="flex flex-col items-center flex-1">
                  <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all",
                    currentStep > step.id ? "bg-primary text-white" :
                    currentStep === step.id ? "bg-primary text-white ring-4 ring-primary/20" :
                    "bg-gray-200 text-gray-500"
                  )}>
                    {currentStep > step.id ? "✓" : step.id}
                  </div>
                  <span className="text-xs mt-2 text-center text-gray-600">
                    {step.title}
                  </span>
                </div>
                {index < STEPS.length - 1 && (
                  <div className={cn(
                    "h-1 flex-1 mx-2 transition-all",
                    currentStep > step.id ? "bg-primary" : "bg-gray-200"
                  )} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Contenido principal */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            {CurrentStepComponent && <CurrentStepComponent />}
          </motion.div>
        </AnimatePresence>
        
        {/* Navegación */}
        <div className="flex items-center justify-between mt-8">
          <Button
            variant="ghost"
            onClick={handleBack}
            disabled={currentStep === 1}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Anterior
          </Button>
          
          {currentStep < STEPS.length ? (
            <Button onClick={handleNext}>
              Siguiente
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleSubmit} disabled={createProjectMutation.isPending}>
              {createProjectMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creando...
                </>
              ) : (
                "Crear Cotización"
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
```

---

### 11. ✅ Componentes de Pasos Individuales

#### 11.1. Paso 1: Información del Proyecto (`frontend/src/components/quotes/steps/step1-project-info.tsx`)

```typescript
// Crear archivo frontend/src/components/quotes/steps/step1-project-info.tsx

"use client"

import { useQuoteCreationStore } from "@/stores/quote-creation-store"
import { ClientAutocomplete } from "@/components/quotes/client-autocomplete"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"

export function Step1ProjectInfo() {
  const {
    projectName,
    clientName,
    clientEmail,
    clientSector,
    currency,
    setProjectName,
    setClientName,
    setClientEmail,
    setClientSector,
    setCurrency,
  } = useQuoteCreationStore()
  
  return (
    <Card className="bg-white/70 backdrop-blur-xl border-white/20 rounded-3xl p-8 shadow-xl">
      <h2 className="text-2xl font-bold mb-6">Información del Proyecto</h2>
      
      <div className="space-y-6">
        <div>
          <Label>Nombre del Proyecto</Label>
          <Input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Ej: Rediseño de E-commerce"
            className="mt-2"
          />
        </div>
        
        <div>
          <Label>Cliente</Label>
          <ClientAutocomplete
            value={clientName}
            onChange={setClientName}
            onSelect={(client) => {
              setClientName(client.name)
              if (client.email) setClientEmail(client.email)
            }}
            className="mt-2"
          />
        </div>
        
        <div>
          <Label>Email del Cliente (Opcional)</Label>
          <Input
            type="email"
            value={clientEmail}
            onChange={(e) => setClientEmail(e.target.value)}
            placeholder="cliente@empresa.com"
            className="mt-2"
          />
        </div>
        
        <div>
          <Label>Sector del Cliente (Opcional)</Label>
          <Input
            value={clientSector || ""}
            onChange={(e) => setClientSector(e.target.value)}
            placeholder="Ej: Tecnología, Retail, Healthcare"
            className="mt-2"
          />
        </div>
      </div>
    </Card>
  )
}
```

#### 11.2. Paso 2: Selección de Servicios (`frontend/src/components/quotes/steps/step2-service-selection.tsx`)

```typescript
// Crear archivo frontend/src/components/quotes/steps/step2-service-selection.tsx

"use client"

import { useGetServices } from "@/lib/queries"
import { ServiceBentoGrid } from "@/components/quotes/service-bento-grid"
import { Card } from "@/components/ui/card"

export function Step2ServiceSelection() {
  const { data: servicesData } = useGetServices()
  const services = servicesData?.items || []
  
  return (
    <Card className="bg-white/70 backdrop-blur-xl border-white/20 rounded-3xl p-8 shadow-xl">
      <h2 className="text-2xl font-bold mb-6">Selecciona los Servicios</h2>
      <p className="text-muted-foreground mb-8">
        Elige los servicios que incluirás en esta cotización
      </p>
      
      <ServiceBentoGrid services={services} />
    </Card>
  )
}
```

#### 11.3. Paso 3: Configuración de Recursos (`frontend/src/components/quotes/steps/step3-resource-configuration.tsx`)

```typescript
// Crear archivo frontend/src/components/quotes/steps/step3-resource-configuration.tsx

"use client"

import { useQuoteCreationStore } from "@/stores/quote-creation-store"
import { ResourceSlider } from "@/components/quotes/resource-slider"
import { Card } from "@/components/ui/card"

export function Step3ResourceConfiguration() {
  const { selectedServices } = useQuoteCreationStore()
  
  return (
    <Card className="bg-white/70 backdrop-blur-xl border-white/20 rounded-3xl p-8 shadow-xl">
      <h2 className="text-2xl font-bold mb-6">Configuración de Recursos</h2>
      <p className="text-muted-foreground mb-8">
        Ajusta las horas estimadas para cada servicio
      </p>
      
      <div className="space-y-6">
        {selectedServices.map((service) => (
          <ResourceSlider
            key={service.service_id}
            serviceId={service.service_id}
            serviceName={service.service_name}
            min={0}
            max={200}
            step={1}
            unit="horas"
          />
        ))}
      </div>
    </Card>
  )
}
```

#### 11.4. Paso 4: Resumen y Ajustes (`frontend/src/components/quotes/steps/step4-summary.tsx`)

```typescript
// Crear archivo frontend/src/components/quotes/steps/step4-summary.tsx

"use client"

import { useEffect } from "react"
import { useQuoteCreationStore } from "@/stores/quote-creation-store"
import { useGenerateExecutiveSummary } from "@/lib/queries/ai"
import { MarginIndicator } from "@/components/quotes/margin-indicator"
import { AnimatedCounter } from "@/components/common/animated-counter"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Loader2, Sparkles } from "lucide-react"

export function Step4Summary() {
  const {
    projectName,
    clientName,
    clientSector,
    selectedServices,
    calculatedQuote,
    executiveSummary,
    executiveSummaryLoading,
    executiveSummaryError,
    notes,
    currency,
    setExecutiveSummary,
    setExecutiveSummaryLoading,
    setExecutiveSummaryError,
    setNotes,
  } = useQuoteCreationStore()
  
  const generateSummaryMutation = useGenerateExecutiveSummary()
  
  // Generar resumen ejecutivo automáticamente
  useEffect(() => {
    if (calculatedQuote && selectedServices.length > 0 && !executiveSummary && !executiveSummaryLoading) {
      handleGenerateSummary()
    }
  }, [calculatedQuote, selectedServices])
  
  const handleGenerateSummary = async () => {
    setExecutiveSummaryLoading(true)
    setExecutiveSummaryError(undefined)
    
    try {
      const result = await generateSummaryMutation.mutateAsync({
        project_name: projectName,
        client_name: clientName,
        client_sector: clientSector,
        services: selectedServices.map(s => ({
          service_id: s.service_id,
          service_name: s.service_name,
          estimated_hours: s.estimated_hours,
          client_price: calculatedQuote?.items.find(i => i.service_id === s.service_id)?.client_price.toString() || "0",
        })),
        total_price: calculatedQuote?.total_client_price.toString() || "0",
        currency,
        language: "es",
      })
      
      setExecutiveSummary(result.summary)
    } catch (error) {
      setExecutiveSummaryError("Error al generar resumen ejecutivo")
      console.error(error)
    } finally {
      setExecutiveSummaryLoading(false)
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Resumen financiero */}
      <Card className="bg-white/70 backdrop-blur-xl border-white/20 rounded-3xl p-8 shadow-xl">
        <h2 className="text-2xl font-bold mb-6">Resumen Financiero</h2>
        
        <div className="grid grid-cols-3 gap-6">
          <div>
            <Label className="text-muted-foreground">Costo Interno</Label>
            <AnimatedCounter
              value={calculatedQuote?.total_internal_cost || 0}
              currency={currency}
              className="text-2xl font-bold mt-2 block"
            />
          </div>
          
          <div>
            <Label className="text-muted-foreground">Precio Cliente</Label>
            <AnimatedCounter
              value={calculatedQuote?.total_client_price || 0}
              currency={currency}
              className="text-2xl font-bold mt-2 block"
            />
          </div>
          
          <div>
            <Label className="text-muted-foreground">Margen</Label>
            <MarginIndicator
              margin={(calculatedQuote?.margin_percentage || 0) / 100}
              currency={currency}
              className="mt-2"
            />
          </div>
        </div>
      </Card>
      
      {/* Resumen ejecutivo */}
      <Card className="bg-white/70 backdrop-blur-xl border-white/20 rounded-3xl p-8 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Resumen Ejecutivo</h2>
          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateSummary}
            disabled={executiveSummaryLoading}
          >
            {executiveSummaryLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generando...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Regenerar
              </>
            )}
          </Button>
        </div>
        
        {executiveSummaryLoading && !executiveSummary && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}
        
        {executiveSummaryError && (
          <div className="text-sm text-red-600 mb-4">{executiveSummaryError}</div>
        )}
        
        {executiveSummary && (
          <Textarea
            value={executiveSummary}
            onChange={(e) => setExecutiveSummary(e.target.value)}
            className="min-h-[200px] bg-white/50"
            placeholder="El resumen ejecutivo aparecerá aquí..."
          />
        )}
      </Card>
      
      {/* Notas adicionales */}
      <Card className="bg-white/70 backdrop-blur-xl border-white/20 rounded-3xl p-8 shadow-xl">
        <Label>Notas Adicionales (Opcional)</Label>
        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Agrega notas adicionales para esta cotización..."
          className="mt-2 min-h-[100px] bg-white/50"
        />
      </Card>
    </div>
  )
}
```

---

## 🧪 Testing

### Tests Unitarios Recomendados

1. **Hooks:**
   - `useSearchClients` - Debounce y cache
   - `useGenerateExecutiveSummary` - Manejo de errores
   - `useQuotationCalculator` - Cálculo automático

2. **Componentes:**
   - `ClientAutocomplete` - Búsqueda y selección
   - `ServiceBentoGrid` - Selección de servicios
   - `MarginIndicator` - Colores según margen
   - `ResourceSlider` - Actualización de valores

3. **Store:**
   - `useQuoteCreationStore` - Estado y acciones

---

## 📝 Plan de Implementación por Fases

### **Fase 1: Hooks y Store (Día 1)**

1. ✅ Implementar `useSearchClients` en `queries/projects.ts`
2. ✅ Implementar `useGenerateExecutiveSummary` en `queries/ai.ts`
3. ✅ Crear `quote-creation-store.ts` con Zustand
4. ✅ Crear `useQuotationCalculator.ts`
5. ✅ Tests unitarios básicos

### **Fase 2: Componentes Base (Día 2)**

1. ✅ Crear `ClientAutocomplete`
2. ✅ Crear `ServiceBentoGrid`
3. ✅ Crear `AnimatedCounter`
4. ✅ Crear `MarginIndicator`
5. ✅ Crear `ResourceSlider`
6. ✅ Tests de componentes

### **Fase 3: Componentes de Pasos (Día 3)**

1. ✅ Crear `Step1ProjectInfo`
2. ✅ Crear `Step2ServiceSelection`
3. ✅ Crear `Step3ResourceConfiguration`
4. ✅ Crear `Step4Summary`
5. ✅ Integración entre pasos

### **Fase 4: Página Principal y Navegación (Día 4)**

1. ✅ Crear `new-stepped/page.tsx`
2. ✅ Implementar navegación entre pasos
3. ✅ Implementar validaciones
4. ✅ Implementar submit final
5. ✅ Integración completa

### **Fase 5: Polish y Optimización (Día 5)**

1. ✅ Ajustar animaciones Framer Motion
2. ✅ Optimizar rendimiento (memo, useMemo)
3. ✅ Mejorar UX (loading states, errores)
4. ✅ Testing end-to-end
5. ✅ Code review

---

## ✅ Checklist de Implementación

### Hooks y Store

- [ ] `useSearchClients` implementado con debounce
- [ ] `useGenerateExecutiveSummary` implementado
- [ ] `useQuoteCreationStore` creado con Zustand
- [ ] `useQuotationCalculator` implementado
- [ ] Tests unitarios pasando

### Componentes Base

- [ ] `ClientAutocomplete` con animaciones
- [ ] `ServiceBentoGrid` con Bento Grid layout
- [ ] `AnimatedCounter` con animación suave
- [ ] `MarginIndicator` con colores dinámicos
- [ ] `ResourceSlider` funcional
- [ ] Tests de componentes pasando

### Componentes de Pasos

- [ ] `Step1ProjectInfo` completo
- [ ] `Step2ServiceSelection` completo
- [ ] `Step3ResourceConfiguration` completo
- [ ] `Step4Summary` con generación de IA
- [ ] Validaciones por paso

### Página Principal

- [ ] `new-stepped/page.tsx` creada
- [ ] Navegación entre pasos funcional
- [ ] Progress bar animado
- [ ] Submit final funcional
- [ ] Manejo de errores completo

### Polish

- [ ] Animaciones Framer Motion optimizadas
- [ ] Loading states en todos los lugares
- [ ] Mensajes de error claros
- [ ] Responsive design verificado
- [ ] Accesibilidad básica (ARIA labels)

---

## 🚀 Próximos Pasos

1. **Implementar Fase 1:** Hooks y Store
2. **Implementar Fase 2:** Componentes Base
3. **Implementar Fase 3:** Componentes de Pasos
4. **Implementar Fase 4:** Página Principal
5. **Implementar Fase 5:** Polish y Optimización

---

## 📚 Referencias

- **Backend Plan:** `docs/development/PLAN_TRABAJO_COTIZACION_BACKEND.md`
- **Apple HIG:** <https://developer.apple.com/design/human-interface-guidelines/>
- **Framer Motion:** <https://www.framer.com/motion/>
- **TanStack Query:** <https://tanstack.com/query/latest>
- **Zustand:** <https://zustand-demo.pmnd.rs/>
- **Shadcn/ui:** <https://ui.shadcn.com/>

---

**Nota Final:** Este plan está diseñado para integrarse perfectamente con el backend planificado y mantener compatibilidad con el código frontend existente. Todos los componentes siguen las convenciones del proyecto y utilizan las tecnologías ya establecidas.
