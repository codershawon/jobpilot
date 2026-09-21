"use client";

import Container from "./Container";
import { 
  BsFileEarmarkTextFill, 
  BsCpuFill, 
  BsSendCheckFill
} from "react-icons/bs";

const steps = [
  {
    step: "০১",
    icon: BsFileEarmarkTextFill,
    title: "রেজুমে স্ক্যান ও প্রোফাইলিং",
    desc: "আপনার PDF বা Word সিভি ড্রপ করুন। এআই স্বয়ংক্রিয়ভাবে টেকনিক্যাল স্কিল, অভিজ্ঞতা ও জেলা চিহ্নিত করে একটি স্ট্রাকচার্ড প্রোফাইল বানায়।",
    accent: "from-cyan-500 to-sky-600",
    border: "group-hover:border-cyan-500/40",
    glow: "bg-cyan-500/10",
  },
  {
    step: "০২",
    icon: BsCpuFill,
    title: "স্মার্ট সার্কুলার ম্যাচিং",
    desc: "বিডিজবস, সরকারি পোর্টাল ও ফেসবুক গ্রুপের শত শত লাইভ সার্কুলার বিশ্লেষণ করে আপনার স্কিলের সাথে শতকরা ম্যাচ স্কোর (Match %) নির্ধারণ করে।",
    accent: "from-sky-500 to-blue-600",
    border: "group-hover:border-sky-500/40",
    glow: "bg-sky-500/10",
  },
  {
    step: "০৩",
    icon: BsSendCheckFill,
    title: "১-ক্লিকে আবেদন ও কভার লেটার",
    desc: "পছন্দের সার্কুলারের রিকোয়ারমেন্ট মিলিয়ে নিখুঁত কভার লেটার এবং কোল্ড মেইল ড্রাফট জেনারেট করে তাৎক্ষণিক আবেদনের জন্য প্রস্তুত করে।",
    accent: "from-teal-500 to-emerald-600",
    border: "group-hover:border-teal-500/40",
    glow: "bg-teal-500/10",
  },
];

export default function HowItWorks() {
  return (
    <section className="w-full py-16">
      <Container>
        {/* Section Header */}
        <div className="text-center space-y-3 max-w-2xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-semibold text-cyan-400">
            <span>সহজ ৩টি ধাপ</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-normal leading-snug">
            কীভাবে কাজ করে <span className="text-transparent bg-clip-text bg-linear-to-r from-cyan-400 to-sky-400">JobPilot AI</span>
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            কোনো জটিল ফরম পূরণের ঝামেলা নেই। আপনার সিভি আপলোড করা থেকে শুরু করে সঠিক চাকরিতে আবেদন—পুরো প্রক্রিয়াই স্বয়ংক্রিয়।
          </p>
        </div>

        {/* 3 Step Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
          {steps.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className={`group relative rounded-2xl bg-slate-900/30 border border-slate-800/80 p-6 sm:p-7 transition-all duration-300 hover:bg-slate-900/60 ${item.border}`}
              >
                {/* Step Number Watermark */}
                <div className="absolute top-5 right-6 text-3xl font-black text-slate-800/40 select-none group-hover:text-slate-700/40 transition-colors">
                  {item.step}
                </div>

                {/* Icon */}
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 ${item.glow} border border-slate-800`}>
                  <Icon className="w-5 h-5 text-cyan-400" />
                </div>

                {/* Content */}
                <h3 className="text-base font-bold text-white mb-2 group-hover:text-cyan-300 transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            );
          })}
        </div>
      </Container>
    </section>
  );
}