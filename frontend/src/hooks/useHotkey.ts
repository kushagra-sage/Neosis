"use client";
import { useEffect } from "react";

/** Bind ⌘K / Ctrl+K (or any single key with cmd/ctrl) to a callback. */
export function useCommandK(callback: () => void): void {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        callback();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [callback]);
}

/** Bind Escape to a callback. */
export function useEscape(callback: () => void, active = true): void {
  useEffect(() => {
    if (!active) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") callback();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [callback, active]);
}
