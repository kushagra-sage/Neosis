"use client";
import { useCallback, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  CheckCircle2,
  FileText,
  Loader2,
  Upload,
  X,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { detectKind, documentsApi, type UploadKind } from "@/lib/api/documents";
import { extractErrorMessage } from "@/lib/api/client";
import { toast } from "@/stores/toast";
import { cn } from "@/lib/utils";

interface QueuedFile {
  id: string;
  name: string;
  size: number;
  kind: UploadKind;
  progress: number;
  status: "uploading" | "done" | "error";
  error?: string;
}

const KIND_LABEL: Record<UploadKind, string> = {
  pdf: "PDF",
  docx: "DOCX",
  txt: "TXT",
  markdown: "Markdown",
};

export function UploadZone({ workspaceId }: { workspaceId: string }) {
  const qc = useQueryClient();
  const [dragging, setDragging] = useState(false);
  const [files, setFiles] = useState<QueuedFile[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (fileList: FileList) => {
      Array.from(fileList).forEach((file) => {
        const kind = detectKind(file.name);
        if (!kind) {
          toast.error("Unsupported file", `${file.name} is not a PDF, DOCX, TXT, or Markdown file.`);
          return;
        }
        const id = `${file.name}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
        setFiles((prev) => [
          ...prev,
          { id, name: file.name, size: file.size, kind, progress: 0, status: "uploading" },
        ]);

        void documentsApi.upload(file, workspaceId, (pct) =>
          setFiles((prev) =>
            prev.map((f) => (f.id === id ? { ...f, progress: pct } : f)),
          ),
        )
          .then(() => {
            setFiles((prev) =>
              prev.map((f) =>
                f.id === id ? { ...f, progress: 100, status: "done" } : f,
              ),
            );
            void qc.invalidateQueries({ queryKey: ["documents", workspaceId] });
            toast.success("Added to knowledge base", file.name);
          })
          .catch((e: unknown) => {
            const error = extractErrorMessage(e, "Upload failed");
            setFiles((prev) =>
              prev.map((f) =>
                f.id === id ? { ...f, status: "error", error } : f,
              ),
            );
            toast.error("Upload failed", error);
          });
      });
    },
    [workspaceId, qc],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  return (
    <div className="flex flex-col gap-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-colors",
          dragging
            ? "border-accent bg-accent-soft/50"
            : "border-border bg-surface-warm/40 hover:border-border-strong",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.txt,.md,.markdown"
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-accent-soft text-accent">
          <Upload size={20} strokeWidth={1.75} />
        </div>
        <p className="text-[15px] font-medium text-ink">
          Drop documents here, or click to browse
        </p>
        <p className="mt-1 text-[13px] text-muted">
          PDF, DOCX, TXT, and Markdown · added to this workspace&apos;s knowledge base
        </p>
      </div>

      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col gap-2"
          >
            {files.map((f) => (
              <motion.div
                key={f.id}
                layout
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-3 rounded-xl border border-border bg-surface p-3"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface-warm text-ink-2">
                  <FileText size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-[13px] font-medium text-ink">
                      {f.name}
                    </p>
                    <span className="shrink-0 rounded bg-surface-warm px-1.5 py-0.5 text-[10px] font-medium text-muted">
                      {KIND_LABEL[f.kind]}
                    </span>
                  </div>
                  <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-surface-sunken">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-300",
                        f.status === "error" ? "bg-danger" : "bg-accent",
                      )}
                      style={{ width: `${f.progress}%` }}
                    />
                  </div>
                  {f.error && (
                    <p className="mt-1 text-[11px] text-danger">{f.error}</p>
                  )}
                </div>
                <div className="shrink-0">
                  {f.status === "uploading" && (
                    <Loader2 size={15} className="animate-spin text-accent" />
                  )}
                  {f.status === "done" && (
                    <CheckCircle2 size={15} className="text-sage" />
                  )}
                  {f.status === "error" && (
                    <button
                      onClick={() =>
                        setFiles((prev) => prev.filter((x) => x.id !== f.id))
                      }
                      className="text-muted hover:text-ink"
                    >
                      <X size={15} />
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
