
import { useCallback, useEffect, useState } from "react";
import {
  UserProfileExtended,
  canInviteUsers,
  canManageUsers,
  canViewFinancials,
} from "@/types/user";
import { apiRequest } from "@/lib/api-client";
import { isAuthenticated, removeAuthToken, setAuthToken } from "@/lib/auth";

type LoginResponse = {
  access_token: string;
  token_type?: string;
};

type CurrentUserResponse = {
  id: number;
  email: string;
  full_name: string;
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
    status: "ACTIVE",
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

    return () => {
      authSubscribers.delete(subscriber);
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
    authUserCache = undefined;
    const currentUser = await fetchCurrentUserShared(true);
    setUser(currentUser);
    setLoading(false);

    if (!currentUser) {
      removeAuthToken();
      setUser(null);
      return { success: false, error: "No se pudo obtener el usuario actual" };
    }

    return { success: true };
  }, [refreshCurrentUser]);

  const logout = useCallback(() => {
    removeAuthToken();
    authUserCache = null;
    notifySubscribers(null);
    setUser(null);
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
