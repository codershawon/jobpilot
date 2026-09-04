import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "JobPilot AI | Autonomous AI Job Search",
  description: "AI-powered job matching & application studio",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      proxyUrl="https://jobpilot-plum-omega.vercel.app/__clerk"
      signInFallbackRedirectUrl="/"
      signUpFallbackRedirectUrl="/">
      <html lang="en">
        <body className={`${inter.className} bg-[#090D16] text-slate-100 antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}