"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";

const NODES = ["Planner", "Retriever", "Analyst", "Writer", "Reviewer"];

export function Hero() {
  return (
    <section className="relative overflow-hidden pt-36 pb-24">
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-50" />
      <div className="relative mx-auto max-w-3xl px-5 text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-ink-2 shadow-card"
        >
          <Sparkles size={13} className="text-accent" />
          Multi-agent research, peer-reviewed by design
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="font-serif text-5xl font-semibold leading-[1.08] tracking-tight text-ink sm:text-6xl"
        >
          From a question to a<br />
          <span className="text-gradient">peer-reviewed answer.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.12 }}
          className="mx-auto mt-6 max-w-xl font-serif text-lg leading-relaxed text-ink-2"
        >
          Noesis plans the inquiry, retrieves evidence from arXiv, Semantic
          Scholar, and OpenAlex, writes a grounded synthesis, and reviews its own
          rigor — so every answer arrives with citations you can trust.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-9 flex items-center justify-center gap-3"
        >
          <Link href="/register">
            <Button size="lg">
              Start researching
              <ArrowRight size={16} />
            </Button>
          </Link>
          <a href="#how">
            <Button size="lg" variant="secondary">
              See how it works
            </Button>
          </a>
        </motion.div>

        {/* Animated pipeline ribbon */}
        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="mt-16"
        >
          <div className="mx-auto flex max-w-2xl items-center justify-between rounded-2xl border border-border bg-surface/60 p-3 shadow-lifted backdrop-blur">
            {NODES.map((n, i) => (
              <div key={n} className="flex flex-1 items-center">
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{
                    duration: 2.4,
                    delay: i * 0.4,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="flex-1 rounded-lg bg-accent-soft px-2 py-2 text-center text-[11px] font-medium text-accent-hover"
                >
                  {n}
                </motion.div>
                {i < NODES.length - 1 && (
                  <div className="h-px w-3 shrink-0 bg-border" />
                )}
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
