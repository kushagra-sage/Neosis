"use client";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { Reveal } from "./Reveal";
import { cn } from "@/lib/utils";

const QA = [
  {
    q: "How is Noesis different from a chatbot?",
    a: "A chatbot answers from its weights. Noesis runs a pipeline: it plans the inquiry, retrieves real papers from scholarly APIs, writes a synthesis that may only cite that evidence, and then peer-reviews its own rigor before showing you anything.",
  },
  {
    q: "Where does the evidence come from?",
    a: "Three live scholarly sources — arXiv, Semantic Scholar, and OpenAlex — plus any documents you add to a workspace. Results are fused with Reciprocal Rank Fusion so papers multiple sources agree on rank highest.",
  },
  {
    q: "Can it hallucinate citations?",
    a: "The Writer is constrained to cite only papers in the retrieved dossier, and the Reviewer scores citation accuracy explicitly. If groundedness is weak, the answer is sent back for revision.",
  },
  {
    q: "Is my research private?",
    a: "Workspaces are scoped to your account, and retrieval is filtered per workspace. Institution plans support on-prem deployment for full data control.",
  },
  {
    q: "What does the self-review actually measure?",
    a: "Four dimensions: groundedness, citation accuracy, coverage, and rigor — each scored 0 to 1, combined into a weighted overall score that gates publication.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section id="faq" className="mx-auto max-w-3xl px-5 py-24">
      <Reveal className="text-center">
        <h2 className="font-serif text-4xl font-semibold tracking-tight text-ink">
          Frequently asked
        </h2>
      </Reveal>
      <div className="mt-12 divide-y divide-border rounded-2xl border border-border bg-surface">
        {QA.map((item, i) => {
          const isOpen = open === i;
          return (
            <div key={i}>
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
              >
                <span className="text-[15px] font-medium text-ink">{item.q}</span>
                <ChevronDown
                  size={17}
                  className={cn(
                    "shrink-0 text-muted transition-transform duration-300",
                    isOpen && "rotate-180",
                  )}
                />
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.28, ease: [0.25, 0.1, 0.25, 1] }}
                    className="overflow-hidden"
                  >
                    <p className="px-5 pb-5 font-serif text-[15px] leading-relaxed text-ink-2">
                      {item.a}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </section>
  );
}
