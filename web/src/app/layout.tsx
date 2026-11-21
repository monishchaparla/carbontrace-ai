import type { Metadata, Viewport } from "next";
import { Public_Sans } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { AppShell } from "@/components/app-shell";
import { getSummary } from "@/lib/api";
import { reviewCount as sampleReviewCount } from "@/lib/sample-data";
import "./globals.css";

const publicSans = Public_Sans({
  variable: "--font-public-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

// Data comes from the API at request time, never baked in at build.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "CarbonTrace AI",
  description: "Turn bills and invoices into audit-ready Scope 1, 2 and 3 emissions.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f5f7f6" },
    { media: "(prefers-color-scheme: dark)", color: "#0e1412" },
  ],
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const summary = await getSummary();
  const reviewCount = summary && summary.documents > 0 ? summary.review_count : sampleReviewCount;
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${publicSans.variable} antialiased`}>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-md focus:bg-surface focus:px-3 focus:py-2 focus:text-sm"
        >
          Skip to content
        </a>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <AppShell reviewCount={reviewCount}>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  );
}
