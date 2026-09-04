"use client";

import { BsFileEarmarkTextFill } from "react-icons/bs";
import { JobItem, CVProfile } from "@/types/job";
import JobCard from "./JobCard";

interface JobGridProps {
  jobs: JobItem[];
  profile?: CVProfile | null;
  appliedJobs: Record<string, boolean>;
  onToggleApply: (id: string) => void;
  onOpenCoverLetter: (job: JobItem) => void;
  onOpenApplyStudio: (job: JobItem) => void;
}

export default function JobGrid({
  jobs,
  profile,
  appliedJobs,
  onToggleApply,
  onOpenCoverLetter,
  onOpenApplyStudio,
}: JobGridProps) {
  if (jobs.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-cyan-950 bg-slate-900/20 p-12 text-center flex flex-col items-center justify-center">
        <div className="mb-3 text-cyan-500/30">
          <BsFileEarmarkTextFill size={40} />
        </div>
        <h3 className="text-base font-semibold text-slate-300">No matching roles found in this filter</h3>
        <p className="text-xs text-slate-500 mt-1">Try selecting another tab or uploading an updated CV.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          job={job}
          profile={profile}
          isApplied={appliedJobs[job.id] || false}
          onToggleApply={onToggleApply}
          onOpenCoverLetter={onOpenCoverLetter}
          onOpenApplyStudio={onOpenApplyStudio}
        />
      ))}
    </div>
  );
}