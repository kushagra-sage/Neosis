import { api } from "./client";
import type { NoteResponse, PaperResponse } from "@/types/api";

export const libraryApi = {
  listPapers: (workspaceId: string, limit = 50): Promise<PaperResponse[]> =>
    api
      .get<PaperResponse[]>(`/workspaces/${workspaceId}/library/papers`, {
        params: { limit },
      })
      .then((r) => r.data),

  deletePaper: (workspaceId: string, paperId: string): Promise<void> =>
    api
      .delete(`/workspaces/${workspaceId}/library/papers/${paperId}`)
      .then(() => undefined),

  listNotes: (workspaceId: string): Promise<NoteResponse[]> =>
    api
      .get<NoteResponse[]>(`/workspaces/${workspaceId}/library/notes`)
      .then((r) => r.data),
};
