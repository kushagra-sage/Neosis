import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Card({
  className,
  interactive = false,
  ...props
}: HTMLAttributes<HTMLDivElement> & { interactive?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-surface shadow-card",
        interactive &&
          "transition-all duration-200 ease-swift hover:-translate-y-0.5 hover:border-border-strong hover:shadow-lifted cursor-pointer",
        className,
      )}
      {...props}
    />
  );
}
