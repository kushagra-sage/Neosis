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

export default function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set =
    (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Mirror the backend Pydantic rules so most 422s never leave the browser.
    const username = form.username.trim();
    const email = form.email.trim();
    if (username.length < 3 || username.length > 32) {
      setError("Username must be 3–32 characters");
      return;
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
      setError("Username can only contain letters, numbers, _ and -");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (/^\d+$/.test(form.password) || /^[a-zA-Z]+$/.test(form.password)) {
      setError("Password must contain both letters and numbers");
      return;
    }

    setLoading(true);
    try {
      await register({ username, email, password: form.password });
      // Redirect handled by useAuth.
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Registration failed"));
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
            <h1 className="text-[15px] font-semibold text-ink">
              Create account
            </h1>
            <p className="mt-0.5 text-[13px] text-muted">
              Start your research journey
            </p>
          </div>

          <OAuthButtons />

          <Input
            id="username"
            label="Username"
            type="text"
            value={form.username}
            onChange={set("username")}
            placeholder="yourname"
            autoComplete="username"
            hint="3–32 characters · letters, numbers, _ and -"
            required
          />
          <Input
            id="email"
            label="Email"
            type="email"
            value={form.email}
            onChange={set("email")}
            placeholder="you@example.com"
            autoComplete="email"
            required
          />
          <Input
            id="password"
            label="Password"
            type="password"
            value={form.password}
            onChange={set("password")}
            placeholder="••••••••"
            autoComplete="new-password"
            hint="At least 8 characters, letters and numbers"
            required
          />

          {error && (
            <p className="rounded-md border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
              {error}
            </p>
          )}

          <Button type="submit" loading={loading} className="mt-1 w-full">
            Create account
          </Button>

          <p className="text-center text-[13px] text-muted">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-accent transition-colors hover:text-accent-hover"
            >
              Sign in
            </Link>
          </p>
        </form>
      </Card>
    </motion.div>
  );
}
