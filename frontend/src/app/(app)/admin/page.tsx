"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  Activity,
  Database,
  Download,
  FileText,
  Layers,
  MessageSquareText,
  ShieldAlert,
  Users,
} from "lucide-react";
import { adminApi, type RangeKey } from "@/lib/api/admin";
import { useAuthStore } from "@/stores/auth";
import { Header } from "@/components/layout/Header";
import { PageFade } from "@/components/layout/PageFade";
import { StatCard } from "@/components/admin/StatCard";
import { MiniChart } from "@/components/admin/MiniChart";
import { Dropdown } from "@/components/ui/Dropdown";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { exportCsv, exportJson } from "@/lib/export";
import { formatLatency, timeAgo } from "@/lib/utils";

const RANGES: { key: RangeKey; label: string }[] = [
  { key: "24h", label: "Last 24 hours" },
  { key: "7d", label: "Last 7 days" },
  { key: "30d", label: "Last 30 days" },
  { key: "90d", label: "Last 90 days" },
  { key: "all", label: "All time" },
];

function bytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}

export default function AdminPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const [range, setRange] = useState<RangeKey>("30d");

  const overview = useQuery({ queryKey: ["admin-overview"], queryFn: adminApi.overview, retry: false });
  const users = useQuery({ queryKey: ["admin-users", range], queryFn: () => adminApi.users(range) });
  const workspaces = useQuery({ queryKey: ["admin-workspaces", range], queryFn: () => adminApi.workspaces(range) });
  const documents = useQuery({ queryKey: ["admin-documents", range], queryFn: () => adminApi.documents(range) });
  const inquiries = useQuery({ queryKey: ["admin-inquiries", range], queryFn: () => adminApi.inquiries(range) });
  const system = useQuery({ queryKey: ["admin-system"], queryFn: adminApi.system, retry: false });

  // 403 → not an admin.
  const forbidden =
    (overview.error as { response?: { status?: number } } | null)?.response?.status === 403;

  if (forbidden) {
    return (
      <PageFade>
        <Header title="Admin" />
        <div className="flex flex-1 items-center justify-center">
          <EmptyState
            icon={ShieldAlert}
            title="Admin access required"
            description="Your account doesn't have administrator privileges. If you believe this is an error, contact your workspace administrator."
            action={<Button onClick={() => router.push("/workspaces")}>Back to workspaces</Button>}
          />
        </div>
      </PageFade>
    );
  }

  const o = overview.data;

  return (
    <PageFade>
      <Header title="Admin Dashboard" subtitle={`Signed in as ${user?.username ?? "admin"}`} />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-6 py-8">
          {/* Range + export toolbar */}
          <div className="mb-6 flex items-center justify-between">
            <Dropdown
              align="start"
              trigger={
                <button className="flex h-9 items-center gap-1.5 rounded-md border border-border bg-surface px-3 text-[13px] font-medium text-ink-2 hover:border-border-strong">
                  <Activity size={14} />
                  {RANGES.find((r) => r.key === range)?.label}
                </button>
              }
              items={RANGES.map((r) => ({ label: r.label, onSelect: () => setRange(r.key) }))}
            />
            <Dropdown
              align="end"
              trigger={
                <Button variant="secondary" size="sm">
                  <Download size={14} />
                  Export
                </Button>
              }
              items={[
                {
                  label: "Recent users (CSV)",
                  onSelect: () =>
                    users.data &&
                    exportCsv(
                      "noesis-users",
                      users.data.recent_users as unknown as Record<string, unknown>[],
                    ),
                },
                {
                  label: "Overview (JSON)",
                  onSelect: () => o && exportJson("noesis-overview", o),
                },
                {
                  label: "Full analytics (JSON)",
                  onSelect: () =>
                    exportJson("noesis-analytics", {
                      overview: o,
                      users: users.data,
                      workspaces: workspaces.data,
                      documents: documents.data,
                      inquiries: inquiries.data,
                      system: system.data,
                    }),
                },
              ]}
            />
          </div>

          {overview.isLoading ? (
            <div className="flex justify-center py-20">
              <Spinner />
            </div>
          ) : (
            <>
              {/* KPI grid */}
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <StatCard icon={Users} label="Total users" value={o?.total_users ?? 0}
                  sublabel={`+${o?.new_users_today ?? 0} today · +${o?.new_users_week ?? 0} this week`} />
                <StatCard icon={Activity} label="Active (DAU/WAU/MAU)"
                  value={`${o?.dau ?? 0}/${o?.wau ?? 0}/${o?.mau ?? 0}`}
                  sublabel={`Growth ${o?.user_growth_rate ?? 0}%`} />
                <StatCard icon={MessageSquareText} label="Inquiries" value={o?.total_inquiries ?? 0}
                  sublabel={`Avg ${formatLatency(inquiries.data?.avg_latency_ms)}`} />
                <StatCard icon={Layers} label="Workspaces" value={o?.total_workspaces ?? 0} />
              </div>

              <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
                <StatCard icon={FileText} label="Documents" value={o?.total_documents ?? 0} />
                <StatCard icon={Database} label="Storage" value={bytes(o?.storage_bytes ?? 0)} />
                <StatCard icon={Activity} label="Redis" value={system.data?.redis ?? "—"} />
                <StatCard icon={Database} label="Qdrant" value={system.data?.qdrant ?? "—"} />
              </div>

              {/* Charts */}
              <div className="mt-6 grid gap-4 lg:grid-cols-2">
                <ChartCard title="User signups">
                  <MiniChart data={users.data?.daily_signups ?? []} label="User signups" />
                </ChartCard>
                <ChartCard title="Query volume">
                  <MiniChart data={inquiries.data?.daily_inquiries ?? []} label="Query volume" />
                </ChartCard>
                <ChartCard title="Document uploads">
                  <MiniChart data={documents.data?.daily_uploads ?? []} label="Document uploads" />
                </ChartCard>
                <ChartCard title="Workspace growth">
                  <MiniChart data={workspaces.data?.daily_created ?? []} label="Workspace growth" />
                </ChartCard>
              </div>

              {/* Tables */}
              <div className="mt-6 grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-border bg-surface p-4">
                  <h3 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted">
                    Recently registered
                  </h3>
                  <div className="flex flex-col gap-1.5">
                    {(users.data?.recent_users ?? []).map((u) => (
                      <div key={u.id} className="flex items-center justify-between gap-2 text-[13px]">
                        <div className="min-w-0">
                          <span className="font-medium text-ink">{u.username}</span>
                          <span className="ml-2 truncate text-muted">{u.email}</span>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          {u.oauth_provider && <Badge tone="sage">{u.oauth_provider}</Badge>}
                          <span className="text-[11px] text-muted">
                            {u.created_at ? timeAgo(u.created_at) : "—"}
                          </span>
                        </div>
                      </div>
                    ))}
                    {(users.data?.recent_users.length ?? 0) === 0 && (
                      <p className="py-4 text-center text-xs text-muted">No users yet</p>
                    )}
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-surface p-4">
                  <h3 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted">
                    Most active workspaces
                  </h3>
                  <div className="flex flex-col gap-1.5">
                    {(workspaces.data?.most_active ?? []).map((w) => (
                      <div key={w.id} className="flex items-center justify-between gap-2 text-[13px]">
                        <span className="min-w-0 truncate font-medium text-ink">{w.name}</span>
                        <Badge tone="accent">{w.inquiries} inquiries</Badge>
                      </div>
                    ))}
                    {(workspaces.data?.most_active.length ?? 0) === 0 && (
                      <p className="py-4 text-center text-xs text-muted">No activity yet</p>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </PageFade>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <h3 className="mb-3 text-[13px] font-medium uppercase tracking-wider text-muted">
        {title}
      </h3>
      {children}
    </div>
  );
}
