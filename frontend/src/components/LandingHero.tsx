"use client";

import React, { useRef, useState } from "react";
import Image from "next/image";
import { 
  BsUpload, 
  BsShieldCheck, 
  BsCheckCircleFill,
  BsFileEarmarkPdf,
  BsSearch,
  BsBuildingsFill,
  BsGeoAltFill,
  BsArrowRight,
  BsLightningChargeFill,
  BsSpeakerFill
} from "react-icons/bs";
import Container from "./Container";

interface LandingBannerProps {
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  loading: boolean;
}

export default function LandingBanner({ onFileUpload, loading }: LandingBannerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const pseudoEvent = {
        target: { files: e.dataTransfer.files },
      } as unknown as React.ChangeEvent<HTMLInputElement>;
      onFileUpload(pseudoEvent);
    }
  };

  return (
    <section className="relative w-full py-10 md:py-20 overflow-hidden">
      {/* Background Soft Glows */}
      <div 
        aria-hidden="true" 
        className="pointer-events-none absolute -top-24 left-1/4 w-120 h-80 bg-cyan-500/10 blur-[120px] rounded-full -z-10" 
      />
      <div 
        aria-hidden="true" 
        className="pointer-events-none absolute top-16 right-4 w-95 h-70 bg-sky-500/10 blur-[130px] rounded-full -z-10" 
      />

      {/* Unified Global Container: হেডার ও ফুটারে যে মার্জিন/উইডথ আছে, ব্যানারও হুবহু তাই পাবে */}
      <Container>
        {/* Main Grid: Left Copy & Upload + Right Native Code Simulation */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
          
          {/* LEFT COLUMN: Clean Pitch & Dropzone */}
          <div className="lg:col-span-7 space-y-5 text-left">
            
            {/* Status Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-cyan-500/30 text-cyan-300 text-xs shadow-sm shadow-cyan-950/40 backdrop-blur-md">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
              <span className="font-medium text-slate-300">Autonomous Career Co-Pilot</span>
              <span className="text-slate-600">|</span>
              <span className="text-cyan-400 flex items-center gap-1 font-semibold">
                <BsSpeakerFill className="w-3 h-3" /> Live
              </span>
            </div>

            {/* Scaled-down balanced heading */}
            <h1 className="text-2xl sm:text-3xl lg:text-[34px] font-bold text-white tracking-tight leading-[1.35]">
              আপনার সিভি দিন, ক্যারিয়ারের বাকি কাজ করবে{" "}
              <span className="text-transparent bg-clip-text bg-linear-to-r from-cyan-400 via-sky-300 to-teal-300">
                অটোনোমাস এআই এজেন্ট
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-slate-400 text-xs sm:text-sm leading-relaxed max-w-lg font-normal">
              বাংলাদেশের শীর্ষ জব পোর্টাল ও রিমোট সাইট থেকে আপনার দক্ষতার নিখুঁত সার্কুলার ফিল্টার করুন, ম্যাচ স্কোর মাপুন এবং ১-ক্লিকে কাস্টম কভার লেটার তৈরি করুন।
            </p>

            {/* Interactive Upload Dropzone */}
            <div className="pt-1 w-full max-w-xl">
              <input
                type="file"
                ref={fileInputRef}
                onChange={onFileUpload}
                accept=".pdf,.docx"
                className="hidden"
                disabled={loading}
              />

              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`group relative cursor-pointer rounded-2xl border transition-all duration-200 p-5 sm:p-6 ${
                  isDragOver
                    ? "border-cyan-400 bg-cyan-950/30 shadow-lg shadow-cyan-500/10 scale-[1.01]"
                    : "border-slate-800 bg-slate-900/60 hover:border-cyan-500/40 hover:bg-slate-900/90 shadow-md shadow-black/40"
                }`}
              >
                {/* Subtle top edge lighting */}
                <div className="absolute inset-x-8 top-0 h-px bg-linear-to-r from-transparent via-cyan-500/40 to-transparent" />

                <div className="flex flex-col sm:flex-row items-center gap-4">
                  {/* Logo Frame */}
                  <div className="relative w-12 h-12 rounded-xl bg-[#090D16] border border-cyan-500/30 p-2 flex items-center justify-center shrink-0 shadow-sm shadow-cyan-500/10 group-hover:scale-105 transition-transform duration-200">
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Image
                        src="/logo.svg"
                        alt="JobPilot Logo"
                        width={32}
                        height={32}
                        className="object-contain"
                      />
                    )}
                  </div>

                  {/* Upload Texts */}
                  <div className="space-y-0.5 text-center sm:text-left flex-1">
                    <p className="text-sm sm:text-base font-semibold text-slate-100 group-hover:text-cyan-300 transition-colors">
                      {loading ? "রেজুমে বিশ্লেষণ করা হচ্ছে..." : "আপনার সিভি সিলেক্ট করুন"}
                    </p>
                    <p className="text-xs text-slate-400 font-normal">PDF বা DOCX ফাইল সমর্থন করে (সর্বোচ্চ ১০MB)</p>
                  </div>

                  {/* Action Button */}
                  <button
                    type="button"
                    className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-linear-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-slate-950 font-bold text-xs shadow-sm shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-all shrink-0 active:scale-95"
                  >
                    <BsUpload className="w-3.5 h-3.5" />
                    <span>আপ্লোড করুন</span>
                  </button>
                </div>
              </div>

              {/* Quick Guarantees */}
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-3 pl-1">
                <span className="flex items-center gap-1.5">
                  <BsShieldCheck className="text-cyan-400 w-3.5 h-3.5" /> ক্লাউড এনক্রিপ্টেড
                </span>
                <span>•</span>
                <span className="flex items-center gap-1.5">
                  <BsCheckCircleFill className="text-emerald-400 w-3.5 h-3.5" /> ১০০% ফ্রি
                </span>
                <span>•</span>
                <span>একবার আপলোডেই অটো-সেভ</span>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: Pure Code Native Interactive Simulation Window */}
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-2xl bg-linear-to-b from-slate-800 to-slate-900/60 p-px shadow-2xl shadow-cyan-950/40">
              <div className="rounded-[15px] bg-[#090D16] p-5 space-y-3.5 backdrop-blur-xl">
                
                {/* Window Bar */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                    <span className="text-[11px] font-mono text-slate-400 ml-2">agent_engine_live</span>
                  </div>
                  <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded-full tracking-wider">
                    MATCHING
                  </span>
                </div>

                {/* Sample Job Card 1 (94% Match) */}
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 hover:border-cyan-500/30 transition-all space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-white leading-tight">Full-Stack Engineer (React &amp; FastAPI)</h4>
                      <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-1">
                        <BsBuildingsFill className="w-3 h-3 text-cyan-400" /> Mukti Tech • <BsGeoAltFill className="w-3 h-3 text-slate-400" /> Dhaka / Hybrid
                      </p>
                    </div>
                    <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded-md shrink-0">
                      94% Match
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-0.5">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800/90 text-cyan-200 font-mono border border-slate-700/50">React</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800/90 text-cyan-200 font-mono border border-slate-700/50">FastAPI</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800/90 text-cyan-200 font-mono border border-slate-700/50">PostgreSQL</span>
                  </div>
                </div>

                {/* Sample Job Card 2 (88% Match) */}
                <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/50 space-y-2 opacity-90">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-semibold text-slate-200 leading-tight">Frontend Developer (Next.js)</h4>
                      <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-1">
                        <BsBuildingsFill className="w-3 h-3 text-sky-400" /> Microters • <BsGeoAltFill className="w-3 h-3 text-slate-400" /> Cumilla / Remote
                      </p>
                    </div>
                    <span className="text-[11px] font-bold text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded-md shrink-0">
                      88% Match
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-0.5">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 font-mono border border-slate-700/50">Next.js</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 font-mono border border-slate-700/50">Tailwind</span>
                  </div>
                </div>

                {/* Action Bar Simulation */}
                <div className="p-2.5 rounded-xl bg-cyan-950/30 border border-cyan-900/40 flex items-center justify-between text-xs">
                  <span className="text-slate-200 font-medium flex items-center gap-1.5">
                    <BsLightningChargeFill className="text-cyan-400" /> কভার লেটার ও কোল্ড মেইল ড্রাফট রেডি
                  </span>
                  <span className="text-cyan-400 font-bold text-[11px] flex items-center gap-1">
                    Instant <BsArrowRight />
                  </span>
                </div>

              </div>
            </div>
          </div>

        </div>

        {/* Bottom Features Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-10 pt-6 border-t border-slate-800/60">
          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-900/30 border border-slate-800/60 hover:border-slate-700/80 transition-all">
            <div className="p-2 rounded-lg bg-cyan-950/60 text-sky-400 shrink-0">
              <BsSearch className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-200">৬৪ জেলা ও রিমোট</h4>
              <p className="text-[11px] text-slate-400 font-normal">আপনার পছন্দের লোকেশনের সার্কুলার ফিল্টার</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-900/30 border border-slate-800/60 hover:border-slate-700/80 transition-all">
            <div className="p-2 rounded-lg bg-sky-950/60 text-sky-400 shrink-0">
              <BsFileEarmarkPdf className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-200">স্মার্ট স্কিল ম্যাচ স্কোর</h4>
              <p className="text-[11px] text-slate-400 font-normal">সিভির সাথে রিকোয়ারমেন্টের নিখুঁত পার্সেন্টেজ</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-900/30 border border-slate-800/60 hover:border-slate-700/80 transition-all">
            <div className="p-2 rounded-lg bg-teal-950/60 text-sky-400 shrink-0">
              <BsShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-200">ক্লাউড ডেটাবেজ ব্যাকআপ</h4>
              <p className="text-[11px] text-slate-400 font-normal">বারবার আপলোড করার ঝামেলা ছাড়াই সেভ</p>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}