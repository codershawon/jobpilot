"use client";

import React from "react";
import { BsCloudArrowUpFill, BsArrowRepeat } from "react-icons/bs";
import { HiSparkles } from "react-icons/hi2";
import { TbBrain } from "react-icons/tb";

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
  return (
    <header className="border-b border-cyan-950/60 pb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider shadow-[0_0_15px_rgba(6,182,212,0.15)]">
            <HiSparkles className="w-3.5 h-3.5 animate-pulse" />
            Autonomous AI Recruiter
          </span>
          <span className="text-slate-500 text-xs font-mono flex items-center gap-1">
            <TbBrain className="w-3.5 h-3.5 text-cyan-500/50" /> Multi-Source Live
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-black tracking-tight text-slate-100 mt-3">
          Job<span className="text-cyan-400">Pilot</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Precision CV parsing, persistent candidate profile & instant multi-platform vacancy syncing.
        </p>
        {lastSynced && (
          <p className="text-xs text-cyan-500/70 font-mono mt-1">
            Last Synced: {lastSynced}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {hasProfile && (
          <button
            onClick={onRefreshJobs}
            disabled={loading || refreshing}
            className="flex items-center gap-2 px-5 py-3.5 rounded-xl bg-slate-900 border border-cyan-500/30 hover:border-cyan-400 text-cyan-400 font-bold text-xs transition duration-200 active:scale-95 shadow-[0_0_15px_rgba(6,182,212,0.1)] disabled:opacity-50"
          >
            <BsArrowRepeat className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            <span>{refreshing ? "Checking Vacancies..." : "Check New Vacancies"}</span>
          </button>
        )}

        <label className="relative group cursor-pointer">
          <div className="absolute -inset-0.5 bg-linear-to-r from-cyan-500 to-cyan-300 rounded-xl blur opacity-25 group-hover:opacity-60 transition duration-300"></div>
          <div className="relative flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs md:text-sm transition active:scale-95 shadow-lg shadow-cyan-500/10">
            <BsCloudArrowUpFill className="w-4 h-4 text-slate-950" />
            <span>{hasProfile ? "Change Resume" : "Upload Resume"}</span>
            <input
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={onFileUpload}
              disabled={loading || refreshing}
            />
          </div>
        </label>
      </div>
    </header>
  );
}