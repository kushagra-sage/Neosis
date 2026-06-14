import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const tones = {
  neutral: "bg-surface-warm text-ink-2 border-border",
  accent: "bg-accent-soft text-accent-hover border-accent/20",
  sage: "bg-sage-soft text-sage border-sage/20",
  amber: "bg-amber-soft text-amber border-amber/20",
  danger: "bg-danger-soft text-danger border-danger/20",
} as const;

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: keyof typeof tones;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
