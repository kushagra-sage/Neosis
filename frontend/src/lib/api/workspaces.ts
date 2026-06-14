import { api } from "./client";
import type {
  PresetResponse,
  WorkspaceCreate,
  WorkspaceResponse,
  WorkspaceStatsResponse,
  WorkspaceUpdate,
} from "@/types/api";

export const workspaceApi = {
  list: (): Promise<WorkspaceResponse[]> =>
    api.get<WorkspaceResponse[]>("/workspaces").then((r) => r.data),

  create: (data: WorkspaceCreate): Promise<WorkspaceResponse> =>
    api.post<WorkspaceResponse>("/workspaces", data).then((r) => r.data),

  get: (id: string): Promise<WorkspaceResponse> =>
    api.get<WorkspaceResponse>(`/workspaces/${id}`).then((r) => r.data),

  update: (id: string, data: WorkspaceUpdate): Promise<WorkspaceResponse> =>
    api
      .patch<WorkspaceResponse>(`/workspaces/${id}`, data)
      .then((r) => r.data),

  remove: (id: string): Promise<void> =>
    api.delete(`/workspaces/${id}`).then(() => undefined),

  stats: (id: string): Promise<WorkspaceStatsResponse> =>
    api
      .get<WorkspaceStatsResponse>(`/workspaces/${id}/stats`)
      .then((r) => r.data),

  presets: (): Promise<PresetResponse[]> =>
    api.get<PresetResponse[]>("/workspaces/presets").then((r) => r.data),

  fromPreset: (key: string): Promise<WorkspaceResponse> =>
    api
      .post<WorkspaceResponse>(`/workspaces/from-preset/${key}`)
      .then((r) => r.data),
};
