
import { useCallback, useEffect, useState } from "react";
import {
  UserProfileExtended,
  canInviteUsers,
  canManageUsers,
  canViewFinancials,
} from "@/types/user";
import { apiRequest } from "@/lib/api-client";
import {
  getRefreshToken,
  isAuthenticated,
  isSessionInactive,
  markUserActivity,
  removeAuthToken,
  setAuthToken,
  setRefreshToken,
  shouldRefreshAccessToken,
} from "@/lib/auth";
import { trackLogout } from "@/lib/analytics";

type LoginResponse = {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
};

type CurrentUserResponse = {
  id: number;
  email: string;
  full_name: string;
  organization_id?: number | null;
  job_title?: string | null;
  specialty?: string | null;
  bio?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  instagram_url?: string | null;
  behance_url?: string | null;
  timezone?: string | null;
  language?: string | null;
  role?:
    | "super_admin"
    | "support_manager"
    | "data_analyst"
    | "owner"
    | "admin_financiero"
    | "product_manager"
    | "collaborator";
};

function mapToExtendedUser(data: CurrentUserResponse): UserProfileExtended {
  return {
    id: String(data.id),
    email: data.email,
    fullName: data.full_name,
    role: data.role || "collaborator",
    organization_id: data.organization_id ?? null,
    status: "ACTIVE",
    job_title: data.job_title ?? undefined,
    specialty: data.specialty ?? undefined,
    bio: data.bio ?? undefined,
    linkedin_url: data.linkedin_url ?? undefined,
    portfolio_url: data.portfolio_url ?? undefined,
    instagram_url: data.instagram_url ?? undefined,
    behance_url: data.behance_url ?? undefined,
    timezone: data.timezone ?? undefined,
    language: data.language ?? undefined,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

let authUserCache: UserProfileExtended | null | undefined = undefined;
let authUserPromise: Promise<UserProfileExtended | null> | null = null;
const authSubscribers = new Set<(user: UserProfileExtended | null) => void>();

function notifySubscribers(user: UserProfileExtended | null) {
  authSubscribers.forEach((callback) => callback(user));
}

async function fetchCurrentUserShared(force = false): Promise<UserProfileExtended | null> {
  if (!isAuthenticated()) {
    authUserCache = null;
    return null;
  }

  if (!force && authUserCache !== undefined) {
    return authUserCache;
  }

  if (authUserPromise) {
    return authUserPromise;
  }

  authUserPromise = (async () => {
    const response = await apiRequest<CurrentUserResponse>("/auth/me");
    if (response.error || !response.data) {
      authUserCache = null;
      return null;
    }

    const mapped = mapToExtendedUser(response.data);
    authUserCache = mapped;
    return mapped;
  })();

  const result = await authUserPromise;
  authUserPromise = null;
  notifySubscribers(result);
  return result;
}

export function useAuth() {
  const [user, setUser] = useState<UserProfileExtended | null>(authUserCache ?? null);
  const [loading, setLoading] = useState(authUserCache === undefined);

  const refreshCurrentUser = useCallback(async (): Promise<UserProfileExtended | null> => {
    const mapped = await fetchCurrentUserShared(true);
    setUser(mapped);
    return mapped;
  }, []);

  useEffect(() => {
    const subscriber = (nextUser: UserProfileExtended | null) => {
      setUser(nextUser);
    };
    authSubscribers.add(subscriber);

    const loadSession = async () => {
      setLoading(true);
      if (!isAuthenticated()) {
        authUserCache = null;
        setUser(null);
        setLoading(false);
        return;
      }

      const currentUser = await fetchCurrentUserShared();
      if (!currentUser) {
        removeAuthToken();
        authUserCache = null;
        setUser(null);
      }
      setLoading(false);
    };
    loadSession();

    const onAuthExpired = () => {
      removeAuthToken();
      authUserCache = null;
      setUser(null);
      setLoading(false);
    };
    if (typeof window !== "undefined") {
      window.addEventListener("nougram:auth-expired", onAuthExpired as EventListener);
    }

    const activityEvents: Array<keyof WindowEventMap> = [
      "click",
      "keydown",
      "mousemove",
      "scroll",
      "touchstart",
    ];
    const onUserActivity = () => {
      if (!isAuthenticated()) return;
      markUserActivity();
    };

    const inactivityInterval = window.setInterval(() => {
      if (!isAuthenticated()) return;
      if (isSessionInactive()) {
        removeAuthToken();
        authUserPromise = null;
        authUserCache = null;
        setUser(null);
        window.dispatchEvent(
          new CustomEvent("nougram:auth-expired", {
            detail: { reason: "inactivity" },
          })
        );
      }
    }, 30_000);

    const tokenRefreshInterval = window.setInterval(async () => {
      if (!isAuthenticated()) return;
      if (isSessionInactive()) return;
      if (!shouldRefreshAccessToken()) return;

      const refreshToken = getRefreshToken();
      if (!refreshToken) return;

      const refreshResponse = await apiRequest<LoginResponse>("/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (refreshResponse.error || !refreshResponse.data?.access_token) {
        removeAuthToken();
        authUserPromise = null;
        authUserCache = null;
        setUser(null);
        window.dispatchEvent(
          new CustomEvent("nougram:auth-expired", {
            detail: { reason: "unauthorized", statusCode: 401, endpoint: "/auth/refresh" },
          })
        );
        return;
      }

      setAuthToken(refreshResponse.data.access_token);
      if (refreshResponse.data.refresh_token) {
        setRefreshToken(refreshResponse.data.refresh_token);
      }
      markUserActivity();
    }, 60_000);

    activityEvents.forEach((eventName) => {
      window.addEventListener(eventName, onUserActivity, { passive: true });
    });

    return () => {
      authSubscribers.delete(subscriber);
      if (typeof window !== "undefined") {
        window.removeEventListener("nougram:auth-expired", onAuthExpired as EventListener);
        activityEvents.forEach((eventName) => {
          window.removeEventListener(eventName, onUserActivity);
        });
        window.clearInterval(inactivityInterval);
        window.clearInterval(tokenRefreshInterval);
      }
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    const response = await apiRequest<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (response.error || !response.data?.access_token) {
      setLoading(false);
      return { success: false, error: response.error || "Error al iniciar sesión" };
    }

    setAuthToken(response.data.access_token);
    if (response.data.refresh_token) {
      setRefreshToken(response.data.refresh_token);
    }
    markUserActivity();
    authUserCache = undefined;
    const currentUser = await fetchCurrentUserShared(true);
    setUser(currentUser);
    setLoading(false);

    if (!currentUser) {
      removeAuthToken();
      setUser(null);
      return { success: false, error: "No se pudo obtener el usuario actual" };
    }

    return { success: true, user: currentUser };
  }, []);

  const logout = useCallback(() => {
    trackLogout();
    removeAuthToken();
    authUserPromise = null;
    authUserCache = null;
    notifySubscribers(null);
    setUser(null);
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("nougram:auth-expired", {
          detail: { reason: "logout" },
        })
      );
    }
  }, []);

  const permissions = {
    canViewFinancials: user ? canViewFinancials(user.role) : false,
    canManageUsers: user ? canManageUsers(user.role) : false,
    canInviteUsers: user ? canInviteUsers(user.role) : false,
  };

  return {
    user,
    loading,
    permissions,
    isAuthenticated: !!user,
    role: user?.role,
    login,
    logout,
    refreshCurrentUser,
  };
}
