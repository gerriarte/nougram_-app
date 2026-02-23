const AUTH_TOKEN_KEY = "auth_token";
const LEGACY_AUTH_KEYS = ["nougram_token", "token", "access_token"];

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
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
