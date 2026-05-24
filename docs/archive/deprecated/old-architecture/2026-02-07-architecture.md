# Arquitectura del Sistema "A:BRA Quote"

## 1. Descripción General

Se implementará una **Arquitectura Full-Stack Desacoplada**. Consiste en un backend (API REST) que maneja toda la lógica de negocio y las conexiones, y un frontend (Single Page Application) que consume esta API. Esta arquitectura permite que el frontend y el backend se desarrollen y escalen de forma independiente.

El desarrollo se acelerará usando **Cursor** como IDE principal para la generación de código (modelos, componentes, lógica de API).

## 2. Diagrama de Componentes

[Usuario (Admin/PM)] | v [Frontend (Next.js / Vercel)] | v (API RESTful - JSON) [Backend (FastAPI/Python / Cloud Run)] | +-----------------------+ | | v v [Base de Datos (PostgreSQL)] [API de IA (Gemini/OpenAI)] | +-----------------------+-----------------------+ | | | v v v [API Google Sheets] [API Google Calendar] [API Apollo.io] (Service Account) (OAuth 2.0) (API Key)


## 3. Componentes Clave

### 3.1. Frontend (Cliente)
* **Stack:** Next.js (React) con TypeScript.
* **Estilos:** Tailwind CSS.
* **Gestión de Estado:** TanStack Query (para estado de servidor) y Zustand (para estado global).
* **Responsabilidad:** Renderizar la UI, manejar la interacción del usuario, gestionar el estado del cliente y realizar llamadas HTTP a la API del backend. No contendrá lógica de negocio crítica ni claves de API.
* **Hosting:** Vercel.

### 3.2. Backend (Servidor)
* **Stack:** Python 3.11+ con FastAPI.
* **Base de Datos:** PostgreSQL (Gestionado, ej. Supabase, Neon o AWS RDS).
* **ORM:** SQLAlchemy (Asíncrono) con Pydantic para validación.
* **Responsabilidad:**
    * Exponer una API RESTful segura.
    * Implementar **toda** la lógica de negocio (cálculos de costos, márgenes, precios).
    * Autenticar usuarios (JWT).
    * Gestionar la conexión segura con la base de datos.
    * Manejar todas las llamadas a APIs de terceros (Google, Apollo, IA).
* **Hosting:** Google Cloud Run o Render (Servicios Serverless/Contenerizados).

### 3.3. Base de Datos
* **Sistema:** PostgreSQL.
* **Justificación:** Ideal para datos financieros y relacionales. Se necesita integridad de datos (relaciones entre Proyectos, Servicios, Costos) que una BD NoSQL no ofrece fácilmente.

### 3.4. Integraciones (Lógica de Backend)
* **Google Sheets API:** Se usará una **Cuenta de Servicio** (Service Account) de Google Cloud. El archivo JSON de credenciales se almacenará de forma segura en las variables de entorno del backend.
* **Google Calendar API:** Se implementará un flujo **OAuth 2.0** donde cada miembro del equipo autoriza a la aplicación (una vez) a leer el estado "libre/ocupado" de su calendario. El backend almacenará los `refresh_tokens` de forma encriptada.
* **Apollo.io API:** Se usará una **API Key** estándar, almacenada en las variables de entorno del backend. El backend actuará como un proxy.
* **Generative AI API (Open AI):** Se usará una **API Key**, almacenada en las variables de entorno del backend.

## 4. Flujo de Autenticación
* Se usará **Google OAuth** como proveedor de identidad principal.
* 1. El Frontend redirige al usuario a la pantalla de login de Google.
* 2. Google devuelve un `code` al Frontend, que lo envía al Backend.
* 3. El Backend intercambia el `code` por un `access_token` y `refresh_token` de Google.
* 4. El Backend verifica el usuario, lo crea si no existe en la DB, y genera un **Token JWT** propio de la aplicación.
* 5. El Frontend almacena este JWT (en `httpOnly cookie` o `localStorage`) y lo envía en el en