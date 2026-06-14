"use client";
import { Fragment, type ReactNode } from "react";

/**
 * Renders a streamed research answer:
 *  - `## headings`, `**bold**`, list bullets
 *  - inline citations like [A1] [S2] [O3] become clickable chips that scroll
 *    to the matching dossier entry
 *  - a terracotta caret pulses while streaming
 */
export function AnswerView({
  text,
  streaming,
  onCitationClick,
}: {
  text: string;
  streaming: boolean;
  onCitationClick?: (label: string) => void;
}) {
  if (!text && !streaming) return null;

  const lines = text.split("\n");

  const renderInline = (line: string, key: number): ReactNode => {
    const parts = line.split(/(\*\*[^*]+\*\*|\[[A-Z]+\d+(?:,\s*[A-Z]+\d+)*\])/g);
    return (
      <Fragment key={key}>
        {parts.map((part, i) => {
          if (/^\*\*[^*]+\*\*$/.test(part)) {
            return <strong key={i}>{part.slice(2, -2)}</strong>;
          }
          if (/^\[[A-Z]+\d+(?:,\s*[A-Z]+\d+)*\]$/.test(part)) {
            const labels = part.slice(1, -1).split(/,\s*/);
            return (
              <span key={i} className="inline-flex gap-0.5 align-baseline">
                {labels.map((label) => (
                  <button
                    key={label}
                    onClick={() => onCitationClick?.(label)}
                    className="rounded border border-accent/25 bg-accent-soft px-1 font-mono text-[10.5px] font-medium leading-[1.5] text-accent-hover transition-colors hover:bg-accent hover:text-white"
                  >
                    {label}
                  </button>
                ))}
              </span>
            );
          }
          return <Fragment key={i}>{part}</Fragment>;
        })}
      </Fragment>
    );
  };

  return (
    <div className="prose-research">
      {lines.map((line, i) => {
        const isLast = i === lines.length - 1;
        const caret = streaming && isLast ? <span className="streaming-caret" /> : null;

        if (line.startsWith("## ")) {
          return (
            <h2 key={i}>
              {renderInline(line.slice(3), i)}
              {caret}
            </h2>
          );
        }
        if (line.startsWith("### ")) {
          return (
            <h3 key={i}>
              {renderInline(line.slice(4), i)}
              {caret}
            </h3>
          );
        }
        if (/^[-*]\s/.test(line)) {
          return (
            <p key={i} className="my-1 pl-5 -indent-3.5">
              <span className="text-border-strong">•&nbsp;&nbsp;</span>
              {renderInline(line.replace(/^[-*]\s/, ""), i)}
              {caret}
            </p>
          );
        }
        if (line.trim() === "") {
          return isLast && caret ? <p key={i}>{caret}</p> : <div key={i} className="h-3" />;
        }
        return (
          <p key={i} className="my-0.5">
            {renderInline(line, i)}
            {caret}
          </p>
        );
      })}
    </div>
  );
}
