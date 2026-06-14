"use client";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

export function FollowUps({
  questions,
  onSelect,
}: {
  questions: string[];
  onSelect: (q: string) => void;
}) {
  if (questions.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mt-6 border-t border-border pt-5"
    >
      <p className="mb-2.5 text-[11px] font-medium uppercase tracking-wider text-muted">
        Further research directions
      </p>
      <div className="flex flex-col gap-1.5">
        {questions.map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            className="group flex items-start gap-2.5 rounded-lg border border-border bg-surface px-3 py-2.5 text-left transition-all duration-150 hover:border-accent/40 hover:bg-accent-soft/30"
          >
            <span className="mt-0.5 font-mono text-[11px] text-accent">{i + 1}</span>
            <span className="flex-1 font-serif text-[13px] leading-relaxed text-ink-2 group-hover:text-ink">
              {q}
            </span>
            <ArrowUpRight
              size={13}
              className="mt-1 shrink-0 text-muted transition-colors group-hover:text-accent"
            />
          </button>
        ))}
      </div>
    </motion.div>
  );
}
