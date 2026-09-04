"use client";

import { BsLinkedin, BsFacebook, BsBuildings } from "react-icons/bs";
import { SiIndeed } from "react-icons/si";

interface Props {
  keyword: string;
  location: string;
}

export default function SocialSearchLinks({ keyword, location }: Props) {
  const kw = encodeURIComponent(keyword || "React Developer");
  const loc = encodeURIComponent(location || "Bangladesh");

  const links = [
    { label: "LinkedIn Posts", icon: BsLinkedin, url: `https://www.linkedin.com/jobs/search/?keywords=${kw}&location=${loc}` },
    { label: "Facebook Groups", icon: BsFacebook, url: `https://www.facebook.com/search/posts/?q=${kw}%20job%20${loc}` },
    { label: "Indeed Jobs", icon: SiIndeed, url: `https://bd.indeed.com/jobs?q=${kw}&l=${loc}` },
    { label: "Glassdoor", icon: BsBuildings, url: `https://www.glassdoor.com/Job/jobs.htm?sc.keyword=${kw}` },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2 pt-2">
      <span className="text-xs text-slate-500 font-mono">Deep Search:</span>
      {links.map((link) => {
        const Icon = link.icon;
        return (
          <a
            key={link.label}
            href={link.url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-cyan-950/60 hover:border-cyan-500/40 text-xs text-slate-400 hover:text-cyan-400 transition"
          >
            <Icon className="w-3 h-3" />
            <span>{link.label}</span>
          </a>
        );
      })}
    </div>
  );
}