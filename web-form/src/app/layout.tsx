import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TechCorp Support | AI-Powered Help Desk",
  description: "Get instant help with TechFlow - powered by our AI support assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
