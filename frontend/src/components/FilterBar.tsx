"use client";

import { 
  BsGridFill, 
  BsLinkedin, 
  BsBriefcaseFill, 
  BsLaptop, 
  BsBuildings,
  BsSearch,
  BsGeoAlt, 
  BsCheckCircleFill
} from "react-icons/bs";
import { SiTarget } from "react-icons/si";

interface FilterBarProps {
  selectedTab: string;
  onSelectTab: (tab: string) => void;
  totalCount: number;
  districts: string[];
  selectedDistrict: string;
  onSelectDistrict: (district: string) => void;
  searchKeyword: string;
  onSearchKeywordChange: (keyword: string) => void;
}

const TABS = [
  { id: "ALL", label: "All Opportunities", icon: BsGridFill },
  { id: "APPLIED", label: "Applied Tracking", icon: BsCheckCircleFill },
  { id: "LINKEDIN", label: "LinkedIn", icon: BsLinkedin },
  { id: "REMOTIVE", label: "Remotive", icon: BsLaptop },
  { id: "ARBEITNOW", label: "Arbeitnow", icon: BsBuildings },
  { id: "BDJOBS", label: "Bdjobs", icon: BsBriefcaseFill },
  { id: "HIGH_MATCH", label: "Top Fit (50%+)", icon: SiTarget },
  { id: "REMOTE", label: "Remote Only", icon: BsLaptop },
];

export default function FilterBar({ 
  selectedTab, 
  onSelectTab, 
  totalCount,
  districts,
  selectedDistrict,
  onSelectDistrict,
  searchKeyword,
  onSearchKeywordChange
}: FilterBarProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {TABS.map((tab) => {
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
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-3">
        {/* Search Bar */}
        <div className="relative w-full sm:flex-1">
          <BsSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-3.5 h-3.5" />
          <input
            type="text"
            placeholder="Search by title, stack (React, Node, etc.), or company..."
            value={searchKeyword}
            onChange={(e) => onSearchKeywordChange(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-900/60 border border-cyan-950/80 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 transition"
          />
        </div>

        {/* Dynamic District Selector */}
        <div className="relative w-full sm:w-56">
          <BsGeoAlt className="absolute left-3.5 top-1/2 -translate-y-1/2 text-cyan-400 w-3.5 h-3.5 pointer-events-none" />
          <select
            value={selectedDistrict}
            onChange={(e) => onSelectDistrict(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-900/60 border border-cyan-950/80 text-xs text-slate-300 focus:outline-none focus:border-cyan-500/60 transition cursor-pointer appearance-none"
          >
            <option value="ALL" className="bg-slate-900 text-slate-200">All Locations / Global</option>
            {districts.map((d) => (
              <option key={d} value={d} className="bg-slate-900 text-slate-200">
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}