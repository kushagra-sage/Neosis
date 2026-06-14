"use client";
import { motion } from "framer-motion";
import { ExternalLink, Library } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import type { DossierItem } from "@/types/api";

const SOURCE_TONE: Record<string, "accent" | "sage" | "amber" | "neutral"> = {
  document: "accent",
  arxiv: "accent",
  semantic_scholar: "sage",
  openalex: "amber",
  local_dense: "neutral",
  local_bm25: "neutral",
  bm25: "neutral",
};

const SOURCE_LABEL: Record<string, string> = {
  document: "Uploaded Document",
  arxiv: "arXiv",
  semantic_scholar: "Semantic Scholar",
  openalex: "OpenAlex",
  local_dense: "Library",
  local_bm25: "Library · BM25",
  bm25: "Library · BM25",
};

export function DossierPanel({ items }: { items: DossierItem[] }) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon={Library}
        title="No evidence yet"
        description="Run an inquiry and the retrieved papers will appear here, ranked by reciprocal rank fusion."
      />
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((item, i) => (
        <motion.div
          key={item.id}
          id={`dossier-${i + 1}`}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.04, duration: 0.25 }}
          className="rounded-lg border border-border bg-surface p-3 transition-colors hover:border-border-strong"
        >
          <div className="flex items-start gap-2.5">
            <span className="mt-0.5 shrink-0 font-mono text-[11px] text-muted">
              [{i + 1}]
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-serif text-[13.5px] font-semibold leading-snug text-ink">
                {item.title}
              </p>
              {item.authors && item.authors.length > 0 && (
                <p className="mt-0.5 truncate text-xs text-muted">
                  {item.authors.slice(0, 4).join(", ")}
                  {item.authors.length > 4 ? " et al." : ""}
                </p>
              )}
              <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                <Badge tone={SOURCE_TONE[item.source] ?? "neutral"}>
                  {SOURCE_LABEL[item.source] ?? item.source}
                </Badge>
                {item.year != null && (
                  <span className="text-[11px] text-muted">{item.year}</span>
                )}
                {item.citation_count != null && (
                  <span className="text-[11px] text-muted">
                    {item.citation_count} citations
                  </span>
                )}
                {item.rrf_score != null && (
                  <span className="font-mono text-[10px] text-muted/60">
                    rrf {item.rrf_score.toFixed(4)}
                  </span>
                )}
              </div>
            </div>
            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                aria-label="Open source"
                className="shrink-0 rounded p-1 text-muted transition-colors hover:bg-surface-warm hover:text-accent"
              >
                <ExternalLink size={13} />
              </a>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
