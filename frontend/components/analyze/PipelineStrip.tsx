"use client";

import { Code2, BrainCircuit, Search, ShieldCheck, Sparkles, Check } from "lucide-react";

const STAGES = [
  { icon: Code2,        title: "Code Ingestion",    desc: "Parsing source" },
  { icon: BrainCircuit, title: "AI Analysis",       desc: "Understanding context" },
  { icon: Search,       title: "Pattern Detection", desc: "Finding issues" },
  { icon: ShieldCheck,  title: "Risk Scoring",      desc: "Calculating impact" },
  { icon: Sparkles,     title: "Smart Review",      desc: "Actionable insights" },
];

export function PipelineStrip() {
  return (
    <div className="flex items-stretch gap-2 overflow-x-auto pb-1">
      {STAGES.map((s, i) => (
        <div key={s.title} className="flex items-center gap-2 flex-1 min-w-[150px]">
          <div className="relative flex-1 flex items-center gap-2.5 bg-[#12131f]/90 border border-[#262a3d] rounded-xl px-3 py-2.5">
            <div className="relative w-8 h-8 rounded-lg bg-[#1a1c2e] border border-[#262a3d] flex items-center justify-center flex-shrink-0">
              <s.icon className="w-4 h-4 text-[#22d3ee]" />
              <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-[#22c55e] flex items-center justify-center">
                <Check className="w-2.5 h-2.5 text-black" strokeWidth={3.5} />
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-[#f4f5fc] truncate">{s.title}</p>
              <p className="text-[10px] text-[#7d84a3] truncate">{s.desc}</p>
            </div>
          </div>
          {i < STAGES.length - 1 && (
            <div className="w-4 h-px bg-gradient-to-r from-[#22d3ee]/60 to-[#818cf8]/60 flex-shrink-0" />
          )}
        </div>
      ))}
    </div>
  );
}
