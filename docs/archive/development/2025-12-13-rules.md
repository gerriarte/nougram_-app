1. La Regla de Oro: Separación de Responsabilidades
"Esta es una arquitectura monolítica desacoplada. El backend (FastAPI/Python) es el único responsable de toda la lógica de negocio, cálculos financieros, y llamadas a APIs de terceros (Google, Apollo, IA). El frontend (Next.js/React) es solo una capa de presentación y gestión de estado. El frontend NUNCA debe contener lógica de negocio, cálculos de precios, o claves de API."

2. Reglas del Stack: Cero Desviaciones
"Solo usaremos el stack tecnológico definido. No introduzcas librerías nuevas sin aprobación."

Frontend: Next.js (App Router), TypeScript, Tailwind CSS.

Componentes: Shadcn/ui. Cuando pido una UI, genera código para componentes de Shadcn (ej. <Table>, <Dialog>, <Button>), no HTML nativo.

Backend: FastAPI (Python), SQLAlchemy (asíncrono), Pydantic.

3. Reglas de Frontend: El "Estilo TanStack"
"Toda la comunicación con nuestra API DEBE gestionarse a través de TanStack Query (React Query)."

Para leer datos (GET): Usa siempre un hook useQuery.

Para modificar datos (POST, PUT, DELETE): Usa siempre un hook useMutation.

NUNCA uses fetch o axios directamente dentro de un componente.

Estado Global: Solo usa Zustand para estado mínimo y global (ej. token de autenticación, info del usuario). No lo uses para datos que vienen de la API.

4. Reglas de TypeScript: Estricto y Explícito
"Todo el código de frontend DEBE ser TypeScript estricto. NUNCA uses el tipo any. Define interfaces (interface) o tipos (type) para todas las props de componentes y para todas las respuestas esperadas de la API. Basa los tipos del frontend en los modelos Pydantic del backend."

5. Reglas de Backend: Seguridad y Anonimización
"La seguridad es crítica. NINGUNA clave de API (Google, Apollo, Gemini/OpenAI) debe salir del backend. Deben ser cargadas solo desde variables de entorno del servidor.

Para el Asistente IA (Módulo 4): Antes de enviar cualquier dato a la API de IA, el backend DEBE anonimizar la información. Reemplaza nombres reales de clientes, empleados y proyectos por IDs o placeholders (ej. 'Cliente_A', 'Empleado_1')."

6. Reglas de Calidad: Código Limpio y en Inglés
"Genera código limpio y modular. Prefiere funciones pequeñas y con un solo propósito.

Nomenclatura: Todos los nombres de variables, funciones, clases y archivos deben estar en inglés (calculateMargin, no calcularMargen).

Comentarios: Añade JSDoc/Docstrings a las funciones complejas, especialmente a la lógica de negocio y cálculos en el backend.

Formularios: Todos los formularios del frontend deben usar React Hook Form y Zod para la validación."