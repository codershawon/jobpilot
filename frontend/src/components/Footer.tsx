"use client";

import React from "react";
import Logo from "./Logo";
import { BsGithub, BsGlobe2, BsShieldCheck } from "react-icons/bs";

export default function Footer() {
  return (
    <footer className="mt-20 border-t border-cyan-950/60 bg-[#090D16]/90 backdrop-blur-md pt-12 pb-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8 pb-8 border-b border-slate-800/60">
          
          {/* Logo & Description */}
          <div className="flex flex-col items-center md:items-start text-center md:text-left space-y-2 max-w-sm">
            <Logo />
            <p className="text-xs text-slate-400 leading-relaxed pt-1">
              Autonomous AI agent for resume parsing, live 64-district job matching, and tailored application drafts in Bangladesh.
            </p>
          </div>

          {/* Quick Badges & Links */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400">
            <div className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800">
              <BsShieldCheck className="text-cyan-400" />
              <span>Encrypted Persistence</span>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800">
              <BsGlobe2 className="text-sky-400" />
              <span>64 Districts Covered</span>
            </div>
            <a
              href="https://github.com/codershawon/jobpilot"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-slate-300 hover:text-cyan-400 transition-colors"
            >
              <BsGithub className="w-4 h-4" />
              <span>GitHub</span>
            </a>
          </div>
        </div>

        {/* Bottom Copyright */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500">
          <p>© {new Date().getFullYear()} JobPilot AI. All rights reserved.</p>
          <p className="text-slate-400">
            Crafted with FastAPI, Next.js & Neon Cloud 🇧🇩
          </p>
        </div>
      </div>
    </footer>
  );
}