"use client";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpDown, Layers, Plus, Search, Star } from "lucide-react";
import { workspaceApi } from "@/lib/api/workspaces";
import { useFavoritesStore } from "@/stores/favorites";
import { Header } from "@/components/layout/Header";
import { PageFade } from "@/components/layout/PageFade";
import { WorkspaceCard } from "@/components/workspace/WorkspaceCard";
import { WorkspaceDialog } from "@/components/workspace/WorkspaceDialog";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Dropdown } from "@/components/ui/Dropdown";
import { OnboardingBanner } from "@/components/layout/OnboardingBanner";
import { cn } from "@/lib/utils";
import type { WorkspaceResponse } from "@/types/api";

type SortKey = "recent" | "name" | "oldest";
const SORT_LABEL: Record<SortKey, string> = {
  recent: "Recently updated",
  name: "Name (A–Z)",
  oldest: "Oldest first",
};

export default function WorkspacesPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("recent");
  const [favOnly, setFavOnly] = useState(false);

  const favIds = useFavoritesStore((s) => s.ids);

  const { data: workspaces, isLoading } = useQuery({
    queryKey: ["workspaces"],
    queryFn: workspaceApi.list,
  });

  const filtered = useMemo(() => {
    let list: WorkspaceResponse[] = workspaces ? [...workspaces] : [];
    if (query.trim()) {
      const q = query.toLowerCase();
      list = list.filter(
        (w) =>
          w.name.toLowerCase().includes(q) ||
          (w.description ?? "").toLowerCase().includes(q),
      );
    }
    if (favOnly) list = list.filter((w) => favIds.includes(w.id));
    list.sort((a, b) => {
      if (sort === "name") return a.name.localeCompare(b.name);
      if (sort === "oldest")
        return +new Date(a.updated_at) - +new Date(b.updated_at);
      return +new Date(b.updated_at) - +new Date(a.updated_at);
    });
    return list;
  }, [workspaces, query, favOnly, favIds, sort]);

  const favorites = useMemo(
    () => filtered.filter((w) => favIds.includes(w.id)),
    [filtered, favIds],
  );
  const showFavSection = !favOnly && !query.trim() && favorites.length > 0;

  return (
    <PageFade>
      <Header
        title="Research Workspaces"
        subtitle="Each workspace organises one line of research"
      />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <OnboardingBanner onCreate={() => setCreateOpen(true)} />

          {/* Toolbar */}
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
              />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search workspaces…"
                className="h-9 w-full rounded-md border border-border bg-surface pl-9 pr-3 text-sm text-ink placeholder:text-muted hover:border-border-strong focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15"
              />
            </div>
            <button
              onClick={() => setFavOnly((v) => !v)}
              className={cn(
                "flex h-9 items-center gap-1.5 rounded-md border px-3 text-[13px] font-medium transition-colors",
                favOnly
                  ? "border-amber/40 bg-amber-soft text-amber"
                  : "border-border bg-surface text-ink-2 hover:border-border-strong",
              )}
            >
              <Star size={14} className={favOnly ? "fill-amber" : ""} />
              Favorites
            </button>
            <Dropdown
              align="end"
              trigger={
                <button className="flex h-9 items-center gap-1.5 rounded-md border border-border bg-surface px-3 text-[13px] font-medium text-ink-2 transition-colors hover:border-border-strong">
                  <ArrowUpDown size={14} />
                  {SORT_LABEL[sort]}
                </button>
              }
              items={(Object.keys(SORT_LABEL) as SortKey[]).map((k) => ({
                label: SORT_LABEL[k],
                onSelect: () => setSort(k),
              }))}
            />
            <Button onClick={() => setCreateOpen(true)}>
              <Plus size={15} />
              New
            </Button>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-32 w-full" />
              ))}
            </div>
          ) : filtered.length > 0 ? (
            <>
              {showFavSection && (
                <div className="mb-8">
                  <h2 className="mb-3 flex items-center gap-1.5 text-[13px] font-medium uppercase tracking-wider text-muted">
                    <Star size={13} className="fill-amber text-amber" />
                    Favorites
                  </h2>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {favorites.map((ws, i) => (
                      <WorkspaceCard key={ws.id} ws={ws} index={i} />
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {(showFavSection ? filtered : filtered).map((ws, i) => (
                  <WorkspaceCard key={ws.id} ws={ws} index={i} />
                ))}
              </div>
            </>
          ) : query.trim() || favOnly ? (
            <EmptyState
              icon={Search}
              title="No matching workspaces"
              description="Try a different search term, or clear the favorites filter."
            />
          ) : (
            <EmptyState
              icon={Layers}
              title="No workspaces yet"
              description="Create your first workspace to start organising research, or pick a quick-start preset for a focused domain."
              action={
                <Button onClick={() => setCreateOpen(true)}>
                  <Plus size={14} />
                  Create your first workspace
                </Button>
              }
            />
          )}
        </div>
      </div>

      <WorkspaceDialog open={createOpen} onClose={() => setCreateOpen(false)} />
    </PageFade>
  );
}
