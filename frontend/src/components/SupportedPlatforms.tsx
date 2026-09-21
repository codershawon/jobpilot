"use client";

import Container from "./Container";
import { 
  BsBriefcaseFill, 
  BsGlobe2, 
  BsLinkedin, 
  BsFacebook, 
  BsShieldCheck 
} from "react-icons/bs";

const platforms = [
  { name: "Bdjobs.com", icon: BsBriefcaseFill, color: "text-emerald-400" },
  { name: "সরকারি চাকরি (AllJobs)", icon: BsShieldCheck, color: "text-teal-400" },
  { name: "LinkedIn Jobs", icon: BsLinkedin, color: "text-sky-400" },
  { name: "Facebook Hiring Groups", icon: BsFacebook, color: "text-blue-400" },
  { name: "Global Remote Portals", icon: BsGlobe2, color: "text-cyan-400" },
];

export default function SupportedPlatforms() {
  return (
    <div className="w-full py-8 border-y border-slate-800/60 bg-slate-900/20 backdrop-blur-xs">
      <Container>
        <div className="flex flex-col md:flex-row items-center justify-between gap-5">
          <span className="text-xs font-semibold uppercase tracking-widest text-slate-400 shrink-0">
            যেসব প্ল্যাটফর্ম থেকে লাইভ সিঙ্ক হয়
          </span>
          <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
            {platforms.map((p, idx) => {
              const Icon = p.icon;
              return (
                <div
                  key={idx}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs font-medium text-slate-300 hover:border-cyan-500/30 transition-colors"
                >
                  <Icon className={`w-3.5 h-3.5 ${p.color}`} />
                  <span>{p.name}</span>
                </div>
              );
            })}
          </div>
        </div>
      </Container>
    </div>
  );
}