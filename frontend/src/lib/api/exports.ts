import { api } from "./client";
import type { ExportFormat } from "@/types/api";

function triggerDownload(blob: Blob, fallbackName: string, disposition?: string): void {
  let filename = fallbackName;
  if (disposition) {
    const m = /filename="?([^"]+)"?/.exec(disposition);
    if (m?.[1]) filename = m[1];
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export const exportApi = {
  /** GET /export/inquiry/{id}?format= — download an inquiry in the chosen format. */
  inquiry: async (inquiryId: string, format: ExportFormat): Promise<void> => {
    const res = await api.get(`/export/inquiry/${inquiryId}`, {
      params: { format },
      responseType: "blob",
    });
    triggerDownload(
      res.data as Blob,
      `noesis-inquiry.${format === "markdown" ? "md" : format === "bibtex" ? "bib" : format}`,
      res.headers["content-disposition"] as string | undefined,
    );
  },

  /** GET /workspaces/{ws}/reviews/{rid}/export?format= */
  review: async (
    workspaceId: string,
    reviewId: string,
    format: ExportFormat,
  ): Promise<void> => {
    const res = await api.get(
      `/workspaces/${workspaceId}/reviews/${reviewId}/export`,
      { params: { format }, responseType: "blob" },
    );
    triggerDownload(
      res.data as Blob,
      `noesis-review.${format === "markdown" ? "md" : format === "bibtex" ? "bib" : format}`,
      res.headers["content-disposition"] as string | undefined,
    );
  },
};
