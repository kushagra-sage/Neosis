import { api } from "./client";
import type {
  InquiryHistoryItem,
  InquiryRequest,
  InquiryResponse,
} from "@/types/api";

export const inquiryApi = {
  /** POST /inquiries — synchronous run; resolves when the pipeline finishes. */
  run: (data: InquiryRequest): Promise<InquiryResponse> =>
    api.post<InquiryResponse>("/inquiries", data).then((r) => r.data),

  /** GET /inquiries — history, optionally scoped to a workspace. */
  list: (
    workspaceId?: string,
    limit = 20,
  ): Promise<InquiryHistoryItem[]> =>
    api
      .get<InquiryHistoryItem[]>("/inquiries", {
        params: { workspace_id: workspaceId, limit },
      })
      .then((r) => r.data),

  /** GET /inquiries/{id} — full inquiry detail. */
  get: (id: string): Promise<InquiryResponse> =>
    api.get<InquiryResponse>(`/inquiries/${id}`).then((r) => r.data),
};
