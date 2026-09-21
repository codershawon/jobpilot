"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";

interface LogoProps {
  className?: string;
  showText?: boolean;
}

export default function Logo({ className = "", showText = true }: LogoProps) {
  return (
    <Link href="/" className={`inline-flex items-center gap-3 select-none group ${className}`}>
      {/* Exact Favicon Mark */}
      <div className="relative w-9 h-9 sm:w-12 sm:h-12 rounded-2xl overflow-hidden shadow-lg shadow-cyan-500/10 group-hover:scale-105 transition-transform duration-300">
        <Image
          src="/logo.svg"
          alt="JobPilot AI Logo"
          width={40}
          height={40}
          priority
          className="w-full h-full object-contain"
        />
      </div>

      {/* Brand Text */}
      {showText && (
        <div className="flex flex-col">
          <span className="text-lg font-black tracking-tight text-white flex items-center gap-1">
            Job<span className="text-transparent bg-clip-text bg-linear-to-r from-cyan-400 to-sky-400">Pilot</span>
            <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 ml-0.5">
              AI
            </span>
          </span>
          <span className="text-[10px] text-slate-400 font-medium tracking-wide -mt-1">
            Autonomous Career Suite
          </span>
        </div>
      )}
    </Link>
  );
}