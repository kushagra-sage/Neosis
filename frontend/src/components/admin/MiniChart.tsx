"use client";
import { useId } from "react";
import type { DailyPoint } from "@/lib/api/admin";

/** Minimal dependency-free area+line chart for daily count series. */
export function MiniChart({
  data,
  height = 120,
  label,
}: {
  data: DailyPoint[];
  height?: number;
  label?: string;
}) {
  const gradId = useId();
  const w = 600;
  const h = height;
  const pad = 6;

  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-dashed border-border text-xs text-muted"
        style={{ height }}
      >
        No data in this range
      </div>
    );
  }

  const max = Math.max(1, ...data.map((d) => d.count));
  const step = data.length > 1 ? (w - pad * 2) / (data.length - 1) : 0;
  const points = data.map((d, i) => {
    const x = pad + i * step;
    const y = h - pad - (d.count / max) * (h - pad * 2);
    return [x, y] as const;
  });

  const line = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${y}`).join(" ");
  const area = `${line} L${points[points.length - 1]![0]},${h - pad} L${points[0]![0]},${h - pad} Z`;

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      className="w-full"
      style={{ height }}
      role="img"
      aria-label={label ?? "Time series chart"}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--n-accent)" stopOpacity="0.25" />
          <stop offset="100%" stopColor="var(--n-accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradId})`} />
      <path
        d={line}
        fill="none"
        stroke="var(--n-accent)"
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
