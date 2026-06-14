"use client";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";
import type { StageEvent } from "@/stores/inquiry";
import { cn } from "@/lib/utils";

const STAGE_DETAIL: Record<string, { label: string; detail: string }> = {
  planning: { label: "Planner", detail: "Decomposing the question into sub-inquiries" },
  retrieving: { label: "Retriever", detail: "Querying arXiv · Semantic Scholar · OpenAlex" },
  retrieved: { label: "Retriever", detail: "Fused evidence with Reciprocal Rank Fusion" },
  analyzing: { label: "Analyst", detail: "Running sandboxed computation" },
  writing: { label: "Writer", detail: "Synthesising a grounded, cited answer" },
  reviewing: { label: "Reviewer", detail: "Scoring groundedness, citations, coverage, rigor" },
  reviewed: { label: "Reviewer", detail: "Review complete" },
  done: { label: "Pipeline", detail: "Inquiry complete" },
};

export function AgentActivity({
  stages,
  streaming,
}: {
  stages: StageEvent[];
  streaming: boolean;
}) {
  if (stages.length === 0) return null;

  return (
    <div className="rounded-xl border border-border bg-surface-warm/40 p-3">
      <p className="mb-2 px-1 text-[11px] font-medium uppercase tracking-wider text-muted">
        Agent activity
      </p>
      <div className="flex flex-col">
        <AnimatePresence initial={false}>
          {stages.map((s, i) => {
            const meta = STAGE_DETAIL[s.stage] ?? { label: s.stage, detail: "" };
            const isLast = i === stages.length - 1;
            const active = streaming && isLast && s.stage !== "done";
            return (
              <motion.div
                key={`${s.stage}-${s.at}`}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25 }}
                className="flex gap-3 px-1 py-1.5"
              >
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "flex h-5 w-5 items-center justify-center rounded-full",
                      active ? "bg-accent-soft" : "bg-sage-soft",
                    )}
                  >
                    {active ? (
                      <Loader2 size={11} className="animate-spin text-accent" />
                    ) : (
                      <Check size={11} className="text-sage" />
                    )}
                  </div>
                  {!isLast && <div className="my-0.5 h-full min-h-3 w-px bg-border" />}
                </div>
                <div className="pb-0.5">
                  <p className="text-[13px] font-medium text-ink">{meta.label}</p>
                  <p className="text-[12px] text-muted">{meta.detail}</p>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
