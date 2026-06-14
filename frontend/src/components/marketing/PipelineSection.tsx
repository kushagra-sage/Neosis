"use client";
import { motion } from "framer-motion";
import { Reveal } from "./Reveal";

const OPERATORS = [
  { name: "Planner", role: "Decomposes the question, classifies the inquiry type, and routes the pipeline.", tone: "accent" },
  { name: "Retriever", role: "Hybrid search across local + arXiv + Semantic Scholar + OpenAlex, fused with RRF.", tone: "amber" },
  { name: "Analyst", role: "Runs sandboxed computation when a question needs statistics or power analysis.", tone: "sage" },
  { name: "Writer", role: "Streams a grounded synthesis, citing only the retrieved dossier.", tone: "accent" },
  { name: "Reviewer", role: "Scores the answer on four dimensions; gates publication and triggers revision.", tone: "sage" },
] as const;

const toneClass: Record<string, string> = {
  accent: "border-accent/30 bg-accent-soft text-accent-hover",
  amber: "border-amber/30 bg-amber-soft text-amber",
  sage: "border-sage/30 bg-sage-soft text-sage",
};

export function PipelineSection() {
  return (
    <section id="pipeline" className="mx-auto max-w-5xl px-5 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <h2 className="font-serif text-4xl font-semibold tracking-tight text-ink">
          The multi-agent pipeline
        </h2>
        <p className="mt-4 font-serif text-lg leading-relaxed text-ink-2">
          A LangGraph state machine where each operator is wrapped in
          production-grade resilience — circuit breakers, bulkheads, and retries.
        </p>
      </Reveal>

      <div className="mt-14 space-y-3">
        {OPERATORS.map((op, i) => (
          <Reveal key={op.name} delay={i * 0.07}>
            <div className="flex items-center gap-5 rounded-2xl border border-border bg-surface p-5">
              <div
                className={`flex h-11 w-28 shrink-0 items-center justify-center rounded-xl border text-[13px] font-semibold ${toneClass[op.tone]}`}
              >
                {op.name}
              </div>
              <p className="font-serif text-[15px] leading-relaxed text-ink-2">
                {op.role}
              </p>
              {i < OPERATORS.length - 1 && (
                <motion.div
                  className="ml-auto hidden text-2xl text-border-strong sm:block"
                  animate={{ x: [0, 4, 0] }}
                  transition={{ duration: 1.8, repeat: Infinity }}
                >
                  ↓
                </motion.div>
              )}
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.1}>
        <div className="mt-6 rounded-2xl border border-dashed border-border bg-surface-warm/40 p-5 text-center">
          <p className="font-mono text-[13px] text-ink-2">
            Reviewer fails (&lt; 0.5) →{" "}
            <span className="text-accent">back to Writer, once</span>, with
            suggestions injected
          </p>
        </div>
      </Reveal>
    </section>
  );
}
