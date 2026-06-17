import type { Metadata } from "next";
import "./globals.css";
import { CommandCenterProvider } from "../context/CommandCenterContext";

export const metadata: Metadata = {
  title: "CRISIS COMMAND | Enterprise Crisis Command Center",
  description: "Enterprise multi-agent crisis management platform powered by AI agents and Band SDK",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark min-h-full scroll-smooth">
      <head>
        {/* Preload critical fonts to reduce FOUT */}
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
          crossOrigin="anonymous"
        />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          rel="preload"
          as="style"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700&family=JetBrains+Mono:wght@500;700&display=swap"
        />
      </head>
      <body className="min-h-full w-full bg-black text-[#e2e2e2] antialiased">
        <CommandCenterProvider>
          {children}
        </CommandCenterProvider>
      </body>
    </html>
  );
}
