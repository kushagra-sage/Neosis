"use client";
import { useRef, useState, type KeyboardEvent } from "react";
import { ArrowUp, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { Kbd } from "@/components/ui/Kbd";

const PLACEHOLDERS = [
  "What are state-of-the-art methods for RA severity classification from radiographs?",
  "Identify research gaps in vision-language models for medical diagnosis",
  "Survey the literature on federated learning for clinical imaging",
  "Design an experiment to evaluate joint-level inflammation biomarkers",
];

export function Composer({
  onSubmit,
  onCancel,
  streaming,
  initialValue = "",
}: {
  onSubmit: (q: string) => void;
  onCancel: () => void;
  streaming: boolean;
  initialValue?: string;
}) {
  const [value, setValue] = useState(initialValue);
  const [placeholder] = useState(
    () => PLACEHOLDERS[Math.floor(Math.random() * PLACEHOLDERS.length)] ?? PLACEHOLDERS[0],
  );
  const taRef = useRef<HTMLTextAreaElement>(null);

  const valid = value.trim().length >= 5;

  const submit = () => {
    if (!valid || streaming) return;
    onSubmit(value.trim());
    setValue("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div
      className={cn(
        "rounded-xl border bg-surface shadow-card transition-colors duration-200",
        streaming
          ? "border-accent/40"
          : "border-border focus-within:border-accent/50 focus-within:shadow-lifted",
      )}
    >
      <textarea
        ref={taRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        disabled={streaming}
        placeholder={placeholder}
        rows={2}
        maxLength={2000}
        className="w-full resize-none bg-transparent px-4 pt-3.5 font-serif text-[15px] leading-relaxed text-ink outline-none placeholder:text-muted/60 disabled:opacity-60"
      />
      <div className="flex items-center justify-between px-3 pb-2.5 pt-1">
        <span className="flex items-center gap-1.5 text-[11px] text-muted">
          <Kbd>⏎</Kbd> to run
          <span className="text-muted/50">·</span>
          <Kbd>⇧⏎</Kbd> newline
        </span>
        {streaming ? (
          <button
            onClick={onCancel}
            className="flex h-8 items-center gap-1.5 rounded-lg border border-danger/25 bg-danger-soft px-3 text-xs font-medium text-danger transition-colors hover:bg-danger hover:text-white"
          >
            <Square size={11} className="fill-current" />
            Stop
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!valid}
            aria-label="Run inquiry"
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-150",
              valid
                ? "bg-accent text-white shadow-card hover:bg-accent-hover active:scale-95"
                : "bg-surface-sunken text-muted",
            )}
          >
            <ArrowUp size={15} strokeWidth={2.25} />
          </button>
        )}
      </div>
    </div>
  );
}
