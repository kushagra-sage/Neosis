"use client";
import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Command } from "cmdk";
import { AnimatePresence, motion } from "framer-motion";
import { History, Layers, LogOut, Plus, Search } from "lucide-react";
import { workspaceApi } from "@/lib/api/workspaces";
import { useUIStore } from "@/stores/ui";
import { useAuth } from "@/hooks/useAuth";
import { useCommandK, useEscape } from "@/hooks/useHotkey";

export function CommandPalette({ onNewWorkspace }: { onNewWorkspace: () => void }) {
  const open = useUIStore((s) => s.commandOpen);
  const setOpen = useUIStore((s) => s.setCommandOpen);
  const router = useRouter();
  const { logout } = useAuth();

  useCommandK(useCallback(() => setOpen(!open), [open, setOpen]));
  useEscape(useCallback(() => setOpen(false), [setOpen]), open);

  const { data: workspaces = [] } = useQuery({
    queryKey: ["workspaces"],
    queryFn: workspaceApi.list,
    enabled: open,
  });

  const go = (path: string) => {
    setOpen(false);
    router.push(path);
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[18vh]">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-ink/25 backdrop-blur-[2px]"
            onClick={() => setOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -6 }}
            transition={{ type: "spring", stiffness: 460, damping: 34 }}
            className="relative z-10 w-full max-w-lg overflow-hidden rounded-xl border border-border bg-surface shadow-dialog"
          >
            <Command label="Command palette">
              <div className="flex items-center gap-2 border-b border-border px-3.5">
                <Search size={15} className="text-muted" />
                <Command.Input
                  autoFocus
                  placeholder="Search workspaces and actions…"
                  className="h-12 w-full bg-transparent text-sm text-ink outline-none placeholder:text-muted"
                />
              </div>
              <Command.List className="max-h-72 overflow-y-auto p-1.5">
                <Command.Empty className="py-8 text-center text-[13px] text-muted">
                  No results.
                </Command.Empty>

                <Command.Group
                  heading="Actions"
                  className="px-1.5 py-1 text-[11px] font-medium uppercase tracking-wider text-muted [&_[cmdk-group-items]]:mt-1"
                >
                  <Command.Item
                    onSelect={() => {
                      setOpen(false);
                      onNewWorkspace();
                    }}
                    className="flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] text-ink-2 data-[selected=true]:bg-accent-soft data-[selected=true]:text-accent-hover"
                  >
                    <Plus size={14} />
                    New workspace
                  </Command.Item>
                  <Command.Item
                    onSelect={() => go("/workspaces")}
                    className="flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] text-ink-2 data-[selected=true]:bg-accent-soft data-[selected=true]:text-accent-hover"
                  >
                    <Layers size={14} />
                    All workspaces
                  </Command.Item>
                  <Command.Item
                    onSelect={() => void logout()}
                    className="flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] text-ink-2 data-[selected=true]:bg-accent-soft data-[selected=true]:text-accent-hover"
                  >
                    <LogOut size={14} />
                    Sign out
                  </Command.Item>
                </Command.Group>

                {workspaces.length > 0 && (
                  <Command.Group
                    heading="Workspaces"
                    className="px-1.5 py-1 text-[11px] font-medium uppercase tracking-wider text-muted [&_[cmdk-group-items]]:mt-1"
                  >
                    {workspaces.map((ws) => (
                      <Command.Item
                        key={ws.id}
                        value={`${ws.name} ${ws.domain}`}
                        onSelect={() => go(`/workspaces/${ws.id}`)}
                        className="flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] text-ink-2 data-[selected=true]:bg-accent-soft data-[selected=true]:text-accent-hover"
                      >
                        <Layers size={14} />
                        <span className="flex-1 truncate">{ws.name}</span>
                        <History size={12} className="text-muted" />
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}
              </Command.List>
            </Command>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
