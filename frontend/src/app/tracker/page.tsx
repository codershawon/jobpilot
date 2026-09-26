"use client";

import { useUser } from "@clerk/nextjs";
import Link from "next/link";
import {
  BsArrowLeft,
  BsArrowRepeat,
  BsBriefcase,
  BsCheckCircle,
  BsCalendarEvent,
  BsTrophy,
} from "react-icons/bs";

import Container from "@/components/Container";
import KanbanBoard from "@/components/KanbanBoard";
import { useApplications } from "@/hooks/useApplications";

export default function TrackerPage() {
  const { isSignedIn, isLoaded } = useUser();
  const { apps, stats, loading, error, refresh, updateApplication, removeApplication } =
    useApplications();

  if (!isLoaded) {
    return (
      <Container className="py-16">
        <p className="text-center text-sm text-slate-500">লোড হচ্ছে...</p>
      </Container>
    );
  }

  if (!isSignedIn) {
    return (
      <Container className="py-16">
        <div className="rounded-2xl border border-cyan-950/60 bg-slate-900/30 p-10 text-center">
          <h2 className="text-lg font-bold text-slate-100">লগইন প্রয়োজন</h2>
          <p className="mt-2 text-sm text-slate-400">
            আবেদন ট্র্যাকার ব্যবহার করতে সাইন ইন করুন। তাহলে যেকোনো ডিভাইস থেকে
            আপনার আবেদনের ইতিহাস দেখতে পারবেন।
          </p>
          <Link
            href="/"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2 text-xs font-bold text-slate-950 transition hover:bg-cyan-400"
          >
            <BsArrowLeft size={12} /> ড্যাশবোর্ডে ফিরুন
          </Link>
        </div>
      </Container>
    );
  }

  const byStatus = stats?.by_status || {};
  const cards = [
    {
      label: "মোট আবেদন",
      value: stats?.total ?? 0,
      icon: BsBriefcase,
      color: "text-cyan-300",
    },
    {
      label: "আবেদন করেছি",
      value: byStatus.APPLIED ?? 0,
      icon: BsCheckCircle,
      color: "text-emerald-300",
    },
    {
      label: "আসছে পরীক্ষা",
      value: stats?.upcoming_exams ?? 0,
      icon: BsCalendarEvent,
      color: "text-amber-300",
    },
    {
      label: "অফার পেয়েছি",
      value: byStatus.OFFER ?? 0,
      icon: BsTrophy,
      color: "text-violet-300",
    },
  ];

  // ফানেল — কতজন কোন ধাপে
  const funnel = [
    { label: "সেভ", n: byStatus.SAVED ?? 0 },
    { label: "আবেদন", n: byStatus.APPLIED ?? 0 },
    { label: "পরীক্ষা", n: byStatus.EXAM ?? 0 },
    { label: "ভাইভা", n: byStatus.INTERVIEW ?? 0 },
    { label: "অফার", n: byStatus.OFFER ?? 0 },
  ];

  return (
    <Container className="space-y-6 py-8">
      {/* হেডার */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-100">আবেদন ট্র্যাকার</h1>
          <p className="mt-0.5 text-xs text-slate-500">
            কোথায় আবেদন করেছেন, কোন ধাপে আছেন — সব এক জায়গায়
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={refresh}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-xl border border-cyan-950 bg-slate-900/60 px-3 py-2 text-xs text-slate-300 transition hover:border-cyan-800 hover:text-slate-100 disabled:opacity-50"
          >
            <BsArrowRepeat size={12} className={loading ? "animate-spin" : ""} />
            রিফ্রেশ
          </button>
          <Link
            href="/"
            className="flex items-center gap-1.5 rounded-xl border border-cyan-950 bg-slate-900/60 px-3 py-2 text-xs text-slate-300 transition hover:border-cyan-800 hover:text-slate-100"
          >
            <BsArrowLeft size={12} /> ড্যাশবোর্ড
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* স্ট্যাট কার্ড */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <div
              key={c.label}
              className="rounded-2xl border border-cyan-950/60 bg-slate-900/30 p-4"
            >
              <div className="flex items-center gap-2">
                <Icon size={13} className={c.color} />
                <span className="text-[11px] text-slate-500">{c.label}</span>
              </div>
              <p className={`mt-1.5 text-2xl font-bold ${c.color}`}>{c.value}</p>
            </div>
          );
        })}
      </div>

      {/* ফানেল */}
      {(stats?.total ?? 0) > 0 && (
        <div className="rounded-2xl border border-cyan-950/60 bg-slate-900/30 p-4">
          <p className="mb-3 text-[11px] uppercase tracking-wider text-slate-500">
            অগ্রগতি
          </p>
          <div className="flex flex-wrap items-center gap-2">
            {funnel.map((f, i) => (
              <div key={f.label} className="flex items-center gap-2">
                <div className="rounded-lg border border-cyan-950/70 bg-slate-950/60 px-3 py-1.5">
                  <span className="text-xs font-bold text-slate-200">{f.n}</span>
                  <span className="ml-1.5 text-[11px] text-slate-500">{f.label}</span>
                </div>
                {i < funnel.length - 1 && (
                  <span className="text-slate-700">→</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* বোর্ড */}
      <KanbanBoard
        apps={apps}
        onUpdate={updateApplication}
        onRemove={removeApplication}
      />
    </Container>
  );
}