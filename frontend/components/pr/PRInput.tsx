"use client";

import { useState } from "react";
import { Search, Loader2, GitPullRequest } from "lucide-react";
import { analyzePR } from "@/lib/api";
import { toast } from "sonner";

interface PRCoords {
  owner: string;
  repo: string;
  pr_number: number;
}

interface Props {
  onResult: (result: unknown, coords: PRCoords) => void;
  owner: string;
  repo: string;
  prNumber: string;
  onOwnerChange: (v: string) => void;
  onRepoChange: (v: string) => void;
  onPrNumberChange: (v: string) => void;
}

export function PRInput({
  onResult,
  owner,
  repo,
  prNumber,
  onOwnerChange,
  onRepoChange,
  onPrNumberChange,
}: Props) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!owner || !repo || !prNumber) return;
    setLoading(true);
    try {
      const result = await analyzePR(owner, repo, parseInt(prNumber));
      onResult(result, { owner, repo, pr_number: parseInt(prNumber) });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to analyze PR");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-[#12131f] border border-[#262a3d] rounded-xl p-5">
      <div className="flex items-center gap-2.5 mb-4">
        <GitPullRequest className="w-5 h-5 text-[#7c3aed]" />
        <h2 className="font-semibold text-[#f4f5fc]">Analyze a Pull Request</h2>
      </div>
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div>
          <label className="text-xs font-medium text-[#a8adc9] block mb-1.5">Owner</label>
          <input
            type="text"
            placeholder="octocat"
            value={owner}
            onChange={(e) => onOwnerChange(e.target.value)}
            className="w-full bg-[#1a1c2e] border border-[#262a3d] rounded-lg px-3 py-2 text-sm text-[#f4f5fc] placeholder:text-[#7d84a3] focus:outline-none focus:border-[#7c3aed] transition-colors"
            required
          />
        </div>
        <div>
          <label className="text-xs font-medium text-[#a8adc9] block mb-1.5">Repository</label>
          <input
            type="text"
            placeholder="hello-world"
            value={repo}
            onChange={(e) => onRepoChange(e.target.value)}
            className="w-full bg-[#1a1c2e] border border-[#262a3d] rounded-lg px-3 py-2 text-sm text-[#f4f5fc] placeholder:text-[#7d84a3] focus:outline-none focus:border-[#7c3aed] transition-colors"
            required
          />
        </div>
        <div>
          <label className="text-xs font-medium text-[#a8adc9] block mb-1.5">PR Number</label>
          <input
            type="number"
            placeholder="42"
            value={prNumber}
            onChange={(e) => onPrNumberChange(e.target.value)}
            className="w-full bg-[#1a1c2e] border border-[#262a3d] rounded-lg px-3 py-2 text-sm text-[#f4f5fc] placeholder:text-[#7d84a3] focus:outline-none focus:border-[#7c3aed] transition-colors"
            required
            min="1"
          />
        </div>
      </div>
      <button
        type="submit"
        disabled={loading || !owner || !repo || !prNumber}
        className="flex items-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
        {loading ? "Analyzing…" : "Analyze PR"}
      </button>
    </form>
  );
}
