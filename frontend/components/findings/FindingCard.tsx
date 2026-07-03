"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Wand2, BookOpen, AlertTriangle, ShieldAlert, Info } from "lucide-react";
import { cn, isGenericExample } from "@/lib/utils";
import { toast } from "sonner";

export interface Finding {
  rule_id: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  file_path?: string;
  line?: number;
  message: string;
  snippet?: string;
  fix_description?: string;
  fix_example?: string;
}

const SEVERITY_CONFIG = {
  critical: { label: "Critical", bg: "bg-red-950/60", text: "text-red-400", border: "border-red-900/60", icon: ShieldAlert },
  high:     { label: "High",     bg: "bg-orange-950/60", text: "text-orange-400", border: "border-orange-900/60", icon: AlertTriangle },
  medium:   { label: "Medium",   bg: "bg-yellow-950/60", text: "text-yellow-400", border: "border-yellow-900/60", icon: AlertTriangle },
  low:      { label: "Low",      bg: "bg-blue-950/60",  text: "text-blue-400",  border: "border-blue-900/60",  icon: Info },
  info:     { label: "Info",     bg: "bg-gray-900/60",  text: "text-gray-400",  border: "border-gray-800/60",  icon: Info },
};

interface Props {
  finding: Finding;
  index?: number;
  onApplyFix?: (finding: Finding) => void;
  applyFixLabel?: string;
}

export function FindingCard({ finding, index = 0, onApplyFix, applyFixLabel = "Apply fix" }: Props) {
  const [expanded, setExpanded] = useState(false);
  const cfg = SEVERITY_CONFIG[finding.severity] ?? SEVERITY_CONFIG.info;
  const Icon = cfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.2 }}
      className={cn("rounded-lg border overflow-hidden", cfg.border, cfg.bg)}
    >
      {/* Header — plain language first */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-white/5 transition-colors"
      >
        <Icon className={cn("w-4 h-4 mt-0.5 flex-shrink-0", cfg.text)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={cn("text-xs font-medium px-1.5 py-0.5 rounded-full border", cfg.text, cfg.border)}>
              {cfg.label}
            </span>
            {finding.file_path && (
              <span className="text-xs text-[#6b7280] font-mono truncate max-w-[200px]">
                {finding.file_path}{finding.line ? `:${finding.line}` : ""}
              </span>
            )}
          </div>
          <p className="text-sm text-[#f9fafb] leading-snug font-medium">{finding.message}</p>
        </div>
        <ChevronDown className={cn("w-4 h-4 flex-shrink-0 text-[#6b7280] transition-transform mt-0.5", expanded && "rotate-180")} />
      </button>

      {/* Expanded details — fix description first, then code, rule ID last */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-3 border-t border-white/10 space-y-3">
              {/* 1. Plain-English fix description — most important, shown first */}
              {finding.fix_description ? (
                <div className="bg-black/20 rounded-lg p-3">
                  <p className="text-xs font-semibold text-[#9ca3af] uppercase tracking-wider mb-1.5">How to fix it</p>
                  <p className="text-sm text-[#d1d5db] leading-relaxed">{finding.fix_description}</p>
                </div>
              ) : (
                <div className="bg-black/20 rounded-lg p-3">
                  <p className="text-xs font-semibold text-[#9ca3af] uppercase tracking-wider mb-1.5">Why this matters</p>
                  <p className="text-sm text-[#d1d5db] leading-relaxed">{finding.message}</p>
                </div>
              )}

              {/* 2. Problem code */}
              {finding.snippet && (
                <div>
                  <p className="text-xs font-semibold text-[#6b7280] uppercase tracking-wider mb-1.5">Problem code</p>
                  <pre className="text-xs font-mono bg-red-950/30 border border-red-900/40 rounded-md p-3 overflow-x-auto text-red-300 leading-relaxed">
                    {finding.snippet}
                  </pre>
                </div>
              )}

              {/* 3. Fixed code */}
              {finding.fix_example && (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="text-xs font-semibold text-[#6b7280] uppercase tracking-wider">
                      {isGenericExample(finding.fix_example!) ? "Reference pattern" : "Fixed code"}
                    </p>
                    {onApplyFix && (
                      isGenericExample(finding.fix_example!) ? (
                        <span className="flex items-center gap-1.5 text-xs text-[#4b5563] border border-[#374151] px-2.5 py-1 rounded-lg">
                          <BookOpen className="w-3 h-3" />
                          Manual fix required
                        </span>
                      ) : (
                        <button
                          onClick={(e) => { e.stopPropagation(); onApplyFix(finding); }}
                          className="flex items-center gap-1.5 text-xs font-medium text-[#2563eb] hover:text-white bg-[#2563eb]/10 hover:bg-[#2563eb] border border-[#2563eb]/40 px-2.5 py-1 rounded-lg transition-all"
                        >
                          <Wand2 className="w-3 h-3" />
                          {applyFixLabel}
                        </button>
                      )
                    )}
                  </div>
                  <pre className="text-xs font-mono bg-green-950/30 border border-green-900/40 rounded-md p-3 overflow-x-auto text-green-300 leading-relaxed">
                    {finding.fix_example}
                  </pre>
                </div>
              )}

              {/* 4. Rule ID — last, small, for reference only */}
              <div className="pt-1 border-t border-white/5">
                <span className="text-[10px] text-[#4b5563] font-mono">Rule: {finding.rule_id}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
