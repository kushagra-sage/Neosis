"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { workspaceApi } from "@/lib/api/workspaces";
import { inquiryApi } from "@/lib/api/inquiries";
import { Header } from "@/components/layout/Header";
import { PageFade } from "@/components/layout/PageFade";
import { HistoryList } from "@/components/inquiry/HistoryList";
import { AnswerView } from "@/components/inquiry/AnswerView";
import { DossierPanel } from "@/components/inquiry/DossierPanel";
import { CriticPanel } from "@/components/inquiry/CriticPanel";
import { Dialog } from "@/components/ui/Dialog";
import { Tabs } from "@/components/ui/Tabs";
import { Spinner } from "@/components/ui/Spinner";
import { formatLatency } from "@/lib/utils";
import { ExportMenu } from "@/components/export/ExportMenu";
import { exportApi } from "@/lib/api/exports";
import type { CriticScores, DossierItem } from "@/types/api";

export default function HistoryPage({
  params,
}: {
  params: { workspaceId: string };
}) {
  const { workspaceId } = params;
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState("answer");

  const { data: workspace } = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => workspaceApi.get(workspaceId),
  });

  const { data: history = [], isLoading } = useQuery({
    queryKey: ["inquiries", workspaceId],
    queryFn: () => inquiryApi.list(workspaceId, 50),
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["inquiry", selectedId],
    queryFn: () => inquiryApi.get(selectedId as string),
    enabled: !!selectedId,
  });

  return (
    <PageFade>
      <Header
        title="Inquiry History"
        subtitle={workspace?.name ?? "Past research questions"}
      />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-8">
          <HistoryList
            items={history}
            loading={isLoading}
            onSelect={(id) => {
              setSelectedId(id);
              setDetailTab("answer");
            }}
          />
        </div>
      </div>

      <Dialog
        open={!!selectedId}
        onClose={() => setSelectedId(null)}
        title="Inquiry detail"
        description={detail ? formatLatency(detail.latency_ms) : undefined}
        width="max-w-2xl"
      >
        {detailLoading || !detail ? (
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        ) : (
          <div className="flex max-h-[70vh] flex-col">
            <div className="mb-3 flex items-start justify-between gap-3">
              <p className="font-serif text-base font-semibold leading-snug text-ink">
                {detail.question}
              </p>
              <div className="shrink-0">
                <ExportMenu
                  onExport={(fmt) => exportApi.inquiry(detail.id, fmt)}
                />
              </div>
            </div>
            <Tabs
              tabs={[
                { id: "answer", label: "Answer" },
                { id: "evidence", label: "Evidence", count: detail.dossier?.length ?? 0 },
                { id: "review", label: "Review" },
              ]}
              active={detailTab}
              onChange={setDetailTab}
            />
            <div className="mt-4 flex-1 overflow-y-auto pr-1">
              {detailTab === "answer" && (
                <AnswerView text={detail.answer ?? "No answer recorded."} streaming={false} />
              )}
              {detailTab === "evidence" && (
                <DossierPanel items={(detail.dossier as DossierItem[]) ?? []} />
              )}
              {detailTab === "review" && (
                <CriticPanel scores={(detail.critic_scores as Partial<CriticScores>) ?? null} />
              )}
            </div>
          </div>
        )}
      </Dialog>
    </PageFade>
  );
}
