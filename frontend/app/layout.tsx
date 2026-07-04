import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { Toaster } from "@/components/ui/sonner";
import { AuthGate } from "@/components/auth/AuthGate";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ReviewMind — AI-Native Code Review",
  description: "AI-powered PR review with security analysis, style checking, and smart reviewer suggestions.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${geistMono.variable} dark h-full`}>
      <body className="h-full bg-[#0a0a0a] text-[#f9fafb] antialiased flex">
        <AuthGate>
          <AppShell>{children}</AppShell>
        </AuthGate>
        <Toaster theme="dark" />
      </body>
    </html>
  );
}
