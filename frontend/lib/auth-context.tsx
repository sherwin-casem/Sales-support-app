"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { authService } from "@/services/auth.service";
import type { AuthResponse, User } from "@/types/auth";

const TOKEN_KEY = "access_token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function persistToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
  }
}

function readToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const applyAuth = useCallback((response: AuthResponse) => {
    setToken(response.access_token);
    setUser(response.user);
    persistToken(response.access_token);
  }, []);

  const refreshSession = useCallback(async (): Promise<boolean> => {
    try {
      const refreshed = await authService.refresh();
      setToken(refreshed.access_token);
      persistToken(refreshed.access_token);
      const me = await authService.me(refreshed.access_token);
      setUser(me);
      return true;
    } catch {
      setToken(null);
      setUser(null);
      persistToken(null);
      return false;
    }
  }, []);

  useEffect(() => {
    async function bootstrap() {
      const stored = readToken();
      if (!stored) {
        const refreshed = await refreshSession();
        setIsLoading(false);
        if (!refreshed) return;
        return;
      }

      setToken(stored);
      try {
        const me = await authService.me(stored);
        setUser(me);
      } catch {
        const refreshed = await refreshSession();
        if (!refreshed) {
          persistToken(null);
          setToken(null);
        }
      } finally {
        setIsLoading(false);
      }
    }

    void bootstrap();
  }, [refreshSession]);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await authService.login({ email, password });
      applyAuth(response);
      toast.success("Welcome back!");
      router.push("/dashboard");
    },
    [applyAuth, router],
  );

  const signup = useCallback(
    async (email: string, password: string, fullName: string) => {
      const response = await authService.signup({ email, password, full_name: fullName });
      applyAuth(response);
      toast.success("Account created successfully");
      router.push("/dashboard");
    },
    [applyAuth, router],
  );

  const logout = useCallback(async () => {
    try {
      if (token) {
        await authService.logout(token);
      }
    } catch {
      // ignore logout errors
    } finally {
      setToken(null);
      setUser(null);
      persistToken(null);
      toast.success("Signed out");
      router.push("/login");
    }
  }, [router, token]);

  const value = useMemo(
    () => ({ user, token, isLoading, login, signup, logout, refreshSession }),
    [user, token, isLoading, login, signup, logout, refreshSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

export function getAccessToken(): string | null {
  return readToken();
}
