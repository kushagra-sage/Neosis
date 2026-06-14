"use client";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Dialog } from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { workspaceApi } from "@/lib/api/workspaces";
import { extractErrorMessage } from "@/lib/api/client";
import { toast } from "@/stores/toast";
import { cn } from "@/lib/utils";
import type { WorkspaceDomain, WorkspaceResponse } from "@/types/api";

const DOMAINS: { value: WorkspaceDomain; label: string }[] = [
  { value: "custom", label: "Custom" },
  { value: "ra_severity", label: "RA Severity" },
  { value: "patent", label: "Patents" },
  { value: "multimodal_ai", label: "Multimodal AI" },
  { value: "vlm", label: "VLM" },
];

/** Create (no `workspace` prop) or edit (with `workspace`) a workspace. */
export function WorkspaceDialog({
  open,
  onClose,
  workspace,
}: {
  open: boolean;
  onClose: () => void;
  workspace?: WorkspaceResponse;
}) {
  const isEdit = !!workspace;
  const qc = useQueryClient();
  const router = useRouter();

  const [name, setName] = useState("");
  const [domain, setDomain] = useState<WorkspaceDomain>("custom");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setName(workspace?.name ?? "");
      setDomain(workspace?.domain ?? "custom");
      setDescription(workspace?.description ?? "");
      setError("");
    }
  }, [open, workspace]);

  const { data: presets = [] } = useQuery({
    queryKey: ["presets"],
    queryFn: workspaceApi.presets,
    enabled: open && !isEdit,
  });

  const createMut = useMutation({
    mutationFn: () =>
      workspaceApi.create({ name: name.trim(), domain, description: description.trim() || null }),
    onSuccess: (ws) => {
      void qc.invalidateQueries({ queryKey: ["workspaces"] });
      toast.success("Workspace created", ws.name);
      onClose();
      router.push(`/workspaces/${ws.id}`);
    },
    onError: (e: unknown) => setError(extractErrorMessage(e, "Failed to create workspace")),
  });

  const updateMut = useMutation({
    mutationFn: () =>
      workspaceApi.update(workspace?.id ?? "", {
        name: name.trim(),
        description: description.trim() || null,
      }),
    onSuccess: (ws) => {
      void qc.invalidateQueries({ queryKey: ["workspaces"] });
      void qc.invalidateQueries({ queryKey: ["workspace", ws.id] });
      toast.success("Workspace updated");
      onClose();
    },
    onError: (e: unknown) => setError(extractErrorMessage(e, "Failed to update workspace")),
  });

  const presetMut = useMutation({
    mutationFn: (key: string) => workspaceApi.fromPreset(key),
    onSuccess: (ws) => {
      void qc.invalidateQueries({ queryKey: ["workspaces"] });
      toast.success("Workspace created", ws.name);
      onClose();
      router.push(`/workspaces/${ws.id}`);
    },
    onError: (e: unknown) => setError(extractErrorMessage(e, "Failed to create workspace")),
  });

  const pending = createMut.isPending || updateMut.isPending || presetMut.isPending;

  const submit = () => {
    if (name.trim().length < 2) {
      setError("Name must be at least 2 characters");
      return;
    }
    if (isEdit) updateMut.mutate();
    else createMut.mutate();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={isEdit ? "Edit workspace" : "New workspace"}
      description={
        isEdit
          ? "Rename or update the research focus."
          : "A workspace organises one line of research."
      }
    >
      {!isEdit && presets.length > 0 && (
        <div className="mb-5">
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted">
            Quick start
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {presets.map((p) => (
              <button
                key={p.key}
                disabled={pending}
                onClick={() => presetMut.mutate(p.key)}
                className="rounded-lg border border-border bg-surface-warm p-2.5 text-left transition-colors hover:border-accent/40 hover:bg-accent-soft/40 disabled:opacity-50"
              >
                <p className="text-[13px] font-medium text-ink">{p.name}</p>
                <p className="mt-0.5 line-clamp-1 text-[11px] text-muted">{p.description}</p>
              </button>
            ))}
          </div>
          <div className="my-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-[11px] text-muted">or custom</span>
            <div className="h-px flex-1 bg-border" />
          </div>
        </div>
      )}

      <div className="flex flex-col gap-4">
        <Input
          id="ws-name"
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. VLM Research 2026"
          maxLength={160}
        />

        {!isEdit && (
          <div className="flex flex-col gap-1.5">
            <span className="text-[13px] font-medium text-ink-2">Domain</span>
            <div className="flex flex-wrap gap-1.5">
              {DOMAINS.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setDomain(d.value)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                    domain === d.value
                      ? "border-accent bg-accent-soft text-accent-hover"
                      : "border-border text-muted hover:border-border-strong hover:text-ink-2",
                  )}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <Textarea
          id="ws-desc"
          label="Description"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What is this research thread about? (optional)"
          maxLength={1000}
        />

        {error && (
          <p className="rounded-md border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button onClick={submit} loading={createMut.isPending || updateMut.isPending}>
            {isEdit ? "Save changes" : "Create workspace"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
