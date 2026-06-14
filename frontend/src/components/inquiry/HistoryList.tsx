"use client";
import { motion } from "framer-motion";
import { CheckCircle2, Clock, History, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatLatency, timeAgo } from "@/lib/utils";
import type { InquiryHistoryItem } from "@/types/api";

const STATUS_META: Record<
  string,
  { icon: typeof CheckCircle2; tone: "sage" | "amber" | "danger" | "neutral"; label: string }
> = {
  success: { icon: CheckCircle2, tone: "sage", label: "Passed" },
  critic_failed: { icon: XCircle, tone: "amber", label: "Revised" },
  failed: { icon: XCircle, tone: "danger", label: "Failed" },
  running: { icon: Clock, tone: "neutral", label: "Running" },
  pending: { icon: Clock, tone: "neutral", label: "Pending" },
};

export function HistoryList({
  items,
  loading,
  onSelect,
}: {
  items: InquiryHistoryItem[];
  loading: boolean;
  onSelect: (id: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        icon={History}
        title="No inquiries yet"
        description="Questions you run in this workspace are recorded here with their answers, evidence, and review scores."
      />
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((item, i) => {
        const meta = STATUS_META[item.status] ?? STATUS_META.pending;
        const Icon = meta!.icon;
        return (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03, duration: 0.25 }}
            onClick={() => onSelect(item.id)}
            className="group flex items-start gap-3 rounded-lg border border-border bg-surface p-3.5 text-left transition-all duration-150 hover:-translate-y-px hover:border-border-strong hover:shadow-card"
          >
            <Icon
              size={15}
              className={
                meta!.tone === "sage"
                  ? "mt-0.5 text-sage"
                  : meta!.tone === "amber"
                    ? "mt-0.5 text-amber"
                    : meta!.tone === "danger"
                      ? "mt-0.5 text-danger"
                      : "mt-0.5 text-muted"
              }
            />
            <div className="min-w-0 flex-1">
              <p className="line-clamp-2 font-serif text-[14px] leading-snug text-ink group-hover:text-accent-hover">
                {item.question}
              </p>
              <div className="mt-1.5 flex items-center gap-2">
                <Badge tone={meta!.tone}>{meta!.label}</Badge>
                {item.inquiry_type && (
                  <span className="text-[11px] text-muted">
                    {item.inquiry_type.replace(/_/g, " ")}
                  </span>
                )}
                <span className="font-mono text-[11px] text-muted/70">
                  {formatLatency(item.latency_ms)}
                </span>
                <span className="ml-auto text-[11px] text-muted/70">
                  {timeAgo(item.created_at)}
                </span>
              </div>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}
