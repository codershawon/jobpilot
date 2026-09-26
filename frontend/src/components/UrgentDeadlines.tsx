"use client";

import { BsAlarmFill, BsArrowRight } from "react-icons/bs";
import { JobItem } from "@/types/job";
import DeadlineBadge, { Urgency } from "./DeadlineBadge";

interface UrgentDeadlinesProps {
  jobs: JobItem[];
  appliedJobs: Record<string, boolean>;
  onOpenApplyStudio: (job: JobItem) => void;
  maxItems?: number;
}

export default function UrgentDeadlines({
  jobs,
  appliedJobs,
  onOpenApplyStudio,
  maxItems = 5,
}: UrgentDeadlinesProps) {
  // ৭ দিনের মধ্যে শেষ হচ্ছে, এখনো আবেদন করিনি — এমন জব
  const urgent = jobs
    .filter((j) => {
      if (appliedJobs[j.id]) return false;
      const d = j.days_left;
      if (d === null || d === undefined || d < 0 || d > 7) return false;
      return (j.match_score ?? 0) >= 40;   // অপ্রাসঙ্গিক জব বাদ
    })
    .sort((a, b) => (a.days_left ?? 99) - (b.days_left ?? 99))
    .slice(0, maxItems);

  if (urgent.length === 0) return null;

  return (
    <div className="rounded-2xl border border-amber-500/30 bg-linear-to-br from-amber-500/[0.07] to-transparent p-4">
      <div className="flex items-center gap-2 mb-3">
        <BsAlarmFill className="text-amber-400" size={15} />
        <h3 className="text-sm font-bold text-amber-200">
          ডেডলাইন ঘনিয়ে আসছে
        </h3>
        <span className="text-[11px] text-amber-400/70">
          ({urgent.length}টি পদ, ৭ দিনের মধ্যে)
        </span>
      </div>

      <div className="space-y-2">
        {urgent.map((job) => (
          <button
            key={job.id}
            onClick={() => onOpenApplyStudio(job)}
            className="w-full flex items-center gap-3 rounded-xl border border-amber-500/20 bg-slate-950/50 px-3.5 py-2.5 text-left transition hover:border-amber-500/50 hover:bg-slate-900/60 group"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-slate-200">
                {job.title}
              </p>
              <p className="truncate text-[11px] text-slate-500">
                {job.company}
              </p>
            </div>

            <DeadlineBadge
              urgency={job.urgency as Urgency}
              daysLeft={job.days_left}
              compact
            />

            <BsArrowRight
              size={13}
              className="text-slate-600 transition group-hover:translate-x-0.5 group-hover:text-amber-400"
            />
          </button>
        ))}
      </div>
    </div>
  );
}