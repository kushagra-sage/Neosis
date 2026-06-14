import axios, { type AxiosInstance } from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const STORAGE_KEY = "noesis-auth";

export const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 60_000,
  headers: { "Content-Type": "application/json" },
});

// Endpoints whose 401s are normal credential failures — never trigger
// the silent-refresh / redirect machinery for these.
const AUTH_PATHS = ["/auth/login", "/auth/register", "/auth/refresh"];
const isAuthPath = (url?: string): boolean =>
  !!url && AUTH_PATHS.some((p) => url.includes(p));

interface PersistedAuth {
  state?: {
    accessToken?: string;
    refreshToken?: string;
    isAuthenticated?: boolean;
  };
}

function readPersisted(): PersistedAuth["state"] | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? ((JSON.parse(raw) as PersistedAuth).state ?? null) : null;
  } catch {
    return null;
  }
}

export function getAccessToken(): string | null {
  return readPersisted()?.accessToken ?? null;
}

// Attach the persisted access token unless the caller set one explicitly.
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Transparent single-flight refresh on 401 (auth endpoints excluded).
let refreshing: Promise<string> | null = null;

api.interceptors.response.use(
  (r) => r,
  async (error: unknown) => {
    const err = error as {
      config?: { url?: string; _retry?: boolean; headers?: Record<string, string> };
      response?: { status?: number };
    };
    const original = err.config ?? {};
    if (
      err.response?.status !== 401 ||
      original._retry ||
      isAuthPath(original.url)
    ) {
      return Promise.reject(error);
    }
    original._retry = true;

    try {
      const refreshToken = readPersisted()?.refreshToken;
      if (!refreshToken) throw new Error("no refresh token");

      if (!refreshing) {
        refreshing = axios
          .post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          })
          .then((r) => {
            const data = r.data as {
              access_token: string;
              refresh_token: string;
            };
            const stored = JSON.parse(
              localStorage.getItem(STORAGE_KEY) ?? "{}",
            ) as PersistedAuth;
            stored.state = {
              ...stored.state,
              accessToken: data.access_token,
              refreshToken: data.refresh_token,
              isAuthenticated: true,
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
            return data.access_token;
          })
          .finally(() => {
            refreshing = null;
          });
      }

      const newToken = await refreshing;
      original.headers = original.headers ?? {};
      original.headers.Authorization = `Bearer ${newToken}`;
      return api(original);
    } catch {
      if (typeof window !== "undefined") {
        localStorage.removeItem(STORAGE_KEY);
        const onAuthPage = ["/login", "/register"].some((p) =>
          window.location.pathname.startsWith(p),
        );
        if (!onAuthPage) window.location.href = "/login";
      }
      return Promise.reject(error);
    }
  },
);

/**
 * Extract a human-readable string from any API error.
 * Handles every FastAPI error shape — string detail, 422 validation arrays
 * of objects, object detail, and network failures. ALWAYS returns a string,
 * so the result is safe to render in JSX.
 */
export function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "response" in err) {
    const detail = (err as { response?: { data?: { detail?: unknown } } })
      .response?.data?.detail;

    if (typeof detail === "string" && detail.trim()) return detail;

    if (Array.isArray(detail)) {
      const msgs = detail
        .map((d) => {
          if (d && typeof d === "object" && "msg" in d) {
            const locArr = (d as { loc?: unknown[] }).loc;
            const loc = Array.isArray(locArr)
              ? locArr.slice(1).map(String).join(".")
              : "";
            const msg = String((d as { msg: unknown }).msg);
            return loc ? `${loc}: ${msg}` : msg;
          }
          return typeof d === "string" ? d : JSON.stringify(d);
        })
        .filter(Boolean);
      if (msgs.length) return msgs.join(" · ");
    }

    if (detail && typeof detail === "object") {
      try {
        return JSON.stringify(detail);
      } catch {
        /* fall through */
      }
    }
  }
  if (err instanceof Error && err.message) {
    if (err.message === "Network Error") {
      return "Cannot reach the server — is the backend running on :8000?";
    }
    return err.message;
  }
  return fallback;
}

export function buildWsUrl(path: string): string {
  return `${API_BASE_URL.replace(/^http/, "ws")}/api/v1${path}`;
}
