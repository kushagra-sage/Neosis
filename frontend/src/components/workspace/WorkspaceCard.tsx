"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BookOpen, FileText, FlaskConical, GitBranch, Star } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { workspaceApi } from "@/lib/api/workspaces";
import { useFavoritesStore } from "@/stores/favorites";
import { timeAgo } from "@/lib/utils";
import type { WorkspaceDomain, WorkspaceResponse } from "@/types/api";

const DOMAIN_META: Record<WorkspaceDomain, { label: string; tone: "accent" | "sage" | "amber" | "neutral" | "danger" }> = {
  ra_severity: { label: "RA Severity", tone: "accent" },
  patent: { label: "Patents", tone: "amber" },
  multimodal_ai: { label: "Multimodal AI", tone: "sage" },
  vlm: { label: "VLM", tone: "danger" },
  custom: { label: "Custom", tone: "neutral" },
};

export function WorkspaceCard({
  ws,
  index = 0,
}: {
  ws: WorkspaceResponse;
  index?: number;
}) {
  const { data: stats } = useQuery({
    queryKey: ["workspace-stats", ws.id],
    queryFn: () => workspaceApi.stats(ws.id),
    staleTime: 60_000,
  });

  const favIds = useFavoritesStore((s) => s.ids);
  const toggleFav = useFavoritesStore((s) => s.toggle);
  const isFav = favIds.includes(ws.id);

  const meta = DOMAIN_META[ws.domain] ?? DOMAIN_META.custom;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <Link href={`/workspaces/${ws.id}`} className="block">
        <Card interactive className="flex h-full flex-col gap-3 p-4">
          <div className="flex items-start justify-between gap-3">
            <p className="font-serif text-[15px] font-semibold leading-snug text-ink">
              {ws.name}
            </p>
            <div className="flex shrink-0 items-center gap-1.5">
              <button
                onClick={(e) => {
                  e.preventDefault();
                  toggleFav(ws.id);
                }}
                aria-label={isFav ? "Unfavorite" : "Favorite"}
                className="rounded p-0.5 text-muted transition-colors hover:text-amber"
              >
                <Star
                  size={14}
                  className={isFav ? "fill-amber text-amber" : ""}
                />
              </button>
              <Badge tone={meta.tone}>{meta.label}</Badge>
            </div>
          </div>

          {ws.description && (
            <p className="line-clamp-2 font-serif text-[13px] leading-relaxed text-ink-2">
              {ws.description}
            </p>
          )}

          <div className="mt-auto flex items-center gap-4 border-t border-border pt-3 text-muted">
            {[
              { icon: FileText, n: stats?.papers ?? 0 },
              { icon: BookOpen, n: stats?.reviews ?? 0 },
              { icon: GitBranch, n: stats?.gaps ?? 0 },
              { icon: FlaskConical, n: stats?.experiments ?? 0 },
            ].map(({ icon: Icon, n }, i) => (
              <span key={i} className="flex items-center gap-1 text-xs">
                <Icon size={12} strokeWidth={1.75} />
                {n}
              </span>
            ))}
            <span className="ml-auto text-[11px] text-muted/70">
              {timeAgo(ws.updated_at)}
            </span>
          </div>
        </Card>
      </Link>
    </motion.div>
  );
}
