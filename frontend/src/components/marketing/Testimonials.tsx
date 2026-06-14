"use client";
import {
  BookOpen,
  FileSearch,
  GitBranch,
  Layers,
  Quote,
  Sparkles,
} from "lucide-react";
import { Reveal } from "./Reveal";

const REASONS = [
  {
    icon: Quote,
    title: "Evidence-backed answers",
    body: "Every response is grounded in retrieved papers — never the model's imagination.",
  },
  {
    icon: GitBranch,
    title: "Citation-aware synthesis",
    body: "Inline citations link each claim to its source, so you can verify in one click.",
  },
  {
    icon: Sparkles,
    title: "Multi-agent research workflow",
    body: "Planner, Retriever, Analyst, Writer, and Reviewer collaborate on every inquiry.",
  },
  {
    icon: Layers,
    title: "Workspace-driven management",
    body: "Organise papers, notes, gaps, and inquiry history by research line.",
  },
  {
    icon: FileSearch,
    title: "Document-grounded retrieval",
    body: "Upload your own PDFs and notes; Noesis searches them alongside scholarly sources.",
  },
  {
    icon: BookOpen,
    title: "Literature review generation",
    body: "Cluster themes, surface consensus and disagreement, and find the open gaps.",
  },
];

/** "Why Noesis" — replaces placeholder testimonials with real platform value. */
export function Testimonials() {
  return (
    <section className="mx-auto max-w-6xl px-5 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <h2 className="font-serif text-4xl font-semibold tracking-tight text-ink">
          Why Noesis
        </h2>
        <p className="mt-4 font-serif text-lg leading-relaxed text-ink-2">
          A research platform built around evidence, rigor, and the way real
          inquiry actually works.
        </p>
      </Reveal>

      <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {REASONS.map((r, i) => (
          <Reveal key={r.title} delay={i * 0.06}>
            <div className="h-full rounded-2xl border border-border bg-surface p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
                <r.icon size={18} strokeWidth={1.75} />
              </div>
              <h3 className="text-[15px] font-semibold text-ink">{r.title}</h3>
              <p className="mt-2 font-serif text-sm leading-relaxed text-ink-2">
                {r.body}
              </p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
