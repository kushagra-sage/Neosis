"use client";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { History, Layers, MessageSquareText, Plus, BookOpen } from "lucide-react";
import { workspaceApi } from "@/lib/api/workspaces";
import { useUIStore } from "@/stores/ui";
import { Logo } from "./Logo";
import { Kbd } from "@/components/ui/Kbd";
import { cn, truncate } from "@/lib/utils";

export function Sidebar({ onNewWorkspace }: { onNewWorkspace: () => void }) {
  const pathname = usePathname();
  const params = useParams<{ workspaceId?: string }>();
  const activeId = params?.workspaceId;
  const setCommandOpen = useUIStore((s) => s.setCommandOpen);

  const { data: workspaces = [] } = useQuery({
    queryKey: ["workspaces"],
    queryFn: workspaceApi.list,
  });

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-paper">
      {/* Brand */}
      <div className="flex h-14 items-center px-4">
        <Link href="/workspaces" className="transition-opacity hover:opacity-80">
          <Logo />
        </Link>
      </div>

      {/* Search trigger */}
      <div className="px-3 pb-3">
        <button
          onClick={() => setCommandOpen(true)}
          className="flex h-8 w-full items-center justify-between rounded-md border border-border bg-surface px-2.5 text-[13px] text-muted transition-colors hover:border-border-strong"
        >
          <span>Search…</span>
          <span className="flex gap-0.5">
            <Kbd>⌘</Kbd>
            <Kbd>K</Kbd>
          </span>
        </button>
      </div>

      {/* Workspaces */}
      <div className="flex-1 overflow-y-auto px-3 pb-4">
        <div className="mb-1.5 flex items-center justify-between px-1.5">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted">
            Workspaces
          </span>
          <button
            onClick={onNewWorkspace}
            aria-label="New workspace"
            className="rounded p-0.5 text-muted transition-colors hover:bg-surface-warm hover:text-accent"
          >
            <Plus size={14} />
          </button>
        </div>

        <nav className="flex flex-col gap-0.5">
          {workspaces.map((ws) => {
            const isActive = ws.id === activeId;
            return (
              <div key={ws.id}>
                <Link
                  href={`/workspaces/${ws.id}`}
                  className={cn(
                    "group flex items-center gap-2 rounded-md px-2 py-1.5 text-[13px] transition-colors",
                    isActive
                      ? "bg-accent-soft font-medium text-accent-hover"
                      : "text-ink-2 hover:bg-surface-warm hover:text-ink",
                  )}
                >
                  <Layers
                    size={14}
                    className={cn(
                      "shrink-0",
                      isActive ? "text-accent" : "text-muted group-hover:text-ink-2",
                    )}
                  />
                  <span className="truncate">{truncate(ws.name, 26)}</span>
                </Link>

                {isActive && (
                  <div className="ml-3 mt-0.5 flex flex-col gap-0.5 border-l border-border pl-3">
                    <Link
                      href={`/workspaces/${ws.id}`}
                      className={cn(
                        "flex items-center gap-2 rounded-md px-2 py-1 text-xs transition-colors",
                        pathname === `/workspaces/${ws.id}`
                          ? "font-medium text-accent-hover"
                          : "text-muted hover:text-ink",
                      )}
                    >
                      <MessageSquareText size={12} />
                      Console
                    </Link>
                    <Link
                      href={`/workspaces/${ws.id}/history`}
                      className={cn(
                        "flex items-center gap-2 rounded-md px-2 py-1 text-xs transition-colors",
                        pathname.endsWith("/history")
                          ? "font-medium text-accent-hover"
                          : "text-muted hover:text-ink",
                      )}
                    >
                      <History size={12} />
                      History
                    </Link>
                    <Link
                      href={`/workspaces/${ws.id}/reviews`}
                      className={cn(
                        "flex items-center gap-2 rounded-md px-2 py-1 text-xs transition-colors",
                        pathname.endsWith("/reviews")
                          ? "font-medium text-accent-hover"
                          : "text-muted hover:text-ink",
                      )}
                    >
                      <BookOpen size={12} />
                      Reviews
                    </Link>
                  </div>
                )}
              </div>
            );
          })}

          {workspaces.length === 0 && (
            <button
              onClick={onNewWorkspace}
              className="flex items-center gap-2 rounded-md px-2 py-1.5 text-[13px] text-muted transition-colors hover:bg-surface-warm hover:text-ink"
            >
              <Plus size={14} className="text-accent" />
              Create your first workspace
            </button>
          )}
        </nav>
      </div>
    </aside>
  );
}
