"use client";
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Sparkles, X } from "lucide-react";

const KEY = "noesis-onboarded";

export function OnboardingBanner({ onCreate }: { onCreate: () => void }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(KEY)) setShow(true);
    } catch {
      /* storage unavailable — skip onboarding */
    }
  }, []);

  const dismiss = () => {
    try {
      localStorage.setItem(KEY, "1");
    } catch {
      /* ignore */
    }
    setShow(false);
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
          className="mb-6 overflow-hidden"
        >
          <div className="relative overflow-hidden rounded-2xl border border-accent/20 bg-accent-soft/50 p-5">
            <div className="pointer-events-none absolute inset-0 bg-grid opacity-30" />
            <div className="relative flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent text-white">
                <Sparkles size={18} strokeWidth={1.75} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-[15px] font-semibold text-ink">
                  Welcome to Noesis
                </h3>
                <p className="mt-1 max-w-xl font-serif text-[13px] leading-relaxed text-ink-2">
                  Start by creating a workspace — a home for one line of research.
                  Then ask a question, and watch the pipeline plan, retrieve,
                  write, and peer-review a grounded answer.
                </p>
                <button
                  onClick={() => {
                    dismiss();
                    onCreate();
                  }}
                  className="mt-3 inline-flex items-center gap-1.5 text-[13px] font-medium text-accent transition-colors hover:text-accent-hover"
                >
                  Create your first workspace
                  <ArrowRight size={14} />
                </button>
              </div>
              <button
                onClick={dismiss}
                aria-label="Dismiss"
                className="shrink-0 rounded-md p-1 text-muted transition-colors hover:bg-surface-warm hover:text-ink"
              >
                <X size={16} />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
