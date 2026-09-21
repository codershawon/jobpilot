"use client";

import Logo from "./Logo";
import Container from "./Container";
import { BsGithub, BsGlobe2, BsShieldCheck } from "react-icons/bs";

export default function Footer() {
  return (
    <footer className="w-full border-t border-cyan-950/40 bg-[#090D16]/95 backdrop-blur-md py-8 transition-all">
      <Container>
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 pb-6 border-b border-slate-800/60">
          {/* Left: Brand Logo & Short Motto */}
          <div className="flex flex-col items-center md:items-start text-center md:text-left gap-1">
            <Logo />
            <p className="text-[11px] text-slate-400 font-normal pl-1">
              বাংলাদেশের জন্য স্বয়ংক্রিয় এআই জব সার্চ ও অ্যাপ্লিকেশন স্যুইট।
            </p>
          </div>

          {/* Right: Security & Network Badges */}
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800">
              <BsShieldCheck className="text-cyan-400 w-3.5 h-3.5" />
              <span>এনক্রিপ্টেড ডাটাবেজ</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800">
              <BsGlobe2 className="text-sky-400 w-3.5 h-3.5" />
              <span>৬৪ জেলা ও রিমোট</span>
            </div>
            <a
              href="https://github.com/codershawon/jobpilot"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-slate-300 hover:text-cyan-400 transition-colors px-2 py-1"
            >
              <BsGithub className="w-4 h-4" />
              <span>GitHub</span>
            </a>
          </div>
        </div>

        {/* Bottom Bar: Copyright & Stack */}
        <div className="pt-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} JobPilot AI. সর্বস্বত্ব সংরক্ষিত।</p>
          <p className="text-slate-400 font-mono text-[11px]">
            FastAPI • Next.js • Neon Cloud 🇧🇩
          </p>
        </div>
      </Container>
    </footer>
  );
}