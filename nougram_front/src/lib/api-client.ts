import { getAuthToken, removeAuthToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type ApiResponse<T> = {
  data?: T;
  error?: string;
};

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const normalizedBase = API_URL.replace(/\/+$/, "");
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
          // Let UI layers redirect or show auth-expired messaging.
          window.dispatchEvent(new CustomEvent("nougram:auth-expired"));
        }
        return { error: "No autorizado. Inicia sesión nuevamente." };
      }

      const errorBody = await response.json().catch(() => ({}));
      const message =
        errorBody?.detail ||
        errorBody?.message ||
        `Error ${response.status}: ${response.statusText}`;
      return { error: String(message) };
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
