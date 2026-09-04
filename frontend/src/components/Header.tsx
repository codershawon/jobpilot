"use client";

import React, { useRef } from "react";
import Image from "next/image";
import { BsUpload, BsArrowRepeat, BsRobot } from "react-icons/bs";

interface HeaderProps {
  loading: boolean;
  refreshing: boolean;
  hasProfile: boolean;
  lastSynced: string | null;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRefreshJobs: () => void;
}

export default function Header({
  loading,
  refreshing,
  hasProfile,
  lastSynced,
  onFileUpload,
  onRefreshJobs,
}: HeaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-cyan-950/40 w-full">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3">
        <div className="relative w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 flex-shrink-0">
          {/* যদি কাস্টম লোগো ইমেজ থাকে: */}
          {/* <Image src="/logo.png" alt="JobPilot" width={28} height={28} className="object-contain" /> */}
          <BsRobot className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              JobPilot <span className="text-cyan-400 text-xs font-mono font-medium px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800">AI</span>
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Autonomous Job Matcher & Smart Copilot
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
        {lastSynced && (
          <span className="text-[11px] font-mono text-slate-400 bg-slate-900/90 border border-slate-800 px-2.5 py-1.5 rounded-lg w-full sm:w-auto text-center">
            Synced: <span className="text-cyan-400">{lastSynced}</span>
          </span>
        )}

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={onFileUpload}
        />

        {/* Upload Resume Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          className="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs sm:text-sm px-4 py-2.5 rounded-xl transition-all shadow-md shadow-cyan-500/10 active:scale-95 disabled:opacity-50"
        >
          <BsUpload className="w-4 h-4" />
          <span>{loading ? "Processing..." : hasProfile ? "Update CV" : "Upload CV"}</span>
        </button>

        {/* Refresh Vacancies Button */}
        {hasProfile && (
          <button
            onClick={onRefreshJobs}
            disabled={refreshing}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-cyan-400 border border-cyan-900/60 font-medium text-xs sm:text-sm px-3.5 py-2.5 rounded-xl transition-all active:scale-95 disabled:opacity-50"
          >
            <BsArrowRepeat className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            <span>{refreshing ? "Syncing..." : "Refresh"}</span>
          </button>
        )}
      </div>
    </header>
  );
}