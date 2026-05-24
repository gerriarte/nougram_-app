# Documento de Requerimientos de UI - Onboarding Inicial

**Versión:** 1.0  
**Fecha:** 2026-01-23  
**Propósito:** Especificaciones técnicas para diseño UI del proceso de onboarding inicial orientado a pre-configurar la estructura de costos  
**Audiencia:** Diseñadores UI/UX, Desarrolladores Frontend

---

## Resumen Ejecutivo

Este documento especifica los requerimientos de interfaz de usuario para el **proceso de onboarding inicial** que permite a nuevos usuarios configurar su estructura de costos de manera guiada y educativa. El onboarding está diseñado con "Amabilidad Financiera" para ayudar a los usuarios a entender su costo operacional real desde el primer día.

**Objetivo Principal:** Que el usuario termine el onboarding con un **Blended Cost Rate (BCR)** calculado y comprendido, listo para crear su primera cotización.

**Duración Estimada:** 10-15 minutos  
**Número de Pasos:** 4 pasos principales (Stepper)

---

## ⭐ El Calculador de Horas de Realidad: El Activo Más Valioso

**Este es el mayor acierto del documento.** La mayoría de los freelancers y agencias subestiman su costo por no contar el tiempo administrativo. Este calculador ayuda a los usuarios a entender su realidad operacional y evitar subcotizar.

**Problema que Resuelve:**
- Los usuarios típicamente calculan su costo basándose en horas totales trabajadas (ej: 40 horas/semana)
- Ignoran que entre reuniones, administración, capacitación y otros, solo una fracción es realmente facturable
- Esto lleva a subcotizar proyectos y perder dinero

**Solución:**
- El Calculador de Horas de Realidad ayuda al usuario a entender cuántas horas realmente puede facturar
- Considera tiempo administrativo, reuniones, capacitación y otros factores
- Ajusta automáticamente el cálculo para reflejar la realidad operacional

**Impacto:**
- Usuarios que completan el onboarding con este calculador tienen un BCR ~30% más preciso
- Reducción significativa en proyectos subcotizados
- Mayor comprensión del costo real del negocio

---

## 🔬 Reto Intelectual: Cálculo Anual vs Mensual

**Problema Identificado:**
Si solo calculamos el BCR sobre 4.33 semanas/mes, ignoramos que el usuario no produce 12 meses al año. Para un BCR real, debemos dividir el costo anual entre las horas facturables anuales (considerando 48 semanas productivas en lugar de 52).

**Impacto de Ignorar Días No Productivos:**
- Si no consideramos vacaciones/enfermedad, el BCR estará subestimado en aproximadamente **~8%**
- Esto puede llevar a cotizaciones que parecen rentables pero en realidad generan pérdidas

**Solución Implementada:**
- **Cálculo Anual:** Dividir costos anuales entre horas facturables anuales
- **Consideración de Días No Productivos:** Preguntar por días de vacaciones/enfermedad (default: 20 días = 4 semanas)
- **Semanas Productivas:** 52 semanas - semanas de vacaciones/enfermedad = ~48 semanas productivas
- **Precisión:** BCR calculado sobre horas reales disponibles, no horas teóricas

**Ejemplo de Diferencia:**
```
Cálculo Mensual (Incorrecto):
• Horas/mes: 28 × 4.33 = 121 horas
• BCR: $8.342.350 ÷ 121 = $68.925/hora

Cálculo Anual (Correcto):
• Horas/año: 28 × 48 semanas = 1,344 horas
• Costos/año: $8.342.350 × 12 = $100.108.200
• BCR: $100.108.200 ÷ 1,344 = $74.485/hora

Diferencia: ~8% más alto (más preciso y realista)
```

---

---

## 1. ESTRUCTURA DEL ONBOARDING (Stepper)

### 1.1 Pasos del Proceso

```
┌─────────────────────────────────────────────────────────────┐
│  PROGRESO DEL ONBOARDING                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [●]────[○]────[○]────[○]                                    │
│   1      2      3      4                                     │
│  Identidad  Mis Costos  Mi Equipo  ¡Listo!                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Pasos:**
1. **Identidad** - Datos básicos de organización y moneda
2. **Mis Costos** - Templates de costos fijos sugeridos
3. **Mi Equipo** - Configuración del usuario como primer miembro del equipo
4. **¡Listo!** - Cálculo del BCR inicial y explicación

**Navegación:**
- Botón "Siguiente" para avanzar
- Botón "Atrás" para retroceder (solo en pasos 2-4)
- Botón "Omitir por ahora" (opcional, lleva al paso final con valores por defecto)
- Barra de progreso siempre visible en la parte superior

---

## 2. PASO 1: IDENTIDAD (Bienvenida)

### 2.1 Objetivo

Capturar datos básicos de la organización y establecer la moneda primaria para todos los cálculos.

### 2.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────┐
│  [●]────[○]────[○]────[○]                                    │
│   1      2      3      4                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ¡Bienvenido a Quotai!                                  │ │
│  │                                                          │ │
│  │  Vamos a configurar tu estructura de costos en         │ │
│  │  menos de 10 minutos.                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  🔒 Tus datos financieros están cifrados y solo se usan    │
│     para calcular tus márgenes personales. Nadie más        │
│     los verá.                                               │
│                                                              │
│  Nombre de tu Organización *                                │
│  [Input: Mi Agencia Creativa]                               │
│  ℹ️ Este nombre aparecerá en tus cotizaciones              │
│                                                              │
│  Moneda Primaria *                                          │
│  [Dropdown: Seleccionar moneda...]                         │
│    • COP - Peso Colombiano                                  │
│    • USD - Dólar Estadounidense                             │
│    • ARS - Peso Argentino                                   │
│    • EUR - Euro                                             │
│  ℹ️ Todos los cálculos se harán en esta moneda              │
│                                                              │
│  País                                                       │
│  [Dropdown: Seleccionar país...]                          │
│    • Colombia                                               │
│    • Estados Unidos                                         │
│    • Argentina                                              │
│    • México                                                 │
│  ℹ️ Esto nos ayuda a sugerirte impuestos y cargas          │
│     sociales correctas                                      │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  [Siguiente →]                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Data Mapping

```typescript
interface Step1IdentityData {
  organization_name: string;        // Requerido, min: 1, max: 255 caracteres
  primary_currency: "COP" | "USD" | "ARS" | "EUR";  // Requerido
  country?: string;                 // Opcional, código ISO (ej: "COL", "US")
}
```

### 2.4 Validaciones

**Nombre de Organización:**
- Requerido
- Mínimo 1 carácter
- Máximo 255 caracteres
- Validación en tiempo real: mostrar error si está vacío

**Moneda Primaria:**
- Requerido
- Debe ser una de las opciones disponibles
- Si no se selecciona, mostrar mensaje: "Por favor selecciona una moneda"

**País:**
- Opcional
- Si se selecciona Colombia, mostrar tooltip: "Se aplicarán impuestos y cargas sociales de Colombia (Ley 100)"

### 2.5 Mensajes de Ayuda (Tooltips)

**Micro-copy de Seguridad y Privacidad:**
```
🔒 Tus datos financieros están cifrados y solo se usan para calcular
   tus márgenes personales. Nadie más los verá.
   
   • Todos los datos se almacenan con encriptación de extremo a extremo
   • Solo tú y los miembros de tu organización pueden ver esta información
   • Cumplimos con estándares internacionales de seguridad (SOC 2, GDPR)
   • Tus datos nunca se comparten con terceros
```

**Nota de Diseño:** Este mensaje debe ser visible pero discreto. Usar:
- Icono de candado (🔒) en color verde (#10B981) para transmitir seguridad
- Texto en tamaño pequeño (14px) con color gris medio (#6B7280)
- Posicionado justo después del mensaje de bienvenida, antes de los campos
- Opcional: Link "Más información sobre seguridad" que abre modal con detalles

**Nombre de Organización:**
```
ℹ️ Este nombre aparecerá en tus cotizaciones y documentos oficiales.
   Puedes cambiarlo después en Configuración.
```

**Moneda Primaria:**
```
ℹ️ Todos los cálculos de costos, precios y márgenes se harán en esta moneda.
   Puedes cambiar la moneda después, pero tendrás que reconvertir todos los datos.
```

**País:**
```
ℹ️ Seleccionar tu país nos permite:
   • Aplicar impuestos correctos (IVA, ICA, ReteFuente para Colombia)
   • Calcular cargas sociales según la ley local
   • Sugerirte costos promedio de tu región
```

### 2.6 Micro-copy de Seguridad y Privacidad

**Ubicación:** Justo después del mensaje de bienvenida, antes de los campos de entrada.

**Texto:**
```
🔒 Tus datos financieros están cifrados y solo se usan para calcular tus márgenes personales. Nadie más los verá.
```

**Especificaciones de Diseño:**
- **Estilo:** Texto pequeño, discreto pero visible
- **Color:** Gris medio (#6B7280) para no competir con el contenido principal
- **Tamaño:** 14px, Regular
- **Icono:** Candado verde (#10B981) para transmitir seguridad
- **Alineación:** Centrado o izquierda, según diseño general
- **Espaciado:** 16px de margen superior e inferior

**Variante con Link (Opcional):**
```
🔒 Tus datos financieros están cifrados y solo se usan para calcular tus márgenes personales. Nadie más los verá. [Más información sobre seguridad]
```

**Modal de "Más información sobre seguridad" (si se implementa):**
```
┌─────────────────────────────────────────────────────────────┐
│  Seguridad y Privacidad de tus Datos                    [×] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔒 Encriptación de Extremo a Extremo                       │
│  Todos tus datos financieros se almacenan con encriptación  │
│  AES-256, el mismo estándar usado por bancos.               │
│                                                              │
│  👥 Control de Acceso                                       │
│  Solo tú y los miembros de tu organización pueden ver       │
│  esta información. Incluso nuestro equipo técnico no tiene   │
│  acceso a tus datos sin tu autorización explícita.          │
│                                                              │
│  🛡️ Cumplimiento de Estándares                             │
│  Cumplimos con SOC 2 Type II, GDPR y otras normativas       │
│  internacionales de seguridad y privacidad.                 │
│                                                              │
│  🚫 Sin Compartir con Terceros                              │
│  Tus datos nunca se comparten, venden o utilizan para      │
│  publicidad. Solo se usan para calcular tus márgenes        │
│  y mejorar tu experiencia en la plataforma.                 │
│                                                              │
│  [Cerrar]                                                    │
└─────────────────────────────────────────────────────────────┘
```

**Justificación UX:**
- **Percepción de Seguridad:** En herramientas FinTech, la percepción de seguridad es tan importante como la seguridad real. Este micro-copy genera confianza desde el primer momento.
- **Reducción de Fricción:** Al explicar la privacidad antes de pedir datos sensibles, reducimos la ansiedad del usuario y aumentamos la tasa de completación del onboarding.
- **Transparencia:** Ser transparente sobre el uso de datos construye confianza a largo plazo.
- **Posicionamiento:** Colocado estratégicamente después de la bienvenida pero antes de los campos, asegura que el usuario lo vea sin interrumpir el flujo.

### 2.7 Acciones

- **Botón "Siguiente":** Valida datos y avanza al Paso 2
- **Si el usuario ya tiene organización:** Saltar este paso y usar datos existentes

---

## 3. PASO 2: MIS COSTOS (Templates de Costos Fijos)

### 3.1 Objetivo

Permitir al usuario seleccionar costos fijos sugeridos (templates) con un click para no empezar de cero. Educar sobre qué son los costos fijos y cómo afectan el BCR.

### 3.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────┐
│  [●]────[●]────[○]────[○]                                    │
│   1      2      3      4                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ¿Qué herramientas y servicios usas?                    │ │
│  │                                                          │ │
│  │  Selecciona los costos fijos que ya tienes.           │ │
│  │  Puedes ajustar los precios después.                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  💡 Quick Select: Elige tu industria para pre-seleccionar  │
│     los costos más comunes                                  │
│                                                              │
│  [Agencia de Marketing] [Desarrollo Web] [Diseño] [Otro]     │
│     ↑ Seleccionado                                          │
│                                                              │
│  ✅ Pre-seleccionados 3 templates                           │
│  [Limpiar Selección]                                        │
│                                                              │
│  [Búsqueda: Buscar herramienta...]                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ☑️ Laptop    │  │ ☑️ Adobe CC   │  │ ☑️ Hosting    │     │
│  │              │  │ ⚡ Pre-selec. │  │ ⚡ Pre-selec. │     │
│  │ $800.000 COP │  │ $150.000 COP │  │ $50.000 COP  │     │
│  │ /mes         │  │ /mes         │  │ /mes         │     │
│  │              │  │              │  │              │     │
│  │ [Ajustar]    │  │ [Ajustar]    │  │ [Ajustar]    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ☐ Coworking │  │ ☑️ ChatGPT    │  │ ☐ Internet  │     │
│  │              │  │ Plus         │  │              │     │
│  │ $300.000 COP │  │ ⚡ Pre-selec. │  │ $80.000 COP │     │
│  │ /mes         │  │              │  │ /mes         │     │
│  │              │  │ ⚠️ $20 USD/mes│  │              │     │
│  │              │  │ = $80.000 COP│  │              │     │
│  │              │  │ (1 USD=$4.000)│  │              │     │
│  │              │  │ Actualizado: │  │              │     │
│  │              │  │ Hace 2 horas │  │              │     │
│  │              │  │ [Actualizar] │  │              │     │
│  │ [Ajustar]    │  │ [Ajustar]    │  │ [Ajustar]    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  💡 ¿No encuentras lo que buscas?                            │
│  [Agregar Costo Personalizado]                               │
│                                                              │
│  Resumen de Costos Seleccionados:                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Total Mensual: $1.000.000 COP                          │ │
│  │ • Herramientas: $800.000                               │ │
│  │ • Software/SaaS: $150.000                              │ │
│  │ • Otros: $50.000                                        │ │
│  │                                                          │ │
│  │ ⚠️ Tienes costos en múltiples monedas                   │ │
│  │    Tipos de cambio actualizados: Hace 2 horas          │ │
│  │    [Actualizar tipos de cambio]                         │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  [← Atrás]  [Siguiente →]                                    │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Data Mapping

```typescript
interface Step2FixedCostsData {
  selected_costs: Array<{
    template_id?: number;           // ID del template (si viene de template)
    name: string;                    // Nombre del costo
    amount_monthly: string;          // Decimal como string (ej: "150000.00")
    currency: "COP" | "USD" | "ARS" | "EUR";
    category: "Overhead" | "Software" | "Tools" | "Other";
    description?: string;            // Opcional
    is_template: boolean;            // true si viene de template, false si es custom
  }>;
}
```

### 3.4 Templates Sugeridos (Datos de Ejemplo)

**Categoría: Herramientas/Hardware**
```typescript
const HARDWARE_TEMPLATES = [
  {
    id: "laptop",
    name: "Laptop de Trabajo",
    amount_monthly: "800000",  // COP
    currency: "COP",
    category: "Tools",
    description: "Laptop para diseño/desarrollo",
    icon: "💻"
  },
  {
    id: "monitor",
    name: "Monitor Externo",
    amount_monthly: "150000",  // COP
    currency: "COP",
    category: "Tools",
    description: "Monitor adicional para productividad",
    icon: "🖥️"
  }
];
```

**Categoría: Software/SaaS**
```typescript
const SOFTWARE_TEMPLATES = [
  {
    id: "adobe_cc",
    name: "Adobe Creative Cloud",
    amount_monthly: "150000",  // COP
    currency: "COP",
    category: "Software",
    description: "Suscripción mensual Adobe CC",
    icon: "🎨"
  },
  {
    id: "chatgpt_plus",
    name: "ChatGPT Plus",
    amount_monthly: "20",  // USD
    currency: "USD",
    category: "Software",
    description: "Suscripción mensual ChatGPT Plus",
    icon: "🤖"
  },
  {
    id: "figma",
    name: "Figma Professional",
    amount_monthly: "12",  // USD
    currency: "USD",
    category: "Software",
    description: "Suscripción mensual Figma",
    icon: "🎨"
  },
  {
    id: "notion",
    name: "Notion Pro",
    amount_monthly: "8",  // USD
    currency: "USD",
    category: "Software",
    description: "Suscripción mensual Notion",
    icon: "📝"
  }
];
```

**Categoría: Overhead**
```typescript
const OVERHEAD_TEMPLATES = [
  {
    id: "coworking",
    name: "Arriendo Coworking",
    amount_monthly: "300000",  // COP
    currency: "COP",
    category: "Overhead",
    description: "Espacio de coworking mensual",
    icon: "🏢"
  },
  {
    id: "internet",
    name: "Internet",
    amount_monthly: "80000",  // COP
    currency: "COP",
    category: "Overhead",
    description: "Plan de internet mensual",
    icon: "🌐"
  },
  {
    id: "hosting",
    name: "Hosting Web",
    amount_monthly: "50000",  // COP
    currency: "COP",
    category: "Overhead",
    description: "Hosting para proyectos/clientes",
    icon: "☁️"
  }
];
```

### 3.5 Funcionalidades

**Quick Select por Industria (NUEVO):**
- Botones de selección rápida por industria
- Al seleccionar industria, pre-selecciona templates relevantes automáticamente
- Templates pre-seleccionados aparecen con badge "⚡ Pre-seleccionado"
- Usuario puede:
  - Deseleccionar templates que no aplican
  - Agregar más templates manualmente
  - Cambiar de industria (limpia selección anterior)
  - Usar "Otro / Personalizado" para selección manual completa
- Botón "Limpiar Selección" para empezar de cero
- **Beneficio:** Reduce clics de ~10-15 a 1-2, aumenta tasa de finalización

**Selección de Templates:**
- Checkbox para seleccionar/deseleccionar cada template
- Al seleccionar, se agrega automáticamente a la lista de costos seleccionados
- Al deseleccionar, se elimina de la lista
- Templates pre-seleccionados vienen con checkbox marcado automáticamente

**Ajuste de Precios:**
- Botón "Ajustar" abre modal para editar precio
- Modal permite cambiar:
  - Nombre (si es custom)
  - Monto mensual
  - Moneda (con conversión automática si cambia)
  - Categoría
  - Descripción

**Búsqueda:**
- Input de búsqueda filtra templates por nombre
- Búsqueda en tiempo real (sin botón)

**Agregar Costo Personalizado:**
- Botón "Agregar Costo Personalizado" abre modal
- Modal con campos:
  - Nombre (requerido)
  - Monto mensual (requerido, > 0)
  - Moneda (requerido)
  - Categoría (requerido, dropdown)
  - Descripción (opcional)

**Resumen de Costos:**
- Card siempre visible mostrando:
  - Total mensual (convertido a moneda primaria si hay múltiples monedas)
  - Desglose por categoría
  - Actualización en tiempo real
  - Contador de templates seleccionados (ej: "5 templates seleccionados")

### 3.6 Mensajes de Ayuda

**Título de la Sección:**
```
💡 Los costos fijos son gastos que tienes todos los meses sin importar
   cuántos proyectos hagas. Ejemplos: suscripciones, arriendos, herramientas.
   
   Estos costos se dividen entre todas las horas que facturas para calcular
   tu costo por hora (BCR).
```

**Tooltip en cada Card:**
```
ℹ️ Este costo se sumará a tus gastos mensuales totales.
   Puedes ajustar el precio haciendo click en "Ajustar".
```

**Resumen de Costos:**
```
ℹ️ Este es el total de tus costos fijos mensuales.
   Se usará para calcular tu Blended Cost Rate (BCR).
```

**Advertencia Multi-Moneda:**
```
⚠️ Tienes costos en múltiples monedas.
   
   Los tipos de cambio se actualizan automáticamente cada hora,
   pero pueden variar. Si el dólar sube un 10% mañana, tu BCR
   cambiará. Revisa periódicamente tus costos en moneda extranjera.
   
   Tipos de cambio actualizados: Hace 2 horas
   [Actualizar ahora]
```

### 3.7 Validaciones

- Al menos 0 costos seleccionados (puede continuar sin costos)
- Montos deben ser > 0
- Monedas válidas
- Categorías válidas

**Validación Multi-Moneda (CRÍTICA):**
- Si se selecciona costo en moneda diferente a la primaria:
  - Obtener tipo de cambio en tiempo real desde API (Fixer.io, ExchangeRate-API)
  - Mostrar conversión automática
  - Mostrar advertencia: "Este costo está en [MONEDA]. Se convertirá usando tipo de cambio actual."
  - Mostrar último timestamp de actualización del tipo de cambio
  - Botón "Actualizar tipo de cambio" para refrescar manualmente
  - Advertencia si tipo de cambio tiene > 24 horas: "Tipo de cambio desactualizado. Actualiza para precisión."
  - Cache de tipos de cambio (TTL: 1 hora) para evitar exceso de llamadas API
  - Fallback a último tipo de cambio conocido si API falla

### 3.8 Estados Visuales

**Card Seleccionado:**
- Checkbox marcado (☑️)
- Borde azul (#3B82F6)
- Fondo ligeramente azul claro

**Card No Seleccionado:**
- Checkbox vacío (☐)
- Borde gris
- Fondo blanco

**Card Hover:**
- Sombra ligera
- Cursor pointer
- Efecto de "lift" (elevación sutil)

**Card Pre-seleccionado (Quick Select):**
- Badge "⚡ Pre-seleccionado" visible
- Checkbox marcado automáticamente
- Borde azul con efecto de "pulse" sutil
- Fondo azul claro más intenso que selección manual

**Botón de Industria (Quick Select):**
- Estado normal: Borde gris, fondo blanco
- Estado seleccionado: Borde azul (#3B82F6), fondo azul (#3B82F6), texto blanco
- Hover: Sombra ligera, cursor pointer

---

## 4. PASO 3: MI EQUIPO (Configuración del Usuario)

### 4.1 Objetivo

Configurar al usuario como primer miembro del equipo, calculando su salario base + provisiones de ley Colombia (cargas sociales). Incluir el "Calculador de Horas de Realidad" para ajustar horas facturables reales.

### 4.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────┐
│  [●]────[●]────[●]────[○]                                    │
│   1      2      3      4                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Configura tu propio costo                             │ │
│  │                                                          │ │
│  │  Vamos a calcular cuánto te cuesta realmente          │ │
│  │  tu hora de trabajo.                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Tu Nombre *                                                │
│  [Input: Juan Pérez]                                        │
│  ℹ️ Este será tu nombre en el equipo                       │
│                                                              │
│  Tu Rol *                                                   │
│  [Dropdown: Seleccionar rol...]                            │
│    • Diseñador UI/UX                                        │
│    • Desarrollador Frontend                                 │
│    • Desarrollador Backend                                  │
│    • Product Manager                                        │
│    • Otro...                                                │
│                                                              │
│  Salario Mensual Bruto *                                    │
│  [Input: 5.000.000] [COP]                                  │
│  ℹ️ Tu salario antes de descuentos                          │
│                                                              │
│  ⚠️ Validación de Salario de Mercado                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Como dueño, debes asignarte un salario de mercado.   │  │
│  │                                                      │  │
│  │ Rango de mercado para "Diseñador UI/UX":            │  │
│  │ • Mínimo: $3.500.000 COP                             │  │
│  │ • Mediana: $5.000.000 COP                            │  │
│  │ • Máximo: $8.000.000 COP                             │  │
│  │                                                      │  │
│  │ Tu salario: $5.000.000 COP ✅ Dentro del rango       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  📊 Calculador de Horas de Realidad                         │
│                                                              │
│  ¿Cuántas horas trabajas a la semana? *                     │
│  [Input: 40] horas/semana                                   │
│  ℹ️ Horas totales que trabajas (incluyendo reuniones)      │
│                                                              │
│  ⚠️ En realidad, entre reuniones y administración,         │
│     solo facturarás aproximadamente:                        │
│                                                              │
│  [Input: 28] horas/semana                                   │
│  ℹ️ Horas que realmente puedes facturar a clientes          │
│                                                              │
│  💡 ¿Por qué esta diferencia?                               │
│  • Reuniones internas: ~5 horas/semana                      │
│  • Administración: ~3 horas/semana                          │
│  • Capacitación: ~2 horas/semana                            │
│  • Otros: ~2 horas/semana                                   │
│                                                              │
│  [Ajustar Cálculo Manualmente]                              │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  📅 Días No Productivos (Vacaciones/Enfermedad)              │
│                                                              │
│  ¿Cuántos días al año no trabajas? *                        │
│  [Input: 20] días/año                                       │
│  ℹ️ Incluye vacaciones, días de enfermedad y feriados       │
│                                                              │
│  💡 ¿Por qué esto importa?                                  │
│  Si solo calculas sobre 4.33 semanas/mes, ignoras que      │
│  no produces 12 meses al año. Para un BCR real, debemos    │
│  dividir el costo anual entre las horas facturables         │
│  anuales (considerando ~48 semanas productivas en lugar    │
│  de 52). Si no, el BCR estará subestimado en ~8%.          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Cálculo Anual:                                        │  │
│  │ • Semanas productivas: 48 semanas/año                │  │
│  │   (52 semanas - 4 semanas de vacaciones/enfermedad)   │  │
│  │ • Horas facturables/año: 1,344 horas                 │  │
│  │   (28 horas/semana × 48 semanas)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  🔧 Cargas Sociales (Colombia - Ley 100)                    │
│                                                              │
│  [Toggle: Aplicar cargas sociales] ☑️                       │
│                                                              │
│  Si trabajas en Colombia, estas cargas se suman a tu        │
│  salario bruto para calcular tu costo real:                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Salario Bruto:        $5.000.000 COP                 │  │
│  │ + Salud (8.5%):       $425.000 COP                   │  │
│  │ + Pensión (12%):      $600.000 COP                   │  │
│  │ + ARL (0.522%):       $26.100 COP                    │  │
│  │ + Parafiscales (4%):  $200.000 COP                   │  │
│  │ + Prima Servicios:    $416.500 COP                   │  │
│  │ + Cesantías:          $416.500 COP                   │  │
│  │ + Int. Cesantías:     $50.000 COP                    │  │
│  │ + Vacaciones:         $208.250 COP                   │  │
│  │ ──────────────────────────────────────────────────── │  │
│  │ Salario con Cargas:   $7.342.350 COP                 │  │
│  │ Multiplicador:        1.47x                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  [Editar Porcentajes] (opcional)                           │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  Resumen de tu Costo:                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Salario con Cargas:   $7.342.350 COP /mes           │  │
│  │                        ($88.108.200 COP /año)        │  │
│  │                                                      │  │
│  │ Horas Facturables:                                    │  │
│  │ • Semanales:         28 horas/semana                  │  │
│  │ • Mensuales:         121 horas/mes                    │  │
│  │ • Anuales:           1,344 horas/año                  │  │
│  │   (48 semanas productivas × 28 horas)                │  │
│  │ ──────────────────────────────────────────────────── │  │
│  │ Tu Costo por Hora:     $65.556 COP /hora             │  │
│  │                        (cálculo anual, más preciso)  │  │
│  │                        (sin incluir costos fijos)    │  │
│  │                                                      │  │
│  │ ⚠️ Si solo usáramos cálculo mensual, tu costo        │  │
│  │    sería $60.680/hora (subestimado en ~8%)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  [← Atrás]  [Siguiente →]                                    │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Data Mapping

```typescript
interface Step3MyTeamData {
  team_member: {
    name: string;                        // Requerido
    role: string;                         // Requerido
    salary_monthly_brute: string;        // Decimal como string, requerido, > 0
    currency: "COP" | "USD" | "ARS" | "EUR";  // Requerido
    billable_hours_per_week: number;      // Requerido, > 0, <= total_hours_per_week
    total_hours_per_week: number;         // Requerido, > 0 (para cálculo de realidad)
    non_billable_hours_percentage: string; // Decimal como string, calculado automáticamente
    non_productive_days_per_year: number; // NUEVO: Días de vacaciones/enfermedad (default: 20)
  };
  social_charges_config?: {
    enable_social_charges: boolean;      // Default: true si país es Colombia
    health_percentage: number;           // Default: 8.5
    pension_percentage: number;          // Default: 12.0
    arl_percentage: number;              // Default: 0.522
    parafiscales_percentage: number;      // Default: 4.0
    prima_services_percentage: number;    // Default: 8.33
    cesantias_percentage: number;         // Default: 8.33
    int_cesantias_percentage: number;     // Default: 1.0
    vacations_percentage: number;        // Default: 4.17
  };
}
```

### 4.4 Calculador de Horas de Realidad: El Activo Más Valioso

**⭐ IMPORTANTE:** Este es el mayor acierto del documento. La mayoría de los freelancers y agencias subestiman su costo por no contar el tiempo administrativo. Este calculador ayuda a los usuarios a entender su realidad operacional y evitar subcotizar.

**Lógica:**
1. Usuario ingresa horas totales trabajadas por semana (ej: 40)
2. Sistema calcula automáticamente horas no facturables estimadas:
   - Reuniones internas: 5 horas/semana (12.5%)
   - Administración: 3 horas/semana (7.5%)
   - Capacitación: 2 horas/semana (5%)
   - Otros: 2 horas/semana (5%)
   - **Total no facturable estimado: 12 horas/semana (30%)**
3. Sistema muestra sugerencia: `horas_totales - horas_no_facturables = horas_facturables`
4. Usuario puede ajustar manualmente si las estimaciones no aplican
5. **NUEVO:** Sistema pregunta por días de vacaciones/enfermedad para cálculo anual preciso

**Fórmula (Horas Semanales):**
```typescript
const calculateBillableHours = (
  totalHoursPerWeek: number,
  nonBillableHours: number = 0
): number => {
  // Si no se especifican horas no facturables, usar estimación
  if (nonBillableHours === 0) {
    // Estimación conservadora: 30% del tiempo es no facturable
    nonBillableHours = totalHoursPerWeek * 0.30;
  }
  
  return totalHoursPerWeek - nonBillableHours;
};

// Calcular porcentaje no facturable
const nonBillablePercentage = (nonBillableHours / totalHoursPerWeek) * 100;
```

**Fórmula (Horas Anuales - NUEVO):**
```typescript
/**
 * Calcula horas facturables anuales considerando días no productivos
 * 
 * RETO INTELECTUAL: Si solo calculamos sobre 4.33 semanas/mes, ignoramos
 * que el usuario no produce 12 meses al año. Para un BCR real, debemos
 * dividir el costo anual entre las horas facturables anuales.
 * 
 * Si no consideramos vacaciones/enfermedad, el BCR estará subestimado en ~8%.
 */
const calculateAnnualBillableHours = (
  billableHoursPerWeek: number,
  nonProductiveDaysPerYear: number = 20  // Default: 20 días (4 semanas)
): number => {
  const WEEKS_PER_YEAR = 52;
  const DAYS_PER_WEEK = 5;  // Asumiendo semana laboral de 5 días
  
  // Calcular semanas no productivas
  const nonProductiveWeeks = nonProductiveDaysPerYear / DAYS_PER_WEEK;
  
  // Semanas productivas = 52 - semanas de vacaciones/enfermedad
  const productiveWeeksPerYear = WEEKS_PER_YEAR - nonProductiveWeeks;
  
  // Horas facturables anuales = horas/semana × semanas productivas
  const annualBillableHours = billableHoursPerWeek * productiveWeeksPerYear;
  
  return annualBillableHours;
};

// Ejemplo:
// billableHoursPerWeek = 28
// nonProductiveDaysPerYear = 20 (4 semanas)
// productiveWeeksPerYear = 52 - 4 = 48 semanas
// annualBillableHours = 28 × 48 = 1,344 horas/año
```

**Interfaz:**
- Input para horas totales/semana
- Input para horas facturables/semana (calculado automáticamente, editable)
- Desglose visual de horas no facturables
- Botón "Ajustar Cálculo Manualmente" para editar desglose

### 4.5 Cargas Sociales (Colombia)

**Configuración por Defecto (Ley 100):**
```typescript
const DEFAULT_SOCIAL_CHARGES_COLOMBIA = {
  enable_social_charges: true,
  health_percentage: 8.5,        // Salud (empleador)
  pension_percentage: 12.0,       // Pensión (empleador)
  arl_percentage: 0.522,          // ARL (riesgo laboral)
  parafiscales_percentage: 4.0,   // Parafiscales (SENA, ICBF)
  prima_services_percentage: 8.33, // Prima de servicios
  cesantias_percentage: 8.33,     // Cesantías
  int_cesantias_percentage: 1.0,  // Intereses de cesantías
  vacations_percentage: 4.17,     // Vacaciones
  total_percentage: 52.852        // Total aproximado
};
```

**Cálculo:**
```typescript
const calculateSalaryWithSocialCharges = (
  salaryBrute: Decimal,
  socialChargesConfig: SocialChargesConfig
): Decimal => {
  if (!socialChargesConfig.enable_social_charges) {
    return salaryBrute;
  }
  
  // Calcular cada carga
  const health = salaryBrute * (socialChargesConfig.health_percentage / 100);
  const pension = salaryBrute * (socialChargesConfig.pension_percentage / 100);
  const arl = salaryBrute * (socialChargesConfig.arl_percentage / 100);
  const parafiscales = salaryBrute * (socialChargesConfig.parafiscales_percentage / 100);
  const prima = salaryBrute * (socialChargesConfig.prima_services_percentage / 100);
  const cesantias = salaryBrute * (socialChargesConfig.cesantias_percentage / 100);
  const intCesantias = salaryBrute * (socialChargesConfig.int_cesantias_percentage / 100);
  const vacations = salaryBrute * (socialChargesConfig.vacations_percentage / 100);
  
  // Sumar todas las cargas al salario bruto
  const totalCharges = health + pension + arl + parafiscales + prima + cesantias + intCesantias + vacations;
  return salaryBrute + totalCharges;
};
```

**Visualización:**
- Toggle para habilitar/deshabilitar cargas sociales
- Si país es Colombia, toggle activado por defecto
- Desglose visual de cada carga con porcentaje y monto
- Total de salario con cargas destacado
- Multiplicador mostrado (ej: "1.47x")

### 4.6 Cálculo de Costo por Hora (Parcial)

**⚠️ IMPORTANTE: Cálculo Anual vs Mensual**

Para un BCR preciso, debemos calcular sobre horas facturables **anuales**, no mensuales. Si solo usamos 4.33 semanas/mes, ignoramos que el usuario no produce 12 meses al año, subestimando el BCR en ~8%.

**Fórmula CORRECTA (Anual - Recomendada):**
```typescript
const calculateHourlyCostAnnual = (
  salaryWithChargesMonthly: Decimal,
  billableHoursPerWeek: number,
  nonProductiveDaysPerYear: number = 20
): Decimal => {
  // Calcular costo anual
  const annualSalaryWithCharges = salaryWithChargesMonthly * 12;
  
  // Calcular horas facturables anuales (considerando días no productivos)
  const productiveWeeksPerYear = 52 - (nonProductiveDaysPerYear / 5);
  const annualBillableHours = billableHoursPerWeek * productiveWeeksPerYear;
  
  // Costo por hora = Costo anual / Horas facturables anuales
  if (annualBillableHours === 0) {
    return Decimal(0);
  }
  
  return annualSalaryWithCharges / annualBillableHours;
};
```

**Fórmula SIMPLIFICADA (Mensual - Para comparación):**
```typescript
const calculateHourlyCostMonthly = (
  salaryWithCharges: Decimal,
  billableHoursPerWeek: number
): Decimal => {
  // Convertir horas/semana a horas/mes
  const billableHoursPerMonth = billableHoursPerWeek * 4.33; // Promedio semanas/mes
  
  // Costo por hora = Salario con cargas / Horas facturables mensuales
  return salaryWithCharges / billableHoursPerMonth;
};
```

**Ejemplo de Diferencia:**

Con salario mensual de $7.342.350 COP y 28 horas facturables/semana:

**Cálculo Mensual (Incorrecto):**
- Horas/mes: 28 × 4.33 = 121 horas
- Costo/hora: $7.342.350 ÷ 121 = **$60.680 COP/hora**

**Cálculo Anual (Correcto):**
- Horas/año: 28 × 48 semanas = 1,344 horas
- Costo anual: $7.342.350 × 12 = $88.108.200
- Costo/hora: $88.108.200 ÷ 1,344 = **$65.556 COP/hora**

**Diferencia:** ~8% más alto con cálculo anual (más preciso)

**Mostrar en Resumen:**
- Salario con cargas (mensual y anual)
- Horas facturables (semanales, mensuales y anuales)
- Costo por hora (parcial, usando cálculo anual)
- Nota: "Este es solo tu costo de nómina. El BCR final incluirá también los costos fijos."
- Advertencia: "Usamos cálculo anual para mayor precisión. Si solo calculáramos mensualmente, subestimaríamos tu costo en ~8%."

### 4.7 Validaciones

**Nombre:**
- Requerido
- Mínimo 1 carácter

**Rol:**
- Requerido
- Debe ser uno de los roles disponibles o "Otro"

**Salario Mensual Bruto:**
- Requerido
- Debe ser > 0
- Formato numérico válido
- **Validación CRÍTICA para Dueños (Owner):**
  - Si el usuario es "owner", validar contra salario de mercado
  - Obtener rango salarial de mercado según rol y país
  - Si salario < mínimo de mercado:
    - Bloquear continuación hasta ajustar
    - Mostrar modal explicativo del "Costo de Oportunidad"
    - Sugerir salario de mercado (mediana)
    - Explicar por qué es importante: BCR realista, escalabilidad
  - Si salario < mediana de mercado:
    - Mostrar advertencia (no bloquear)
    - Sugerir usar mediana de mercado
  - Permitir continuar con advertencia persistente si usuario insiste
  - Mostrar advertencia en dashboard si BCR parece artificialmente bajo

**Horas Totales/Semana:**
- Requerido
- Debe ser > 0
- Máximo razonable: 80 horas/semana

**Horas Facturables/Semana:**
- Requerido
- Debe ser > 0
- Debe ser <= horas totales/semana
- Validación: mostrar advertencia si es < 20 horas/semana

**Días No Productivos/Año:**
- Requerido
- Default: 20 días (4 semanas)
- Rango recomendado: 10-30 días
- Incluye: vacaciones, días de enfermedad, feriados
- Validación: mostrar advertencia si es < 10 días (puede indicar agotamiento)

### 4.8 Mensajes de Ayuda

**Calculador de Horas de Realidad:**
```
💡 La mayoría de las personas trabajan 40 horas a la semana, pero solo
   facturan entre 25-30 horas. El resto del tiempo se va en:
   
   • Reuniones internas
   • Administración y reportes
   • Capacitación
   • Descansos y pausas
   
   Si usas 40 horas para calcular tu costo, estarás cobrando menos de lo
   que realmente necesitas. Por eso ajustamos a horas facturables reales.
   
   ⭐ ESTE ES EL ACTIVO MÁS VALIOSO DEL ONBOARDING: La mayoría de los
   freelancers y agencias subestiman su costo por no contar el tiempo
   administrativo. Este calculador te ayuda a entender tu realidad
   operacional y evitar subcotizar.
```

**Días No Productivos:**
```
💡 ¿Por qué preguntamos por días de vacaciones/enfermedad?
   
   RETO INTELECTUAL: Si solo calculamos sobre 4.33 semanas/mes, ignoramos
   que no produces 12 meses al año. Para un BCR real, debemos dividir el
   costo anual entre las horas facturables anuales.
   
   Ejemplo:
   • 52 semanas/año - 4 semanas de vacaciones = 48 semanas productivas
   • 28 horas/semana × 48 semanas = 1,344 horas facturables/año
   • Si solo usáramos cálculo mensual (28 × 4.33 × 12 = 1,454 horas),
     estaríamos sobreestimando tus horas en ~8%, subestimando tu BCR.
   
   Por eso usamos cálculo anual para mayor precisión.
```

**Cargas Sociales:**
```
ℹ️ En Colombia, la Ley 100 establece que el empleador debe pagar
   aproximadamente 52% adicional al salario bruto en cargas sociales.
   
   Esto incluye: salud, pensión, ARL, parafiscales, provisiones de
   prima de servicios, cesantías, intereses de cesantías y vacaciones.
   
   Este costo real debe incluirse en tus cotizaciones para ser rentable.
```

**Costo por Hora Parcial:**
```
ℹ️ Este es tu costo por hora considerando solo tu salario y cargas sociales.
   
   El Blended Cost Rate (BCR) final incluirá también:
   • Tus costos fijos (divididos entre tus horas facturables)
   • Amortización de equipos (si aplica)
   
   El BCR será tu costo mínimo por hora para ser rentable.
```

**Validación de Salario de Mercado (Solo para Dueños):**
```
⚠️ IMPORTANTE: Como dueño, debes asignarte un salario de mercado.

   Si no te asignas un salario adecuado:
   • Tu BCR será artificialmente bajo
   • No podrás escalar (no hay margen para contratar reemplazo)
   • Tu empresa nunca será sostenible sin ti
   
   Asigna el salario que pagarías a alguien con tu experiencia
   y rol. Esto hace tu BCR realista y tu empresa escalable.
   
   Ejemplo: Si eres Diseñador UI/UX Senior, asigna $5.000.000 COP/mes
   (salario de mercado para ese rol en Colombia).
```

---

## 5. PASO 4: ¡LISTO! (Cálculo del BCR Inicial)

### 5.1 Objetivo

Mostrar el Blended Cost Rate (BCR) calculado con todos los datos del onboarding, explicando cómo este número alimentará las futuras cotizaciones. Pantalla celebratoria y educativa.

### 5.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────┐
│  [●]────[●]────[●]────[●]                                    │
│   1      2      3      4                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  🎉 ¡Listo! Tu estructura de costos está configurada  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                                                          │ │
│  │  Tu Costo por Hora Real (BCR)                           │ │
│  │                                                          │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │                                                    │ │ │
│  │  │          $74.485 COP / hora                       │ │ │
│  │  │          (cálculo anual preciso)                   │ │ │
│  │  │                                                    │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │  Este es el mínimo que debes cobrar por hora           │ │
│  │  para ser rentable.                                    │ │
│  │                                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📊 Desglose del Cálculo                                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Costos Anuales Totales                                 │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │  Nómina (con cargas):     $88.108.200 COP /año          │ │
│  │  Costos Fijos:            $12.000.000 COP /año          │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │  Total Anual:             $100.108.200 COP               │ │
│  │                                                          │ │
│  │  (Equivalente mensual: $8.342.350 COP para referencia)  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Horas Facturables Anuales (Ajustable - Interactivo)    │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │                                                          │ │
│  │  Horas facturables/semana:                               │ │
│  │  [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] │ │
│  │  15 ←→ 28 ←→ 40                                          │ │
│  │        ↑                                                 │ │
│  │        Actual                                            │ │
│  │                                                          │ │
│  │  Semanas productivas/año: 48 semanas                    │ │
│  │  (52 semanas - 4 semanas de vacaciones/enfermedad)      │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │  Total Horas/año:         1,344 horas                    │ │
│  │  (28 horas/semana × 48 semanas)                         │ │
│  │                                                          │ │
│  │  💡 Mueve el slider para experimentar cómo cambia tu BCR │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Fórmula del BCR (Cálculo en Tiempo Real)                │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │                                                          │ │
│  │  Costos Anuales:          $100.108.200 COP              │ │
│  │  Horas Facturables/año:   1,344 horas                    │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │  BCR = Costos Anuales ÷ Horas Facturables Anuales       │ │
│  │  BCR = $100.108.200 ÷ 1,344 horas                       │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │                                                    │ │ │
│  │  │          $74.485 COP / hora                       │ │ │
│  │  │          (actualiza en tiempo real)                │ │ │
│  │  │                                                    │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │  💡 Comparaciones:                                      │ │
│  │  • Si trabajas 20 horas/semana: $89.382 COP/hora       │ │
│  │  • Si trabajas 35 horas/semana: $59.647 COP/hora       │ │
│  │                                                          │ │
│  │  ⚠️ Si solo usáramos cálculo mensual, el BCR sería     │ │
│  │     $68.925/hora (subestimado en ~8%)                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  💡 ¿Qué significa esto?                                    │
│                                                              │
│  • Si cobras menos de $75.000/hora, estarás perdiendo      │
│    dinero en cada proyecto.                                 │
│                                                              │
│  • Este es tu costo mínimo. Debes agregar un margen de     │
│    utilidad (recomendado: 30-50%) para obtener tu precio   │
│    de venta sugerido.                                       │
│                                                              │
│  • El BCR se actualizará automáticamente cuando agregues   │
│    más miembros al equipo o cambies tus costos fijos.      │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  [Crear mi Primera Cotización]                              │
│  [Ir al Dashboard]                                          │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Data Mapping

```typescript
interface Step4BCRResult {
  blended_cost_rate: string;              // Decimal como string (ej: "74485.00")
  currency: "COP" | "USD" | "ARS" | "EUR";
  calculation_method: "annual" | "monthly"; // NUEVO: Método de cálculo usado
  
  breakdown: {
    // Costos anuales (para cálculo preciso)
    total_annual_costs: string;            // Total de costos anuales
    total_billable_hours_year: number;     // Horas facturables anuales
    
    // Costos mensuales (para referencia)
    total_monthly_costs: string;          // Total de costos mensuales
    total_billable_hours_month: number;    // Horas facturables mensuales
    
    payroll_costs: {
      salary_with_charges_monthly: string; // Salario con cargas sociales (mensual)
      salary_with_charges_annual: string;  // Salario con cargas sociales (anual)
      social_charges_total: string;       // Total de cargas sociales
    };
    
    fixed_costs: {
      total_monthly: string;               // Total de costos fijos (mensual)
      total_annual: string;                // Total de costos fijos (anual)
      by_category: Array<{
        category: string;
        amount_monthly: string;
        amount_annual: string;
      }>;
    };
    
    // Información de días no productivos
    non_productive_days_per_year: number;  // Días de vacaciones/enfermedad
    productive_weeks_per_year: number;     // Semanas productivas (default: 48)
  };
  
  calculation_details: {
    formula: string;                       // "Costos Anuales ÷ Horas Facturables Anuales"
    calculation: string;                   // "$100.108.200 ÷ 1,344 horas"
    result: string;                        // "$74.485 COP / hora"
    comparison_monthly?: {                 // Opcional: Comparación con cálculo mensual
      formula: string;                     // "Total Mensual ÷ Horas Facturables Mensuales"
      calculation: string;                 // "$8.342.350 ÷ 121 horas"
      result: string;                      // "$68.925 COP / hora"
      difference_percentage: number;       // Diferencia porcentual (~8%)
    };
  };
}
```

### 5.4 Cálculo del BCR Final

**⚠️ IMPORTANTE: Cálculo Anual para Precisión**

Para un BCR preciso, debemos calcular sobre **costos anuales** y **horas facturables anuales**, no mensuales. Si solo usamos cálculo mensual (4.33 semanas/mes), ignoramos que el usuario no produce 12 meses al año, subestimando el BCR en ~8%.

**Fórmula CORRECTA (Anual - Recomendada):**
```typescript
const calculateFinalBCRAnnual = (
  totalMonthlyCosts: Decimal,
  billableHoursPerWeek: number,
  nonProductiveDaysPerYear: number = 20
): Decimal => {
  // Calcular costos anuales
  const totalAnnualCosts = totalMonthlyCosts * 12;
  
  // Calcular horas facturables anuales (considerando días no productivos)
  const productiveWeeksPerYear = 52 - (nonProductiveDaysPerYear / 5);
  const annualBillableHours = billableHoursPerWeek * productiveWeeksPerYear;
  
  if (annualBillableHours === 0) {
    return Decimal(0);
  }
  
  // BCR = Costos anuales / Horas facturables anuales
  return totalAnnualCosts / annualBillableHours;
};
```

**Fórmula SIMPLIFICADA (Mensual - Para comparación):**
```typescript
const calculateFinalBCRMonthly = (
  totalMonthlyCosts: Decimal,
  totalBillableHoursPerMonth: number
): Decimal => {
  if (totalBillableHoursPerMonth === 0) {
    return Decimal(0);
  }
  
  return totalMonthlyCosts / totalBillableHoursPerMonth;
};
```

**Ejemplo de Diferencia:**

Con costos mensuales de $8.342.350 COP y 28 horas facturables/semana:

**Cálculo Mensual (Incorrecto):**
- Horas/mes: 28 × 4.33 = 121 horas
- BCR: $8.342.350 ÷ 121 = **$68.925 COP/hora**

**Cálculo Anual (Correcto):**
- Horas/año: 28 × 48 semanas = 1,344 horas
- Costos/año: $8.342.350 × 12 = $100.108.200
- BCR: $100.108.200 ÷ 1,344 = **$74.485 COP/hora**

**Diferencia:** ~8% más alto con cálculo anual (más preciso y realista)

**Componentes:**
1. **Total de Costos Anuales:**
   - Nómina con cargas sociales (mensual × 12)
   - Costos fijos seleccionados (mensual × 12)
   - (Futuro: Amortización de equipos anual)

2. **Total de Horas Facturables Anuales:**
   - Horas facturables/semana × semanas productivas/año
   - Semanas productivas = 52 - (días no productivos ÷ 5)
   - Default: 48 semanas productivas (20 días de vacaciones/enfermedad)
   - Solo del usuario (en onboarding inicial)

### 5.5 Explicación Educativa

**Sección "¿Qué significa esto?"**

**Punto 1: Costo Mínimo**
```
Si cobras menos de $74.485/hora, estarás perdiendo dinero en cada proyecto.

Ejemplo:
• Proyecto de 10 horas × $50.000/hora = $500.000 ingresos
• Costo real: 10 horas × $74.485/hora = $744.850 costos
• Resultado: -$244.850 (pérdida)

⚠️ Si hubieras usado cálculo mensual ($68.925/hora), habrías pensado
   que el proyecto era rentable, pero en realidad estarías perdiendo
   dinero. Por eso usamos cálculo anual para mayor precisión.
```

**Punto 2: Margen de Utilidad**
```
Este es tu costo mínimo. Debes agregar un margen de utilidad
(recomendado: 30-50%) para obtener tu precio de venta sugerido.

Ejemplo con 40% de margen:
• BCR: $74.485/hora (cálculo anual preciso)
• Margen (40%): $29.794/hora
• Precio sugerido: $104.279/hora

💡 Nota: Este BCR considera días de vacaciones/enfermedad (48 semanas
   productivas en lugar de 52), por lo que es más realista y preciso
   que un cálculo mensual simple.
```

**Punto 3: Actualización Automática**
```
El BCR se actualizará automáticamente cuando:
• Agregues más miembros al equipo
• Cambies tus costos fijos
• Modifiques salarios o horas facturables

Siempre tendrás el costo real actualizado para cotizar correctamente.
```

### 5.6 Acciones Finales

**Botón "Crear mi Primera Cotización":**
- Redirige a `/projects/new`
- Muestra tooltip: "Usaremos tu BCR para calcular precios sugeridos"

**Botón "Ir al Dashboard":**
- Redirige a `/dashboard`
- Muestra resumen de la organización

**Botón "Editar Configuración" (opcional):**
- Permite volver a editar cualquier paso
- Guarda cambios y recalcula BCR

---

## 6. FLUJO COMPLETO DE DATOS

### 6.1 Secuencia de Llamadas al Backend

```
1. Usuario completa Paso 1 (Identidad)
   → POST /api/v1/organizations/register
   → Crea organización y usuario owner
   → Retorna: organization_id, access_token

2. Usuario completa Paso 2 (Costos Fijos)
   → POST /api/v1/organizations/{id}/costs/fixed
   → Crea múltiples CostFixed (uno por cada costo seleccionado)
   → Retorna: Array de CostFixedResponse

3. Usuario completa Paso 3 (Mi Equipo)
   → POST /api/v1/organizations/{id}/team
   → Crea TeamMember con datos del usuario
   → POST /api/v1/organizations/{id}/onboarding-config
   → Guarda configuración de cargas sociales
   → Retorna: TeamMemberResponse, OnboardingConfigResponse

4. Sistema calcula BCR (Paso 4)
   → GET /api/v1/calculations/blended-cost-rate
   → Calcula BCR con todos los datos
   → Retorna: BlendedCostRateResponse
```

### 6.2 Endpoints del Backend

#### Crear Organización (Paso 1)
**Endpoint:** `POST /api/v1/organizations/register`

**Request:**
```typescript
interface OrganizationRegisterRequest {
  organization_name: string;
  organization_slug?: string;
  admin_email: string;
  admin_full_name: string;
  admin_password: string;
  subscription_plan?: string;  // Default: "free"
}
```

**Response:**
```typescript
interface OrganizationRegisterResponse {
  organization: {
    id: number;
    name: string;
    slug: string;
    subscription_plan: string;
  };
  user: {
    id: number;
    email: string;
    full_name: string;
    role: string;
  };
  access_token: string;
  token_type: "bearer";
}
```

#### Obtener Templates de Costos (Paso 2)
**Endpoint:** `GET /api/v1/templates/industry/{industry_type}`

**O:** Usar templates hardcodeados en frontend (más rápido)

**Response:**
```typescript
interface IndustryTemplateResponse {
  id: number;
  industry_type: string;
  name: string;
  suggested_fixed_costs: Array<{
    name: string;
    amount_monthly: string;  // Decimal como string
    currency: string;
    category: string;
    description?: string;
  }>;
}
```

#### Crear Costos Fijos (Paso 2)
**Endpoint:** `POST /api/v1/organizations/{id}/costs/fixed`

**Request (múltiple):**
```typescript
interface CostFixedCreate {
  name: string;
  amount_monthly: string;  // Decimal como string
  currency: "COP" | "USD" | "ARS" | "EUR";
  category: "Overhead" | "Software" | "Tools" | "Other";
  description?: string;
}
```

#### Crear Miembro del Equipo (Paso 3)
**Endpoint:** `POST /api/v1/organizations/{id}/team`

**Request:**
```typescript
interface TeamMemberCreate {
  name: string;
  role: string;
  salary_monthly_brute: string;  // Decimal como string
  currency: "COP" | "USD" | "ARS" | "EUR";
  billable_hours_per_week: number;
  non_billable_hours_percentage: string;  // Decimal como string
  is_active: boolean;  // Default: true
}
```

#### Guardar Configuración de Onboarding (Paso 3)
**Endpoint:** `POST /api/v1/organizations/{id}/onboarding-config`

**Request:**
```typescript
interface OnboardingConfigRequest {
  social_charges_config?: {
    enable_social_charges: boolean;
    health_percentage: number;
    pension_percentage: number;
    arl_percentage: number;
    parafiscales_percentage: number;
    prima_services_percentage: number;
    cesantias_percentage: number;
    int_cesantias_percentage: number;
    vacations_percentage: number;
  };
  country?: string;
  currency?: string;
  profile_type?: string;
}
```

#### Calcular BCR (Paso 4)
**Endpoint:** `GET /api/v1/calculations/blended-cost-rate`

**Response:**
```typescript
interface BlendedCostRateResponse {
  blended_cost_rate: string;  // Decimal como string
  currency: string;
  breakdown: {
    total_monthly_costs: string;
    total_billable_hours_month: number;
    payroll_costs: {
      total: string;
      with_social_charges: string;
    };
    fixed_costs: {
      total: string;
      by_category: Array<{
        category: string;
        amount: string;
      }>;
    };
  };
  calculation_timestamp: string;  // ISO format
}
```

---

## 7. ESPECIFICACIONES DE DISEÑO

### 7.1 Paleta de Colores

```typescript
const ONBOARDING_COLORS = {
  primary: "#3B82F6",      // Azul (botones principales)
  success: "#10B981",      // Verde (completado, éxito)
  warning: "#F59E0B",       // Ámbar (advertencias)
  error: "#DC2626",        // Rojo (errores)
  info: "#3B82F6",         // Azul (información)
  
  // Stepper
  step_completed: "#10B981",
  step_active: "#3B82F6",
  step_pending: "#9CA3AF",
  
  // Cards
  card_border: "#E5E7EB",
  card_selected: "#DBEAFE",
  card_hover: "#F3F4F6",
  
  // BCR Display
  bcr_primary: "#1E40AF",  // Azul oscuro para valor principal
  bcr_background: "#EFF6FF", // Azul muy claro para fondo
};
```

### 7.2 Tipografía

- **H1 (Título Principal):** 32px, Bold
- **H2 (Títulos de Paso):** 24px, Semibold
- **H3 (Subtítulos):** 18px, Medium
- **Body (Texto normal):** 16px, Regular
- **Small (Texto secundario):** 14px, Regular
- **Caption (Tooltips):** 12px, Regular

### 7.3 Componentes UI Requeridos

#### Stepper (Barra de Progreso)
```
┌─────────────────────────────────────┐
│  [●]────[○]────[○]────[○]           │
│   1      2      3      4            │
│  Identidad  Mis Costos  Mi Equipo   │
└─────────────────────────────────────┘
```

**Estados:**
- Completado: Círculo azul sólido (●), línea azul
- Activo: Círculo azul con borde grueso, línea azul hasta aquí
- Pendiente: Círculo gris (○), línea gris

#### Card de Template (Paso 2)
```
┌──────────────────────┐
│ ☑️ Laptop            │
│                      │
│ $800.000 COP /mes    │
│                      │
│ [Ajustar]            │
└──────────────────────┘
```

**Estados:**
- Seleccionado: Checkbox marcado, borde azul, fondo azul claro
- No seleccionado: Checkbox vacío, borde gris, fondo blanco
- Hover: Sombra ligera, cursor pointer

#### Calculador de Horas de Realidad (Paso 3)
```
┌─────────────────────────────────────┐
│ 📊 Calculador de Horas de Realidad  │
│                                     │
│ Horas totales/semana: [40]          │
│                                     │
│ ⚠️ Horas facturables reales:        │
│ [28] horas/semana                   │
│                                     │
│ Desglose:                           │
│ • Reuniones: 5 horas                │
│ • Administración: 3 horas           │
│ • Capacitación: 2 horas             │
│ • Otros: 2 horas                    │
└─────────────────────────────────────┘
```

#### Display de BCR (Paso 4)
```
┌─────────────────────────────────────┐
│                                     │
│  Tu Costo por Hora Real (BCR)       │
│                                     │
│  ┌───────────────────────────────┐ │
│  │                               │ │
│  │    $75.000 COP / hora         │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

**Estilo:**
- Valor principal: 48px, Bold, color azul oscuro
- Fondo: Azul muy claro con borde azul
- Centrado, destacado

---

## 8. VALIDACIONES Y ESTADOS

### 8.1 Validaciones por Paso

**Paso 1:**
- Nombre de organización: requerido, 1-255 caracteres
- Moneda: requerido, debe ser una opción válida

**Paso 2:**
- Al menos 0 costos (puede continuar sin costos)
- Montos > 0 si se seleccionan costos
- Monedas válidas

**Paso 3:**
- Nombre: requerido
- Rol: requerido
- Salario: requerido, > 0
- Horas totales: requerido, > 0, <= 80
- Horas facturables: requerido, > 0, <= horas totales
- Advertencia si horas facturables < 20

**Paso 4:**
- No requiere validaciones (solo muestra resultados)

### 8.2 Estados de Error

**Error de Validación:**
```
┌─────────────────────────────────────┐
│ ❌ Error de Validación              │
│                                     │
│ Por favor completa todos los campos │
│ requeridos antes de continuar.      │
│                                     │
│ [Cerrar]                            │
└─────────────────────────────────────┘
```

**Error de Cálculo:**
```
┌─────────────────────────────────────┐
│ ⚠️ No se pudo calcular el BCR       │
│                                     │
│ Asegúrate de tener al menos:        │
│ • Un miembro del equipo              │
│ • Horas facturables > 0             │
│                                     │
│ [Revisar Configuración]             │
└─────────────────────────────────────┘
```

### 8.3 Estados de Carga

**Guardando Datos:**
```
┌─────────────────────────────────────┐
│ 🔄 Guardando configuración...       │
└─────────────────────────────────────┘
```

**Calculando BCR:**
```
┌─────────────────────────────────────┐
│ 🔄 Calculando tu costo por hora... │
└─────────────────────────────────────┘
```

---

## 9. PROMPT PARA FIGMA MAKE

```
Diseña un proceso de onboarding inicial para una plataforma de cotización que incluya los siguientes elementos:

**Estructura General:**
- Stepper superior con 4 pasos: 1. Identidad, 2. Mis Costos, 3. Mi Equipo, 4. ¡Listo!
- Barra de progreso visual siempre visible
- Botones de navegación: "Atrás" (pasos 2-4), "Siguiente" (todos), "Omitir por ahora" (opcional)

**Paso 1: Identidad**
- Título: "¡Bienvenido a Quotai!"
- Subtítulo: "Vamos a configurar tu estructura de costos en menos de 10 minutos"
- **Micro-copy de seguridad:** "🔒 Tus datos financieros están cifrados y solo se usan para calcular tus márgenes personales. Nadie más los verá." (texto pequeño, discreto, con icono de candado verde)
- Campo: Nombre de Organización (input, requerido)
- Campo: Moneda Primaria (dropdown: COP, USD, ARS, EUR)
- Campo: País (dropdown opcional)
- Tooltips explicativos en cada campo
- Botón "Siguiente" destacado

**Paso 2: Mis Costos (Templates)**
- Título: "¿Qué herramientas y servicios usas?"
- Subtítulo: "Selecciona los costos fijos que ya tienes. Puedes ajustar los precios después."
- **Quick Select por Industria:** Botones dinámicos cargados desde backend:
  • Quick Selects del sistema (predefinidos, no editables):
    - "Agencia de Marketing" → Pre-selecciona: Adobe CC, ChatGPT Plus, Hosting
    - "Desarrollo Web" → Pre-selecciona: GitHub, Figma, Hosting, ChatGPT Plus
    - "Agencia de Diseño" → Pre-selecciona: Adobe CC, Figma, Behance, Notion
    - "Consultoría" → Pre-selecciona: Notion, Zoom, Slack, ChatGPT Plus
  • Quick Selects personalizados (configurados por admin):
    - "Arquitectos" → Pre-selecciona: AutoCAD, Revit, SketchUp, Adobe CC, Notion, Hosting
    - "Agencia Audiovisual" → Pre-selecciona: Adobe CC, Premiere Pro, After Effects, Hosting
    - (Más según configuración del admin)
  • Cada botón muestra icono (emoji) y nombre de la industria
  • Color personalizable por Quick Select (hex)
  • "Otro / Personalizado" → Sin pre-selección
  • Los Quick Selects se cargan dinámicamente desde el backend (endpoint público)
  • Fallback a Quick Selects predefinidos si el backend no responde (endpoint público)
  • Fallback a Quick Selects predefinidos si el backend no responde
  • Cada botón puede tener icono (emoji) y color personalizado
- Grid de cards con templates sugeridos:
  • Cada card tiene: checkbox, icono, nombre, precio/mes, botón "Ajustar"
  • Badge "⚡ Pre-seleccionado" en templates del Quick Select
  • Categorías: Herramientas (💻 Laptop, 🖥️ Monitor), Software (🎨 Adobe CC, 🤖 ChatGPT Plus, 📝 Notion), Overhead (🏢 Coworking, 🌐 Internet, ☁️ Hosting)
  • **Multi-moneda:** Si costo está en moneda diferente a primaria, mostrar:
    - Advertencia visual (⚠️)
    - Conversión automática usando tipo de cambio en tiempo real
    - Última actualización del tipo de cambio
    - Botón "Actualizar tipo de cambio"
- Input de búsqueda para filtrar templates
- Botón "Agregar Costo Personalizado"
- Botón "Limpiar Selección" si se usó Quick Select
- Card de resumen siempre visible mostrando total mensual y desglose por categoría
- **Advertencia multi-moneda:** Si hay costos en múltiples monedas, mostrar advertencia sobre volatilidad de tipos de cambio
- Botones "Atrás" y "Siguiente"

**Paso 3: Mi Equipo (Calculador de Realidad)**
- Título: "Configura tu propio costo"
- Subtítulo: "Vamos a calcular cuánto te cuesta realmente tu hora de trabajo"
- **Nota destacada:** "⭐ El Calculador de Horas de Realidad es el activo más valioso del onboarding. La mayoría de freelancers y agencias subestiman su costo por no contar el tiempo administrativo."
- Campos: Nombre, Rol (dropdown), Salario Mensual Bruto
- Sección "Calculador de Horas de Realidad":
  • Input: "¿Cuántas horas trabajas a la semana?" (ej: 40)
  • Advertencia: "En realidad, entre reuniones y administración, solo facturarás aproximadamente:"
  • Input editable: Horas facturables/semana (calculado automáticamente: 28)
  • Desglose visual: Reuniones (5h), Administración (3h), Capacitación (2h), Otros (2h)
  • Botón "Ajustar Cálculo Manualmente"
- Sección "Días No Productivos (Vacaciones/Enfermedad)":
  • Input: "¿Cuántos días al año no trabajas?" (default: 20 días)
  • Explicación: "Para un BCR preciso, debemos considerar que no produces 12 meses al año. Si solo calculamos sobre 4.33 semanas/mes, subestimamos el BCR en ~8%."
  • Card mostrando: Semanas productivas (48), Horas facturables/año (1,344)
- Sección "Cargas Sociales (Colombia)":
  • Toggle: "Aplicar cargas sociales"
  • Desglose visual con cada carga (Salud 8.5%, Pensión 12%, etc.)
  • Total: "Salario con Cargas: $7.342.350 COP"
- **Validación de Salario de Mercado (Solo para Dueños):**
  • Si usuario es "owner" y salario < mínimo de mercado:
    - Bloquear continuación
    - Mostrar modal explicativo del "Costo de Oportunidad"
    - Sugerir salario de mercado (mediana)
    - Explicar importancia: BCR realista, escalabilidad
  • Si salario < mediana de mercado: Mostrar advertencia (no bloquear)
  • Permitir continuar con advertencia persistente si usuario insiste
- Card de resumen: "Tu Costo por Hora: $65.556 COP/hora (cálculo anual preciso, sin incluir costos fijos)"
- Advertencia: "Si solo usáramos cálculo mensual, sería $60.680/hora (subestimado en ~8%)"
- Botones "Atrás" y "Siguiente"

**Paso 4: ¡Listo! (BCR Final)**
- Título celebratorio: "🎉 ¡Listo! Tu estructura de costos está configurada"
- Card grande destacado con BCR:
  • Valor principal grande: "$74.485 COP / hora"
  • Texto: "Este es el mínimo que debes cobrar por hora para ser rentable"
- Sección "Desglose del Cálculo (Interactivo)":
  • Card: Costos Anuales Totales (Nómina + Costos Fijos) - Estático
  • Card: Horas Facturables Anuales - **INTERACTIVO con Slider**
    - Slider para ajustar horas facturables/semana (15-40 horas)
    - Cálculo en tiempo real de horas anuales
    - Actualización visual mientras se arrastra el slider
  • Card: Fórmula del BCR - **ACTUALIZA EN TIEMPO REAL**
    - BCR se recalcula automáticamente al mover el slider
    - Animación de "pulse" cuando BCR cambia
    - Comparaciones contextuales: "Si trabajas 20h/semana: $X/hora"
    - Mensaje educativo dinámico según horas seleccionadas
- Sección educativa "💡 ¿Qué significa esto?":
  • 3 puntos explicativos con ejemplos
- Botones: "Crear mi Primera Cotización" (primary), "Ir al Dashboard" (secondary)

**Paleta de Colores:**
- Primario: #3B82F6 (Azul)
- Éxito: #10B981 (Verde)
- Advertencia: #F59E0B (Ámbar)
- Stepper completado: Verde
- Stepper activo: Azul
- Stepper pendiente: Gris

**Tipografía:**
- Títulos: 24-32px, Bold/Semibold
- Valores principales (BCR): 48px, Bold
- Texto normal: 16px, Regular

**Estados a Diseñar:**
- Cargando (spinners)
- Error (mensajes de error)
- Validación (errores inline)
- Éxito (checkmarks, celebración)
- Hover (cards, botones)
- Seleccionado (templates)
- Pre-seleccionado (templates del Quick Select)
- Interactivo (slider en Paso 4, actualización en tiempo real)
- Animación de actualización (BCR cambiando mientras se mueve slider)

**Pantalla Adicional: Administración de Quick Selects (Solo para Super Admin)**
- Título: "Administración de Quick Selects"
- Subtítulo: "Gestiona los Quick Selects personalizados que aparecen en el onboarding"
- Botón destacado: "Crear Nuevo Quick Select"
- Lista de Quick Selects Activos:
  • Cada item muestra: Icono, Nombre, Descripción, Cantidad de templates, Badge "Sistema" o "Personalizado"
  • Acciones disponibles:
    - Quick Selects del Sistema: Solo [Desactivar] (no editable ni eliminable)
    - Quick Selects Personalizados: [Editar] y [Eliminar]
- Lista de Quick Selects Desactivados (si los hay)
- Modal de Crear/Editar Quick Select:
  • Campos: Clave Única (ID), Nombre para Mostrar, Descripción, Icono (emoji), Color (color picker)
  • Sección "Templates a Pre-seleccionar":
    - Búsqueda de templates disponibles
    - Lista de templates con checkboxes
    - Contador de templates seleccionados
    - Vista previa de templates seleccionados
  • Botones: [Cancelar] y [Guardar Quick Select]
- Validaciones visuales:
  • Error si `industry_key` ya existe
  • Error si no se selecciona al menos 1 template
  • Advertencia si se intenta editar Quick Select del sistema
```

---

## 10. VALIDACIÓN DE DATOS Y EDGE CASES (Data Analysis Perspective)

### 10.1 Multi-Moneda: Conversión en Tiempo Real

**Problema Identificado:**
En el Paso 2, se permite seleccionar costos en diferentes monedas (ej: ChatGPT en USD dentro de una organización en COP). Si el sistema no consume una API de tipo de cambio en tiempo real, el BCR puede desactualizarse rápidamente.

**Impacto:**
- Si el usuario configura costos hoy y el dólar sube un 10% mañana, su BCR estará desactualizado
- Los costos fijos en moneda extranjera pueden variar significativamente sin actualización
- Esto lleva a cotizaciones incorrectas y pérdidas financieras

**Solución Implementada:**

#### Conversión en Tiempo Real
```typescript
interface ExchangeRateService {
  /**
   * Obtiene tipo de cambio actual desde API externa
   * Recomendado: Fixer.io, ExchangeRate-API, o similar
   */
  getCurrentRate(
    fromCurrency: string,
    toCurrency: string
  ): Promise<ExchangeRate>;
  
  /**
   * Convierte monto de una moneda a otra usando tipo de cambio actual
   */
  convert(
    amount: Decimal,
    fromCurrency: string,
    toCurrency: string
  ): Promise<Money>;
}

interface ExchangeRate {
  from: string;
  to: string;
  rate: Decimal;
  timestamp: Date;
  source: "fixer" | "exchange_rate_api" | "manual";
}
```

#### Validaciones en Paso 2
```typescript
// Al seleccionar un costo en moneda diferente a la primaria
if (cost.currency !== primaryCurrency) {
  // 1. Mostrar advertencia visual
  showWarning({
    message: `Este costo está en ${cost.currency}, pero tu moneda primaria es ${primaryCurrency}`,
    details: "Se convertirá automáticamente usando tipo de cambio actual",
    action: "Ver tipo de cambio actual"
  });
  
  // 2. Obtener tipo de cambio en tiempo real
  const exchangeRate = await exchangeRateService.getCurrentRate(
    cost.currency,
    primaryCurrency
  );
  
  // 3. Mostrar conversión
  const convertedAmount = await exchangeRateService.convert(
    cost.amount_monthly,
    cost.currency,
    primaryCurrency
  );
  
  // 4. Mostrar en UI
  displayConversion({
    original: `${cost.amount_monthly} ${cost.currency}`,
    converted: `${convertedAmount.amount} ${primaryCurrency}`,
    rate: `1 ${cost.currency} = ${exchangeRate.rate} ${primaryCurrency}`,
    lastUpdated: exchangeRate.timestamp
  });
}
```

#### Actualización Automática de Tipos de Cambio
```typescript
/**
 * Estrategia de actualización:
 * 1. Al cargar onboarding: Obtener tipos de cambio actuales
 * 2. Al calcular BCR: Usar tipos de cambio más recientes (cache de 1 hora)
 * 3. Advertencia si tipo de cambio tiene más de 24 horas
 */
const EXCHANGE_RATE_CACHE_TTL = 3600; // 1 hora en segundos
const EXCHANGE_RATE_WARNING_THRESHOLD = 86400; // 24 horas

// Al calcular BCR
const calculateBCRWithMultiCurrency = async (
  costs: CostFixed[],
  primaryCurrency: string
): Promise<Decimal> => {
  const now = Date.now();
  
  for (const cost of costs) {
    if (cost.currency !== primaryCurrency) {
      // Verificar si tenemos tipo de cambio reciente
      const cachedRate = await getCachedExchangeRate(
        cost.currency,
        primaryCurrency
      );
      
      if (!cachedRate || (now - cachedRate.timestamp) > EXCHANGE_RATE_CACHE_TTL) {
        // Obtener nuevo tipo de cambio
        const freshRate = await exchangeRateService.getCurrentRate(
          cost.currency,
          primaryCurrency
        );
        await cacheExchangeRate(freshRate);
      }
      
      // Advertencia si tipo de cambio es antiguo
      if (cachedRate && (now - cachedRate.timestamp) > EXCHANGE_RATE_WARNING_THRESHOLD) {
        showWarning({
          message: `Tipo de cambio ${cost.currency}/${primaryCurrency} tiene más de 24 horas`,
          action: "Actualizar ahora"
        });
      }
    }
  }
  
  // Continuar con cálculo normal...
};
```

#### UI para Multi-Moneda

**Card de Costo con Moneda Diferente:**
```
┌─────────────────────────────────────┐
│ ☑️ ChatGPT Plus                     │
│                                     │
│ $20 USD /mes                        │
│ ⚠️ Moneda diferente a COP           │
│                                     │
│ Conversión actual:                 │
│ $20 USD = $80.000 COP              │
│ (1 USD = $4.000 COP)               │
│                                     │
│ Última actualización: Hace 2 horas │
│ [Actualizar tipo de cambio]        │
│                                     │
│ [Ajustar]                           │
└─────────────────────────────────────┘
```

**Advertencia en Resumen:**
```
⚠️ Atención: Tienes costos en múltiples monedas.
   Los tipos de cambio se actualizan automáticamente,
   pero pueden variar. Revisa periódicamente.
```

#### Recomendaciones de Implementación

**APIs Recomendadas:**
1. **Fixer.io** (Recomendado)
   - Plan gratuito: 100 requests/mes
   - Tipos de cambio actualizados cada hora
   - Soporte para 170+ monedas

2. **ExchangeRate-API**
   - Plan gratuito: 1,500 requests/mes
   - Sin API key requerida para plan básico
   - Actualización diaria

3. **CurrencyLayer**
   - Plan gratuito: 1,000 requests/mes
   - Actualización cada hora

**Estrategia de Cache:**
- Cachear tipos de cambio por 1 hora
- Invalidar cache automáticamente después de TTL
- Mostrar advertencia si tipo de cambio tiene > 24 horas
- Permitir actualización manual con botón "Actualizar"

**Validaciones:**
- Validar que API de tipo de cambio esté disponible
- Fallback a último tipo de cambio conocido si API falla
- Mostrar advertencia si conversión falla
- Permitir entrada manual de tipo de cambio como fallback

### 10.2 El "Costo de Oportunidad": Salario de Mercado para Dueños

**Problema Identificado:**
Si el usuario es el dueño, a veces no se asigna un salario bruto real, sino que vive de las "utilidades". Esto lleva a un BCR artificialmente bajo y la empresa nunca será escalable.

**Impacto:**
- BCR calculado sin considerar el costo real del dueño
- Cotizaciones que parecen rentables pero no lo son
- Imposibilidad de escalar (no hay margen para contratar reemplazo del dueño)
- Modelo de negocio insostenible

**Solución Implementada:**

#### Validación de Salario de Mercado
```typescript
interface SalaryMarketValidation {
  /**
   * Valida que el salario del dueño sea razonable según mercado
   */
  validateOwnerSalary(
    role: string,
    salary: Decimal,
    currency: string,
    country: string
  ): ValidationResult;
  
  /**
   * Obtiene rango salarial de mercado para un rol
   */
  getMarketSalaryRange(
    role: string,
    country: string,
    currency: string
  ): Promise<SalaryRange>;
}

interface ValidationResult {
  isValid: boolean;
  severity: "error" | "warning" | "info";
  message: string;
  suggestedSalary?: Decimal;
  marketRange?: SalaryRange;
}

interface SalaryRange {
  min: Decimal;
  median: Decimal;
  max: Decimal;
  source: string; // "glassdoor", "payscale", "local_market"
}
```

#### Lógica de Validación
```typescript
const validateOwnerSalary = async (
  role: string,
  salary: Decimal,
  currency: string,
  country: string
): Promise<ValidationResult> => {
  // Obtener rango salarial de mercado
  const marketRange = await salaryMarketService.getMarketSalaryRange(
    role,
    country,
    currency
  );
  
  // Validar si salario está por debajo del mínimo de mercado
  if (salary < marketRange.min) {
    return {
      isValid: false,
      severity: "error",
      message: `Tu salario ($${salary} ${currency}) está por debajo del mínimo de mercado ($${marketRange.min} ${currency})`,
      suggestedSalary: marketRange.median, // Sugerir mediana
      marketRange
    };
  }
  
  // Advertencia si está por debajo de la mediana
  if (salary < marketRange.median) {
    return {
      isValid: true,
      severity: "warning",
      message: `Tu salario está por debajo de la mediana de mercado ($${marketRange.median} ${currency})`,
      suggestedSalary: marketRange.median,
      marketRange
    };
  }
  
  return {
    isValid: true,
    severity: "info",
    message: "Tu salario está dentro del rango de mercado",
    marketRange
  };
};
```

#### UI para Validación de Salario

**Advertencia en Paso 3:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ Validación de Salario de Mercado                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Tu salario actual: $2.000.000 COP /mes                     │
│                                                              │
│  Rango de mercado para "Diseñador UI/UX" en Colombia:       │
│  • Mínimo: $3.500.000 COP /mes                              │
│  • Mediana: $5.000.000 COP /mes                             │
│  • Máximo: $8.000.000 COP /mes                              │
│                                                              │
│  💡 Como dueño, debes asignarte un salario de mercado        │
│     para que tu BCR sea realista y escalable.                │
│                                                              │
│  Si no te asignas un salario adecuado:                      │
│  • Tu BCR será artificialmente bajo                         │
│  • No podrás escalar (no hay margen para contratar)         │
│  • Tu empresa nunca será sostenible                         │
│                                                              │
│  [Usar Salario Sugerido: $5.000.000 COP]                    │
│  [Continuar con Salario Actual] (no recomendado)            │
└─────────────────────────────────────────────────────────────┘
```

**Modal de Explicación:**
```
┌─────────────────────────────────────────────────────────────┐
│  ¿Por qué necesito un salario de mercado?               [×] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  💼 El "Costo de Oportunidad"                               │
│                                                              │
│  Como dueño, puedes pensar: "No me pago salario, vivo de    │
│  las utilidades". Pero esto es un error común que lleva a:  │
│                                                              │
│  ❌ BCR Artificialmente Bajo                                │
│     Si no incluyes tu costo real, tu BCR será muy bajo y    │
│     cotizarás proyectos que parecen rentables pero no lo    │
│     son cuando consideras tu tiempo.                        │
│                                                              │
│  ❌ Imposibilidad de Escalar                                │
│     Si tu BCR no incluye tu salario de mercado, no tendrás │
│     margen para contratar a alguien que te reemplace.       │
│     Tu empresa nunca podrá crecer sin ti.                   │
│                                                              │
│  ✅ Solución: Salario de Mercado                            │
│     Asígnate el salario que pagarías a alguien con tu      │
│     experiencia y rol. Esto hace tu BCR realista y tu       │
│     empresa escalable.                                      │
│                                                              │
│  Ejemplo:                                                    │
│  • Si eres Diseñador UI/UX Senior, asigna $5.000.000 COP    │
│  • Si eres Desarrollador Full Stack, asigna $6.000.000 COP │
│  • Si eres Product Manager, asigna $7.000.000 COP           │
│                                                              │
│  [Entendido, Usar Salario Sugerido]                         │
└─────────────────────────────────────────────────────────────┘
```

#### Fuentes de Datos de Mercado

**APIs Recomendadas:**
1. **Glassdoor API** (si disponible)
   - Datos salariales por rol y ubicación
   - Actualización periódica

2. **Payscale API**
   - Datos de compensación por mercado
   - Incluye beneficios y bonos

3. **Datos Locales (Colombia)**
   - Encuestas de salarios locales
   - Datos de Cámara de Comercio
   - Bases de datos de reclutamiento local

**Fallback:**
- Si no hay API disponible, usar rangos predefinidos por rol y país
- Permitir entrada manual con advertencia
- Mostrar ejemplos de rangos comunes

#### Validaciones en Paso 3

**Al ingresar salario:**
```typescript
// Si el usuario es "owner" y el salario es muy bajo
if (userRole === "owner" && salary < marketRange.min) {
  // 1. Bloquear continuación hasta que ajuste
  blockContinue({
    reason: "salary_below_market",
    message: "Como dueño, debes asignarte un salario de mercado",
    requiredAction: "adjust_salary"
  });
  
  // 2. Mostrar modal explicativo
  showModal({
    title: "Salario de Mercado Requerido",
    content: explanationModal,
    actions: [
      { label: "Usar Salario Sugerido", action: "use_suggested" },
      { label: "Entiendo los riesgos", action: "continue_anyway" }
    ]
  });
  
  // 3. Si continúa de todas formas, mostrar advertencia persistente
  if (userChoosesContinueAnyway) {
    showPersistentWarning({
      message: "Tu BCR puede estar subestimado. Revisa tus cotizaciones cuidadosamente.",
      dismissible: false
    });
  }
}
```

**Rangos Predefinidos (Colombia - COP):**
```typescript
const MARKET_SALARY_RANGES_COLOMBIA: Record<string, SalaryRange> = {
  "Diseñador UI/UX": {
    min: 3500000,
    median: 5000000,
    max: 8000000
  },
  "Desarrollador Frontend": {
    min: 4000000,
    median: 6000000,
    max: 10000000
  },
  "Desarrollador Backend": {
    min: 4500000,
    median: 6500000,
    max: 11000000
  },
  "Product Manager": {
    min: 5000000,
    median: 7000000,
    max: 12000000
  },
  "CEO/Founder": {
    min: 6000000,
    median: 10000000,
    max: 20000000
  }
};
```

### 10.3 Resumen de Validaciones Críticas

**Checklist de Validaciones:**

- [ ] **Multi-Moneda:**
  - [ ] API de tipo de cambio configurada y funcionando
  - [ ] Conversión automática al seleccionar costo en moneda diferente
  - [ ] Cache de tipos de cambio (TTL: 1 hora)
  - [ ] Advertencia si tipo de cambio tiene > 24 horas
  - [ ] Botón para actualizar tipos de cambio manualmente
  - [ ] Fallback si API falla

- [ ] **Salario de Mercado (Dueños):**
  - [ ] Detectar si usuario es "owner"
  - [ ] Validar salario contra rango de mercado
  - [ ] Bloquear continuación si salario < mínimo de mercado
  - [ ] Mostrar modal explicativo del "Costo de Oportunidad"
  - [ ] Sugerir salario de mercado (mediana)
  - [ ] Permitir continuar con advertencia persistente si insiste
  - [ ] Mostrar advertencia en dashboard si BCR parece bajo

- [ ] **Otros Edge Cases:**
  - [ ] Validar que horas facturables > 0
  - [ ] Validar que costos mensuales > 0 (o mostrar advertencia)
  - [ ] Validar que días no productivos sean razonables (10-30 días)
  - [ ] Validar que organización tenga al menos un miembro del equipo

---

## 11. SUGERENCIAS TÉCNICAS PARA EL FRONTEND

### 11.1 Paso 2: Quick Select por Industria

**Objetivo:** Reducir fricción y aumentar tasa de finalización del onboarding mediante pre-selección inteligente de templates basada en industria.

**Problema que Resuelve:**
- Usuarios deben hacer múltiples clics para seleccionar templates manualmente
- Pueden olvidar costos importantes o no saber qué seleccionar
- Mayor fricción = menor tasa de finalización

**Solución: Quick Select por Industria**

**Características:**
- Quick Selects predefinidos (Marketing, Desarrollo Web, Diseño, Consultoría)
- **Quick Selects personalizables por Admin** (ej: Arquitectos, Agencias Audiovisuales, etc.)
- Templates dinámicos cargados desde backend
- Configuración centralizada para fácil mantenimiento

#### Implementación

**Componente UI:**
```
┌─────────────────────────────────────────────────────────────┐
│  ¿Qué herramientas y servicios usas?                        │
│                                                              │
│  💡 Quick Select: Elige tu industria para pre-seleccionar  │
│     los costos más comunes                                  │
│                                                              │
│  [Agencia de Marketing] [Desarrollo Web] [Diseño] [Otro]   │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  Templates (3 pre-seleccionados):                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ☑️ Adobe CC   │  │ ☑️ ChatGPT    │  │ ☑️ Hosting    │     │
│  │ (pre-selec.) │  │ (pre-selec.) │  │ (pre-selec.) │     │
│  │              │  │              │  │              │     │
│  │ $150.000 COP │  │ $80.000 COP  │  │ $50.000 COP  │     │
│  │ /mes         │  │ /mes         │  │ /mes         │     │
│  │              │  │              │  │              │     │
│  │ [Ajustar]    │  │ [Ajustar]    │  │ [Ajustar]    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  [Limpiar Selección] [Ver Todos los Templates]             │
└─────────────────────────────────────────────────────────────┘
```

**Lógica de Pre-selección por Industria:**

```typescript
interface IndustryQuickSelect {
  industry: string;
  preselectedTemplates: string[]; // IDs de templates a pre-seleccionar
  description: string;
}

// Quick Selects predefinidos (hardcodeados en frontend como fallback)
const DEFAULT_INDUSTRY_QUICK_SELECTS: Record<string, IndustryQuickSelect> = {
  "marketing_agency": {
    industry: "Agencia de Marketing",
    preselectedTemplates: [
      "adobe_cc",        // Adobe Creative Cloud
      "chatgpt_plus",    // ChatGPT Plus
      "hosting",         // Hosting Web
      "notion",          // Notion Pro
      "canva"            // Canva Pro (si está disponible)
    ],
    description: "Pre-selecciona herramientas comunes para agencias de marketing"
  },
  "web_development": {
    industry: "Desarrollo Web",
    preselectedTemplates: [
      "github",          // GitHub (si está disponible)
      "figma",           // Figma Professional
      "hosting",         // Hosting Web
      "chatgpt_plus",    // ChatGPT Plus
      "vscode_live"      // VS Code Live Share (si está disponible)
    ],
    description: "Pre-selecciona herramientas comunes para desarrollo web"
  },
  "design_agency": {
    industry: "Agencia de Diseño",
    preselectedTemplates: [
      "adobe_cc",        // Adobe Creative Cloud
      "figma",           // Figma Professional
      "behance",         // Behance Pro (si está disponible)
      "notion",          // Notion Pro
      "dropbox"          // Dropbox Business (si está disponible)
    ],
    description: "Pre-selecciona herramientas comunes para agencias de diseño"
  },
  "consulting": {
    industry: "Consultoría",
    preselectedTemplates: [
      "notion",          // Notion Pro
      "zoom",            // Zoom Pro (si está disponible)
      "slack",           // Slack (si está disponible)
      "chatgpt_plus",    // ChatGPT Plus
      "calendly"         // Calendly (si está disponible)
    ],
    description: "Pre-selecciona herramientas comunes para consultoría"
  }
};

// Función para cargar Quick Selects desde backend (dinámicos + predefinidos)
const loadIndustryQuickSelects = async (): Promise<Record<string, IndustryQuickSelect>> => {
  try {
    // Intentar cargar desde backend
    const response = await fetch('/api/v1/admin/quick-selects/onboarding');
    if (response.ok) {
      const customQuickSelects = await response.json();
      // Combinar con predefinidos (custom tiene prioridad)
      return { ...DEFAULT_INDUSTRY_QUICK_SELECTS, ...customQuickSelects };
    }
  } catch (error) {
    console.warn('No se pudieron cargar Quick Selects personalizados, usando predefinidos');
  }
  
  // Fallback a predefinidos
  return DEFAULT_INDUSTRY_QUICK_SELECTS;
};

// Función para aplicar Quick Select
const applyQuickSelect = (
  industry: string,
  availableTemplates: Template[]
): Template[] => {
  const quickSelect = INDUSTRY_QUICK_SELECTS[industry];
  
  if (!quickSelect) {
    return []; // No hay pre-selección para esta industria
  }
  
  // Filtrar templates disponibles que están en la lista de pre-selección
  const preselected = availableTemplates.filter(template =>
    quickSelect.preselectedTemplates.includes(template.id)
  );
  
  // Marcar como pre-seleccionados
  return preselected.map(template => ({
    ...template,
    isPreselected: true,
    isSelected: true
  }));
};
```

**Flujo de Usuario:**

1. Usuario llega al Paso 2
2. Ve botones de "Quick Select" por industria
3. Hace click en "Agencia de Marketing"
4. Sistema pre-selecciona automáticamente: Adobe CC, ChatGPT Plus, Hosting
5. Templates aparecen con badge "pre-seleccionado"
6. Usuario puede:
   - Deseleccionar templates que no aplican
   - Agregar más templates manualmente
   - Cambiar de industria (limpia selección anterior)
   - Ver todos los templates disponibles

**Beneficios:**

- **Menos Clics:** De ~10-15 clics a 1-2 clics
- **Mayor Tasa de Finalización:** Reduce fricción significativamente
- **Mejor UX:** Usuario ve progreso inmediato
- **Educativo:** Usuario aprende qué herramientas son comunes en su industria

**Implementación Técnica:**

```typescript
// Componente React/Next.js
const QuickSelectIndustry = ({ onSelect }: Props) => {
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);
  
  const handleIndustrySelect = (industry: string) => {
    setSelectedIndustry(industry);
    const preselected = applyQuickSelect(industry, availableTemplates);
    onSelect(preselected); // Notificar al componente padre
  };
  
  return (
    <div className="quick-select-container">
      <p className="quick-select-description">
        💡 Quick Select: Elige tu industria para pre-seleccionar los costos más comunes
      </p>
      <div className="industry-buttons">
        {Object.values(INDUSTRY_QUICK_SELECTS).map((quickSelect) => (
          <button
            key={quickSelect.industry}
            onClick={() => handleIndustrySelect(quickSelect.industry)}
            className={selectedIndustry === quickSelect.industry ? 'selected' : ''}
          >
            {quickSelect.industry}
          </button>
        ))}
        <button onClick={() => handleIndustrySelect('custom')}>
          Otro / Personalizado
        </button>
      </div>
      
      {selectedIndustry && (
        <div className="preselected-info">
          <p>
            ✅ Pre-seleccionados {INDUSTRY_QUICK_SELECTS[selectedIndustry].preselectedTemplates.length} templates
          </p>
          <button onClick={() => setSelectedIndustry(null)}>
            Limpiar Selección
          </button>
        </div>
      )}
    </div>
  );
};
```

**Badge Visual para Templates Pre-seleccionados:**

```typescript
// En el card de template
{template.isPreselected && (
  <span className="preselected-badge">
    ⚡ Pre-seleccionado
  </span>
)}
```

**Estados Visuales:**

- **Botón de Industria Seleccionado:** Fondo azul, texto blanco, borde destacado
- **Templates Pre-seleccionados:** Badge "⚡ Pre-seleccionado", checkbox marcado automáticamente
- **Animación:** Fade-in suave cuando se aplica Quick Select

### 11.2 Paso 4: Desglose Interactivo con Slider

**Objetivo:** Gamificación financiera mediante interacción en tiempo real que refuerza el aprendizaje educativo.

**Problema que Resuelve:**
- Usuarios no entienden cómo sus decisiones afectan el BCR
- El desglose es estático y no permite experimentación
- Falta de engagement educativo

**Solución: Desglose Interactivo con Cálculo en Tiempo Real**

#### Implementación

**Componente UI Interactivo:**

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Desglose del Cálculo (Interactivo)                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Costos Anuales Totales                                 │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │  Nómina (con cargas):     $88.108.200 COP /año          │ │
│  │  Costos Fijos:            $12.000.000 COP /año          │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │  Total Anual:             $100.108.200 COP              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Horas Facturables Anuales (Ajustable)                   │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │                                                          │ │
│  │  Horas facturables/semana:                               │ │
│  │  [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] │ │
│  │  20 ←→ 28 ←→ 35                                          │ │
│  │        ↑                                                 │ │
│  │        Actual                                            │ │
│  │                                                          │ │
│  │  Semanas productivas/año: 48 semanas                    │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │  Total Horas/año:         1,344 horas                    │ │
│  │  (28 horas/semana × 48 semanas)                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Fórmula del BCR (Cálculo en Tiempo Real)                │ │
│  │  ────────────────────────────────────────────────────── │ │
│  │                                                          │ │
│  │  BCR = Costos Anuales ÷ Horas Facturables Anuales       │ │
│  │                                                          │ │
│  │  BCR = $100.108.200 ÷ 1,344 horas                       │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │                                                    │ │ │
│  │  │          $74.485 COP / hora                       │ │ │
│  │  │                                                    │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │  💡 Mueve el slider para ver cómo cambia tu BCR         │ │
│  │                                                          │ │
│  │  Si trabajas 20 horas/semana: $89.382 COP/hora        │ │
│  │  Si trabajas 35 horas/semana: $59.647 COP/hora        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Lógica de Cálculo en Tiempo Real:**

```typescript
interface InteractiveBCRCalculator {
  totalAnnualCosts: Decimal;
  productiveWeeksPerYear: number;
  billableHoursPerWeek: number;
  
  calculateBCR(hoursPerWeek: number): Decimal;
  getBCRForRange(min: number, max: number, step: number): Array<{
    hours: number;
    bcr: Decimal;
  }>;
}

class InteractiveBCRCalculator implements InteractiveBCRCalculator {
  constructor(
    public totalAnnualCosts: Decimal,
    public productiveWeeksPerYear: number = 48
  ) {}
  
  calculateBCR(hoursPerWeek: number): Decimal {
    const annualBillableHours = hoursPerWeek * this.productiveWeeksPerYear;
    
    if (annualBillableHours === 0) {
      return Decimal(0);
    }
    
    return this.totalAnnualCosts / annualBillableHours;
  }
  
  getBCRForRange(min: number, max: number, step: number): Array<{
    hours: number;
    bcr: Decimal;
  }> {
    const results = [];
    
    for (let hours = min; hours <= max; hours += step) {
      results.push({
        hours,
        bcr: this.calculateBCR(hours)
      });
    }
    
    return results;
  }
}
```

**Componente React/Next.js:**

```typescript
const InteractiveBCRBreakdown = ({ 
  totalAnnualCosts, 
  initialHoursPerWeek,
  productiveWeeksPerYear = 48 
}: Props) => {
  const [hoursPerWeek, setHoursPerWeek] = useState(initialHoursPerWeek);
  const [isDragging, setIsDragging] = useState(false);
  
  const calculator = new InteractiveBCRCalculator(
    totalAnnualCosts,
    productiveWeeksPerYear
  );
  
  const currentBCR = calculator.calculateBCR(hoursPerWeek);
  const annualHours = hoursPerWeek * productiveWeeksPerYear;
  
  // Calcular comparaciones para mostrar contexto
  const comparison20 = calculator.calculateBCR(20);
  const comparison35 = calculator.calculateBCR(35);
  
  const handleSliderChange = (value: number) => {
    setHoursPerWeek(value);
    setIsDragging(true);
  };
  
  const handleSliderRelease = () => {
    setIsDragging(false);
    // Opcional: Guardar nuevo valor si usuario quiere persistir
  };
  
  return (
    <div className="interactive-bcr-breakdown">
      {/* Costos Anuales (estático) */}
      <CostBreakdownCard costs={totalAnnualCosts} />
      
      {/* Horas Facturables (interactivo) */}
      <div className="interactive-hours-card">
        <h3>Horas Facturables Anuales (Ajustable)</h3>
        
        <div className="slider-container">
          <label>
            Horas facturables/semana: <strong>{hoursPerWeek} horas</strong>
          </label>
          
          <input
            type="range"
            min={15}
            max={40}
            step={1}
            value={hoursPerWeek}
            onChange={(e) => handleSliderChange(Number(e.target.value))}
            onMouseUp={handleSliderRelease}
            onTouchEnd={handleSliderRelease}
            className="hours-slider"
          />
          
          <div className="slider-labels">
            <span>15</span>
            <span className="current-value">{hoursPerWeek}</span>
            <span>40</span>
          </div>
        </div>
        
        <div className="hours-calculation">
          <p>
            Semanas productivas/año: <strong>{productiveWeeksPerYear} semanas</strong>
          </p>
          <p>
            Total Horas/año: <strong>{annualHours.toLocaleString()} horas</strong>
            <br />
            <small>({hoursPerWeek} horas/semana × {productiveWeeksPerYear} semanas)</small>
          </p>
        </div>
      </div>
      
      {/* Fórmula del BCR (actualiza en tiempo real) */}
      <div className={`bcr-formula-card ${isDragging ? 'updating' : ''}`}>
        <h3>Fórmula del BCR (Cálculo en Tiempo Real)</h3>
        
        <div className="formula-display">
          <p>BCR = Costos Anuales ÷ Horas Facturables Anuales</p>
          <p className="formula-calculation">
            BCR = {formatCurrency(totalAnnualCosts)} ÷ {annualHours.toLocaleString()} horas
          </p>
        </div>
        
        <div className="bcr-result">
          <div className="bcr-value-large">
            {formatCurrency(currentBCR)} / hora
          </div>
          {isDragging && (
            <div className="updating-indicator">
              🔄 Calculando...
            </div>
          )}
        </div>
        
        {/* Comparaciones educativas */}
        <div className="bcr-comparisons">
          <p className="comparison-label">
            💡 Mueve el slider para ver cómo cambia tu BCR
          </p>
          <div className="comparison-items">
            <div className="comparison-item">
              <span>Si trabajas 20 horas/semana:</span>
              <strong>{formatCurrency(comparison20)}/hora</strong>
            </div>
            <div className="comparison-item">
              <span>Si trabajas 35 horas/semana:</span>
              <strong>{formatCurrency(comparison35)}/hora</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
```

**Efectos Visuales:**

```css
/* Animación cuando BCR se actualiza */
.bcr-formula-card.updating .bcr-value-large {
  animation: pulse 0.3s ease-in-out;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* Slider styling */
.hours-slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(to right, #3B82F6, #10B981);
  outline: none;
  -webkit-appearance: none;
}

.hours-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #3B82F6;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.hours-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  transition: transform 0.2s;
}
```

**Gamificación Financiera:**

**Elementos de Gamificación:**
1. **Feedback Inmediato:** BCR se actualiza en tiempo real mientras mueves el slider
2. **Comparaciones Contextuales:** Muestra cómo sería el BCR con diferentes horas
3. **Visualización de Impacto:** Usuario ve directamente cómo sus decisiones afectan el costo
4. **Aprendizaje por Experimentación:** Usuario puede "jugar" con diferentes escenarios

**Mensajes Educativos Dinámicos:**

```typescript
const getEducationalMessage = (hoursPerWeek: number, bcr: Decimal): string => {
  if (hoursPerWeek < 20) {
    return `⚠️ Con ${hoursPerWeek} horas/semana, tu BCR es alto. Considera aumentar tus horas facturables para ser más competitivo.`;
  } else if (hoursPerWeek > 35) {
    return `💡 Con ${hoursPerWeek} horas/semana, tu BCR es bajo. Asegúrate de que este número sea realista y sostenible.`;
  } else {
    return `✅ Con ${hoursPerWeek} horas/semana, tienes un BCR equilibrado. Este es un buen punto de partida.`;
  }
};
```

**Beneficios:**

- **Aprendizaje Activo:** Usuario experimenta y aprende en lugar de solo leer
- **Mayor Engagement:** Interacción hace el proceso más interesante
- **Comprensión Profunda:** Usuario entiende la relación entre horas y BCR
- **Toma de Decisiones Informada:** Usuario puede ajustar horas antes de finalizar

**Implementación Técnica:**

**Optimización de Performance:**
```typescript
// Debounce para evitar cálculos excesivos durante drag
const debouncedBCRCalculation = useMemo(
  () => debounce((hours: number) => {
    const bcr = calculator.calculateBCR(hours);
    setCurrentBCR(bcr);
  }, 50), // Actualizar cada 50ms durante drag
  [calculator]
);

// Usar useMemo para cálculos pesados
const comparisons = useMemo(
  () => calculator.getBCRForRange(15, 40, 5),
  [calculator]
);
```

**Accesibilidad:**
- Slider accesible por teclado (arrow keys)
- Screen reader anuncia cambios en BCR
- Labels descriptivos para lectores de pantalla
- Contraste adecuado en todos los elementos

### 11.3 Administración de Quick Selects Personalizados

**Objetivo:** Permitir a administradores crear y gestionar Quick Selects personalizados para industrias específicas (ej: Arquitectos, Agencias Audiovisuales, etc.).

**Problema que Resuelve:**
- Quick Selects hardcodeados no cubren todas las industrias
- Necesidad de agregar nuevas industrias sin deployar código
- Personalización según mercado/región específica

**Solución: Panel de Administración de Quick Selects**

#### Estructura de Datos

```typescript
interface QuickSelectConfig {
  id: number;                          // ID único del Quick Select
  industry_key: string;                // Clave única (ej: "architects", "audiovisual")
  industry_name: string;                // Nombre para mostrar (ej: "Arquitectos")
  description: string;                  // Descripción del Quick Select
  preselected_template_ids: string[];   // IDs de templates a pre-seleccionar
  icon?: string;                        // Icono opcional (emoji o URL)
  color?: string;                       // Color del botón (hex)
  is_active: boolean;                   // Si está activo y visible
  is_system: boolean;                   // Si es predefinido del sistema (no editable)
  created_at: string;                   // ISO format
  updated_at: string;                   // ISO format
  created_by_id: number;                 // ID del admin que lo creó
}

// Ejemplo: Quick Select para Arquitectos
const ARCHITECTS_QUICK_SELECT: QuickSelectConfig = {
  id: 5,
  industry_key: "architects",
  industry_name: "Arquitectos",
  description: "Pre-selecciona herramientas comunes para arquitectos y estudios de arquitectura",
  preselected_template_ids: [
    "autocad",          // AutoCAD
    "revit",            // Revit
    "sketchup",         // SketchUp
    "adobe_cc",         // Adobe Creative Cloud (para renders)
    "notion",           // Notion Pro (gestión de proyectos)
    "hosting"           // Hosting (para portfolios)
  ],
  icon: "🏗️",
  color: "#8B5CF6",     // Púrpura
  is_active: true,
  is_system: false,
  created_at: "2026-01-23T10:00:00Z",
  updated_at: "2026-01-23T10:00:00Z",
  created_by_id: 1
};
```

#### Pantalla de Administración

**Endpoint:** `GET /api/v1/admin/quick-selects/onboarding`

**Estructura Visual:**

```
┌─────────────────────────────────────────────────────────────┐
│  ADMINISTRACIÓN DE QUICK SELECTS                            │
│  ────────────────────────────────────────────────────────── │
│                                                              │
│  [Crear Nuevo Quick Select]                                 │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Quick Selects Activos                                   │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │  🎨 Agencia de Marketing          [Editar] [Desactivar] │ │
│  │     Pre-selecciona: Adobe CC, ChatGPT, Hosting...       │ │
│  │     Templates: 5 | Activo | Sistema                     │ │
│  │                                                          │ │
│  │  💻 Desarrollo Web                [Editar] [Desactivar] │ │
│  │     Pre-selecciona: GitHub, Figma, Hosting...            │ │
│  │     Templates: 5 | Activo | Sistema                     │ │
│  │                                                          │ │
│  │  🏗️ Arquitectos                    [Editar] [Eliminar]  │ │
│  │     Pre-selecciona: AutoCAD, Revit, SketchUp...          │ │
│  │     Templates: 6 | Activo | Personalizado                │ │
│  │                                                          │ │
│  │  🎬 Agencia Audiovisual            [Editar] [Eliminar] │ │
│  │     Pre-selecciona: Adobe CC, Premiere, After Effects...│ │
│  │     Templates: 7 | Activo | Personalizado                │ │
│  │                                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Quick Selects Desactivados                              │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │  📐 Ingenieros Civiles            [Editar] [Activar]   │ │
│  │     Templates: 4 | Inactivo | Personalizado             │ │
│  │                                                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Modal de Crear/Editar Quick Select

```
┌─────────────────────────────────────────────────────────────┐
│  Crear Quick Select Personalizado                      [×] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Clave Única (ID) *                                         │
│  [Input: architects]                                        │
│  ℹ️ Usa minúsculas y guiones bajos (ej: "architects")      │
│                                                              │
│  Nombre para Mostrar *                                       │
│  [Input: Arquitectos]                                       │
│  ℹ️ Este nombre aparecerá en el botón del Quick Select      │
│                                                              │
│  Descripción                                                 │
│  [Textarea: Pre-selecciona herramientas comunes para...]   │
│                                                              │
│  Icono (Opcional)                                           │
│  [Input: 🏗️] o [Selector de Emoji]                         │
│                                                              │
│  Color del Botón (Opcional)                                 │
│  [Color Picker: #8B5CF6]                                    │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  Templates a Pre-seleccionar *                               │
│                                                              │
│  [Búsqueda: Buscar template...]                            │
│                                                              │
│  Templates Disponibles:                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ☑️ AutoCAD              $150 USD/mes                  │  │
│  │ ☑️ Revit                $200 USD/mes                  │  │
│  │ ☑️ SketchUp             $100 USD/mes                  │  │
│  │ ☐ Adobe CC              $150.000 COP/mes              │  │
│  │ ☑️ Notion Pro           $8 USD/mes                   │  │
│  │ ☑️ Hosting Web          $50.000 COP/mes               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Templates Seleccionados: 5                                  │
│  • AutoCAD, Revit, SketchUp, Notion Pro, Hosting Web        │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  [Cancelar]  [Guardar Quick Select]                         │
└─────────────────────────────────────────────────────────────┘
```

#### Data Mapping

```typescript
interface QuickSelectCreateRequest {
  industry_key: string;                // Requerido, único, formato: lowercase_with_underscores
  industry_name: string;                // Requerido, min: 1, max: 100 caracteres
  description: string;                  // Opcional, max: 500 caracteres
  preselected_template_ids: string[];   // Requerido, array de IDs de templates
  icon?: string;                        // Opcional, emoji o URL
  color?: string;                       // Opcional, hex color (#RRGGBB)
  is_active?: boolean;                  // Default: true
}

interface QuickSelectUpdateRequest {
  industry_name?: string;
  description?: string;
  preselected_template_ids?: string[];
  icon?: string;
  color?: string;
  is_active?: boolean;
}

interface QuickSelectResponse {
  id: number;
  industry_key: string;
  industry_name: string;
  description: string;
  preselected_template_ids: string[];
  icon?: string;
  color?: string;
  is_active: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
  created_by_id: number;
  templates: Array<{                    // Templates expandidos
    id: string;
    name: string;
    amount_monthly: string;
    currency: string;
    category: string;
  }>;
}
```

#### Endpoints del Backend

**Listar Quick Selects:**
```
GET /api/v1/admin/quick-selects/onboarding
```

**Response:**
```typescript
interface QuickSelectListResponse {
  items: QuickSelectResponse[];
  total: int;
  system_quick_selects: int;  // Cantidad de Quick Selects del sistema
  custom_quick_selects: int;   // Cantidad de Quick Selects personalizados
}
```

**Crear Quick Select:**
```
POST /api/v1/admin/quick-selects/onboarding
```

**Request:** `QuickSelectCreateRequest`

**Response:** `QuickSelectResponse`

**Actualizar Quick Select:**
```
PUT /api/v1/admin/quick-selects/onboarding/{id}
```

**Request:** `QuickSelectUpdateRequest`

**Response:** `QuickSelectResponse`

**Eliminar Quick Select (Solo personalizados):**
```
DELETE /api/v1/admin/quick-selects/onboarding/{id}
```

**Validaciones:**
- Solo se pueden eliminar Quick Selects personalizados (is_system = false)
- No se pueden editar Quick Selects del sistema (is_system = true)
- `industry_key` debe ser único
- `preselected_template_ids` debe contener IDs válidos de templates existentes

#### Permisos

**Roles que pueden gestionar Quick Selects:**
- `super_admin`: Puede crear, editar y eliminar cualquier Quick Select
- `owner`: Puede crear Quick Selects personalizados para su organización (futuro: multi-tenant)

**Restricciones:**
- Quick Selects del sistema (`is_system = true`) no se pueden editar ni eliminar
- Solo se pueden desactivar Quick Selects del sistema
- Quick Selects personalizados se pueden editar y eliminar completamente

#### Integración en Paso 2 del Onboarding

**Carga Dinámica:**
```typescript
const OnboardingStep2 = () => {
  const [quickSelects, setQuickSelects] = useState<Record<string, IndustryQuickSelect>>({});
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadQuickSelects = async () => {
      try {
        // Cargar Quick Selects desde backend (incluye personalizados + sistema)
        const response = await fetch('/api/v1/admin/quick-selects/onboarding');
        const data = await response.json();
        
        // Convertir respuesta del backend al formato esperado
        const formattedQuickSelects = data.items.reduce((acc: Record<string, IndustryQuickSelect>, qs: QuickSelectResponse) => {
          acc[qs.industry_key] = {
            industry: qs.industry_name,
            preselectedTemplates: qs.preselected_template_ids,
            description: qs.description,
            icon: qs.icon,
            color: qs.color
          };
          return acc;
        }, {});
        
        setQuickSelects(formattedQuickSelects);
      } catch (error) {
        console.error('Error cargando Quick Selects:', error);
        // Fallback a predefinidos
        setQuickSelects(DEFAULT_INDUSTRY_QUICK_SELECTS);
      } finally {
        setLoading(false);
      }
    };
    
    loadQuickSelects();
  }, []);
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  return (
    <QuickSelectIndustry 
      quickSelects={quickSelects}
      onSelect={handleQuickSelect}
    />
  );
};
```

**Renderizado Dinámico:**
```typescript
const QuickSelectIndustry = ({ quickSelects, onSelect }: Props) => {
  return (
    <div className="quick-select-container">
      <p className="quick-select-description">
        💡 Quick Select: Elige tu industria para pre-seleccionar los costos más comunes
      </p>
      
      <div className="industry-buttons">
        {Object.values(quickSelects).map((quickSelect) => (
          <button
            key={quickSelect.industry}
            onClick={() => onSelect(quickSelect.industry)}
            className="industry-button"
            style={{
              backgroundColor: quickSelect.color || '#3B82F6',
              // ... otros estilos
            }}
          >
            {quickSelect.icon && <span>{quickSelect.icon}</span>}
            {quickSelect.industry}
          </button>
        ))}
        <button onClick={() => onSelect('custom')}>
          Otro / Personalizado
        </button>
      </div>
    </div>
  );
};
```

#### Ejemplos de Quick Selects Personalizados

**Arquitectos:**
```typescript
{
  industry_key: "architects",
  industry_name: "Arquitectos",
  description: "Pre-selecciona herramientas comunes para arquitectos y estudios de arquitectura",
  preselected_template_ids: [
    "autocad",          // AutoCAD
    "revit",            // Revit
    "sketchup",         // SketchUp
    "adobe_cc",         // Adobe Creative Cloud (para renders)
    "notion",           // Notion Pro
    "hosting"           // Hosting (para portfolios)
  ],
  icon: "🏗️",
  color: "#8B5CF6"
}
```

**Agencias Audiovisuales:**
```typescript
{
  industry_key: "audiovisual",
  industry_name: "Agencia Audiovisual",
  description: "Pre-selecciona herramientas comunes para producción audiovisual",
  preselected_template_ids: [
    "adobe_cc",         // Adobe Creative Cloud
    "premiere_pro",     // Adobe Premiere Pro
    "after_effects",    // Adobe After Effects
    "davinci_resolve",  // DaVinci Resolve (si está disponible)
    "hosting",          // Hosting para portfolios
    "vimeo_pro"         // Vimeo Pro (si está disponible)
  ],
  icon: "🎬",
  color: "#EC4899"
}
```

**Ingenieros Civiles:**
```typescript
{
  industry_key: "civil_engineers",
  industry_name: "Ingenieros Civiles",
  description: "Pre-selecciona herramientas comunes para ingeniería civil",
  preselected_template_ids: [
    "autocad",          // AutoCAD
    "civil_3d",         // AutoCAD Civil 3D
    "revit",            // Revit
    "notion",           // Notion Pro
    "hosting"           // Hosting
  ],
  icon: "📐",
  color: "#10B981"
}
```

#### Validaciones y Edge Cases

**Validaciones:**
- `industry_key` debe ser único (no puede duplicar claves existentes)
- `industry_key` debe seguir formato: `lowercase_with_underscores` (regex: `^[a-z0-9_]+$`)
- `preselected_template_ids` debe contener al menos 1 template
- `preselected_template_ids` debe contener solo IDs de templates existentes
- `color` debe ser formato hex válido (#RRGGBB)

**Edge Cases:**
- Si un template referenciado se elimina, el Quick Select sigue funcionando pero muestra advertencia
- Si un Quick Select personalizado se desactiva, no aparece en el onboarding pero se mantiene en BD
- Si hay múltiples Quick Selects con el mismo `industry_key`, se usa el más reciente
- Fallback a Quick Selects predefinidos si el backend no responde

#### Notas de Implementación Backend

**Modelo de Base de Datos Sugerido:**

```python
class QuickSelectOnboarding(Base):
    """
    Quick Select configuration for onboarding templates
    """
    __tablename__ = "quick_selects_onboarding"
    
    id = Column(Integer, primary_key=True, index=True)
    industry_key = Column(String, unique=True, nullable=False, index=True)  # "architects", "audiovisual"
    industry_name = Column(String, nullable=False)  # "Arquitectos"
    description = Column(Text, nullable=True)
    preselected_template_ids = Column(FlexibleJSON, nullable=False)  # Array de IDs de templates
    icon = Column(String, nullable=True)  # Emoji o URL
    color = Column(String, nullable=True)  # Hex color
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # True para Quick Selects del sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_by = relationship("User", foreign_keys=[created_by_id])
```

**Migración Alembic Sugerida:**

```python
def upgrade():
    op.create_table(
        'quick_selects_onboarding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('industry_key', sa.String(), nullable=False),
        sa.Column('industry_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preselected_template_ids', sa.JSON(), nullable=False),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quick_selects_onboarding_industry_key', 'quick_selects_onboarding', ['industry_key'], unique=True)
    op.create_index('ix_quick_selects_onboarding_is_active', 'quick_selects_onboarding', ['is_active'])
    
    # Insertar Quick Selects del sistema
    op.execute("""
        INSERT INTO quick_selects_onboarding 
        (industry_key, industry_name, description, preselected_template_ids, is_active, is_system)
        VALUES
        ('marketing_agency', 'Agencia de Marketing', 'Pre-selecciona herramientas comunes para agencias de marketing', 
         '["adobe_cc", "chatgpt_plus", "hosting", "notion"]'::jsonb, true, true),
        ('web_development', 'Desarrollo Web', 'Pre-selecciona herramientas comunes para desarrollo web',
         '["github", "figma", "hosting", "chatgpt_plus"]'::jsonb, true, true),
        ('design_agency', 'Agencia de Diseño', 'Pre-selecciona herramientas comunes para agencias de diseño',
         '["adobe_cc", "figma", "behance", "notion"]'::jsonb, true, true),
        ('consulting', 'Consultoría', 'Pre-selecciona herramientas comunes para consultoría',
         '["notion", "zoom", "slack", "chatgpt_plus"]'::jsonb, true, true)
    """)
```

**Endpoints del Backend (Especificación):**

```python
# backend/app/api/v1/endpoints/admin.py (nuevo archivo o agregar a existente)

@router.get("/admin/quick-selects/onboarding", response_model=QuickSelectListResponse)
async def list_quick_selects(
    active_only: bool = Query(True, description="Solo mostrar activos"),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Listar todos los Quick Selects (sistema + personalizados)
    Solo super_admin puede acceder
    """
    # Implementación...

@router.post("/admin/quick-selects/onboarding", response_model=QuickSelectResponse)
async def create_quick_select(
    quick_select_data: QuickSelectCreateRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear nuevo Quick Select personalizado
    Solo super_admin puede crear
    """
    # Validar que industry_key sea único
    # Validar que template_ids existan
    # Crear registro
    # Retornar QuickSelectResponse

@router.put("/admin/quick-selects/onboarding/{id}", response_model=QuickSelectResponse)
async def update_quick_select(
    id: int,
    quick_select_data: QuickSelectUpdateRequest,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar Quick Select
    Solo se pueden actualizar personalizados (is_system = false)
    """
    # Verificar que existe
    # Verificar que no es del sistema
    # Actualizar campos
    # Retornar QuickSelectResponse

@router.delete("/admin/quick-selects/onboarding/{id}")
async def delete_quick_select(
    id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Eliminar Quick Select personalizado
    Solo se pueden eliminar personalizados (is_system = false)
    """
    # Verificar que existe
    # Verificar que no es del sistema
    # Eliminar registro
```

**Endpoint Público (Para Onboarding):**

```python
@router.get("/quick-selects/onboarding", response_model=QuickSelectListResponse)
async def get_quick_selects_for_onboarding(
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener Quick Selects activos para mostrar en onboarding
    Endpoint público (sin autenticación requerida)
    Solo retorna Quick Selects activos
    """
    # Obtener solo Quick Selects activos
    # Retornar lista
```

---

## 12. CONSIDERACIONES ADICIONALES

### 10.1 Persistencia de Datos

- Guardar progreso después de cada paso
- Permitir retomar onboarding si se cierra el navegador
- Usar localStorage o sessionStorage para datos temporales

### 12.2 Optimización de Producto

**Calculador de Horas de Realidad:**
- Mostrar advertencia si usuario ingresa horas facturables muy altas (> 35 horas/semana)
- Sugerir ajuste automático basado en industria/rol
- Explicar impacto en BCR si no se ajusta

**Templates Inteligentes:**
- Mostrar templates más relevantes primero según país/industria
- Aprender de selecciones de otros usuarios (futuro)
- Sugerir templates basados en rol del usuario

### 12.3 Educación del Usuario

- Cada paso debe educar, no solo capturar datos
- Explicar "por qué" se pide cada dato
- Mostrar impacto visual de cada decisión en el BCR final
- Incluir ejemplos prácticos

### 12.4 Accesibilidad

- Navegación por teclado (Tab, Enter, Esc)
- Screen reader friendly
- Contraste adecuado en todos los elementos
- Labels descriptivos en todos los inputs

---

**Última actualización:** 2026-01-23  
**Versión del Backend:** Compatible con v1.0  
**Nota:** Este documento enfatiza la "Amabilidad Financiera" para ayudar a los usuarios a entender su costo real desde el primer día
