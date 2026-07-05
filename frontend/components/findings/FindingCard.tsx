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
  critical: { label: "CRITICAL", score: 9.8, bg: "bg-red-950/40", text: "text-red-400", border: "border-red-900/60", iconBg: "bg-red-500/15 border-red-500/40", icon: ShieldAlert },
  high:     { label: "HIGH",     score: 8.2, bg: "bg-orange-950/40", text: "text-orange-400", border: "border-orange-900/60", iconBg: "bg-orange-500/15 border-orange-500/40", icon: AlertTriangle },
  medium:   { label: "WARNING",  score: 5.6, bg: "bg-yellow-950/30", text: "text-yellow-400", border: "border-yellow-900/60", iconBg: "bg-yellow-500/15 border-yellow-500/40", icon: AlertTriangle },
  low:      { label: "LOW",      score: 3.1, bg: "bg-blue-950/30",  text: "text-blue-400",  border: "border-blue-900/60",  iconBg: "bg-blue-500/15 border-blue-500/40", icon: Info },
  info:     { label: "INFO",     score: 1.2, bg: "bg-gray-900/40",  text: "text-gray-400",  border: "border-gray-800/60",  iconBg: "bg-gray-500/15 border-gray-500/40", icon: Info },
};

// Short display titles per rule — the big headline on each card
const RULE_TITLES: Record<string, string> = {
  SEC001: "Hardcoded Secret",
  SEC002: "SQL Injection",
  SEC003: "Insecure Dependency",
  SEC004: "Missing Validation",
  SEC005: "Unsafe Deserialization",
  STY001: "Function Too Long",
  STY002: "Missing Docstring",
  STY003: "Naming Convention",
  STY004: "Forbidden Import",
  STY005: "Line Too Long",
  STY006: "TODO Without Ticket",
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
      {/* Header — big title + risk score */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3.5 px-4 py-3.5 text-left hover:bg-white/5 transition-colors"
      >
        <div className={cn("w-11 h-11 rounded-xl border flex items-center justify-center flex-shrink-0", cfg.iconBg)}>
          <Icon className={cn("w-5 h-5", cfg.text)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold font-display tracking-tight text-[#f4f5fc] leading-tight">
              {RULE_TITLES[finding.rule_id] ?? finding.rule_id}
            </h3>
            <span className={cn("text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-md border", cfg.text, cfg.border, cfg.bg)}>
              {cfg.label}
            </span>
          </div>
          <p className="text-xs text-[#a8adc9] mt-0.5 truncate">{finding.message}</p>
          {finding.file_path && (
            <p className="text-[11px] text-[#7d84a3] font-mono mt-0.5 truncate">
              {finding.file_path}{finding.line ? `:${finding.line}` : ""}
            </p>
          )}
        </div>
        <div className="flex flex-col items-center flex-shrink-0 pl-1">
          <span className={cn("text-2xl font-bold font-display leading-none", cfg.text)}>{cfg.score.toFixed(1)}</span>
          <span className="text-[9px] uppercase tracking-widest text-[#7d84a3] mt-1">risk</span>
        </div>
        <ChevronDown className={cn("w-4 h-4 flex-shrink-0 text-[#7d84a3] transition-transform", expanded && "rotate-180")} />
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
                  <p className="text-xs font-semibold text-[#a8adc9] uppercase tracking-wider mb-1.5">How to fix it</p>
                  <p className="text-sm text-[#c7cbe3] leading-relaxed">{finding.fix_description}</p>
                </div>
              ) : (
                <div className="bg-black/20 rounded-lg p-3">
                  <p className="text-xs font-semibold text-[#a8adc9] uppercase tracking-wider mb-1.5">Why this matters</p>
                  <p className="text-sm text-[#c7cbe3] leading-relaxed">{finding.message}</p>
                </div>
              )}

              {/* 2. Problem code */}
              {finding.snippet && (
                <div>
                  <p className="text-xs font-semibold text-[#7d84a3] uppercase tracking-wider mb-1.5">Problem code</p>
                  <pre className="text-xs font-mono bg-red-950/30 border border-red-900/40 rounded-md p-3 overflow-x-auto text-red-300 leading-relaxed">
                    {finding.snippet}
                  </pre>
                </div>
              )}

              {/* 3. Fixed code */}
              {finding.fix_example && (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="text-xs font-semibold text-[#7d84a3] uppercase tracking-wider">
                      {isGenericExample(finding.fix_example!) ? "Reference pattern" : "Fixed code"}
                    </p>
                    {onApplyFix && (
                      isGenericExample(finding.fix_example!) ? (
                        <span className="flex items-center gap-1.5 text-xs text-[#363a52] border border-[#262a3d] px-2.5 py-1 rounded-lg">
                          <BookOpen className="w-3 h-3" />
                          Manual fix required
                        </span>
                      ) : (
                        <button
                          onClick={(e) => { e.stopPropagation(); onApplyFix(finding); }}
                          className="flex items-center gap-1.5 text-xs font-medium text-[#7c3aed] hover:text-white bg-[#7c3aed]/10 hover:bg-[#7c3aed] border border-[#7c3aed]/40 px-2.5 py-1 rounded-lg transition-all"
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
                <span className="text-[10px] text-[#363a52] font-mono">Rule: {finding.rule_id}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
