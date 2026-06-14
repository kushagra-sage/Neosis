"use client";
import { Reveal } from "./Reveal";

const STEPS = [
  {
    n: "01",
    title: "Ask anything",
    body: "Pose a research question in plain language. The Planner decomposes it into sub-questions and decides which sources and tools the inquiry needs.",
  },
  {
    n: "02",
    title: "Evidence is gathered",
    body: "The Retriever queries arXiv, Semantic Scholar, and OpenAlex in parallel, fuses the rankings, and assembles a de-duplicated dossier.",
  },
  {
    n: "03",
    title: "A grounded answer is written",
    body: "The Writer streams a synthesis in real time, citing only papers from the dossier with inline, clickable references.",
  },
  {
    n: "04",
    title: "Rigor is reviewed",
    body: "The Reviewer scores the answer on four dimensions and, if it's weak, sends it back to the Writer with concrete suggestions.",
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="border-y border-border bg-surface-warm/40 py-24">
      <div className="mx-auto max-w-5xl px-5">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="font-serif text-4xl font-semibold tracking-tight text-ink">
            How Noesis works
          </h2>
          <p className="mt-4 font-serif text-lg leading-relaxed text-ink-2">
            Four stages, one continuous loop — visible to you the whole way.
          </p>
        </Reveal>

        <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-border bg-border sm:grid-cols-2">
          {STEPS.map((s, i) => (
            <Reveal key={s.n} delay={i * 0.08}>
              <div className="h-full bg-surface p-8">
                <span className="font-mono text-sm font-semibold text-accent">
                  {s.n}
                </span>
                <h3 className="mt-3 text-lg font-semibold text-ink">{s.title}</h3>
                <p className="mt-2 font-serif text-sm leading-relaxed text-ink-2">
                  {s.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
