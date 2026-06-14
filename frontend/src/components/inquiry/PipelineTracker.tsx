"use client";
import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const OPERATORS = [
  { id: "planner", label: "Planner", stages: ["planning"] },
  { id: "retriever", label: "Retriever", stages: ["retrieving", "retrieved"] },
  { id: "analyst", label: "Analyst", stages: ["analyzing"] },
  { id: "writer", label: "Writer", stages: ["writing"] },
  { id: "reviewer", label: "Reviewer", stages: ["reviewing", "reviewed"] },
] as const;

const STAGE_ORDER = [
  "planning",
  "retrieving",
  "retrieved",
  "analyzing",
  "writing",
  "reviewing",
  "reviewed",
  "done",
];

type OpState = "idle" | "running" | "done";

function operatorState(
  op: (typeof OPERATORS)[number],
  current: string | null,
  seen: string[],
): OpState {
  if (current === "done") return "done";
  if (current && (op.stages as readonly string[]).includes(current)) return "running";
  const currentIdx = current ? STAGE_ORDER.indexOf(current) : -1;
  const opLastIdx = Math.max(
    ...op.stages.map((s) => STAGE_ORDER.indexOf(s)),
  );
  if (
    (currentIdx > opLastIdx && opLastIdx !== -1) ||
    op.stages.some((s) => seen.includes(s))
  ) {
    // an operator is "done" once any later stage has started
    if (currentIdx > opLastIdx) return "done";
  }
  return "idle";
}

export function PipelineTracker({
  currentStage,
  seenStages,
}: {
  currentStage: string | null;
  seenStages: string[];
}) {
  return (
    <div className="flex items-center gap-0">
      {OPERATORS.map((op, i) => {
        const state = operatorState(op, currentStage, seenStages);
        return (
          <div key={op.id} className="flex items-center">
            <motion.div
              animate={
                state === "running"
                  ? { scale: [1, 1.04, 1] }
                  : { scale: 1 }
              }
              transition={
                state === "running"
                  ? { repeat: Infinity, duration: 1.4, ease: "easeInOut" }
                  : { duration: 0.2 }
              }
              className={cn(
                "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors duration-300",
                state === "idle" && "border-border bg-surface text-muted",
                state === "running" &&
                  "border-accent/40 bg-accent-soft text-accent-hover",
                state === "done" && "border-sage/30 bg-sage-soft text-sage",
              )}
            >
              {state === "running" && <Loader2 size={10} className="animate-spin" />}
              {state === "done" && <Check size={10} />}
              {op.label}
            </motion.div>
            {i < OPERATORS.length - 1 && (
              <div
                className={cn(
                  "h-px w-4 transition-colors duration-300",
                  state === "done" ? "bg-sage/40" : "bg-border",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
