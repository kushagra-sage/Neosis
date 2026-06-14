"use client";
import { BookOpen, Quote } from "lucide-react";
import { Reveal } from "./Reveal";

const SAMPLE = [
  { label: "A1", title: "RA-JointNet: Multi-label Joint Severity Classification", src: "arXiv", year: 2024 },
  { label: "S2", title: "Vision Transformers for Rheumatological Assessment", src: "Semantic Scholar", year: 2024 },
  { label: "O3", title: "DEEP Dataset: Standardised RA Radiograph Collection", src: "OpenAlex", year: 2023 },
];

export function EvidenceSection() {
  return (
    <section className="border-y border-border bg-surface-warm/40 py-24">
      <div className="mx-auto grid max-w-5xl gap-12 px-5 lg:grid-cols-2 lg:items-center">
        <Reveal>
          <div>
            <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
              <Quote size={18} />
            </div>
            <h2 className="font-serif text-3xl font-semibold tracking-tight text-ink">
              Every claim, traceable
            </h2>
            <p className="mt-4 font-serif text-[15px] leading-relaxed text-ink-2">
              Noesis builds an evidence dossier before it writes a word. Inline
              citations link straight back to the source paper — click any{" "}
              <span className="rounded border border-accent/25 bg-accent-soft px-1 font-mono text-[12px] text-accent-hover">
                A1
              </span>{" "}
              to inspect the work it rests on. No invented references, ever.
            </p>
            <ul className="mt-5 space-y-2.5">
              {[
                "Relevance scored by Reciprocal Rank Fusion",
                "Citation counts and venue surfaced inline",
                "Source previews with one-click access",
              ].map((t) => (
                <li key={t} className="flex items-center gap-2.5 text-sm text-ink-2">
                  <BookOpen size={14} className="text-accent" />
                  {t}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>

        <Reveal delay={0.12}>
          <div className="space-y-2.5">
            {SAMPLE.map((s) => (
              <div
                key={s.label}
                className="flex items-start gap-3 rounded-xl border border-border bg-surface p-4 shadow-card"
              >
                <span className="mt-0.5 font-mono text-[11px] text-muted">
                  [{s.label}]
                </span>
                <div className="min-w-0">
                  <p className="font-serif text-[13.5px] font-semibold leading-snug text-ink">
                    {s.title}
                  </p>
                  <div className="mt-1.5 flex items-center gap-2">
                    <span className="rounded-full border border-accent/20 bg-accent-soft px-2 py-0.5 text-[11px] font-medium text-accent-hover">
                      {s.src}
                    </span>
                    <span className="text-[11px] text-muted">{s.year}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
