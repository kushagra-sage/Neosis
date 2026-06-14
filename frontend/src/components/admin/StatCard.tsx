import type { LucideIcon } from "lucide-react";

export function StatCard({
  icon: Icon,
  label,
  value,
  sublabel,
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  sublabel?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-center gap-2 text-muted">
        <Icon size={15} strokeWidth={1.75} />
        <span className="text-[12px] font-medium uppercase tracking-wider">
          {label}
        </span>
      </div>
      <p className="mt-2 font-serif text-3xl font-semibold text-ink">{value}</p>
      {sublabel && <p className="mt-0.5 text-xs text-muted">{sublabel}</p>}
    </div>
  );
}
