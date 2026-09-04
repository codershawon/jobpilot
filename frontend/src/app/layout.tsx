import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "JobPilot AI | Autonomous AI Job Search & Application Studio",
  description: "AI-powered job matching, automated resume tailoring, cover letter generator, and autonomous job application agent.",
  keywords: ["AI Job Search", "JobPilot", "Auto Apply", "Resume Parser", "Bangladesh Tech Jobs"],
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#090D16] text-slate-100 antialiased`}>
        {children}
      </body>
    </html>
  );
}