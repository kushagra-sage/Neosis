"use client";

/**
 * OAuth entry points. Both providers are handled entirely by the backend:
 * the buttons navigate to the backend's begin-OAuth route, which redirects to
 * the provider and ultimately back to /oauth/callback with a token pair.
 *
 * Google is enabled when the backend has GOOGLE_CLIENT_ID configured; the
 * begin route returns 501 otherwise, so we still render it (parity with GitHub)
 * and let the backend decide. Override the URLs with env vars if the backend
 * is hosted elsewhere.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const GITHUB_URL =
  process.env.NEXT_PUBLIC_GITHUB_OAUTH_URL ??
  `${API_BASE}/api/v1/auth/oauth/github`;
const GOOGLE_URL =
  process.env.NEXT_PUBLIC_GOOGLE_OAUTH_URL ??
  `${API_BASE}/api/v1/auth/oauth/google`;

function GitHubIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.7 1.3 3.4 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17.3 4.7 18.3 5 18.3 5c.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.6-1.5 7.9-5.8 7.9-10.9C23.5 5.7 18.3.5 12 .5z" />
    </svg>
  );
}
function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M22.5 12.2c0-.7-.1-1.4-.2-2H12v3.9h5.9a5 5 0 0 1-2.2 3.3v2.7h3.6c2.1-2 3.2-4.9 3.2-7.9z" />
      <path fill="#34A853" d="M12 23c2.9 0 5.4-1 7.2-2.6l-3.6-2.7c-1 .7-2.3 1.1-3.6 1.1-2.8 0-5.1-1.9-6-4.4H2.3v2.8A11 11 0 0 0 12 23z" />
      <path fill="#FBBC05" d="M6 14.4a6.6 6.6 0 0 1 0-4.2V7.4H2.3a11 11 0 0 0 0 9.8L6 14.4z" />
      <path fill="#EA4335" d="M12 5.4c1.6 0 3 .5 4.1 1.6l3.1-3.1A11 11 0 0 0 12 1 11 11 0 0 0 2.3 7.4L6 10.2c.9-2.6 3.2-4.8 6-4.8z" />
    </svg>
  );
}

export function OAuthButtons() {
  return (
    <div className="flex flex-col gap-2.5">
      <a
        href={GITHUB_URL}
        className="flex h-9 items-center justify-center gap-2 rounded-md border border-border bg-surface text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface-warm"
      >
        <GitHubIcon />
        Continue with GitHub
      </a>
      <a
        href={GOOGLE_URL}
        className="flex h-9 items-center justify-center gap-2 rounded-md border border-border bg-surface text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface-warm"
      >
        <GoogleIcon />
        Continue with Google
      </a>

      <div className="my-1 flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-[11px] text-muted">or</span>
        <div className="h-px flex-1 bg-border" />
      </div>
    </div>
  );
}
