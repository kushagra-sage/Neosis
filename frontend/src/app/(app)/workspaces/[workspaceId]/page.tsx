"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { workspaceApi } from "@/lib/api/workspaces";
import { useInquirySocket } from "@/hooks/useInquirySocket";
import { useInquiryStream } from "@/stores/inquiry";
import { extractErrorMessage } from "@/lib/api/client";
import { toast } from "@/stores/toast";
import { Header } from "@/components/layout/Header";
import { PageFade } from "@/components/layout/PageFade";
import { Composer } from "@/components/inquiry/Composer";
import { StageFeed } from "@/components/inquiry/StageFeed";
import { PipelineTracker } from "@/components/inquiry/PipelineTracker";
import { AnswerView } from "@/components/inquiry/AnswerView";
import { FollowUps } from "@/components/inquiry/FollowUps";
import { DossierPanel } from "@/components/inquiry/DossierPanel";
import { CriticPanel } from "@/components/inquiry/CriticPanel";
import { AgentActivity } from "@/components/inquiry/AgentActivity";
import { KnowledgeBase } from "@/components/library/KnowledgeBase";
import { Tabs } from "@/components/ui/Tabs";
import { Dropdown } from "@/components/ui/Dropdown";
import { Dialog } from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { WorkspaceDialog } from "@/components/workspace/WorkspaceDialog";
import { Spinner } from "@/components/ui/Spinner";
import { Sparkles } from "lucide-react";

export default function WorkspaceConsolePage({
  params,
}: {
  params: { workspaceId: string };
}) {
  const { workspaceId } = params;
  const qc = useQueryClient();
  const router = useRouter();

  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [panelTab, setPanelTab] = useState("dossier");

  const { data: workspace, isLoading } = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => workspaceApi.get(workspaceId),
  });

  const { submit, cancel } = useInquirySocket(workspaceId);
  const {
    question,
    answer,
    stages,
    currentStage,
    dossier,
    critic,
    followUps,
    isStreaming,
    error,
  } = useInquiryStream();

  const seenStages = stages.map((s) => s.stage);

  const scrollToCitation = (label: string) => {
    const idx = dossier.findIndex((d) => {
      const num = parseInt(label.replace(/[A-Z]+/g, ""), 10);
      return dossier.indexOf(d) === num - 1;
    });
    const target = idx >= 0 ? idx + 1 : parseInt(label.replace(/[A-Z]+/g, ""), 10);
    setPanelTab("dossier");
    requestAnimationFrame(() => {
      document
        .getElementById(`dossier-${target}`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await workspaceApi.remove(workspaceId);
      await qc.invalidateQueries({ queryKey: ["workspaces"] });
      toast.success("Workspace deleted");
      router.push("/workspaces");
    } catch (e: unknown) {
      toast.error("Could not delete", extractErrorMessage(e, "Please try again."));
      setDeleting(false);
      setDeleteOpen(false);
    }
  };

  if (isLoading) {
    return (
      <PageFade>
        <div className="flex flex-1 items-center justify-center">
          <Spinner />
        </div>
      </PageFade>
    );
  }

  if (!workspace) {
    return (
      <PageFade>
        <Header title="Workspace not found" />
        <div className="flex flex-1 items-center justify-center">
          <p className="font-serif text-sm text-muted">
            This workspace doesn&apos;t exist or you don&apos;t have access.
          </p>
        </div>
      </PageFade>
    );
  }

  const hasActivity = stages.length > 0 || answer.length > 0 || isStreaming;

  return (
    <PageFade>
      <Header
        title={workspace.name}
        subtitle={workspace.description ?? "Research console"}
      />
      <div className="flex min-h-0 flex-1">
        {/* ── Console column ───────────────────────────────────────────── */}
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-center justify-between border-b border-border px-6 py-2.5">
            <div className="min-h-[24px]">
              {hasActivity && (
                <PipelineTracker currentStage={currentStage} seenStages={seenStages} />
              )}
            </div>
            <Dropdown
              align="end"
              trigger={
                <button
                  aria-label="Workspace actions"
                  className="rounded-md p-1.5 text-muted transition-colors hover:bg-surface-warm hover:text-ink"
                >
                  <MoreHorizontal size={16} />
                </button>
              }
              items={[
                { label: "Edit workspace", icon: Pencil, onSelect: () => setEditOpen(true) },
                { label: "Delete workspace", icon: Trash2, danger: true, onSelect: () => setDeleteOpen(true) },
              ]}
            />
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="mx-auto max-w-2xl">
              {!hasActivity ? (
                <div className="flex flex-col items-center justify-center pt-16 text-center">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-border bg-surface-warm">
                    <Sparkles size={20} className="text-accent" strokeWidth={1.5} />
                  </div>
                  <h2 className="font-serif text-xl text-ink">
                    What do you want to know?
                  </h2>
                  <p className="mt-2 max-w-md font-serif text-sm leading-relaxed text-muted">
                    Ask a research question. Noesis plans the inquiry, retrieves
                    evidence from arXiv, Semantic Scholar, and OpenAlex,
                    synthesizes a grounded answer, and peer-reviews its own rigor.
                  </p>
                </div>
              ) : (
                <>
                  <StageFeed stages={stages} />
                  {(isStreaming || stages.length > 0) && (
                    <div className="mb-4">
                      <AgentActivity stages={stages} streaming={isStreaming} />
                    </div>
                  )}
                  {question && (
                    <p className="mb-4 font-serif text-lg font-semibold leading-snug text-ink">
                      {question}
                    </p>
                  )}
                  <AnswerView
                    text={answer}
                    streaming={isStreaming}
                    onCitationClick={scrollToCitation}
                  />
                  {error && (
                    <p className="mt-4 rounded-md border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
                      {error}
                    </p>
                  )}
                  {!isStreaming && followUps.length > 0 && (
                    <FollowUps questions={followUps} onSelect={submit} />
                  )}
                </>
              )}
            </div>
          </div>

          <div className="border-t border-border bg-paper px-6 py-4">
            <div className="mx-auto max-w-2xl">
              <Composer onSubmit={submit} onCancel={cancel} streaming={isStreaming} />
            </div>
          </div>
        </div>

        {/* ── Inspector column ─────────────────────────────────────────── */}
        <aside className="hidden w-80 shrink-0 flex-col border-l border-border bg-paper lg:flex">
          <div className="px-4 pt-3">
            <Tabs
              tabs={[
                { id: "dossier", label: "Evidence", count: dossier.length },
                { id: "review", label: "Review" },
                { id: "library", label: "Library" },
              ]}
              active={panelTab}
              onChange={setPanelTab}
            />
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {panelTab === "dossier" && <DossierPanel items={dossier} />}
            {panelTab === "review" && <CriticPanel scores={critic} />}
            {panelTab === "library" && <KnowledgeBase workspaceId={workspaceId} />}
          </div>
        </aside>
      </div>

      <WorkspaceDialog
        open={editOpen}
        onClose={() => setEditOpen(false)}
        workspace={workspace}
      />

      <Dialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete workspace?"
        description="This permanently removes the workspace and everything in it."
      >
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteOpen(false)} disabled={deleting}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete} loading={deleting}>
            Delete workspace
          </Button>
        </div>
      </Dialog>
    </PageFade>
  );
}
