import type { Config } from "tailwindcss";

/**
 * Noesis design tokens — warm editorial research surface with a calm dark mode.
 *
 * Colors are driven by CSS variables (see globals.css) so light/dark themes
 * swap by toggling the `dark` class on <html>. Each token maps to an
 * `--n-*` variable with an HSL-free hex fallback baked into globals.css.
 */
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "var(--n-paper)",
        surface: "var(--n-surface)",
        "surface-warm": "var(--n-surface-warm)",
        "surface-sunken": "var(--n-surface-sunken)",
        border: "var(--n-border)",
        "border-strong": "var(--n-border-strong)",
        ink: "var(--n-ink)",
        "ink-2": "var(--n-ink-2)",
        muted: "var(--n-muted)",
        accent: "var(--n-accent)",
        "accent-hover": "var(--n-accent-hover)",
        "accent-soft": "var(--n-accent-soft)",
        sage: "var(--n-sage)",
        "sage-soft": "var(--n-sage-soft)",
        amber: "var(--n-amber)",
        "amber-soft": "var(--n-amber-soft)",
        danger: "var(--n-danger)",
        "danger-soft": "var(--n-danger-soft)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        serif: ["'Source Serif 4'", "Georgia", "serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "var(--n-shadow-card)",
        lifted: "var(--n-shadow-lifted)",
        dialog: "var(--n-shadow-dialog)",
      },
      borderColor: { DEFAULT: "var(--n-border)" },
      borderRadius: { md: "8px", lg: "12px", xl: "16px", "2xl": "20px" },
      transitionTimingFunction: {
        swift: "cubic-bezier(0.25, 0.1, 0.25, 1)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "grid-pan": {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "40px 40px" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s cubic-bezier(0.25,0.1,0.25,1) both",
      },
    },
  },
  plugins: [],
};

export default config;
