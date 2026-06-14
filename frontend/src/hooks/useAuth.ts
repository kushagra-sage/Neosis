"use client";
import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { authApi } from "@/lib/api/auth";
import type { RegisterRequest } from "@/types/api";

/**
 * Authentication actions with correct ordering:
 *   credentials → token pair → profile (explicit token) → persist → navigate.
 * `me()` receives the token explicitly because the axios interceptor reads
 * localStorage, which has not been written yet at that point.
 */
export function useAuth() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const setAuth = useAuthStore((s) => s.setAuth);
  const clear = useAuthStore((s) => s.clear);

  const login = useCallback(
    async (username: string, password: string) => {
      const tokens = await authApi.login(username, password);
      const profile = await authApi.me(tokens.access_token);
      setAuth(tokens, profile);
      router.push("/workspaces");
    },
    [setAuth, router],
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      const tokens = await authApi.register(data);
      const profile = await authApi.me(tokens.access_token);
      setAuth(tokens, profile);
      router.push("/workspaces");
    },
    [setAuth, router],
  );

  const logout = useCallback(async () => {
    try {
      if (refreshToken) await authApi.logout(refreshToken);
    } catch {
      /* token already invalid — proceed with local logout */
    }
    clear();
    router.push("/login");
  }, [refreshToken, clear, router]);

  return { login, register, logout, user, isAuthenticated };
}
