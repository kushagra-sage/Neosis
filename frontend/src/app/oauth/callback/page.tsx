"use client";
import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { authApi } from "@/lib/api/auth";
import { Logo } from "@/components/layout/Logo";
import { Spinner } from "@/components/ui/Spinner";

/**
 * OAuth landing route.
 *
 * The backend (GitHub + Google) redirects here with the issued token pair as
 * query params: /oauth/callback?access_token=…&refresh_token=…
 * We persist them via the auth store, fetch the profile with the fresh token,
 * and forward into the app — mirroring the email/password login exactly.
 */
function OAuthCallbackInner() {
  const router = useRouter();
  const params = useSearchParams();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [error, setError] = useState<string | null>(null);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");
    const oauthError = params.get("error");

    if (oauthError || !accessToken || !refreshToken) {
      setError("Sign-in failed. Please try again.");
      const t = setTimeout(() => router.replace("/login?error=oauth_failed"), 1400);
      return () => clearTimeout(t);
    }

    (async () => {
      try {
        const profile = await authApi.me(accessToken);
        setAuth(
          {
            access_token: accessToken,
            refresh_token: refreshToken,
            token_type: "bearer",
            expires_in: 3600,
          },
          profile,
        );
        router.replace("/workspaces");
      } catch {
        setError("Could not complete sign-in. Please try again.");
        setTimeout(() => router.replace("/login?error=oauth_failed"), 1400);
      }
    })();
  }, [params, router, setAuth]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 bg-paper">
      <Logo size="lg" />
      {error ? (
        <p className="text-sm text-danger">{error}</p>
      ) : (
        <div className="flex items-center gap-2.5 text-sm text-muted">
          <Spinner className="h-4 w-4" />
          Completing sign-in…
        </div>
      )}
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-paper">
          <Spinner />
        </div>
      }
    >
      <OAuthCallbackInner />
    </Suspense>
  );
}
