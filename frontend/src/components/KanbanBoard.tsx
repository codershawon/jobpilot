"use client";

import { useState } from "react";
import {
  BsBookmark,
  BsCheckCircleFill,
  BsFileEarmarkText,
  BsPeople,
  BsTrophy,
  BsXCircle,
  BsBoxArrowUpRight,
  BsTrash,
  BsPencil,
} from "react-icons/bs";
import DeadlineBadge, { Urgency } from "./DeadlineBadge";
import {
  ApplicationItem,
  AppStatus,
} from "@/hooks/useApplications";

interface KanbanBoardProps {
  apps: ApplicationItem[];
  onUpdate: (id: string, patch: Partial<ApplicationItem>) => Promise<unknown>;
  onRemove: (id: string) => Promise<void>;
}

const COLUMNS: {
  id: AppStatus;
  label: string;
  icon: typeof BsBookmark;
  accent: string;
}[] = [
  { id: "SAVED", label: "সেভ করেছি", icon: BsBookmark, accent: "slate" },
  { id: "APPLIED", label: "আবেদন করেছি", icon: BsCheckCircleFill, accent: "cyan" },
  { id: "EXAM", label: "পরীক্ষা", icon: BsFileEarmarkText, accent: "amber" },
  { id: "INTERVIEW", label: "ভাইভা", icon: BsPeople, accent: "violet" },
  { id: "OFFER", label: "অফার", icon: BsTrophy, accent: "emerald" },
  { id: "REJECTED", label: "বাতিল", icon: BsXCircle, accent: "rose" },
];

const ACCENT: Record<string, { border: string; text: string; dot: string }> = {
  slate: { border: "border-slate-700/60", text: "text-slate-400", dot: "bg-slate-500" },
  cyan: { border: "border-cyan-500/40", text: "text-cyan-300", dot: "bg-cyan-400" },
  amber: { border: "border-amber-500/40", text: "text-amber-300", dot: "bg-amber-400" },
  violet: { border: "border-violet-500/40", text: "text-violet-300", dot: "bg-violet-400" },
  emerald: { border: "border-emerald-500/40", text: "text-emerald-300", dot: "bg-emerald-400" },
  rose: { border: "border-rose-500/40", text: "text-rose-300", dot: "bg-rose-400" },
};

const NEXT_STATUS: Record<AppStatus, AppStatus | null> = {
  SAVED: "APPLIED",
  APPLIED: "EXAM",
  EXAM: "INTERVIEW",
  INTERVIEW: "OFFER",
  OFFER: null,
  REJECTED: null,
};

export default function KanbanBoard({ apps, onUpdate, onRemove }: KanbanBoardProps) {
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<ApplicationItem>>({});

  const startEdit = (app: ApplicationItem) => {
    setEditing(app.id);
    setDraft({
      tracking_id: app.tracking_id || "",
      fee_paid: app.fee_paid,
      admit_downloaded: app.admit_downloaded,
      exam_date: app.exam_date || "",
      notes: app.notes || "",
    });
  };

  const saveEdit = async (id: string) => {
    const patch: Partial<ApplicationItem> = { ...draft };
    // খালি স্ট্রিং পাঠালে ব্যাকএন্ড তারিখ পার্স করতে পারবে না
    if (!patch.exam_date) delete patch.exam_date;
    await onUpdate(id, patch);
    setEditing(null);
  };

  if (apps.length === 0) {
    return (
      <div className="rounded-2xl border border-cyan-950/60 bg-slate-900/30 p-10 text-center">
        <p className="text-sm text-slate-400">এখনো কোনো আবেদন যোগ করা হয়নি।</p>
        <p className="mt-1.5 text-xs text-slate-500">
          জব কার্ডে &ldquo;Mark Applied&rdquo; চাপলে এখানে দেখা যাবে।
        </p>
      </div>
    );
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-3">
      {COLUMNS.map((col) => {
        const items = apps.filter((a) => a.status === col.id);
        const style = ACCENT[col.accent];
        const Icon = col.icon;

        return (
          <div key={col.id} className="w-[270px] shrink-0">
            <div className={`mb-2.5 flex items-center gap-2 rounded-xl border ${style.border} bg-slate-900/50 px-3 py-2`}>
              <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
              <Icon size={12} className={style.text} />
              <span className="text-xs font-semibold text-slate-200">{col.label}</span>
              <span className="ml-auto text-[11px] text-slate-500">{items.length}</span>
            </div>

            <div className="space-y-2">
              {items.map((app) => {
                const next = NEXT_STATUS[app.status];
                const isEditing = editing === app.id;

                return (
                  <div
                    key={app.id}
                    className="rounded-xl border border-cyan-950/70 bg-slate-950/60 p-3 transition hover:border-cyan-800/60"
                  >
                    <p className="text-xs font-semibold leading-snug text-slate-200">
                      {app.title}
                    </p>
                    <p className="mt-0.5 truncate text-[11px] text-slate-500">
                      {app.company}
                    </p>

                    <div className="mt-2 flex flex-wrap items-center gap-1.5">
                      {app.days_left !== null && app.days_left !== undefined && (
                        <DeadlineBadge
                          urgency={app.urgency as Urgency}
                          daysLeft={app.days_left}
                          compact
                        />
                      )}
                      {app.tracking_id && (
                        <span className="rounded bg-slate-900 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
                          {app.tracking_id}
                        </span>
                      )}
                      {app.fee_paid && (
                        <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] text-emerald-300">
                          ফি দেওয়া
                        </span>
                      )}
                      {app.admit_downloaded && (
                        <span className="rounded bg-cyan-500/15 px-1.5 py-0.5 text-[10px] text-cyan-300">
                          প্রবেশপত্র
                        </span>
                      )}
                    </div>

                    {app.exam_date && (
                      <p className="mt-1.5 text-[11px] text-amber-300">
                        পরীক্ষা: {app.exam_date}
                      </p>
                    )}

                    {isEditing ? (
                      <div className="mt-2.5 space-y-2 border-t border-cyan-950/60 pt-2.5">
                        <input
                          type="text"
                          placeholder="ট্র্যাকিং আইডি / User ID"
                          value={draft.tracking_id ?? ""}
                          onChange={(e) =>
                            setDraft((d) => ({ ...d, tracking_id: e.target.value }))
                          }
                          className="w-full rounded-lg border border-cyan-950/80 bg-slate-900/60 px-2.5 py-1.5 text-[11px] text-slate-200 placeholder-slate-600 focus:border-cyan-500/60 focus:outline-none"
                        />
                        <input
                          type="date"
                          value={draft.exam_date ?? ""}
                          onChange={(e) =>
                            setDraft((d) => ({ ...d, exam_date: e.target.value }))
                          }
                          className="w-full rounded-lg border border-cyan-950/80 bg-slate-900/60 px-2.5 py-1.5 text-[11px] text-slate-300 focus:border-cyan-500/60 focus:outline-none"
                        />
                        <textarea
                          placeholder="নোট"
                          rows={2}
                          value={draft.notes ?? ""}
                          onChange={(e) =>
                            setDraft((d) => ({ ...d, notes: e.target.value }))
                          }
                          className="w-full resize-none rounded-lg border border-cyan-950/80 bg-slate-900/60 px-2.5 py-1.5 text-[11px] text-slate-200 placeholder-slate-600 focus:border-cyan-500/60 focus:outline-none"
                        />
                        <div className="flex gap-3 text-[11px] text-slate-400">
                          <label className="flex items-center gap-1.5">
                            <input
                              type="checkbox"
                              checked={!!draft.fee_paid}
                              onChange={(e) =>
                                setDraft((d) => ({ ...d, fee_paid: e.target.checked }))
                              }
                              className="accent-cyan-500"
                            />
                            ফি দিয়েছি
                          </label>
                          <label className="flex items-center gap-1.5">
                            <input
                              type="checkbox"
                              checked={!!draft.admit_downloaded}
                              onChange={(e) =>
                                setDraft((d) => ({
                                  ...d,
                                  admit_downloaded: e.target.checked,
                                }))
                              }
                              className="accent-cyan-500"
                            />
                            প্রবেশপত্র
                          </label>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => saveEdit(app.id)}
                            className="flex-1 rounded-lg bg-cyan-500 px-2 py-1.5 text-[11px] font-bold text-slate-950 transition hover:bg-cyan-400"
                          >
                            সেভ
                          </button>
                          <button
                            onClick={() => setEditing(null)}
                            className="rounded-lg border border-cyan-950 px-2.5 py-1.5 text-[11px] text-slate-400 transition hover:text-slate-200"
                          >
                            বাতিল
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-2.5 flex items-center gap-1.5 border-t border-cyan-950/60 pt-2.5">
                        {next && (
                          <button
                            onClick={() => onUpdate(app.id, { status: next })}
                            className="rounded-lg bg-slate-900 px-2 py-1 text-[10px] font-medium text-slate-300 transition hover:bg-cyan-950 hover:text-cyan-300"
                          >
                            → {COLUMNS.find((c) => c.id === next)?.label}
                          </button>
                        )}
                        {app.status !== "REJECTED" && (
                          <button
                            onClick={() => onUpdate(app.id, { status: "REJECTED" })}
                            className="rounded-lg px-1.5 py-1 text-[10px] text-slate-600 transition hover:text-rose-300"
                          >
                            বাতিল
                          </button>
                        )}
                        <button
                          onClick={() => startEdit(app)}
                          title="বিস্তারিত"
                          className="ml-auto p-1 text-slate-600 transition hover:text-cyan-400"
                        >
                          <BsPencil size={11} />
                        </button>
                        {app.url && (
                          <a
                            href={app.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="সার্কুলার দেখুন"
                            className="p-1 text-slate-600 transition hover:text-cyan-400"
                          >
                            <BsBoxArrowUpRight size={11} />
                          </a>
                        )}
                        <button
                          onClick={() => onRemove(app.id)}
                          title="মুছুন"
                          className="p-1 text-slate-600 transition hover:text-rose-400"
                        >
                          <BsTrash size={11} />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}