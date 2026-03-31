import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Text to SQL",
  description: "Convert natural language to SQL queries using AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
