"use client";
import { Monitor, Moon, Sun } from "lucide-react";
import { useThemeStore, type Theme } from "@/stores/theme";
import { cn } from "@/lib/utils";

const OPTIONS: { value: Theme; icon: typeof Sun; label: string }[] = [
  { value: "light", icon: Sun, label: "Light" },
  { value: "dark", icon: Moon, label: "Dark" },
  { value: "system", icon: Monitor, label: "System" },
];

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  return (
    <div
      className={cn(
        "inline-flex items-center gap-0.5 rounded-lg border border-border bg-surface-warm p-0.5",
        compact && "scale-95",
      )}
    >
      {OPTIONS.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          aria-label={label}
          title={label}
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md transition-colors",
            theme === value
              ? "bg-surface text-ink shadow-card"
              : "text-muted hover:text-ink",
          )}
        >
          <Icon size={14} />
        </button>
      ))}
    </div>
  );
}
