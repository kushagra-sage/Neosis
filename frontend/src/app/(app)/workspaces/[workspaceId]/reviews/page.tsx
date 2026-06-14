"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  BookOpen,
  Loader2,
  Sparkles,
  Trash2,
} from "lucide-react";
import { reviewsApi } from "@/lib/api/reviews";
import { exportApi } from "@/lib/api/exports";
import { workspaceApi } from "@/lib/api/workspaces";
import { extractErrorMessage } from "@/lib/api/client";
import { toast } from "@/stores/toast";
import { Header } from "@/components/layout/Header";
import { PageFade } from "@/components/layout/PageFade";
import { AnswerView } from "@/components/inquiry/AnswerView";
import { ExportMenu } from "@/components/export/ExportMenu";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { timeAgo } from "@/lib/utils";
import type { ExportFormat, ReviewCitation } from "@/types/api";

export default function ReviewsPage({
  params,
}: {
  params: { workspaceId: string };
}) {
  const { workspaceId } = params;
  const qc = useQueryClient();
  const [topic, setTopic] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);

  const { data: workspace } = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => workspaceApi.get(workspaceId),
  });

  const { data: reviews, isLoading } = useQuery({
    queryKey: ["reviews", workspaceId],
    queryFn: () => reviewsApi.list(workspaceId),
  });

  const detail = useQuery({
    queryKey: ["review", workspaceId, openId],
    queryFn: () => reviewsApi.get(workspaceId, openId as string),
    enabled: !!openId,
  });

  const generate = useMutation({
    mutationFn: (t: string) => reviewsApi.create(workspaceId, t),
    onSuccess: (review) => {
      void qc.invalidateQueries({ queryKey: ["reviews", workspaceId] });
      setTopic("");
      setOpenId(review.id);
      toast.success("Literature review ready");
    },
    onError: (e: unknown) =>
      toast.error("Generation failed", extractErrorMessage(e, "Please try again.")),
  });

  const remove = useMutation({
    mutationFn: (id: string) => reviewsApi.remove(workspaceId, id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["reviews", workspaceId] });
      if (openId) setOpenId(null);
      toast.success("Review deleted");
    },
  });

  // ── Detail view ──────────────────────────────────────────────────────────
  if (openId) {
    const r = detail.data;
    return (
      <PageFade>
        <Header
          title="Literature Review"
          subtitle={workspace?.name ?? undefined}
        />
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-6 py-8">
            <div className="mb-4 flex items-center justify-between">
              <Button variant="ghost" size="sm" onClick={() => setOpenId(null)}>
                <ArrowLeft size={14} />
                All reviews
              </Button>
              {r && (
                <ExportMenu
                  onExport={(fmt: ExportFormat) =>
                    exportApi.review(workspaceId, r.id, fmt)
                  }
                />
              )}
            </div>

            {detail.isLoading || !r ? (
              <div className="flex justify-center py-20">
                <Loader2 className="animate-spin text-accent" />
              </div>
            ) : (
              <Card className="p-7">
                <h1 className="font-serif text-2xl font-semibold leading-snug text-ink">
                  {r.title}
                </h1>
                <p className="mt-1 text-[13px] text-muted">
                  {r.citations.length} sources · {timeAgo(r.created_at)}
                </p>
                <div className="mt-5 border-t border-border pt-5">
                  <AnswerView text={r.content} streaming={false} />
                </div>

                {r.citations.length > 0 && (
                  <div className="mt-6 border-t border-border pt-5">
                    <h2 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted">
                      References
                    </h2>
                    <ol className="flex flex-col gap-2">
                      {r.citations.map((c: ReviewCitation, i: number) => (
                        <li key={i} className="flex gap-2 text-[13px] text-ink-2">
                          <span className="font-mono text-muted">[{i + 1}]</span>
                          <span>
                            {(c.authors ?? []).slice(0, 3).join(", ") || "Unknown"}
                            {c.year ? ` (${c.year})` : ""}. <em>{c.title}</em>
                            {c.venue ? `. ${c.venue}` : ""}
                            {c.source ? (
                              <Badge tone="neutral" className="ml-2">
                                {c.source}
                              </Badge>
                            ) : null}
                          </span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      </PageFade>
    );
  }

  // ── List + generate view ───────────────────────────────────────────────────
  return (
    <PageFade>
      <Header
        title="Literature Reviews"
        subtitle={workspace?.name ?? "Generate a structured, cited review"}
      />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-8">
          <Card className="p-5">
            <div className="mb-2 flex items-center gap-2">
              <Sparkles size={16} className="text-accent" />
              <h2 className="text-[15px] font-semibold text-ink">
                Generate a literature review
              </h2>
            </div>
            <p className="mb-3 font-serif text-[13px] leading-relaxed text-ink-2">
              Enter a topic. Noesis retrieves a broad evidence base, clusters
              themes, detects consensus, disagreements, and gaps, then writes a
              structured review with references.
            </p>
            <Textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Attention collapse in vision transformers for medical imaging"
              rows={3}
              disabled={generate.isPending}
            />
            <div className="mt-3 flex justify-end">
              <Button
                onClick={() => generate.mutate(topic.trim())}
                loading={generate.isPending}
                disabled={topic.trim().length < 5}
              >
                {generate.isPending ? "Researching…" : "Generate review"}
              </Button>
            </div>
            {generate.isPending && (
              <p className="mt-2 text-center text-xs text-muted">
                Retrieving sources, clustering themes, and synthesizing — this can
                take a moment.
              </p>
            )}
          </Card>

          <div className="mt-8">
            <h3 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted">
              Saved reviews
            </h3>
            {isLoading ? (
              <div className="flex flex-col gap-2">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : reviews && reviews.length > 0 ? (
              <div className="flex flex-col gap-2">
                {reviews.map((rv) => (
                  <div
                    key={rv.id}
                    className="group flex items-center gap-3 rounded-xl border border-border bg-surface p-4 transition-colors hover:border-border-strong"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-accent">
                      <BookOpen size={16} />
                    </div>
                    <button
                      onClick={() => setOpenId(rv.id)}
                      className="min-w-0 flex-1 text-left"
                    >
                      <p className="truncate text-[14px] font-medium text-ink">
                        {rv.title}
                      </p>
                      <p className="text-[11px] text-muted">{timeAgo(rv.created_at)}</p>
                    </button>
                    <ExportMenu
                      onExport={(fmt: ExportFormat) =>
                        exportApi.review(workspaceId, rv.id, fmt)
                      }
                    />
                    <button
                      onClick={() => remove.mutate(rv.id)}
                      disabled={remove.isPending}
                      aria-label="Delete review"
                      className="shrink-0 rounded-md p-1.5 text-muted opacity-0 transition-all hover:bg-danger-soft hover:text-danger group-hover:opacity-100"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={BookOpen}
                title="No reviews yet"
                description="Generate your first literature review above to see it saved here."
              />
            )}
          </div>
        </div>
      </div>
    </PageFade>
  );
}
