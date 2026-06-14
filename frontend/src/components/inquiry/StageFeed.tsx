"use client";
import { AnimatePresence, motion } from "framer-motion";
import type { StageEvent } from "@/stores/inquiry";

const STAGE_LABEL: Record<string, string> = {
  planning: "Planning the inquiry",
  retrieving: "Searching arXiv, Semantic Scholar, OpenAlex",
  retrieved: "Evidence dossier assembled",
  analyzing: "Running computational analysis",
  writing: "Writing the grounded synthesis",
  reviewing: "Peer-reviewing rigor",
  reviewed: "Review complete",
  done: "Inquiry complete",
};

export function StageFeed({ stages }: { stages: StageEvent[] }) {
  if (stages.length === 0) return null;

  return (
    <div className="mb-4 flex flex-col gap-1">
      <AnimatePresence initial={false}>
        {stages.slice(-4).map((s) => (
          <motion.div
            key={`${s.stage}-${s.at}`}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex items-center gap-2 text-xs text-muted"
          >
            <span className="text-accent">▸</span>
            {STAGE_LABEL[s.stage] ?? s.stage}
            <span className="font-mono text-[10px] text-muted/50">
              {new Date(s.at).toLocaleTimeString("en-US", {
                hour12: false,
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
