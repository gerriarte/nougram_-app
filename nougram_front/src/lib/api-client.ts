import { getAuthToken, removeAuthToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type ApiResponse<T> = {
  data?: T;
  error?: string;
  /** Set when response.ok is false; allows UI to handle 402 (credits) etc. */
  statusCode?: number;
};

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  if (!API_URL) {
    return {
      error:
        "Configuracion faltante: NEXT_PUBLIC_API_URL no esta definida en el entorno de despliegue.",
    };
  }
  const normalizedBase = API_URL.replace(/\/+$/, "");
  try {
    const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = `${normalizedBase}${normalizedEndpoint}`;
    const token = getAuthToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        removeAuthToken();
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("nougram:auth-expired"));
        }
        return { error: "No autorizado. Inicia sesión nuevamente.", statusCode: 401 };
      }
      if (response.status === 429) {
        return {
          error: "Demasiados intentos. Espera un minuto e intenta nuevamente.",
          statusCode: 429,
        };
      }

      const errorBody = await response.json().catch(() => ({}));
      const message =
        (typeof errorBody?.detail === "string"
          ? errorBody.detail
          : errorBody?.message) ||
        `Error ${response.status}: ${response.statusText}`;
      return { error: String(message), statusCode: response.status };
    }

    if (response.status === 204) {
      return {};
    }

    const data = (await response.json()) as T;
    return { data };
  } catch (error) {
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      return {
        error: `Error de conexión. Verifica que el backend esté disponible en ${normalizedBase}`,
      };
    }
    return { error: error instanceof Error ? error.message : "Error de red" };
  }
}
