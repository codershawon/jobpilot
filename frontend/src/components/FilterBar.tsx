"use client";

import {
  BsGridFill,
  BsSearch,
  BsGeoAlt,
  BsCheckCircleFill,
  BsXLg,
} from "react-icons/bs";
import { SiTarget } from "react-icons/si";
import { HiSparkles } from "react-icons/hi2";

export interface Category {
  id: string;
  label_bn: string;
  label_en: string;
}

interface FilterBarProps {
  /* স্ট্যাটাস ট্যাব — শুধু ALL / APPLIED / HIGH_MATCH */
  selectedTab: string;
  onSelectTab: (tab: string) => void;
  totalCount: number;

  /* সেক্টর — একাধিক বাছা যায় */
  sectors: Category[];
  selectedSectors: string[];
  onToggleSector: (id: string) => void;

  /* কাজের ক্ষেত্র — একটাই */
  functions: Category[];
  selectedFunction: string;
  onSelectFunction: (id: string) => void;

  /* উৎস — ড্রপডাউনে */
  sources: Category[];
  selectedSource: string;
  onSelectSource: (id: string) => void;

  /* জেলা ও কি-ওয়ার্ড */
  districts: string[];
  selectedDistrict: string;
  onSelectDistrict: (district: string) => void;
  searchKeyword: string;
  onSearchKeywordChange: (keyword: string) => void;

  /* CV থেকে পাওয়া কাজের ক্ষেত্র — সাজেশন দেখাতে */
  profileFunction?: string | null;
  onClearAll: () => void;
}

const STATUS_TABS = [
  { id: "ALL", label: "সব", icon: BsGridFill },
  { id: "HIGH_MATCH", label: "ভালো ম্যাচ (৫০%+)", icon: SiTarget },
  { id: "APPLIED", label: "আবেদন করেছি", icon: BsCheckCircleFill },
];

export default function FilterBar({
  selectedTab,
  onSelectTab,
  totalCount,
  sectors,
  selectedSectors,
  onToggleSector,
  functions,
  selectedFunction,
  onSelectFunction,
  sources,
  selectedSource,
  onSelectSource,
  districts,
  selectedDistrict,
  onSelectDistrict,
  searchKeyword,
  onSearchKeywordChange,
  profileFunction,
  onClearAll,
}: FilterBarProps) {
  const hasActiveFilter =
    selectedSectors.length > 0 ||
    selectedFunction !== "ALL" ||
    selectedSource !== "ALL" ||
    selectedDistrict !== "ALL" ||
    searchKeyword.trim() !== "";

  const profileLabel = functions.find((f) => f.id === profileFunction)?.label_bn;

  return (
    <div className="space-y-4 rounded-2xl bg-slate-900/30 border border-cyan-950/60 p-4">
      {/* ─── CV ভিত্তিক সাজেশন ─── */}
      {profileLabel && selectedFunction === profileFunction && (
        <div className="flex items-center gap-2 text-xs text-cyan-300">
          <HiSparkles size={14} />
          <span>
            আপনার CV অনুযায়ী <strong>{profileLabel}</strong> ক্যাটাগরি বেছে নেওয়া
            হয়েছে
          </span>
          <button
            onClick={() => onSelectFunction("ALL")}
            className="ml-1 underline text-slate-400 hover:text-slate-200"
          >
            সব দেখুন
          </button>
        </div>
      )}

      {/* ─── স্ট্যাটাস ট্যাব ─── */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {STATUS_TABS.map((tab) => {
          const isActive = selectedTab === tab.id;
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`flex items-center gap-2 whitespace-nowrap px-4 py-2.5 rounded-xl text-xs font-semibold transition duration-200 ${
                isActive
                  ? "bg-cyan-500 text-slate-950 shadow-[0_0_20px_rgba(6,182,212,0.3)]"
                  : "bg-slate-900/60 border border-cyan-950/60 text-slate-400 hover:text-slate-200 hover:border-cyan-800/60"
              }`}
            >
              <Icon size={14} />
              <span>
                {tab.label} {tab.id === "ALL" && `(${totalCount})`}
              </span>
            </button>
          );
        })}

        {hasActiveFilter && (
          <button
            onClick={onClearAll}
            className="flex items-center gap-1.5 whitespace-nowrap px-3 py-2.5 rounded-xl text-xs font-medium text-slate-500 hover:text-rose-300 transition"
          >
            <BsXLg size={11} />
            <span>ফিল্টার মুছুন</span>
          </button>
        )}
      </div>

      {/* ─── সেক্টর (একাধিক বাছা যায়) ─── */}
      <div>
        <p className="text-[11px] uppercase tracking-wider text-slate-500 mb-2">
          সেক্টর
        </p>
        <div className="flex flex-wrap gap-2">
          {sectors.map((s) => {
            const isActive = selectedSectors.includes(s.id);
            return (
              <button
                key={s.id}
                onClick={() => onToggleSector(s.id)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
                  isActive
                    ? "bg-cyan-500/15 border border-cyan-500/60 text-cyan-300"
                    : "bg-slate-950/60 border border-cyan-950/70 text-slate-400 hover:text-slate-200 hover:border-cyan-800/60"
                }`}
              >
                {s.label_bn}
              </button>
            );
          })}
        </div>
      </div>

      {/* ─── কাজের ক্ষেত্র (একটাই) ─── */}
      <div>
        <p className="text-[11px] uppercase tracking-wider text-slate-500 mb-2">
          কাজের ক্ষেত্র
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onSelectFunction("ALL")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
              selectedFunction === "ALL"
                ? "bg-cyan-500/15 border border-cyan-500/60 text-cyan-300"
                : "bg-slate-950/60 border border-cyan-950/70 text-slate-400 hover:text-slate-200 hover:border-cyan-800/60"
            }`}
          >
            সব
          </button>
          {functions.map((f) => {
            const isActive = selectedFunction === f.id;
            return (
              <button
                key={f.id}
                onClick={() => onSelectFunction(f.id)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
                  isActive
                    ? "bg-cyan-500/15 border border-cyan-500/60 text-cyan-300"
                    : "bg-slate-950/60 border border-cyan-950/70 text-slate-400 hover:text-slate-200 hover:border-cyan-800/60"
                }`}
              >
                {f.label_bn}
              </button>
            );
          })}
        </div>
      </div>

      {/* ─── সার্চ, জেলা, উৎস ─── */}
      <div className="flex flex-col sm:flex-row items-center gap-3 pt-1">
        <div className="relative w-full sm:flex-1">
          <BsSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-3.5 h-3.5" />
          <input
            type="text"
            placeholder="পদের নাম, প্রতিষ্ঠান বা স্কিল দিয়ে খুঁজুন..."
            value={searchKeyword}
            onChange={(e) => onSearchKeywordChange(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-900/60 border border-cyan-950/80 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 transition"
          />
        </div>

        <div className="relative w-full sm:w-52">
          <BsGeoAlt className="absolute left-3.5 top-1/2 -translate-y-1/2 text-cyan-400 w-3.5 h-3.5 pointer-events-none" />
          <select
            value={selectedDistrict}
            onChange={(e) => onSelectDistrict(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-900/60 border border-cyan-950/80 text-xs text-slate-300 focus:outline-none focus:border-cyan-500/60 transition cursor-pointer appearance-none"
          >
            <option value="ALL" className="bg-slate-900 text-slate-200">
              সব জেলা / আন্তর্জাতিক
            </option>
            {districts.map((d) => (
              <option key={d} value={d} className="bg-slate-900 text-slate-200">
                {d}
              </option>
            ))}
          </select>
        </div>

        <div className="relative w-full sm:w-44">
          <select
            value={selectedSource}
            onChange={(e) => onSelectSource(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl bg-slate-900/60 border border-cyan-950/80 text-xs text-slate-300 focus:outline-none focus:border-cyan-500/60 transition cursor-pointer appearance-none"
          >
            <option value="ALL" className="bg-slate-900 text-slate-200">
              সব উৎস
            </option>
            {sources.map((s) => (
              <option key={s.id} value={s.id} className="bg-slate-900 text-slate-200">
                {s.label_bn}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}