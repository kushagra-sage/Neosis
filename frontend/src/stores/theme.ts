"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | "system";

interface ThemeState {
  theme: Theme;
  resolved: "light" | "dark";
  hydrated: boolean;
  setTheme: (t: Theme) => void;
  markHydrated: () => void;
  applyResolved: () => void;
}

function systemPrefersDark(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resolve(theme: Theme): "light" | "dark" {
  if (theme === "system") return systemPrefersDark() ? "dark" : "light";
  return theme;
}

function paint(resolved: "light" | "dark"): void {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", resolved === "dark");
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "system",
      resolved: "light",
      hydrated: false,

      setTheme: (theme) => {
        const resolved = resolve(theme);
        paint(resolved);
        set({ theme, resolved });
      },

      markHydrated: () => set({ hydrated: true }),

      applyResolved: () => {
        const resolved = resolve(get().theme);
        paint(resolved);
        set({ resolved });
      },
    }),
    {
      name: "noesis-theme",
      partialize: (s) => ({ theme: s.theme }),
      onRehydrateStorage: () => (state) => {
        state?.markHydrated();
        state?.applyResolved();
      },
    },
  ),
);
