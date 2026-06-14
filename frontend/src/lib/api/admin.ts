import { api } from "./client";

export type RangeKey = "24h" | "7d" | "30d" | "90d" | "all";

export interface OverviewAnalytics {
  generated_at: string;
  total_users: number;
  new_users_today: number;
  new_users_week: number;
  new_users_month: number;
  dau: number;
  wau: number;
  mau: number;
  user_growth_rate: number;
  total_inquiries: number;
  total_workspaces: number;
  total_documents: number;
  storage_bytes: number;
}

export interface DailyPoint {
  date: string;
  count: number;
}

export interface RecentUser {
  id: string;
  username: string;
  email: string;
  oauth_provider: string | null;
  created_at: string | null;
  last_active_at: string | null;
}

export interface UsersAnalytics {
  daily_signups: DailyPoint[];
  recent_users: RecentUser[];
}

export interface WorkspacesAnalytics {
  daily_created: DailyPoint[];
  most_active: { id: string; name: string; inquiries: number }[];
}

export interface DocumentsAnalytics {
  daily_uploads: DailyPoint[];
  by_kind: { kind: string; count: number }[];
  storage_bytes: number;
}

export interface InquiriesAnalytics {
  daily_inquiries: DailyPoint[];
  avg_latency_ms: number;
  by_status: { status: string; count: number }[];
}

export interface SystemAnalytics {
  redis: string;
  qdrant: string;
  inquiry_error_rate: number;
  failed_inquiries: number;
  total_inquiries: number;
}

export const adminApi = {
  overview: (): Promise<OverviewAnalytics> =>
    api.get<OverviewAnalytics>("/admin/analytics/overview").then((r) => r.data),
  users: (range: RangeKey): Promise<UsersAnalytics> =>
    api.get<UsersAnalytics>("/admin/analytics/users", { params: { range } }).then((r) => r.data),
  workspaces: (range: RangeKey): Promise<WorkspacesAnalytics> =>
    api.get<WorkspacesAnalytics>("/admin/analytics/workspaces", { params: { range } }).then((r) => r.data),
  documents: (range: RangeKey): Promise<DocumentsAnalytics> =>
    api.get<DocumentsAnalytics>("/admin/analytics/documents", { params: { range } }).then((r) => r.data),
  inquiries: (range: RangeKey): Promise<InquiriesAnalytics> =>
    api.get<InquiriesAnalytics>("/admin/analytics/inquiries", { params: { range } }).then((r) => r.data),
  system: (): Promise<SystemAnalytics> =>
    api.get<SystemAnalytics>("/admin/analytics/system").then((r) => r.data),
};
