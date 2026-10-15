import type { Metadata, Viewport } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "SBUniversity", template: "%s · SBUniversity" },
  description: "Exams, results, certificates and live rankings in one place.",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#FDF6EE" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const body = (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
  return process.env.NEXT_PUBLIC_DEMO_MODE === "true" ? body : <ClerkProvider>{body}</ClerkProvider>;
}
