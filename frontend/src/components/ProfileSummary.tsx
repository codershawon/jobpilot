"use client";

import React from "react";
import { BsGeoAltFill, BsBriefcaseFill, BsGlobeAmericas } from "react-icons/bs";
import { CVProfile } from "@/types/job";

interface ProfileSummaryProps {
  profile: CVProfile;
  totalFound: number;
}

export default function ProfileSummary({ profile, totalFound }: ProfileSummaryProps) {
  return (
    <section className="relative rounded-3xl bg-slate-900/60 border border-cyan-950/80 p-6 md:p-8 backdrop-blur-xl shadow-[0_0_30px_rgba(6,182,212,0.03)]">
      <div className="flex flex-col md:flex-row justify-between gap-6">
        <div>
          <h2 className="text-2xl md:text-3xl font-bold text-slate-100">{profile.full_name}</h2>
          <div className="flex flex-wrap items-center gap-4 text-xs md:text-sm text-slate-400 mt-2.5">
            {profile.location && (
              <span className="flex items-center gap-1.5 text-cyan-400">
                <BsGeoAltFill size={14} /> {profile.location}
              </span>
            )}
            <span className="flex items-center gap-1.5 text-cyan-400">
              <BsBriefcaseFill size={14} /> {profile.years_of_experience} Yrs Experience
            </span>
            <span className="flex items-center gap-1.5 text-cyan-400">
              <BsGlobeAmericas size={14} /> {profile.open_to_remote ? "Open to Remote" : "On-site"}
            </span>
          </div>
          {profile.summary && (
            <p className="text-slate-300 text-sm mt-4 leading-relaxed max-w-3xl border-l-2 border-cyan-500/40 pl-3.5">
              {profile.summary}
            </p>
          )}
        </div>

        <div className="flex md:flex-col justify-between md:justify-center items-start md:items-end border-t md:border-t-0 md:border-l border-cyan-950/60 pt-4 md:pt-0 md:pl-8">
          <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Matched Roles</span>
          <span className="text-4xl md:text-5xl font-black text-cyan-400 tracking-tight mt-1">{totalFound}</span>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-cyan-950/60">
        <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-3">
          Identified Skills Matrix
        </span>
        <div className="flex flex-wrap gap-2">
          {profile.skills.map((skill, index) => (
            <span
              key={index}
              className="px-3 py-1.5 rounded-lg bg-slate-950/80 border border-cyan-900/40 text-xs font-medium text-slate-200 shadow-sm"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}