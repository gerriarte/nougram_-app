const AUTH_TOKEN_KEY = "auth_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const LEGACY_AUTH_KEYS = ["nougram_token", "token", "access_token"];
const LAST_ACTIVITY_KEY = "nougram_last_activity_at";
const INACTIVITY_TIMEOUT_MS = 10 * 60 * 1000;

/**
 * After a protected request returns 401 and refresh fails, we set this so parallel
 * dashboard calls do not hammer the API or spam the console. Cleared on new login
 * (setAuthToken) or explicit logout.
 */
let authSessionInvalidated = false;

export function markAuthSessionInvalidated(): void {
  authSessionInvalidated = true;
}

export function clearAuthSessionInvalidated(): void {
  authSessionInvalidated = false;
}

export function shouldShortCircuitAuthenticatedApi(
  normalizedEndpoint: string
): boolean {
  if (!authSessionInvalidated) return false;
  if (getAuthToken()) return false;
  const ep = normalizedEndpoint.toLowerCase();
  if (
    ep.startsWith("/auth/login") ||
    ep.startsWith("/auth/register") ||
    ep.startsWith("/auth/forgot-password") ||
    ep.startsWith("/auth/reset-password") ||
    ep.startsWith("/auth/verify-email") ||
    ep.startsWith("/auth/refresh")
  ) {
    return false;
  }
  return true;
}

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  const currentToken = localStorage.getItem(AUTH_TOKEN_KEY);
  if (currentToken) return currentToken;

  for (const key of LEGACY_AUTH_KEYS) {
    const legacyToken = localStorage.getItem(key);
    if (legacyToken) {
      // Migrate legacy token key transparently to avoid forced re-login after deploys.
      localStorage.setItem(AUTH_TOKEN_KEY, legacyToken);
      return legacyToken;
    }
  }

  const sessionToken = sessionStorage.getItem(AUTH_TOKEN_KEY);
  if (sessionToken) {
    localStorage.setItem(AUTH_TOKEN_KEY, sessionToken);
    return sessionToken;
  }

  for (const key of LEGACY_AUTH_KEYS) {
    const legacySessionToken = sessionStorage.getItem(key);
    if (legacySessionToken) {
      localStorage.setItem(AUTH_TOKEN_KEY, legacySessionToken);
      return legacySessionToken;
    }
  }

  return null;
}

export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  const hadToken = Boolean(getAuthToken());
  authSessionInvalidated = false;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  // Keep compatibility for any legacy readers during rollout.
  localStorage.setItem("nougram_token", token);
  if (!hadToken && typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("nougram:session-restored"));
  }
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function removeRefreshToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function markUserActivity(): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(LAST_ACTIVITY_KEY, String(Date.now()));
}

export function getLastUserActivityAt(): number {
  if (typeof window === "undefined") return 0;
  const raw = localStorage.getItem(LAST_ACTIVITY_KEY);
  const parsed = raw ? Number(raw) : 0;
  return Number.isFinite(parsed) ? parsed : 0;
}

export function isSessionInactive(): boolean {
  const lastActivityAt = getLastUserActivityAt();
  if (!lastActivityAt) return false;
  return Date.now() - lastActivityAt >= INACTIVITY_TIMEOUT_MS;
}

export function shouldRefreshAccessToken(bufferMs = 2 * 60 * 1000): boolean {
  const token = getAuthToken();
  if (!token) return false;

  try {
    const payloadBase64 = token.split(".")[1];
    if (!payloadBase64) return true;
    const payloadJson = atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/"));
    const payload = JSON.parse(payloadJson) as { exp?: number };
    if (!payload.exp) return true;
    const expiresAtMs = payload.exp * 1000;
    return expiresAtMs - Date.now() <= bufferMs;
  } catch {
    return true;
  }
}

export function removeAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(LAST_ACTIVITY_KEY);
  LEGACY_AUTH_KEYS.forEach((key) => localStorage.removeItem(key));
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
  LEGACY_AUTH_KEYS.forEach((key) => sessionStorage.removeItem(key));
}

export function isAuthenticated(): boolean {
  return !!getAuthToken();
}
