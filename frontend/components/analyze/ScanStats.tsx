"use client";

import { FileCode, ShieldAlert, AlertTriangle, Info, Bug } from "lucide-react";
import type { Finding } from "@/components/findings/FindingCard";

interface Props {
  filesScanned: number;
  findings: Finding[];
}

export function ScanStats({ filesScanned, findings }: Props) {
  const critical = findings.filter((f) => f.severity === "critical" || f.severity === "high").length;
  const warnings = findings.filter((f) => f.severity === "medium").length;
  const info = findings.filter((f) => f.severity === "low" || f.severity === "info").length;

  const stats = [
    { label: "Files Scanned", value: filesScanned, icon: FileCode,     color: "text-[#22d3ee]", ring: "border-[#22d3ee]/30" },
    { label: "Issues Found",  value: findings.length, icon: Bug,       color: "text-[#818cf8]", ring: "border-[#818cf8]/30" },
    { label: "Critical",      value: critical, icon: ShieldAlert,      color: "text-red-400",   ring: "border-red-500/30" },
    { label: "Warnings",      value: warnings, icon: AlertTriangle,    color: "text-amber-400", ring: "border-amber-500/30" },
    { label: "Info",          value: info, icon: Info,                 color: "text-sky-400",   ring: "border-sky-500/30" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {stats.map((s) => (
        <div
          key={s.label}
          className={`relative flex items-center justify-between bg-[#12131f]/90 border ${s.ring} rounded-xl px-4 py-3.5 overflow-hidden`}
        >
          <div>
            <p className={`text-2xl font-bold font-display ${s.color}`}>{s.value}</p>
            <p className="text-[11px] text-[#7d84a3] mt-0.5">{s.label}</p>
          </div>
          <s.icon className={`w-5 h-5 ${s.color} opacity-70`} />
          <div className={`absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-current to-transparent opacity-30 ${s.color}`} />
        </div>
      ))}
    </div>
  );
}
