"use client";

import { BsClock, BsExclamationTriangleFill } from "react-icons/bs";

export type Urgency =
  | "expired"
  | "critical"
  | "urgent"
  | "soon"
  | "normal"
  | "unknown";

interface DeadlineBadgeProps {
  urgency?: Urgency;
  daysLeft?: number | null;
  deadline?: string | null;
  compact?: boolean;
}

const STYLES: Record<Urgency, { box: string; icon: string }> = {
  expired: {
    box: "bg-slate-800/60 border-slate-700/60 text-slate-500 line-through",
    icon: "text-slate-600",
  },
  critical: {
    box: "bg-rose-500/15 border-rose-500/50 text-rose-300 animate-pulse",
    icon: "text-rose-400",
  },
  urgent: {
    box: "bg-amber-500/15 border-amber-500/50 text-amber-300",
    icon: "text-amber-400",
  },
  soon: {
    box: "bg-cyan-500/10 border-cyan-500/40 text-cyan-300",
    icon: "text-cyan-400",
  },
  normal: {
    box: "bg-slate-900/60 border-cyan-950/70 text-slate-400",
    icon: "text-slate-500",
  },
  unknown: {
    box: "bg-slate-900/40 border-slate-800/60 text-slate-500",
    icon: "text-slate-600",
  },
};

function labelFor(urgency: Urgency, daysLeft?: number | null): string {
  if (daysLeft === null || daysLeft === undefined) return "তারিখ নেই";
  if (daysLeft < 0) return `${Math.abs(daysLeft)} দিন আগে শেষ`;
  if (daysLeft === 0) return "আজই শেষ দিন";
  if (daysLeft === 1) return "আগামীকাল শেষ";
  return `${daysLeft} দিন বাকি`;
}

export default function DeadlineBadge({
  urgency = "unknown",
  daysLeft,
  deadline,
  compact = false,
}: DeadlineBadgeProps) {
  const style = STYLES[urgency] ?? STYLES.unknown;
  const Icon = urgency === "critical" ? BsExclamationTriangleFill : BsClock;

  const dateText = deadline
    ? new Date(deadline).toLocaleDateString("bn-BD", {
        day: "numeric",
        month: "short",
      })
    : null;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] font-medium ${style.box}`}
      title={deadline ? `শেষ তারিখ: ${deadline}` : "শেষ তারিখ উল্লেখ নেই"}
    >
      <Icon size={11} className={style.icon} />
      <span>{labelFor(urgency, daysLeft)}</span>
      {!compact && dateText && (
        <span className="opacity-60">· {dateText}</span>
      )}
    </span>
  );
}