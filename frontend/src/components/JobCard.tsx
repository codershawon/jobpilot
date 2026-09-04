"use client";
import React, { useState } from "react";
import { CVProfile, JobItem } from "@/types/job";
import { BsGeoAltFill, BsCheckCircleFill, BsCheckCircle } from "react-icons/bs";
import { HiSparkles, HiArrowTopRightOnSquare } from "react-icons/hi2";
import { IoDocumentTextOutline } from "react-icons/io5";

interface JobCardProps {
  job: JobItem;
  profile?: CVProfile | null;
  isApplied: boolean;
  onToggleApply: (id: string) => void;
  onOpenCoverLetter: (job: JobItem) => void;
  onOpenApplyStudio: (job: JobItem) => void;
}

export default function JobCard({
  job,
  profile,
  isApplied,
  onToggleApply,
  onOpenCoverLetter,
  onOpenApplyStudio, 
}: JobCardProps) {
  const [copiedKit, setCopiedKit] = useState(false);
  const score = job.match_score || 40;

  const handleCopyApplyKit = () => {
    if (!profile) return;
    const kitText = `Candidate: ${profile.full_name}
      Email: ${profile.email || "N/A"}
      Phone: ${profile.phone || "N/A"}
      Location: ${profile.location || "Bangladesh"}
      Skills: ${profile.skills.join(", ")}

      --- Cover Letter / Pitch ---
      ${job.cover_letter || "Experienced developer passionate about building scalable solutions."}`;

          navigator.clipboard.writeText(kitText);
          setCopiedKit(true);
          setTimeout(() => setCopiedKit(false), 2000);
        };

  return (
    <div className="flex flex-col justify-between rounded-2xl bg-slate-900/40 border border-cyan-950/60 hover:border-cyan-500/40 p-6 transition duration-300 group hover:shadow-[0_0_25px_rgba(6,182,212,0.06)]">
      <div>
        <div className="flex items-center justify-between gap-2">
          <span className="px-2.5 py-1 rounded-md bg-slate-950 border border-cyan-950 text-slate-300 text-xs font-medium font-mono">
            {job.source}
          </span>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-cyan-400 text-xs font-bold shadow-[0_0_12px_rgba(6,182,212,0.12)]">
            <HiSparkles size={14} />
            <span>{score}% Match</span>
          </div>
        </div>

        <h3 className="text-lg font-bold text-slate-100 mt-4 group-hover:text-cyan-300 transition line-clamp-1">
          {job.title}
        </h3>
        <p className="text-sm font-medium text-slate-400 mt-0.5">{job.company}</p>

        <div className="flex items-center gap-3 text-xs text-slate-400 mt-2.5">
          <span className="flex items-center gap-1">
            <BsGeoAltFill size={14} color="#67e8f9" /> {job.location}
          </span>
          {job.is_remote && (
            <span className="px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/30 text-cyan-400">
              Remote
            </span>
          )}
        </div>

        {job.match_reason && (
          <div className="mt-4 p-3.5 rounded-xl bg-slate-950/90 border border-cyan-950/80 text-xs text-slate-300 leading-relaxed">
            <strong className="text-cyan-400">Fit Reason:</strong> {job.match_reason}
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-cyan-950/60 flex items-center justify-between gap-3">
        <button
          onClick={() => onToggleApply(job.id)}
          className={`flex items-center gap-1.5 text-xs font-medium px-3.5 py-2 rounded-xl transition ${
            isApplied
              ? "bg-cyan-950 text-cyan-400 border border-cyan-500/40"
              : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-cyan-950"
          }`}
        >
          {isApplied ? (
            <BsCheckCircleFill size={14} color="#67e8f9" />
          ) : (
            <BsCheckCircle size={14} />
          )}
          <span>{isApplied ? "Applied" : "Mark Applied"}</span>
        </button>

        <div className="flex items-center gap-2">
          {profile && (
            <button
              onClick={handleCopyApplyKit}
              title="Copy Profile Details + Cover Letter to Clipboard"
              className="px-3 py-2 rounded-xl bg-slate-950 hover:bg-slate-900 border border-cyan-950 hover:border-cyan-800 text-xs font-semibold text-slate-300 transition"
            >
              {copiedKit ? "✓ Kit Copied" : "Copy Kit"}
            </button>
          )}
          {job.cover_letter && (
            <button
              onClick={() => onOpenCoverLetter(job)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-950 hover:bg-slate-900 border border-cyan-950 hover:border-cyan-800 text-xs font-semibold text-slate-200 transition"
            >
              <span className="text-cyan-400">
                <IoDocumentTextOutline size={14} />
              </span>
              <span>Cover Letter</span>
            </button>
          )}
          <button
            onClick={() => onOpenApplyStudio(job)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition shadow-[0_0_15px_rgba(6,182,212,0.2)]"
          >
            <span>Auto-Apply</span>
            <HiArrowTopRightOnSquare size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}