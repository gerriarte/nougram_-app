const AUTH_TOKEN_KEY = "auth_token";
const LEGACY_AUTH_KEYS = ["nougram_token", "token", "access_token"];

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
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  // Keep compatibility for any legacy readers during rollout.
  localStorage.setItem("nougram_token", token);
}

export function removeAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  LEGACY_AUTH_KEYS.forEach((key) => localStorage.removeItem(key));
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
  LEGACY_AUTH_KEYS.forEach((key) => sessionStorage.removeItem(key));
}

export function isAuthenticated(): boolean {
  return !!getAuthToken();
}
