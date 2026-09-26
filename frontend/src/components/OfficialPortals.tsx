"use client";

import { useEffect, useState } from "react";
import { BsShieldCheck, BsBoxArrowUpRight, BsBank, BsBuilding } from "react-icons/bs";
import { API_BASE_URL } from "@/config/api";

interface Portal {
  external_id: string;
  title: string;
  company: string;
  url: string;
  description: string;
  category: string;
  note?: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  bank: "ব্যাংক",
  govt: "সরকারি",
  private: "প্রাইভেট",
};

export default function OfficialPortals() {
  const [portals, setPortals] = useState<Portal[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/portals`)
      .then((r) => r.json())
      .then((d) => d.portals && setPortals(d.portals))
      .catch(() => {});
  }, []);

  if (portals.length === 0) return null;

  const shown = expanded ? portals : portals.slice(0, 3);

  return (
    <div className="rounded-2xl border border-cyan-950/60 bg-slate-900/30 p-4">
      <div className="mb-3 flex items-center gap-2">
        <BsShieldCheck className="text-cyan-400" size={15} />
        <h3 className="text-sm font-bold text-slate-200">অফিসিয়াল নিয়োগ পোর্টাল</h3>
        <span className="text-[11px] text-slate-500">
          এই সাইটগুলো থেকে স্বয়ংক্রিয়ভাবে আনা যায় না — সরাসরি দেখে নিন
        </span>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((p) => (
          <a
            key={p.external_id}
            href={p.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex flex-col rounded-xl border border-cyan-950/70 bg-slate-950/60 p-3.5 transition hover:border-cyan-500/50 hover:bg-slate-900/60"
          >
            <div className="mb-1.5 flex items-start justify-between gap-2">
              <span className="flex items-center gap-1.5 rounded-md bg-slate-900 px-2 py-0.5 text-[10px] font-medium text-slate-400">
                {p.category === "bank" ? <BsBank size={9} /> : <BsBuilding size={9} />}
                {CATEGORY_LABELS[p.category] ?? p.category}
              </span>
              <BsBoxArrowUpRight
                size={11}
                className="mt-0.5 shrink-0 text-slate-600 transition group-hover:text-cyan-400"
              />
            </div>

            <p className="text-xs font-semibold leading-snug text-slate-200 group-hover:text-cyan-300">
              {p.title}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-500">{p.company}</p>
            <p className="mt-2 line-clamp-2 text-[11px] leading-relaxed text-slate-500">
              {p.description}
            </p>
          </a>
        ))}
      </div>

      {portals.length > 3 && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="mt-3 text-[11px] text-slate-500 underline transition hover:text-cyan-400"
        >
          {expanded ? "কম দেখুন" : `আরও ${portals.length - 3}টি পোর্টাল দেখুন`}
        </button>
      )}
    </div>
  );
}