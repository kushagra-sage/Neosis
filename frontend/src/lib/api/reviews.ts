import { api } from "./client";
import type {
  LiteratureReviewListItem,
  LiteratureReviewResponse,
} from "@/types/api";

export const reviewsApi = {
  /** POST /workspaces/{id}/reviews — generate a new literature review. */
  create: (workspaceId: string, topic: string): Promise<LiteratureReviewResponse> =>
    api
      .post<LiteratureReviewResponse>(`/workspaces/${workspaceId}/reviews`, { topic })
      .then((r) => r.data),

  list: (workspaceId: string): Promise<LiteratureReviewListItem[]> =>
    api
      .get<LiteratureReviewListItem[]>(`/workspaces/${workspaceId}/reviews`)
      .then((r) => r.data),

  get: (workspaceId: string, reviewId: string): Promise<LiteratureReviewResponse> =>
    api
      .get<LiteratureReviewResponse>(`/workspaces/${workspaceId}/reviews/${reviewId}`)
      .then((r) => r.data),

  remove: (workspaceId: string, reviewId: string): Promise<void> =>
    api.delete(`/workspaces/${workspaceId}/reviews/${reviewId}`).then(() => undefined),
};
