"use client";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Reveal } from "./Reveal";
import { Button } from "@/components/ui/Button";

export function CTA() {
  return (
    <section className="px-5 py-24">
      <Reveal className="mx-auto max-w-4xl">
        <div className="relative overflow-hidden rounded-3xl border border-border bg-surface px-8 py-16 text-center shadow-lifted">
          <div className="pointer-events-none absolute inset-0 bg-grid opacity-40" />
          <div className="relative">
            <h2 className="font-serif text-4xl font-semibold tracking-tight text-ink">
              Answers you can cite.
            </h2>
            <p className="mx-auto mt-4 max-w-md font-serif text-lg leading-relaxed text-ink-2">
              Start a workspace, ask your hardest question, and watch the pipeline
              work.
            </p>
            <Link href="/register" className="mt-8 inline-block">
              <Button size="lg">
                Get started free
                <ArrowRight size={16} />
              </Button>
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
