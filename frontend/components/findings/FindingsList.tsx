"use client";

import { useState, useMemo } from "react";
import { Search, Filter, Download, CheckCircle2 } from "lucide-react";
import { FindingCard, type Finding } from "./FindingCard";
import { cn } from "@/lib/utils";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;

interface Props {
  findings: Finding[];
  title?: string;
  onApplyFix?: (finding: Finding) => void;
  applyFixLabel?: string;
}

export function FindingsList({ findings, title, onApplyFix, applyFixLabel }: Props) {
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string[]>([]);

  const filtered = useMemo(() => {
    return findings.filter((f) => {
      const matchesSeverity = severityFilter.length === 0 || severityFilter.includes(f.severity);
      const matchesSearch =
        !search ||
        f.rule_id.toLowerCase().includes(search.toLowerCase()) ||
        f.message.toLowerCase().includes(search.toLowerCase()) ||
        (f.file_path ?? "").toLowerCase().includes(search.toLowerCase());
      return matchesSeverity && matchesSearch;
    });
  }, [findings, search, severityFilter]);

  const toggleSeverity = (s: string) =>
    setSeverityFilter((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(findings, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "reviewmind-findings.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const severityCount = (s: string) => findings.filter((f) => f.severity === s).length;

  if (findings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <CheckCircle2 className="w-12 h-12 text-green-500 mb-4 opacity-80" />
        <p className="text-lg font-semibold text-[#f9fafb] mb-1">No issues found</p>
        <p className="text-sm text-[#6b7280]">Your code looks clean. Nice work.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {title && (
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-[#f9fafb]">{title}</h3>
          <button onClick={exportJSON} className="flex items-center gap-1.5 text-xs text-[#6b7280] hover:text-[#f9fafb] transition-colors px-2 py-1.5 rounded-md border border-[#374151] hover:border-[#6b7280]">
            <Download className="w-3 h-3" />
            Export JSON
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6b7280]" />
          <input
            type="text"
            placeholder="Search by rule, message, or file..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-sm bg-[#1f2937] border border-[#374151] rounded-lg text-[#f9fafb] placeholder:text-[#6b7280] focus:outline-none focus:border-[#2563eb]"
          />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <Filter className="w-3.5 h-3.5 text-[#6b7280]" />
          {SEVERITIES.map((s) => {
            const count = severityCount(s);
            if (count === 0) return null;
            const active = severityFilter.includes(s);
            const colors: Record<string, string> = { critical: "text-red-400 border-red-900", high: "text-orange-400 border-orange-900", medium: "text-yellow-400 border-yellow-900", low: "text-blue-400 border-blue-900", info: "text-gray-400 border-gray-700" };
            return (
              <button
                key={s}
                onClick={() => toggleSeverity(s)}
                className={cn("text-xs px-2 py-1 rounded-md border capitalize transition-all", colors[s], active ? "opacity-100 bg-white/10" : "opacity-50 hover:opacity-75")}
              >
                {s} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Results count */}
      <p className="text-xs text-[#6b7280]">
        Showing {filtered.length} of {findings.length} finding{findings.length !== 1 ? "s" : ""}
      </p>

      {/* Findings */}
      <div className="space-y-2">
        {filtered.map((f, i) => (
          <FindingCard key={`${f.rule_id}-${i}`} finding={f} index={i} onApplyFix={onApplyFix} applyFixLabel={applyFixLabel} />
        ))}
        {filtered.length === 0 && (
          <p className="text-sm text-[#6b7280] py-4 text-center">No findings match your filters.</p>
        )}
      </div>
    </div>
  );
}
