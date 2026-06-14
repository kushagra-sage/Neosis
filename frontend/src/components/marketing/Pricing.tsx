"use client";
import Link from "next/link";
import { Check } from "lucide-react";
import { Reveal } from "./Reveal";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const TIERS = [
  {
    name: "Researcher",
    price: "Free Beta",
    blurb: "For individual researchers. Free while Noesis is in beta.",
    features: [
      "Unlimited inquiries",
      "arXiv · Semantic Scholar · OpenAlex retrieval",
      "Workspaces & inquiry history",
      "Document upload & RAG",
    ],
    cta: "Start free",
    href: "/register",
    state: "available" as const,
  },
  {
    name: "Lab",
    price: "Coming Soon",
    blurb: "For active labs and research groups.",
    features: [
      "Everything in Researcher",
      "Shared workspaces",
      "Literature review mode",
      "Export to PDF / DOCX / BibTeX",
    ],
    cta: "Coming soon",
    href: "/register",
    state: "soon" as const,
  },
  {
    name: "Institution",
    price: "Contact Us",
    blurb: "For departments and enterprises.",
    features: [
      "Everything in Lab",
      "SSO & SAML",
      "On-prem deployment",
      "Dedicated support",
    ],
    cta: "Contact us",
    href: "mailto:hello@noesis.app",
    state: "contact" as const,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="border-y border-border bg-surface-warm/40 py-24">
      <div className="mx-auto max-w-5xl px-5">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="font-serif text-4xl font-semibold tracking-tight text-ink">
            Pricing
          </h2>
          <p className="mt-3 font-serif text-lg leading-relaxed text-ink-2">
            Free for researchers during the beta. Plans for labs and institutions
            are on the way.
          </p>
        </Reveal>

        <div className="mt-12 grid gap-4 lg:grid-cols-3">
          {TIERS.map((t, i) => (
            <Reveal key={t.name} delay={i * 0.08}>
              <div
                className={cn(
                  "flex h-full flex-col rounded-2xl border bg-surface p-6",
                  t.state === "available"
                    ? "border-accent shadow-lifted ring-1 ring-accent/20"
                    : "border-border",
                )}
              >
                {t.state === "available" && (
                  <span className="mb-3 inline-flex w-fit rounded-full bg-accent px-2.5 py-0.5 text-[11px] font-semibold text-white">
                    Available now
                  </span>
                )}
                <h3 className="text-[15px] font-semibold text-ink">{t.name}</h3>
                <div className="mt-2">
                  <span className="font-serif text-2xl font-semibold text-ink">
                    {t.price}
                  </span>
                </div>
                <p className="mt-2 text-[13px] text-ink-2">{t.blurb}</p>
                <ul className="mt-5 flex-1 space-y-2.5">
                  {t.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-[13px] text-ink-2">
                      <Check size={15} className="mt-0.5 shrink-0 text-sage" />
                      {f}
                    </li>
                  ))}
                </ul>
                {t.state === "soon" ? (
                  <Button variant="secondary" className="mt-6 w-full" disabled>
                    {t.cta}
                  </Button>
                ) : t.state === "contact" ? (
                  <a href={t.href} className="mt-6">
                    <Button variant="secondary" className="w-full">
                      {t.cta}
                    </Button>
                  </a>
                ) : (
                  <Link href={t.href} className="mt-6">
                    <Button className="w-full">{t.cta}</Button>
                  </Link>
                )}
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
