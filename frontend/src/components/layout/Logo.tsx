import { cn } from "@/lib/utils";

export function Logo({ size = "md" }: { size?: "md" | "lg" }) {
  return (
    <span className="inline-flex items-center gap-2">
      {/* Three converging strata — inquiry, evidence, synthesis. */}
      <svg
        width={size === "lg" ? 22 : 18}
        height={size === "lg" ? 22 : 18}
        viewBox="0 0 18 18"
        fill="none"
        aria-hidden
      >
        <rect x="2" y="3" width="14" height="2.6" rx="1.3" fill="#C2522B" />
        <rect x="4" y="7.7" width="10" height="2.6" rx="1.3" fill="#C2522B" opacity="0.65" />
        <rect x="6" y="12.4" width="6" height="2.6" rx="1.3" fill="#C2522B" opacity="0.35" />
      </svg>
      <span
        className={cn(
          "font-serif font-semibold tracking-tight text-ink",
          size === "lg" ? "text-xl" : "text-[17px]",
        )}
      >
        noesis
      </span>
    </span>
  );
}
