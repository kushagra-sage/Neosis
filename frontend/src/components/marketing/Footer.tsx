import Link from "next/link";
import { Logo } from "@/components/layout/Logo";

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface-warm/40">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-5 py-10 sm:flex-row">
        <div className="flex flex-col items-center gap-2 sm:items-start">
          <Logo />
          <p className="text-xs text-muted">
            Research Intelligence OS · © {new Date().getFullYear()}
          </p>
        </div>
        <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-[13px] text-ink-2">
          <a href="#features" className="hover:text-ink">Features</a>
          <a href="#pipeline" className="hover:text-ink">Pipeline</a>
          <a href="#pricing" className="hover:text-ink">Pricing</a>
          <a href="#faq" className="hover:text-ink">FAQ</a>
          <Link href="/login" className="hover:text-ink">Sign in</Link>
        </nav>
      </div>
    </footer>
  );
}
