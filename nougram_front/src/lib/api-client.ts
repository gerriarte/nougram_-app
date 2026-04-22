import {
  getAuthToken,
  getRefreshToken,
  markUserActivity,
  markAuthSessionInvalidated,
  removeAuthToken,
  setAuthToken,
  setRefreshToken,
  shouldRefreshAccessToken,
  shouldShortCircuitAuthenticatedApi,
} from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
let lastExpiredTokenNotified: string | null = null;
let refreshPromise: Promise<boolean> | null = null;

type RefreshResponse = {
  access_token: string;
  refresh_token?: string;
};

function shouldNotifyAuthExpired(endpoint: string, token: string | null): boolean {
  if (!token) return false;

  // Do not emit global "session expired" events for auth endpoints
  // (e.g. wrong credentials on login should not open the expired-session modal).
  const normalizedEndpoint = endpoint.toLowerCase();
  if (normalizedEndpoint.startsWith("/auth/login")) return false;
  if (normalizedEndpoint.startsWith("/auth/register")) return false;
  if (normalizedEndpoint.startsWith("/auth/forgot-password")) return false;
  if (normalizedEndpoint.startsWith("/auth/reset-password")) return false;
  if (normalizedEndpoint.startsWith("/auth/verify-email")) return false;

  // Avoid firing multiple times for the same expired token when many requests fail together.
  if (lastExpiredTokenNotified === token) return false;
  lastExpiredTokenNotified = token;
  return true;
}

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
  const normalizeEndpoint = (rawEndpoint: string): string => {
    return rawEndpoint.startsWith("/") ? rawEndpoint : `/${rawEndpoint}`;
  };

  const withTrailingSlash = (value: string): string =>
    value.endsWith("/") ? value : `${value}/`;

  const requestOnce = async (normalizedEndpoint: string): Promise<Response> => {
    const url = `${normalizedBase}${normalizedEndpoint}`;
    const token = getAuthToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return fetch(url, {
      ...options,
      headers,
    });
  };

  const shouldSkipRefresh = (normalizedEndpoint: string): boolean => {
    const endpointLower = normalizedEndpoint.toLowerCase();
    return (
      endpointLower.startsWith("/auth/login") ||
      endpointLower.startsWith("/auth/register") ||
      endpointLower.startsWith("/auth/forgot-password") ||
      endpointLower.startsWith("/auth/reset-password") ||
      endpointLower.startsWith("/auth/verify-email") ||
      endpointLower.startsWith("/auth/refresh")
    );
  };

  const refreshAccessToken = async (): Promise<boolean> => {
    if (refreshPromise) return refreshPromise;

    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    refreshPromise = (async () => {
      try {
        const refreshResponse = await fetch(`${normalizedBase}/auth/refresh`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!refreshResponse.ok) return false;
        const payload = (await refreshResponse.json()) as RefreshResponse;
        if (!payload.access_token) return false;

        setAuthToken(payload.access_token);
        if (payload.refresh_token) {
          setRefreshToken(payload.refresh_token);
        }
        markUserActivity();
        return true;
      } catch {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();

    return refreshPromise;
  };

  try {
    const normalizedEndpoint = normalizeEndpoint(endpoint);
    if (shouldShortCircuitAuthenticatedApi(normalizedEndpoint)) {
      return {
        error: "No autorizado. Inicia sesión nuevamente.",
        statusCode: 401,
      };
    }

    const tokenAtRequestStart = getAuthToken();
    if (tokenAtRequestStart && lastExpiredTokenNotified !== tokenAtRequestStart) {
      // A new token replaced the previous one; clear stale dedupe state.
      lastExpiredTokenNotified = null;
    }

    if (
      tokenAtRequestStart &&
      getRefreshToken() &&
      shouldRefreshAccessToken() &&
      !shouldSkipRefresh(normalizedEndpoint)
    ) {
      await refreshAccessToken();
    }

    let response = await requestOnce(normalizedEndpoint);
    if (response.status === 404) {
      const alternateEndpoint = normalizedEndpoint.endsWith("/")
        ? normalizedEndpoint.replace(/\/+$/, "")
        : withTrailingSlash(normalizedEndpoint);
      if (alternateEndpoint !== normalizedEndpoint) {
        response = await requestOnce(alternateEndpoint);
      }
    }

    if (!response.ok) {
      if (response.status === 401) {
        const canRefresh = !shouldSkipRefresh(normalizedEndpoint);
        if (canRefresh) {
          const refreshed = await refreshAccessToken();
          if (refreshed) {
            response = await requestOnce(normalizedEndpoint);
            if (response.ok) {
              if (response.status === 204) return {};
              const retriedData = (await response.json()) as T;
              return { data: retriedData };
            }
          }
        }

        const hadBearerSession =
          Boolean(tokenAtRequestStart) && !shouldSkipRefresh(normalizedEndpoint);
        if (hadBearerSession) {
          markAuthSessionInvalidated();
        }
        removeAuthToken();
        if (
          typeof window !== "undefined" &&
          shouldNotifyAuthExpired(normalizedEndpoint, tokenAtRequestStart)
        ) {
          window.dispatchEvent(
            new CustomEvent("nougram:auth-expired", {
              detail: {
                reason: "unauthorized",
                statusCode: 401,
                endpoint: normalizedEndpoint,
              },
            })
          );
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
      if (tokenAtRequestStart) {
        markUserActivity();
      }
      return {};
    }

    const data = (await response.json()) as T;
    if (tokenAtRequestStart) {
      markUserActivity();
    }
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
