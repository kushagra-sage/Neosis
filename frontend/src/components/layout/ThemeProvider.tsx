"use client";
import { useEffect, type ReactNode } from "react";
import { useThemeStore } from "@/stores/theme";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme = useThemeStore((s) => s.theme);
  const applyResolved = useThemeStore((s) => s.applyResolved);

  useEffect(() => {
    applyResolved();
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      if (useThemeStore.getState().theme === "system") applyResolved();
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [theme, applyResolved]);

  return <>{children}</>;
}
