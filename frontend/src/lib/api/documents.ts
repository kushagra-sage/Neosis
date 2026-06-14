import { api } from "./client";
import type { DocumentListItem, DocumentResponse } from "@/types/api";

export type UploadKind = "pdf" | "docx" | "txt" | "markdown";

export function detectKind(filename: string): UploadKind | null {
  const ext = filename.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "pdf":
      return "pdf";
    case "docx":
    case "doc":
      return "docx";
    case "txt":
      return "txt";
    case "md":
    case "markdown":
      return "markdown";
    default:
      return null;
  }
}

export const documentsApi = {
  /** POST /documents/upload — multipart upload to the workspace knowledge base. */
  upload: (
    file: File,
    workspaceId?: string,
    onProgress?: (pct: number) => void,
  ): Promise<DocumentResponse> => {
    const form = new FormData();
    form.append("file", file);
    if (workspaceId) form.append("workspace_id", workspaceId);
    return api
      .post<DocumentResponse>("/documents/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (onProgress && e.total) {
            onProgress(Math.min(99, Math.round((e.loaded / e.total) * 100)));
          }
        },
      })
      .then((r) => {
        onProgress?.(100);
        return r.data;
      });
  },

  /** GET /documents — list the caller's documents (optionally per workspace). */
  list: (workspaceId?: string): Promise<DocumentListItem[]> =>
    api
      .get<DocumentListItem[]>("/documents", {
        params: { workspace_id: workspaceId },
      })
      .then((r) => r.data),

  /** GET /documents/{id} */
  get: (id: string): Promise<DocumentResponse> =>
    api.get<DocumentResponse>(`/documents/${id}`).then((r) => r.data),

  /** DELETE /documents/{id} */
  remove: (id: string): Promise<void> =>
    api.delete(`/documents/${id}`).then(() => undefined),
};
