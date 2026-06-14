"use client";
import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuth } from "@/hooks/useAuth";
import { extractErrorMessage } from "@/lib/api/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { OAuthButtons } from "@/components/marketing/OAuthButtons";

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username.trim(), password);
      // Redirect handled by useAuth — keep the spinner during navigation.
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Login failed"));
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
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <h1 className="text-[15px] font-semibold text-ink">Sign in</h1>
            <p className="mt-0.5 text-[13px] text-muted">
              Continue your research
            </p>
          </div>

          <OAuthButtons />

          <Input
            id="username"
            label="Username or email"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="username or email"
            autoComplete="username"
            required
          />
          <Input
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
            required
          />

          <div className="-mt-1 flex justify-end">
            <Link
              href="/forgot-password"
              className="text-[12px] text-muted transition-colors hover:text-accent"
            >
              Forgot password?
            </Link>
          </div>

          {error && (
            <p className="rounded-md border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
              {error}
            </p>
          )}

          <Button type="submit" loading={loading} className="mt-1 w-full">
            Sign in
          </Button>

          <p className="text-center text-[13px] text-muted">
            No account?{" "}
            <Link
              href="/register"
              className="font-medium text-accent transition-colors hover:text-accent-hover"
            >
              Create one
            </Link>
          </p>
        </form>
      </Card>
    </motion.div>
  );
}
