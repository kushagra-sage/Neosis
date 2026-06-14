"use client";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, LayoutDashboard, LogOut, Settings, User } from "lucide-react";
import { api } from "@/lib/api/client";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { Dropdown } from "@/components/ui/Dropdown";
import { ThemeToggle } from "./ThemeToggle";
import { cn } from "@/lib/utils";
import type { HealthResponse } from "@/types/api";

export function Header({ title, subtitle }: { title?: string; subtitle?: string }) {
  const { user, logout } = useAuth();
  const router = useRouter();

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<HealthResponse>("/health").then((r) => r.data),
    refetchInterval: 20_000,
    retry: false,
  });

  const online = health?.status === "ok";

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-paper px-6">
      <div className="min-w-0">
        {title && (
          <h1 className="truncate text-[15px] font-semibold tracking-tight text-ink">
            {title}
          </h1>
        )}
        {subtitle && <p className="truncate text-xs text-muted">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1.5 text-xs text-muted">
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              online ? "bg-sage" : "bg-danger",
            )}
          />
          {online ? "Connected" : "Offline"}
        </span>

        <ThemeToggle compact />

        <Dropdown
          align="end"
          trigger={
            <button className="flex items-center gap-2 rounded-md border border-border bg-surface px-2.5 py-1.5 text-[13px] text-ink-2 transition-colors hover:border-border-strong">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent-soft text-[10px] font-semibold uppercase text-accent-hover">
                {user?.username?.charAt(0) ?? "?"}
              </span>
              <span className="max-w-[120px] truncate">{user?.username}</span>
              <ChevronDown size={13} className="text-muted" />
            </button>
          }
          items={[
            { label: user?.email ?? "Account", icon: User, onSelect: () => undefined },
            { label: "Settings", icon: Settings, onSelect: () => router.push("/settings") },
            { label: "Admin", icon: LayoutDashboard, onSelect: () => router.push("/admin") },
            { label: "Sign out", icon: LogOut, danger: true, onSelect: () => void logout() },
          ]}
        />
      </div>
    </header>
  );
}
