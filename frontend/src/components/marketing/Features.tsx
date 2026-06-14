"use client";
import {
  Brain,
  FileSearch,
  GitBranch,
  Layers,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Reveal } from "./Reveal";

const FEATURES = [
  {
    icon: Sparkles,
    title: "Multi-agent reasoning",
    body: "Five specialised operators — Planner, Retriever, Analyst, Writer, Reviewer — orchestrated as a directed graph, not a single prompt.",
  },
  {
    icon: FileSearch,
    title: "Hybrid retrieval",
    body: "Dense vectors, BM25, and three live scholarly APIs fused with Reciprocal Rank Fusion so the best evidence rises to the top.",
  },
  {
    icon: ShieldCheck,
    title: "Automated peer review",
    body: "Every answer is scored on groundedness, citation accuracy, coverage, and rigor — and sent back for revision if it falls short.",
  },
  {
    icon: Layers,
    title: "Research workspaces",
    body: "Organise papers, notes, gaps, experiments, and inquiry history by research line, with domain presets to start fast.",
  },
  {
    icon: GitBranch,
    title: "Grounded citations",
    body: "The Writer may only cite papers actually in the retrieved dossier, with inline [A1] [S2] [O3] labels you can click to verify.",
  },
  {
    icon: Brain,
    title: "Research memory",
    body: "Findings, gaps, and ideas persist across inquiries, so each question builds on everything the workspace already knows.",
  },
];

export function Features() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-5 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <h2 className="font-serif text-4xl font-semibold tracking-tight text-ink">
          A research process, not a chat box
        </h2>
        <p className="mt-4 font-serif text-lg leading-relaxed text-ink-2">
          Noesis treats a question the way a careful researcher does — decompose,
          gather, reason, write, and critique.
        </p>
      </Reveal>

      <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => (
          <Reveal key={f.title} delay={i * 0.06}>
            <div className="group h-full rounded-2xl border border-border bg-surface p-6 transition-all duration-300 hover:-translate-y-1 hover:border-border-strong hover:shadow-lifted">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent transition-colors group-hover:bg-accent group-hover:text-white">
                <f.icon size={18} strokeWidth={1.75} />
              </div>
              <h3 className="text-[15px] font-semibold text-ink">{f.title}</h3>
              <p className="mt-2 font-serif text-sm leading-relaxed text-ink-2">
                {f.body}
              </p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
