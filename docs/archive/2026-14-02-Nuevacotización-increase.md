Especificación de API - Módulo de Cotizaciones
Para construir el backend correspondiente al módulo de Creación de Cotizaciones (Quote Builder), se recomienda la siguiente estructura de datos y endpoints.

Endpoints
1. Crear Cotización
Método: `POST`
Ruta: `/api/quotes`
Descripción: Crea una nueva cotización en estado draft (borrador).
2. Actualizar Cotización (Borrador)
Método: `PUT` / `PATCH`
Ruta: `/api/quotes/:id`
Descripción: Actualiza los datos de una cotización existente mientras está en borrador.
3. Crear Nueva Versión
Método: `POST`
Ruta: `/api/quotes/:id/versions`
Descripción: Archiva la versión actual (historial) y crea una nueva (incrementa version).
Estructura de Datos (Payload)
El frontend envía un objeto JSON completo con la configuración de la cotización. A continuación se detalla la interfaz TypeScript y un ejemplo en JSON.

Interfaz TypeScript (Referencia)
// Tipos auxiliares
type PricingType = 'hourly' | 'fixed' | 'recurring' | 'project_value';
// Alocación de Recursos (Costos por Recurso)
interface ResourceAllocation {
  id?: string; // Opcional al crear, presente al actualizar
  teamMemberId: number; // ID del recurso/empleado en base de datos
  hours: number;
  role?: string; // Opcional (puede venir del recurso)
  startDate?: string; // ISO Date YYYY-MM-DD
  endDate?: string;   // ISO Date YYYY-MM-DD
}
// Ítem de Cotización (Servicio)
interface QuoteItem {
  id?: string; // Opcional al crear
  serviceId: number; // ID del servicio base
  serviceName: string; // Nombre personalizado del servicio
  // Tipo de Precio y Lógica
  pricingType: PricingType;
  
  // -- Campos según PricingType --
  estimatedHours?: number; // Para 'hourly'
  fixedPrice?: number;     // Para 'fixed' (Precio Base Cliente)
  recurringPrice?: number; // Para 'recurring' (Precio Base Cliente)
  projectValue?: number;   // Para 'project_value'
  
  // -- Configuración General --
  quantity: number;        // Cantidad (por defecto 1)
  billingFrequency?: 'monthly' | 'annual'; // Para 'recurring'
  durationMonths?: number; // Duración del contrato (para 'recurring')
  
  // -- Recursos y Costos --
  allocations?: ResourceAllocation[]; // Lista de recursos asignados a este ítem
  // -- Sobrescrituras --
  manualPrice?: number; // Precio final manual (si aplica)
}
// Contingencia
interface Contingency {
  description: string;
  type: 'fixed' | 'percentage';
  value: number;
}
// Payload Principal (Quote)
interface CreateQuoteRequest {
  // Información del Proyecto
  projectName: string;
  clientName: string;
  clientCompany?: string;
  clientEmail: string;
  currency: 'COP' | 'USD';
  
  // Configuración Financiera
  targetMargin: number; // Margen objetivo global (ej. 35)
  selectedTaxIds: number[]; // IDs de impuestos aplicables
  allowLowMargin: boolean; // Flag para permitir márgenes bajos
  contingency?: Contingency; // Módulo de imprevistos
  
  // Ítems (Servicios)
  items: QuoteItem[];
}
Ejemplo de JSON (Request Body)
{
  "projectName": "Desarrollo E-commerce 2024",
  "clientName": "Juan Pérez",
  "clientCompany": "Tech Solutions SAS",
  "clientEmail": "juan@techsolutions.com",
  "currency": "COP",
  "targetMargin": 35,
  "selectedTaxIds": [1, 3], 
  "allowLowMargin": false,
  "contingency": {
    "description": "Riesgo de cambios en alcance",
    "type": "percentage",
    "value": 5
  },
  "items": [
    {
      "serviceId": 101,
      "serviceName": "Desarrollo Backend",
      "pricingType": "hourly",
      "estimatedHours": 120,
      "quantity": 1,
      "allocations": [
        {
          "teamMemberId": 5,
          "hours": 80,
          "role": "Senior Dev"
        },
        {
            "teamMemberId": 8,
            "hours": 40,
            "role": "Junior Dev"
        }
      ]
    },
    {
      "serviceId": 204,
      "serviceName": "Licencia de Software",
      "pricingType": "fixed",
      "fixedPrice": 5000000,
      "quantity": 1,
      "allocations": [] 
    }
  ]
}
Lógica de Backend Recomendada
Cálculo de Costos:

Al recibir el payload, el backend debe calcular el Costo Interno basándose en los allocations.
Costo Interno Item = Sum(horas_recurso * costo_hora_recurso).
Nota: El frontend puede enviar cálculos preliminares, pero el backend debe ser la fuente de verdad.
Validación de Márgenes:

Si allowLowMargin es false y el margen calculado es menor a targetMargin (o al mínimo global), el backend podría rechazar la creación o marcarla "para revisión".
Gestión de Versiones:

Al guardar, si es una edición, se recomienda NO sobrescribir el registro histórico si ya fue enviado al cliente. Crear una nueva versión (v2, v3).