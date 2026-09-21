import type { Metadata } from "next";
import { Hind_Siliguri, Plus_Jakarta_Sans } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const englishFont = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-english",
  display: "swap",
});

const banglaFont = Hind_Siliguri({
  subsets: ["bengali"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-bangla",
  display: "swap",
});

export const metadata: Metadata = {
  title: "JobPilot AI - Autonomous Career Suite",
  description: "Smart AI Job Finding & Application Agent",
  icons: {
    icon: "/logo.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="bn" className={`${englishFont.variable} ${banglaFont.variable}`}>
        <body className="font-bangla bg-[#090D16] text-slate-100 antialiased selection:bg-cyan-500 selection:text-slate-950">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}