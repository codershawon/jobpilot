"use client";

import React, { useState, useEffect } from "react";
import { IoCloseOutline } from "react-icons/io5";
import { HiSparkles, HiArrowTopRightOnSquare } from "react-icons/hi2";
import { FiCopy, FiCheck } from "react-icons/fi";
import { BsCheckCircleFill, BsPersonFill, BsEnvelopeFill, BsTelephoneFill, BsGeoAltFill } from "react-icons/bs";
import { JobItem, CVProfile } from "@/types/job";

interface Props {
  job: JobItem | null;
  profile: CVProfile | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirmApply: (jobId: string) => void;
}

export default function ApplyStudioModal({
  job,
  profile,
  isOpen,
  onClose,
  onConfirmApply,
}: Props) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [coverLetter, setCoverLetter] = useState("");
  const [customQuestion, setCustomQuestion] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [generatingAnswer, setGeneratingAnswer] = useState(false);
  const [copiedAll, setCopiedAll] = useState(false);

  // অটো-ফিল প্রিলোডার
  useEffect(() => {
    if (profile && job) {
      setFullName(profile.full_name || "");
      setEmail(profile.email || "");
      setPhone(profile.phone || "");
      setLocation(profile.location || profile.district || "Bangladesh");
      setCoverLetter(
        job.cover_letter ||
          `Dear Hiring Team at ${job.company},\n\nI am excited to apply for the ${job.title} position. With ${profile.years_of_experience} years of hands-on experience in ${profile.skills.slice(0, 4).join(", ")}, I am confident in my ability to add immediate value to your engineering team.\n\nBest regards,\n${profile.full_name}`
      );
      setCustomQuestion("");
      setAiAnswer("");
    }
  }, [profile, job]);

  if (!isOpen || !job || !profile) return null;

  // এআই স্ক্রিনিং প্রশ্ন জেনারেটর
  const handleGenerateAnswer = async () => {
    if (!customQuestion.trim()) return;
    setGeneratingAnswer(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/jobs/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile: profile,
          jobs: [{ ...job, description: `Question: ${customQuestion}\nJob Description: ${job.description}` }],
          generate_cover_letters_for_top: 1,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const generated = data.matched_jobs?.[0]?.cover_letter;
        setAiAnswer(generated || `Based on my background in ${profile.skills.slice(0, 3).join(", ")}, I have extensive experience tackling this exact requirement.`);
      } else {
        setAiAnswer(`I have ${profile.years_of_experience}+ years of experience actively working with ${profile.skills.slice(0, 3).join(", ")} delivering high-performance applications.`);
      }
    } catch {
      setAiAnswer(`I have ${profile.years_of_experience}+ years of experience actively working with ${profile.skills.slice(0, 3).join(", ")}.`);
    } finally {
      setGeneratingAnswer(false);
    }
  };

  const handleCopyAndLaunch = () => {
    const fullPayload = `--- CANDIDATE DETAILS ---
Name: ${fullName}
Email: ${email}
Phone: ${phone}
Location: ${location}
Skills: ${profile.skills.join(", ")}

--- COVER LETTER / PITCH ---
${coverLetter}
${aiAnswer ? `\n--- SCREENING ANSWER ---\nQ: ${customQuestion}\nA: ${aiAnswer}` : ""}`;

    navigator.clipboard.writeText(fullPayload);
    setCopiedAll(true);
    onConfirmApply(job.id);

    setTimeout(() => {
      setCopiedAll(false);
      window.open(job.url, "_blank");
      onClose();
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 overflow-y-auto">
      <div className="w-full max-w-3xl bg-slate-900 border border-cyan-900/60 rounded-3xl p-6 md:p-8 shadow-[0_0_60px_rgba(6,182,212,0.12)] my-8">
        
        <div className="flex items-center justify-between border-b border-cyan-950 pb-4">
          <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
            <HiSparkles className="w-5 h-5 animate-pulse" />
            <span>AI Auto-Apply Studio</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
          >
            <IoCloseOutline size={24} />
          </button>
        </div>

        {/* টার্গেট জব ইনফো */}
        <div className="mt-4 p-4 rounded-2xl bg-slate-950/70 border border-cyan-950 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30">
              {job.source}
            </span>
            <h3 className="text-base font-bold text-slate-100 mt-1.5">{job.title}</h3>
            <p className="text-xs text-slate-400">{job.company} • {job.location}</p>
          </div>
          <div className="text-right">
            <span className="text-xs font-bold text-cyan-400 bg-cyan-950/80 px-3 py-1 rounded-full border border-cyan-500/30">
              {job.match_score || 40}% Fit
            </span>
          </div>
        </div>

        {/* প্রি-ফিল্ড ফর্ম ফিল্ডস (Editable) */}
        <div className="mt-6 space-y-4">
          <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-400">
            Verified Candidate Details (Auto-Filled)
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="relative">
              <BsPersonFill className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-3.5 h-3.5" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Full Name"
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-cyan-950 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div className="relative">
              <BsEnvelopeFill className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-3.5 h-3.5" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email Address"
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-cyan-950 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div className="relative">
              <BsTelephoneFill className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-3.5 h-3.5" />
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Phone Number"
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-cyan-950 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div className="relative">
              <BsGeoAltFill className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-3.5 h-3.5" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Location"
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-cyan-950 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          {/* কভার লেটার প্রিভিউ ও এডিটর */}
          <div>
            <label className="text-xs uppercase font-semibold tracking-wider text-slate-400 block mb-2">
              Tailored Pitch / Cover Letter (Editable)
            </label>
            <textarea
              rows={5}
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              className="w-full p-3.5 rounded-2xl bg-slate-950 border border-cyan-950 text-xs text-slate-300 leading-relaxed focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          {/* এআই স্ক্রিনিং প্রশ্ন উত্তরকারী */}
          <div className="p-4 rounded-2xl bg-slate-950/80 border border-cyan-950/80 space-y-2">
            <span className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5">
              <HiSparkles className="w-3.5 h-3.5" /> Optional: Answer Employer Screening Question
            </span>
            <div className="flex gap-2">
              <input
                type="text"
                value={customQuestion}
                onChange={(e) => setCustomQuestion(e.target.value)}
                placeholder="Paste question (e.g. Why are you a good fit for this role?)"
                className="flex-1 px-3 py-2 rounded-xl bg-slate-900 border border-cyan-950 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={handleGenerateAnswer}
                disabled={generatingAnswer || !customQuestion.trim()}
                className="px-4 py-2 rounded-xl bg-slate-900 border border-cyan-500/40 text-cyan-400 text-xs font-bold hover:bg-slate-800 disabled:opacity-40 transition"
              >
                {generatingAnswer ? "Generating..." : "AI Answer"}
              </button>
            </div>
            {aiAnswer && (
              <textarea
                rows={2}
                value={aiAnswer}
                onChange={(e) => setAiAnswer(e.target.value)}
                className="w-full mt-2 p-2.5 rounded-xl bg-slate-900 border border-cyan-900/60 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
              />
            )}
          </div>
        </div>

        {/* ফুটার অ্যাকশন */}
        <div className="mt-6 pt-4 border-t border-cyan-950 flex flex-wrap items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition"
          >
            Cancel
          </button>

          <button
            onClick={handleCopyAndLaunch}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition shadow-[0_0_20px_rgba(6,182,212,0.25)] active:scale-95"
          >
            {copiedAll ? <FiCheck className="w-4 h-4" /> : <FiCopy className="w-4 h-4" />}
            <span>{copiedAll ? "Copied & Opening Portal..." : "Copy All & Launch Portal"}</span>
            <HiArrowTopRightOnSquare className="w-4 h-4" />
          </button>
        </div>

      </div>
    </div>
  );
}