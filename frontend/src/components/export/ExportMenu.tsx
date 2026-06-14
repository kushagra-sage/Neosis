"use client";
import { useState } from "react";
import { Download, FileCode, FileText, FileType, Loader2 } from "lucide-react";
import { Dropdown } from "@/components/ui/Dropdown";
import { Button } from "@/components/ui/Button";
import { toast } from "@/stores/toast";
import { extractErrorMessage } from "@/lib/api/client";
import type { ExportFormat } from "@/types/api";

const FORMATS: { fmt: ExportFormat; label: string; icon: typeof FileText }[] = [
  { fmt: "pdf", label: "PDF document", icon: FileType },
  { fmt: "docx", label: "Word (DOCX)", icon: FileText },
  { fmt: "markdown", label: "Markdown", icon: FileCode },
  { fmt: "bibtex", label: "BibTeX (citations)", icon: FileCode },
];

export function ExportMenu({
  onExport,
  size = "sm",
  label = "Export",
}: {
  onExport: (fmt: ExportFormat) => Promise<void>;
  size?: "sm" | "md";
  label?: string;
}) {
  const [busy, setBusy] = useState(false);

  const run = async (fmt: ExportFormat) => {
    setBusy(true);
    try {
      await onExport(fmt);
      toast.success("Export ready", `Downloaded as ${fmt.toUpperCase()}.`);
    } catch (e: unknown) {
      toast.error("Export failed", extractErrorMessage(e, "Please try again."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dropdown
      align="end"
      trigger={
        <Button variant="secondary" size={size} disabled={busy}>
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
          {label}
        </Button>
      }
      items={FORMATS.map((f) => ({
        label: f.label,
        icon: f.icon,
        onSelect: () => void run(f.fmt),
      }))}
    />
  );
}
