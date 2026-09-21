"use client";

import React from "react";
import { TbLoader2 } from "react-icons/tb";

const LoaderIcon = TbLoader2 as React.ComponentType<React.SVGProps<SVGSVGElement>>;

export default function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-28 text-center animate-in fade-in duration-300">
      <div className="relative">
        <LoaderIcon className="w-14 h-14 text-cyan-400 animate-spin" />
        <div className="absolute inset-0 blur-lg bg-cyan-400/20 animate-pulse"></div>
      </div>
      <h3 className="mt-6 text-xl font-bold text-slate-100">Executing Autonomous Pipeline</h3>
      <p className="text-slate-400 text-sm max-w-sm mt-1.5">
        Extracting profile skills, querying live aggregators, and computing LLM match matrices.
      </p>
    </div>
  );
}