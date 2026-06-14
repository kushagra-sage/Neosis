import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Logo } from "@/components/layout/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Toaster } from "@/components/ui/Toaster";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-paper px-4">
      <div className="absolute inset-x-0 top-0 flex items-center justify-between p-5">
        <Link
          href="/"
          className="flex items-center gap-1.5 text-[13px] text-muted transition-colors hover:text-ink"
        >
          <ArrowLeft size={14} />
          Home
        </Link>
        <ThemeToggle compact />
      </div>

      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <Logo size="lg" />
          <p className="font-serif text-[13px] italic text-muted">
            From question to peer-reviewed answer.
          </p>
        </div>
        {children}
      </div>
      <Toaster />
    </div>
  );
}
