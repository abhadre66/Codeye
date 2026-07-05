"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileCode, UploadCloud, GitPullRequest, ChevronLeft, Loader2, Clock, ShieldAlert, AlertTriangle, CircleDashed, CheckCircle2, XCircle } from "lucide-react";
import { getHistory, getHistoryEntry, updateHistoryStatus, type HistoryEntry, type HistoryStatus } from "@/lib/api";
import { FindingsList } from "@/components/findings/FindingsList";
import type { Finding } from "@/components/findings/FindingCard";
import { toast } from "sonner";

interface RawFinding {
  rule_id: string; severity: string; file_path?: string; line?: number;
  message: string; snippet?: string; fix_description?: string; fix_example?: string;
}
interface FixSuggestion {
  rule_id: string; severity: string; file_path?: string; line?: number;
  problem: string; fix_description: string; fix_example: string;
}

const SOURCE_CONFIG: Record<string, { icon: typeof FileCode; label: string; color: string }> = {
  paste:  { icon: FileCode,       label: "Pasted code", color: "text-blue-400" },
  upload: { icon: UploadCloud,    label: "Uploaded file", color: "text-orange-400" },
  pr:     { icon: GitPullRequest, label: "PR review",    color: "text-purple-400" },
};

const STATUS_CONFIG: Record<HistoryStatus, { icon: typeof CircleDashed; label: string; chip: string }> = {
  pending:   { icon: CircleDashed, label: "Pending",   chip: "text-amber-400 border-amber-500/40 bg-amber-500/10" },
  fixed:     { icon: CheckCircle2, label: "Fixed",     chip: "text-green-400 border-green-500/40 bg-green-500/10" },
  dismissed: { icon: XCircle,      label: "Dismissed", chip: "text-[#7d84a3] border-[#363a52] bg-[#1a1c2e]" },
};

function normalizeFindings(source: string, payload: Record<string, unknown>): Finding[] {
  const result = (payload.result ?? {}) as Record<string, unknown>;

  if (source === "pr") {
    const raw = [
      ...((result.security_findings ?? []) as RawFinding[]),
      ...((result.style_findings ?? []) as RawFinding[]),
    ];
    return raw.map((f) => ({
      rule_id: f.rule_id, severity: f.severity as Finding["severity"], file_path: f.file_path, line: f.line,
      message: f.message, snippet: f.snippet, fix_description: f.fix_description, fix_example: f.fix_example,
    }));
  }

  const analysis = (result.analysis ?? {}) as Record<string, unknown>;
  const raw = [
    ...((analysis.security_findings ?? []) as RawFinding[]),
    ...((analysis.style_findings ?? []) as RawFinding[]),
  ];
  const suggestions = (result.suggestions ?? []) as FixSuggestion[];
  if (suggestions.length > 0) {
    return suggestions.map((s) => ({
      rule_id: s.rule_id, severity: s.severity as Finding["severity"], file_path: s.file_path, line: s.line,
      message: s.problem,
      snippet: raw.find((f) => f.rule_id === s.rule_id && f.line === s.line)?.snippet,
      fix_description: s.fix_description, fix_example: s.fix_example || undefined,
    }));
  }
  return raw.map((f) => ({
    rule_id: f.rule_id, severity: f.severity as Finding["severity"], file_path: f.file_path, line: f.line,
    message: f.message, snippet: f.snippet,
  }));
}

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<{ label: string; source: string; status: HistoryStatus; created_at: string; findings: Finding[] } | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusSaving, setStatusSaving] = useState(false);

  const changeStatus = async (status: HistoryStatus) => {
    if (selectedId === null || !detail || statusSaving || detail.status === status) return;
    setStatusSaving(true);
    try {
      await updateHistoryStatus(selectedId, status);
      setDetail({ ...detail, status });
      setEntries((prev) => prev?.map((e) => (e.id === selectedId ? { ...e, status } : e)) ?? prev);
      toast.success(`Marked as ${STATUS_CONFIG[status].label.toLowerCase()}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update status");
    } finally {
      setStatusSaving(false);
    }
  };

  useEffect(() => {
    getHistory()
      .then((r) => setEntries(r.history))
      .catch((err) => toast.error(err instanceof Error ? err.message : "Failed to load history"));
  }, []);

  const openEntry = async (id: number) => {
    setSelectedId(id);
    setDetailLoading(true);
    try {
      const r = await getHistoryEntry(id);
      setDetail({
        label: r.label,
        source: r.source,
        status: r.status,
        created_at: r.created_at,
        findings: normalizeFindings(r.source, r.payload),
      });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load entry");
      setSelectedId(null);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="px-4 sm:px-8 py-6 sm:py-8 max-w-5xl">
      <AnimatePresence mode="wait">
        {selectedId === null ? (
          <motion.div key="list" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="mb-6">
              <h1 className="text-2xl font-bold font-display tracking-tight text-[#f4f5fc] mb-1">History</h1>
              <p className="text-[#7d84a3] text-sm">Every analysis you've run — pasted code, uploaded files, and PR reviews.</p>
            </div>

            {entries === null ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-[#7d84a3] animate-spin" />
              </div>
            ) : entries.length === 0 ? (
              <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-8 text-center">
                <Clock className="w-8 h-8 text-[#363a52] mx-auto mb-3" />
                <p className="text-[#f4f5fc] font-medium mb-1">No history yet</p>
                <p className="text-sm text-[#7d84a3]">Run an analysis or review a PR — it'll show up here.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {entries.map((e) => {
                  const cfg = SOURCE_CONFIG[e.source] ?? SOURCE_CONFIG.paste;
                  const Icon = cfg.icon;
                  return (
                    <button
                      key={e.id}
                      onClick={() => openEntry(e.id)}
                      className="w-full flex items-center gap-3 px-4 py-3 bg-[#12131f] border border-[#262a3d] hover:border-[#363a52] rounded-xl text-left transition-colors"
                    >
                      <Icon className={`w-4 h-4 flex-shrink-0 ${cfg.color}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[#f4f5fc] truncate">{e.label}</p>
                        <p className="text-xs text-[#7d84a3]">{cfg.label} · {timeAgo(e.created_at)}</p>
                      </div>
                      <div className="flex items-center gap-3 text-xs flex-shrink-0">
                        {e.security_count > 0 && (
                          <span className="hidden sm:flex items-center gap-1 text-red-400">
                            <ShieldAlert className="w-3.5 h-3.5" /> {e.security_count}
                          </span>
                        )}
                        {e.style_count > 0 && (
                          <span className="hidden sm:flex items-center gap-1 text-yellow-400">
                            <AlertTriangle className="w-3.5 h-3.5" /> {e.style_count}
                          </span>
                        )}
                        {e.findings_count === 0 && <span className="hidden sm:inline text-green-400">Clean</span>}
                        {(() => {
                          const sc = STATUS_CONFIG[e.status] ?? STATUS_CONFIG.pending;
                          const SIcon = sc.icon;
                          return (
                            <span className={`flex items-center gap-1 px-2 py-1 rounded-md border text-[11px] font-medium ${sc.chip}`}>
                              <SIcon className="w-3 h-3" /> {sc.label}
                            </span>
                          );
                        })()}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div key="detail" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <button
              onClick={() => { setSelectedId(null); setDetail(null); }}
              className="flex items-center gap-1.5 text-sm text-[#7d84a3] hover:text-[#f4f5fc] transition-colors mb-4"
            >
              <ChevronLeft className="w-4 h-4" /> Back to history
            </button>

            {detailLoading || !detail ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-[#7d84a3] animate-spin" />
              </div>
            ) : (
              <>
                <div className="mb-6 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div>
                    <h1 className="text-2xl font-bold font-display tracking-tight text-[#f4f5fc] mb-1">{detail.label}</h1>
                    <p className="text-[#7d84a3] text-sm">
                      {SOURCE_CONFIG[detail.source]?.label ?? detail.source} · {timeAgo(detail.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 bg-[#12131f] border border-[#262a3d] rounded-xl p-1.5">
                    {(Object.keys(STATUS_CONFIG) as HistoryStatus[]).map((s) => {
                      const sc = STATUS_CONFIG[s];
                      const SIcon = sc.icon;
                      const active = detail.status === s;
                      return (
                        <button
                          key={s}
                          onClick={() => changeStatus(s)}
                          disabled={statusSaving}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all disabled:opacity-60 ${
                            active ? sc.chip : "border-transparent text-[#7d84a3] hover:text-[#f4f5fc]"
                          }`}
                        >
                          <SIcon className="w-3.5 h-3.5" /> {sc.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-6">
                  <FindingsList findings={detail.findings} />
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
