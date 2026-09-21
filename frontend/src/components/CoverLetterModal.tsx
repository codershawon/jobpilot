"use client";

import React, { useState } from "react";
import { JobItem } from "@/types/job";
import { GiSparkles } from "react-icons/gi";
import { BiCheck, BiCopy, BiX } from "react-icons/bi";

interface Props {
  job: JobItem | null;
  onClose: () => void;
}

export default function CoverLetterModal({ job, onClose }: Props) {
  const [copied, setCopied] = useState(false);

  if (!job) return null;

  const handleCopy = () => {
    if (job.cover_letter) {
      navigator.clipboard.writeText(job.cover_letter);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in duration-200">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold">
            <GiSparkles size={20} />
            <span>AI Tailored Cover Letter</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition"
          >
            <BiX size={20} />
          </button>
        </div>

        <div className="mt-4">
          <h4 className="text-lg font-medium text-zinc-100">
            {job.title} <span className="text-zinc-500 font-normal">at</span> {job.company}
          </h4>
          <p className="text-xs text-zinc-400 mt-1">Generated specifically based on your CV & job requirements.</p>

          <div className="mt-4 p-4 rounded-xl bg-zinc-950 border border-zinc-800/80 text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap max-h-87.5 overflow-y-auto">
            {job.cover_letter || "No tailored cover letter generated for this lower match score."}
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition"
          >
            Close
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm transition shadow-lg shadow-emerald-600/20"
          >
            {copied ? <BiCheck size={16} /> : <BiCopy size={16} />}
            {copied ? "Copied to Clipboard!" : "Copy Cover Letter"}
          </button>
        </div>
      </div>
    </div>
  );
}