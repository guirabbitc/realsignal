import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "ValiDate",
  description: "Separate real demand from politeness in customer interviews.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header>
          <Link href="/" className="brand">ValiDate</Link>
          <span className="tagline">Evidence of real demand, not politeness</span>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
