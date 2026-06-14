"use client";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { FileText, Library, Loader2, Trash2 } from "lucide-react";
import { documentsApi } from "@/lib/api/documents";
import { extractErrorMessage } from "@/lib/api/client";
import { toast } from "@/stores/toast";
import { UploadZone } from "./UploadZone";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/utils";
import type { DocumentListItem } from "@/types/api";

function statusTone(status: string): "sage" | "amber" | "danger" | "neutral" {
  if (status === "indexed") return "sage";
  if (status === "failed") return "danger";
  if (status === "processing" || status === "pending") return "amber";
  return "neutral";
}

export function KnowledgeBase({ workspaceId }: { workspaceId: string }) {
  const qc = useQueryClient();
  const { data: documents, isLoading } = useQuery({
    queryKey: ["documents", workspaceId],
    queryFn: () => documentsApi.list(workspaceId),
  });

  const remove = useMutation({
    mutationFn: (id: string) => documentsApi.remove(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["documents", workspaceId] });
      toast.success("Document removed");
    },
    onError: (e: unknown) =>
      toast.error("Could not remove", extractErrorMessage(e, "Please try again.")),
  });

  return (
    <div className="flex flex-col gap-6">
      <UploadZone workspaceId={workspaceId} />

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-[13px] font-medium uppercase tracking-wider text-muted">
            Knowledge base
          </h3>
          {documents && documents.length > 0 && (
            <span className="text-xs text-muted">
              {documents.length} {documents.length === 1 ? "document" : "documents"}
            </span>
          )}
        </div>

        {isLoading ? (
          <div className="flex flex-col gap-2">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : documents && documents.length > 0 ? (
          <div className="flex flex-col gap-2">
            {documents.map((d: DocumentListItem) => (
              <div
                key={d.id}
                className="group flex items-start gap-3 rounded-xl border border-border bg-surface p-3.5"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface-warm text-ink-2">
                  <FileText size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[14px] font-medium text-ink">
                    {d.filename}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <Badge tone={statusTone(d.status)}>
                      {d.status === "indexed"
                        ? `Indexed · ${d.chunk_count} chunks`
                        : d.status}
                    </Badge>
                    <span className="text-[11px] uppercase text-muted">{d.kind}</span>
                    <span className="text-[11px] text-muted">
                      {(d.file_size / 1024).toFixed(0)} KB
                    </span>
                    <span className="text-[11px] text-muted">
                      {formatDate(d.created_at)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => remove.mutate(d.id)}
                  disabled={remove.isPending}
                  aria-label="Remove document"
                  className="shrink-0 rounded-md p-1.5 text-muted opacity-0 transition-all hover:bg-danger-soft hover:text-danger group-hover:opacity-100"
                >
                  {remove.isPending ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Library}
            title="No documents yet"
            description="Upload PDFs, Word documents, or notes to ground this workspace's inquiries in your own sources."
          />
        )}
      </div>
    </div>
  );
}
