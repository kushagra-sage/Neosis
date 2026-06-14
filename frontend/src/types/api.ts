/**
 * TypeScript mirrors of the backend Pydantic schemas.
 * These types are the single source of truth for the frontend API layer —
 * every field name and shape matches the FastAPI response models exactly.
 */

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  oauth_provider: string | null;
  created_at: string;
}

export interface UserStatsResponse {
  total_workspaces: number;
  total_papers: number;
  total_inquiries: number;
  reviews_generated: number;
  member_since: string;
}

// ── Workspaces ────────────────────────────────────────────────────────────────

export type WorkspaceDomain =
  | "ra_severity"
  | "patent"
  | "multimodal_ai"
  | "vlm"
  | "custom";

export interface WorkspaceCreate {
  name: string;
  domain?: WorkspaceDomain;
  description?: string | null;
}

export interface WorkspaceUpdate {
  name?: string;
  description?: string | null;
}

export interface WorkspaceResponse {
  id: string;
  name: string;
  slug: string;
  domain: WorkspaceDomain;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceStatsResponse {
  papers: number;
  notes: number;
  questions: number;
  experiments: number;
  reviews: number;
  gaps: number;
  ideas: number;
  inquiries: number;
}

export interface PresetResponse {
  key: string;
  name: string;
  domain: WorkspaceDomain;
  description: string;
}

// ── Inquiries ─────────────────────────────────────────────────────────────────

export interface InquiryRequest {
  question: string;
  workspace_id?: string | null;
  inquiry_type?: string | null;
}

export interface DossierItem {
  id: string;
  title: string;
  authors?: string[];
  year?: number | null;
  venue?: string | null;
  abstract?: string | null;
  source: string;
  url?: string | null;
  rrf_score?: number | null;
  citation_count?: number | null;
}

export interface CriticScores {
  groundedness: number;
  citation_accuracy: number;
  coverage: number;
  rigor: number;
  overall: number;
  pass?: boolean;
  reasoning?: string;
  suggestions?: string[];
}

export type InquiryStatus =
  | "pending"
  | "running"
  | "success"
  | "critic_failed"
  | "failed";

export interface InquiryResponse {
  id: string;
  question: string;
  inquiry_type: string | null;
  status: InquiryStatus | string;
  answer: string | null;
  dossier: DossierItem[] | null;
  critic_scores: Partial<CriticScores> | null;
  follow_ups: string[] | null;
  latency_ms: number | null;
  created_at: string;
}

export interface InquiryHistoryItem {
  id: string;
  question: string;
  inquiry_type: string | null;
  status: InquiryStatus | string;
  latency_ms: number | null;
  created_at: string;
}

// ── Library ───────────────────────────────────────────────────────────────────

export interface PaperResponse {
  id: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  abstract: string | null;
  source: string;
  arxiv_id: string | null;
  doi: string | null;
  url: string | null;
  citation_count: number | null;
  indexed: boolean;
  chunk_count: number;
  created_at: string;
}

export interface NoteResponse {
  id: string;
  workspace_id: string;
  paper_id: string | null;
  title: string | null;
  body: string;
  tags: string[];
  created_at: string;
}

// ── WebSocket events (WS /ws/inquiry) ────────────────────────────────────────

export type WsEvent =
  | { type: "stage"; stage: string; [k: string]: unknown }
  | { type: "token"; content: string }
  | { type: "dossier"; items: DossierItem[] }
  | { type: "critic"; scores: Partial<CriticScores> }
  | { type: "done"; inquiry_id: string }
  | { type: "error"; message: string };

// ── System ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  version: string;
}


// ── Documents (knowledge base) ────────────────────────────────────────────────

export type DocumentKind = "pdf" | "docx" | "txt" | "markdown";
export type DocumentStatus = "pending" | "processing" | "indexed" | "failed";

export interface DocumentResponse {
  id: string;
  filename: string;
  mime_type: string;
  file_size: number;
  kind: DocumentKind | string;
  status: DocumentStatus | string;
  chunk_count: number;
  workspace_id: string | null;
  error: string | null;
  created_at: string;
}

export interface DocumentListItem {
  id: string;
  filename: string;
  kind: DocumentKind | string;
  status: DocumentStatus | string;
  file_size: number;
  chunk_count: number;
  workspace_id: string | null;
  created_at: string;
}


// ── Literature Review mode ────────────────────────────────────────────────────

export interface ReviewCitation {
  label?: string;
  title?: string;
  authors?: string[];
  year?: number | null;
  venue?: string | null;
  source?: string;
  url?: string | null;
  doi?: string | null;
  arxiv_id?: string | null;
}

export interface LiteratureReviewResponse {
  id: string;
  workspace_id: string;
  title: string;
  query: string;
  content: string;
  citations: ReviewCitation[];
  critic_scores: Record<string, unknown>;
  created_at: string;
}

export interface LiteratureReviewListItem {
  id: string;
  title: string;
  query: string;
  created_at: string;
}

export type ExportFormat = "markdown" | "bibtex" | "docx" | "pdf";
