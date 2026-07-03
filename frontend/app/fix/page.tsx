"use client";

import { useState } from "react";
import { Loader2, Wrench } from "lucide-react";
import { suggestFixes } from "@/lib/api";
import { CodeEditor } from "@/components/code/CodeEditor";
import { FindingsList } from "@/components/findings/FindingsList";
import type { Finding } from "@/components/findings/FindingCard";
import { toast } from "sonner";

export default function FixPage() {
  const [code, setCode] = useState("");
  const [filename, setFilename] = useState("snippet.py");
  const [findings, setFindings] = useState<Finding[] | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFix = async () => {
    if (!code.trim()) return;
    setLoading(true);
    try {
      const resp = await suggestFixes(code, filename);
      const result = (resp as { result?: { findings?: Finding[] } }).result ?? {};
      const fixes = result.findings ?? [];
      setFindings(fixes);
      if (fixes.length === 0) toast.success("No fixes needed — code looks good!");
      else toast.info(`${fixes.length} fix suggestion${fixes.length !== 1 ? "s" : ""} ready`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Fix suggestion failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-8 py-8 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#f9fafb] mb-1">Fix Suggestions</h1>
        <p className="text-[#6b7280] text-sm">Get concrete, copy-paste fix examples for every issue in your code.</p>
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
            onClick={handleFix}
            disabled={loading || !code.trim()}
            className="flex items-center gap-2 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wrench className="w-4 h-4" />}
            {loading ? "Generating fixes…" : "Suggest Fixes"}
          </button>
        </div>

        <div className="rounded-xl overflow-hidden border border-[#374151]">
          <CodeEditor value={code} onChange={setCode} filename={filename} height="380px" placeholder="// Paste code to get fix suggestions" />
        </div>

        {findings !== null && (
          <div className="bg-[#111827] border border-[#374151] rounded-xl p-6">
            <FindingsList findings={findings} title="Fix suggestions" />
          </div>
        )}
      </div>
    </div>
  );
}
