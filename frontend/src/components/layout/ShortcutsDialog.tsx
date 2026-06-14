"use client";
import { useEffect, useState } from "react";
import { Dialog } from "@/components/ui/Dialog";
import { Kbd } from "@/components/ui/Kbd";

const SHORTCUTS = [
  { keys: ["⌘", "K"], label: "Open command palette" },
  { keys: ["⏎"], label: "Run inquiry" },
  { keys: ["⇧", "⏎"], label: "New line in composer" },
  { keys: ["Esc"], label: "Close dialog / palette" },
  { keys: ["?"], label: "Show this help" },
];

export function ShortcutsDialog() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const typing =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;
      if (e.key === "?" && !typing) {
        e.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <Dialog
      open={open}
      onClose={() => setOpen(false)}
      title="Keyboard shortcuts"
      description="Move through Noesis without leaving the keyboard."
    >
      <div className="flex flex-col gap-1">
        {SHORTCUTS.map((s) => (
          <div
            key={s.label}
            className="flex items-center justify-between rounded-md px-1 py-2"
          >
            <span className="text-[13px] text-ink-2">{s.label}</span>
            <span className="flex gap-1">
              {s.keys.map((k) => (
                <Kbd key={k}>{k}</Kbd>
              ))}
            </span>
          </div>
        ))}
      </div>
    </Dialog>
  );
}
