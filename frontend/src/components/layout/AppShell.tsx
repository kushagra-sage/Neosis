"use client";
import { useState, type ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { CommandPalette } from "./CommandPalette";
import { WorkspaceDialog } from "@/components/workspace/WorkspaceDialog";
import { Toaster } from "@/components/ui/Toaster";
import { ShortcutsDialog } from "./ShortcutsDialog";

export function AppShell({ children }: { children: ReactNode }) {
  const [createOpen, setCreateOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-paper">
      <Sidebar onNewWorkspace={() => setCreateOpen(true)} />
      <div className="flex min-w-0 flex-1 flex-col">{children}</div>

      <CommandPalette onNewWorkspace={() => setCreateOpen(true)} />
      <WorkspaceDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      <ShortcutsDialog />
      <Toaster />
    </div>
  );
}
