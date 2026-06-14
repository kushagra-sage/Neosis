"use client";
import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { cn } from "@/lib/utils";
import type { CriticScores } from "@/types/api";

const DIMENSIONS: { key: keyof CriticScores; label: string; hint: string }[] = [
  { key: "groundedness", label: "Groundedness", hint: "Every claim traceable to a cited source" },
  { key: "citation_accuracy", label: "Citation accuracy", hint: "Sources represented faithfully" },
  { key: "coverage", label: "Coverage", hint: "Key literature addressed" },
  { key: "rigor", label: "Rigor", hint: "Methodologically sound, no overclaiming" },
];

function barColor(v: number): string {
  if (v >= 0.8) return "bg-sage";
  if (v >= 0.5) return "bg-amber";
  return "bg-danger";
}

export function CriticPanel({ scores }: { scores: Partial<CriticScores> | null }) {
  if (!scores) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="Awaiting peer review"
        description="After the Writer finishes, the Reviewer scores the answer on four research dimensions and gates publication."
      />
    );
  }

  const overall = scores.overall ?? 0;
  const passed = scores.pass ?? overall >= 0.5;

  return (
    <div className="flex flex-col gap-5">
      {/* Verdict */}
      <div
        className={cn(
          "flex items-center justify-between rounded-lg border p-3.5",
          passed
            ? "border-sage/30 bg-sage-soft"
            : "border-amber/30 bg-amber-soft",
        )}
      >
        <div>
          <p
            className={cn(
              "text-[13px] font-semibold",
              passed ? "text-sage" : "text-amber",
            )}
          >
            {passed ? "Passed peer review" : "Sent back for revision"}
          </p>
          {scores.reasoning && (
            <p className="mt-0.5 font-serif text-xs leading-relaxed text-ink-2">
              {scores.reasoning}
            </p>
          )}
        </div>
        <span
          className={cn(
            "font-mono text-xl font-bold",
            passed ? "text-sage" : "text-amber",
          )}
        >
          {Math.round(overall * 100)}
        </span>
      </div>

      {/* Dimension bars */}
      <div className="flex flex-col gap-3.5">
        {DIMENSIONS.map((d) => {
          const raw = scores[d.key];
          const v = typeof raw === "number" ? raw : 0;
          return (
            <div key={d.key}>
              <div className="mb-1 flex items-baseline justify-between">
                <span className="text-[13px] font-medium text-ink">{d.label}</span>
                <span className="font-mono text-xs text-muted">
                  {Math.round(v * 100)}%
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-surface-sunken">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${v * 100}%` }}
                  transition={{ duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }}
                  className={cn("h-full rounded-full", barColor(v))}
                />
              </div>
              <p className="mt-0.5 text-[11px] text-muted">{d.hint}</p>
            </div>
          );
        })}
      </div>

      {scores.suggestions && scores.suggestions.length > 0 && (
        <div>
          <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-muted">
            Reviewer suggestions
          </p>
          <ul className="flex flex-col gap-1.5">
            {scores.suggestions.map((s, i) => (
              <li
                key={i}
                className="border-l-2 border-border pl-2.5 font-serif text-xs leading-relaxed text-ink-2"
              >
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
