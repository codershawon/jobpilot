"use client";

import React, { useRef } from "react";
import { UserButton, SignInButton, useUser } from "@clerk/nextjs";
import { 
  BsUpload, 
  BsArrowRepeat, 
  BsPersonCircle,
} from "react-icons/bs";
import Logo from "./Logo";
import Container from "./Container";
import Link from "next/link";

interface HeaderProps {
  loading: boolean;
  refreshing: boolean;
  hasProfile: boolean;
  lastSynced?: string | null;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRefreshJobs: () => void;
}

export default function Header({
  loading,
  refreshing,
  hasProfile,
  onFileUpload,
  onRefreshJobs,
}: HeaderProps) {
  const { isSignedIn, isLoaded } = useUser();
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-md bg-[#090D16]/80 border-b border-slate-800/80">
      <Container className="h-16 flex items-center justify-between">
        
        {/* Brand Left */}
        <Logo />

        {/* Center: Realtime Autonomous Status Badge */}
        <div className="hidden md:inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-cyan-950/80 shadow-inner">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
          </span>
          <span className="text-xs font-medium text-slate-300">
            Autonomous Agent: <span className="text-cyan-400 font-semibold">Ready</span>
          </span>
        </div>

        {/* Actions Right */}
        <div className="flex items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={onFileUpload}
            accept=".pdf,.docx"
            className="hidden"
            disabled={loading}
          />

          {hasProfile && (
            <div className="flex items-center gap-2">
              <button
                onClick={onRefreshJobs}
                disabled={refreshing || loading}
                className="group flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-cyan-300 transition-all active:scale-95 disabled:opacity-50"
                title="Sync live jobs from portals"
              >
                <BsArrowRepeat className={`w-3.5 h-3.5 text-cyan-400 ${refreshing ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-500"}`} />
                <span className="hidden sm:inline">{refreshing ? "Syncing..." : "Sync Jobs"}</span>
              </button>
              <Link
                  href="/tracker"
                  className="flex items-center gap-1.5 rounded-xl border border-cyan-950 bg-slate-900/60 px-3 py-2 text-xs text-slate-300 transition hover:border-cyan-800 hover:text-slate-100"
                >
                  Tracker
                </Link>

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 hover:text-cyan-200 transition-all active:scale-95 disabled:opacity-50"
              >
                <BsUpload className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Change CV</span>
              </button>
            </div>
          )}

          {/* User Sign-In / Account */}
          {isLoaded && (
            <div className="flex items-center">
              {isSignedIn ? (
                <UserButton
                  appearance={{
                    elements: {
                      userButtonAvatarBox: "w-8 h-8 rounded-xl border border-cyan-500/40 ring-2 ring-cyan-500/10 hover:scale-105 transition-transform",
                    },
                  }}
                />
              ) : (
                <SignInButton mode="modal">
                  <button className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-slate-950 transition-all shadow-md shadow-cyan-500/20 active:scale-95">
                    <BsPersonCircle className="w-3.5 h-3.5" />
                    <span>Sign In</span>
                  </button>
                </SignInButton>
              )}
            </div>
          )}
        </div>

      </Container>
    </header>
  );
}