import type { Metadata } from "next";
import { Outfit, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import ToastContainer from "../components/ToastContainer";
import ErrorBoundary from "../components/ErrorBoundary";
import { QueryProvider } from "../lib/query-client";

// Outfit: Modern, clean geometric sans-serif with personality
const outfit = Outfit({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

// JetBrains Mono: Excellent developer font for code/data
const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Project Progress DB",
  description: "議事録からタスク・リスクを自動抽出するプロジェクト管理ツール",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className={`${outfit.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased">
        <QueryProvider>
          <ErrorBoundary>
            {children}
            <ToastContainer />
          </ErrorBoundary>
        </QueryProvider>
      </body>
    </html>
  );
}
