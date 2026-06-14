"use client";
import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, MailCheck } from "lucide-react";
import { authApi } from "@/lib/api/auth";
import { extractErrorMessage } from "@/lib/api/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.forgotPassword(email.trim());
      if (res.status === "unavailable") {
        setUnavailable(true);
      } else {
        setDone(true);
      }
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Something went wrong"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <Card className="p-6">
        {done ? (
          <div className="flex flex-col items-center gap-3 py-4 text-center">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sage-soft text-sage">
              <MailCheck size={20} />
            </div>
            <h1 className="text-[15px] font-semibold text-ink">Check your email</h1>
            <p className="font-serif text-[13px] leading-relaxed text-ink-2">
              If an account exists for that address, we&apos;ve sent a link to
              reset your password. The link expires shortly for your security.
            </p>
            <Link href="/login" className="mt-2">
              <Button variant="secondary" size="sm">
                <ArrowLeft size={14} />
                Back to sign in
              </Button>
            </Link>
          </div>
        ) : unavailable ? (
          <div className="flex flex-col items-center gap-3 py-4 text-center">
            <h1 className="text-[15px] font-semibold text-ink">
              Password reset temporarily unavailable
            </h1>
            <p className="font-serif text-[13px] leading-relaxed text-ink-2">
              Our email service isn&apos;t configured right now, so we can&apos;t
              send reset links. Please try again later or contact support.
            </p>
            <Link href="/login" className="mt-2">
              <Button variant="secondary" size="sm">
                <ArrowLeft size={14} />
                Back to sign in
              </Button>
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <h1 className="text-[15px] font-semibold text-ink">
                Reset your password
              </h1>
              <p className="mt-0.5 text-[13px] text-muted">
                Enter your email and we&apos;ll send you a reset link.
              </p>
            </div>

            <Input
              id="email"
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />

            {error && (
              <p className="rounded-md border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
                {error}
              </p>
            )}

            <Button type="submit" loading={loading} className="mt-1 w-full">
              Send reset link
            </Button>

            <Link
              href="/login"
              className="flex items-center justify-center gap-1.5 text-[13px] text-muted transition-colors hover:text-ink"
            >
              <ArrowLeft size={14} />
              Back to sign in
            </Link>
          </form>
        )}
      </Card>
    </motion.div>
  );
}
