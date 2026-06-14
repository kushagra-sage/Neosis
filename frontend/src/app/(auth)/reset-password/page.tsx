"use client";
import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { authApi } from "@/lib/api/auth";
import { extractErrorMessage } from "@/lib/api/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

function ResetPasswordInner() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!token) {
      setError("This reset link is invalid or has expired.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (/^\d+$/.test(password) || /^[a-zA-Z]+$/.test(password)) {
      setError("Password must contain both letters and numbers");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await authApi.resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.replace("/login"), 1600);
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Could not reset password"));
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <Card className="p-6">
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sage-soft text-sage">
            <CheckCircle2 size={20} />
          </div>
          <h1 className="text-[15px] font-semibold text-ink">Password updated</h1>
          <p className="font-serif text-[13px] leading-relaxed text-ink-2">
            Your password has been changed. Redirecting you to sign in…
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <h1 className="text-[15px] font-semibold text-ink">
            Choose a new password
          </h1>
          <p className="mt-0.5 text-[13px] text-muted">
            Enter a new password for your account.
          </p>
        </div>

        <Input
          id="password"
          label="New password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          autoComplete="new-password"
          hint="At least 8 characters, letters and numbers"
          required
        />
        <Input
          id="confirm"
          label="Confirm password"
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="••••••••"
          autoComplete="new-password"
          required
        />

        {error && (
          <p className="rounded-md border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
            {error}
          </p>
        )}

        <Button type="submit" loading={loading} className="mt-1 w-full">
          Update password
        </Button>

        <Link
          href="/login"
          className="text-center text-[13px] text-muted transition-colors hover:text-ink"
        >
          Back to sign in
        </Link>
      </form>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <Suspense fallback={<Card className="p-6 text-center text-sm text-muted">Loading…</Card>}>
        <ResetPasswordInner />
      </Suspense>
    </motion.div>
  );
}
