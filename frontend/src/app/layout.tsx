import type { Metadata } from "next";
import "@/styles/globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Noesis — Research Intelligence OS",
  description:
    "A multi-agent research copilot: it plans the inquiry, retrieves the evidence, writes the synthesis, and peer-reviews its own rigor.",
};

// Runs before paint to set the theme class and avoid a flash of the wrong theme.
const themeScript = `
(function(){
  try {
    var raw = localStorage.getItem('noesis-theme');
    var theme = raw ? (JSON.parse(raw).state || {}).theme : 'system';
    var dark = theme === 'dark' || (theme !== 'light' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (dark) document.documentElement.classList.add('dark');
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
