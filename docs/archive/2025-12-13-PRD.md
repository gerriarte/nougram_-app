# PRD: Plataforma de Rentabilidad y Operaciones "A:BRA Quote"

## 1. Visión General

**Problema:** Las agencias de servicios (como la nuestra) luchan por cotizar proyectos de forma rentable. A menudo se subestiman los costos reales (costo por hora, herramientas) y no hay visibilidad sobre qué clientes o servicios son realmente rentables, lo que dificulta la escalabilidad.

**Solución:** "A:BRA Quote" es una plataforma interna diseñada para centralizar la parametrización de costos, estandarizar la valorización de servicios, generar cotizaciones rentables y predecibles, y proporcionar insights accionables a través de un dashboard de BI asistido por IA para mejorar la toma de decisiones financieras.

**Audiencia Objetivo:**
* **Primario:** Fundador / Director de Operaciones (para estrategia de precios y BI).
* **Secundario:** Project Managers / Líderes de Cuentas (para crear cotizaciones).
* **Terciario:** Administrador Financiero (para cargar costos).

---

## 2. Historias de Usuario y Funcionalidades Clave

### Módulo 1: Motor de Costos (Parametrización)
* **Épica:** Como Director, necesito un lugar central para registrar todos mis costos fijos (overhead) y costos de personal (nómina) para entender mi costo operativo real.
* **HU-1.1:** Como Admin, puedo registrar, editar y eliminar costos fijos (ej. alquiler, internet, luz).
* **HU-1.2:** Como Admin, puedo registrar a cada miembro del equipo, su salario bruto y sus horas facturables disponibles (descontando vacaciones, etc.).
* **HU-1.3:** Como Admin, puedo registrar los costos de suscripción de software (ej. SEMrush, Adobe) y asignarlos como "Overhead" o "Costo Directo" (si se usa en un servicio específico).
* **HU-1.4:** El sistema debe calcular y mostrarme automáticamente el **Costo-Hora-Agencia Total** (Blended Cost Rate).

### Módulo 2: Catálogo de Servicios y Valorización
* **Épica:** Como Director, quiero definir mi oferta de servicios y asignarles un precio basado en costos reales y mi margen deseado.
* **HU-2.1:** Como Admin, puedo crear, editar y eliminar servicios (ej. "Auditoría SEO", "Diseño de Landing Page").
* **HU-2.2:** Como Admin, puedo asignar un **Margen de Ganancia Objetivo** (ej. 40%) a cada servicio o a una categoría de servicios.
* **HU-2.3:** El sistema debe calcular y mostrar una **Tarifa por Hora Sugerida** (Billable Rate) para cada servicio, basada en el Costo-Hora-Agencia + Margen Objetivo.

### Módulo 3: Estimador de Proyectos (Quoting)
* **Épica:** Como PM, necesito crear cotizaciones para clientes de forma rápida y precisa, sabiendo que cada cotización es rentable por diseño.
* **HU-3.1:** Como PM, puedo iniciar una nueva cotización para un cliente.
* **HU-3.2:** Como PM, puedo buscar y añadir servicios desde el Catálogo (Módulo 2) a mi cotización.
* **HU-3.3:** Como PM, debo ingresar las **horas estimadas** para cada servicio en la cotización.
* **HU-3.4:** Mientras construyo la cotización, el sistema debe mostrarme en tiempo real:
    * **Costo Interno Total** (Horas Estimadas * Costo-Hora-Agencia)
    * **Precio para el Cliente** (Horas Estimadas * Tarifa por Hora Sugerida)
    * **Margen de Ganancia Bruto** (en $ y %).
* **HU-3.5:** El sistema debe **alertarme visualmente** (ej. en rojo) si el margen de una cotización cae por debajo del Margen Objetivo.
 **HU-3.5:** El sistema podrá generar la cotización en 4 monedas principales: Pesos Colombianos, Peso Argentino, Dolar, Euro

### Módulo 4: Dashboard y Asistente IA (Business Intelligence)
* **Épica:** Como Director, necesito insights para entender qué está funcionando y qué no, y recibir consejos para evolucionar mis cobros.
* **HU-4.1:** Como Director, puedo ver un dashboard con KPIs clave: Rentabilidad Promedio, Tasa de Utilización del Equipo, Servicios Más/Menos Rentables.
* **HU-4.2:** El sistema debe tener un componente de "Asistente IA" que yo pueda consultar.
* **HU-4.3:** El Asistente IA debe poder responder preguntas como:
    * "Mis estimaciones para 'Diseño Web' suelen ser un 20% más bajas que las horas reales. ¿Debería subir mi tarifa para este servicio?"
    * "Mi costo de herramientas ha subido. ¿Cuánto necesito aumentar mi tarifa por hora para mantener mi margen del 40%?"

---

## 3. Integraciones

* **Google Sheets:** El Admin debe poder importar masivamente costos fijos y de personal desde una plantilla de Google Sheet.
* **Google Calendar:** El sistema debe poder leer la disponibilidad real (tiempo libre/ocupado) de los calendarios del equipo para refinar el cálculo de "horas facturables disponibles".
* **Apollo.io:** El PM debe poder buscar un contacto/empresa en Apollo.io desde el Estimador (Módulo 3) para autocompletar la información del cliente en la cotización.

## 4. Métricas de Éxito

* **Reducción del Tiempo de Cotización:** Reducir en un 50% el tiempo necesario para generar una cotización.
* **Aumento del Margen de Ganancia:** Aumentar el margen de ganancia promedio realizado en todos los proyectos en un 15% en 6 meses.
* **Precisión de Estimación:** Reducir la desviación entre horas estimadas y horas reales (requiere time-tracking futuro) a menos del 10%.