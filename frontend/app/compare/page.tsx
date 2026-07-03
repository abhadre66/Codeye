"use client";

import { useState } from "react";
import { Loader2, GitCompare } from "lucide-react";
import { compare } from "@/lib/api";
import { CodeEditor } from "@/components/code/CodeEditor";
import { CodeDiff } from "@/components/diff/CodeDiff";
import { FindingsList } from "@/components/findings/FindingsList";
import type { Finding } from "@/components/findings/FindingCard";
import { toast } from "sonner";

interface CompareResult {
  complexity_delta?: number;
  new_findings?: Finding[];
  fixed_findings?: Finding[];
  diff_summary?: { additions: number; deletions: number };
}

export default function ComparePage() {
  const [before, setBefore] = useState("");
  const [after, setAfter] = useState("");
  const [filename, setFilename] = useState("snippet.py");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCompare = async () => {
    if (!before.trim() || !after.trim()) return;
    setLoading(true);
    try {
      const resp = await compare(before, after, filename);
      const res = (resp as { result?: CompareResult }).result ?? {};
      setResult(res as CompareResult);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Compare failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-8 py-8 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#f9fafb] mb-1">Before / After Compare</h1>
        <p className="text-[#6b7280] text-sm">Compare two versions of code to see what changed, and what got introduced or fixed.</p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            placeholder="filename.py"
            className="bg-[#111827] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#f9fafb] placeholder:text-[#6b7280] focus:outline-none focus:border-[#2563eb] transition-colors w-52"
          />
          <button
            onClick={handleCompare}
            disabled={loading || !before.trim() || !after.trim()}
            className="flex items-center gap-2 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
            {loading ? "Comparing…" : "Compare"}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-medium text-[#9ca3af] mb-2">Before</p>
            <div className="rounded-xl overflow-hidden border border-[#374151]">
              <CodeEditor value={before} onChange={setBefore} filename={filename} height="340px" placeholder="// Paste original code" />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-[#9ca3af] mb-2">After</p>
            <div className="rounded-xl overflow-hidden border border-[#374151]">
              <CodeEditor value={after} onChange={setAfter} filename={filename} height="340px" placeholder="// Paste revised code" />
            </div>
          </div>
        </div>

        {result && (
          <div className="space-y-4">
            <CodeDiff
              original={before}
              modified={after}
              filename={filename}
              complexityDelta={result.complexity_delta ?? 0}
            />
            {(result.new_findings ?? []).length > 0 && (
              <div className="bg-[#111827] border border-[#374151] rounded-xl p-6">
                <FindingsList findings={result.new_findings ?? []} title="New issues introduced" />
              </div>
            )}
            {(result.fixed_findings ?? []).length > 0 && (
              <div className="bg-[#111827] border border-green-900/30 rounded-xl p-6">
                <p className="text-sm font-semibold text-green-400 mb-3">{result.fixed_findings!.length} issue{result.fixed_findings!.length !== 1 ? "s" : ""} fixed</p>
                <FindingsList findings={result.fixed_findings ?? []} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
