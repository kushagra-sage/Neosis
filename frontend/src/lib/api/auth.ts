import { api } from "./client";
import type {
  RegisterRequest,
  TokenResponse,
  UserResponse,
  UserStatsResponse,
} from "@/types/api";

export const authApi = {
  /** POST /auth/register — JSON body → 201 + token pair. */
  register: (data: RegisterRequest): Promise<TokenResponse> =>
    api.post<TokenResponse>("/auth/register", data).then((r) => r.data),

  /**
   * POST /auth/login — the backend uses OAuth2PasswordRequestForm, so the
   * body must be application/x-www-form-urlencoded with `username` and
   * `password` fields (username also accepts an email).
   */
  login: (username: string, password: string): Promise<TokenResponse> => {
    const body = new URLSearchParams({ username, password }).toString();
    return api
      .post<TokenResponse>("/auth/login", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      .then((r) => r.data);
  },

  /**
   * GET /auth/me — accepts an explicit token so it can be called in the
   * window between receiving a token pair and persisting it (the request
   * interceptor only reads from localStorage).
   */
  me: (accessToken?: string): Promise<UserResponse> =>
    api
      .get<UserResponse>("/auth/me", {
        headers: accessToken
          ? { Authorization: `Bearer ${accessToken}` }
          : undefined,
      })
      .then((r) => r.data),

  /** GET /auth/me/stats — aggregate research stats. */
  stats: (): Promise<UserStatsResponse> =>
    api.get<UserStatsResponse>("/auth/me/stats").then((r) => r.data),

  /** POST /auth/refresh — rotate the refresh token. */
  refresh: (refreshToken: string): Promise<TokenResponse> =>
    api
      .post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken })
      .then((r) => r.data),

  /** POST /auth/logout — revoke a refresh token (200). */
  logout: (refreshToken: string): Promise<void> =>
    api
      .post("/auth/logout", { refresh_token: refreshToken })
      .then(() => undefined),

  /** POST /auth/forgot-password — always 200; neutral to prevent enumeration. */
  forgotPassword: (email: string): Promise<{ detail: string; status: string }> =>
    api
      .post<{ detail: string; status: string }>("/auth/forgot-password", { email })
      .then((r) => r.data),

  /** POST /auth/reset-password — complete a reset with a token. */
  resetPassword: (token: string, newPassword: string): Promise<{ detail: string }> =>
    api
      .post<{ detail: string }>("/auth/reset-password", {
        token,
        new_password: newPassword,
      })
      .then((r) => r.data),
};
