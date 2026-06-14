"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Github,
  KeyRound,
  Mail,
  Monitor,
  Moon,
  Palette,
  Sun,
  User as UserIcon,
} from "lucide-react";
import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/stores/auth";
import { useThemeStore, type Theme } from "@/stores/theme";
import { Header } from "@/components/layout/Header";
import { PageFade } from "@/components/layout/PageFade";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { cn, formatDate } from "@/lib/utils";

const THEME_OPTIONS: { value: Theme; icon: typeof Sun; label: string }[] = [
  { value: "light", icon: Sun, label: "Light" },
  { value: "dark", icon: Moon, label: "Dark" },
  { value: "system", icon: Monitor, label: "System" },
];

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  const { data: stats } = useQuery({
    queryKey: ["me-stats"],
    queryFn: authApi.stats,
    retry: false,
  });

  const [notifyResearch, setNotifyResearch] = useState(true);
  const [notifyProduct, setNotifyProduct] = useState(false);

  const initials = (user?.username ?? "?").charAt(0).toUpperCase();

  return (
    <PageFade>
      <Header title="Settings" subtitle="Manage your account and preferences" />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-2xl px-6 py-8">
          {/* Profile */}
          <Section icon={UserIcon} title="Profile">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-accent-soft text-2xl font-semibold text-accent-hover">
                {initials}
              </div>
              <div>
                <p className="text-[15px] font-semibold text-ink">{user?.username}</p>
                <p className="text-[13px] text-muted">{user?.email}</p>
                {stats && (
                  <p className="mt-0.5 text-xs text-muted">
                    Member since {formatDate(stats.member_since)}
                  </p>
                )}
              </div>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <Input id="username" label="Username" defaultValue={user?.username ?? ""} readOnly />
              <Input id="email" label="Email" defaultValue={user?.email ?? ""} readOnly />
            </div>
            <p className="mt-2 text-xs text-muted">
              Profile editing is read-only in this build. Account identity is managed
              through your sign-in provider.
            </p>
          </Section>

          {/* Appearance */}
          <Section icon={Palette} title="Appearance">
            <p className="mb-3 text-[13px] text-ink-2">Theme</p>
            <div className="inline-flex gap-1.5">
              {THEME_OPTIONS.map(({ value, icon: Icon, label }) => (
                <button
                  key={value}
                  onClick={() => setTheme(value)}
                  className={cn(
                    "flex items-center gap-2 rounded-lg border px-3 py-2 text-[13px] font-medium transition-colors",
                    theme === value
                      ? "border-accent bg-accent-soft text-accent-hover"
                      : "border-border text-ink-2 hover:border-border-strong",
                  )}
                >
                  <Icon size={15} />
                  {label}
                </button>
              ))}
            </div>
          </Section>

          {/* Notifications */}
          <Section icon={Mail} title="Notification preferences">
            <Toggle
              label="Research updates"
              description="Notify me when an inquiry or literature review finishes."
              checked={notifyResearch}
              onChange={setNotifyResearch}
            />
            <Toggle
              label="Product announcements"
              description="Occasional emails about new Noesis features."
              checked={notifyProduct}
              onChange={setNotifyProduct}
            />
            <p className="mt-1 text-xs text-muted">
              Preferences are stored locally in this build.
            </p>
          </Section>

          {/* Connected accounts */}
          <Section icon={Github} title="Connected accounts">
            <div className="flex items-center justify-between rounded-lg border border-border px-3.5 py-3">
              <div className="flex items-center gap-2.5">
                <Github size={16} className="text-ink-2" />
                <span className="text-[13px] text-ink">GitHub</span>
              </div>
              {user?.oauth_provider === "github" ? (
                <Badge tone="sage">Connected</Badge>
              ) : (
                <Badge tone="neutral">Not connected</Badge>
              )}
            </div>
            <div className="mt-2 flex items-center justify-between rounded-lg border border-border px-3.5 py-3">
              <div className="flex items-center gap-2.5">
                <span className="text-[13px] font-semibold text-ink-2">G</span>
                <span className="text-[13px] text-ink">Google</span>
              </div>
              {user?.oauth_provider === "google" ? (
                <Badge tone="sage">Connected</Badge>
              ) : (
                <Badge tone="neutral">Not connected</Badge>
              )}
            </div>
          </Section>

          {/* Security */}
          <Section icon={KeyRound} title="Security">
            <p className="text-[13px] text-ink-2">
              To change your password, sign out and use the{" "}
              <span className="font-medium text-accent">Forgot password</span> flow
              on the sign-in screen.
            </p>
          </Section>
        </div>
      </div>
    </PageFade>
  );
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof UserIcon;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-5 rounded-2xl border border-border bg-surface p-6">
      <div className="mb-4 flex items-center gap-2">
        <Icon size={16} className="text-accent" />
        <h2 className="text-[15px] font-semibold text-ink">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <div>
        <p className="text-[13px] font-medium text-ink">{label}</p>
        <p className="text-xs text-muted">{description}</p>
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-5 w-9 shrink-0 rounded-full transition-colors",
          checked ? "bg-accent" : "bg-surface-sunken",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform",
            checked ? "translate-x-4" : "translate-x-0.5",
          )}
        />
      </button>
    </div>
  );
}
