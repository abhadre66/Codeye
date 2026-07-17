"use client";

import { useEffect, useState } from "react";
import { GitPullRequest, ChevronLeft, Loader2, RefreshCw, GitBranch } from "lucide-react";
import { listOpenPRs, ApiError, type PRListItem } from "@/lib/api";
import { timeAgo } from "@/lib/utils";

interface Props {
  owner: string;
  repo: string;
  onSelect: (pr: PRListItem) => void;
  onBack: () => void;
  onReconnect: () => void;
  analyzingPR?: number | null;
}

export function PRPicker({ owner, repo, onSelect, onBack, onReconnect, analyzingPR }: Props) {
  const [pulls, setPulls] = useState<PRListItem[] | null>(null);
  const [error, setError] = useState<{ message: string; needsReconnect: boolean } | null>(null);

  useEffect(() => {
    let cancelled = false;
    setPulls(null);
    setError(null);
    listOpenPRs(owner, repo)
      .then((res) => { if (!cancelled) setPulls(res.pulls); })
      .catch((err) => {
        if (cancelled) return;
        const needsReconnect =
          err instanceof ApiError &&
          (err.code === "github_permission_denied" || err.status === 403);
        setError({
          message: err instanceof Error ? err.message : "Failed to load pull requests",
          needsReconnect,
        });
      });
    return () => { cancelled = true; };
  }, [owner, repo]);

  return (
    <div className="bg-[#12131f] border border-[#262a3d] rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-[#262a3d]">
        <button
          onClick={onBack}
          className="flex items-center gap-1 text-sm text-[#7d84a3] hover:text-[#f4f5fc] transition-colors"
        >
          <ChevronLeft className="w-4 h-4" /> Repos
        </button>
        <span className="text-sm font-medium text-[#f4f5fc]">
          {owner}/{repo}
        </span>
        <span className="ml-auto text-xs text-[#7d84a3]">
          {pulls ? `${pulls.length} open PR${pulls.length !== 1 ? "s" : ""}` : ""}
        </span>
      </div>

      {error ? (
        <div className="p-8 text-center">
          <p className="text-[#f4f5fc] font-medium mb-1">Couldn&apos;t load pull requests</p>
          <p className="text-sm text-[#7d84a3] mb-4">{error.message}</p>
          {error.needsReconnect && (
            <button
              onClick={onReconnect}
              className="inline-flex items-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
            >
              <RefreshCw className="w-4 h-4" /> Reconnect GitHub
            </button>
          )}
        </div>
      ) : !pulls ? (
        <div className="p-8 flex items-center justify-center gap-2 text-[#7d84a3] text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading open pull requests…
        </div>
      ) : pulls.length === 0 ? (
        <div className="p-8 text-center text-sm text-[#7d84a3]">
          No open pull requests in this repository.
        </div>
      ) : (
        <div className="max-h-[420px] overflow-y-auto divide-y divide-[#1a1c2e]">
          {pulls.map((pr) => (
            <button
              key={pr.number}
              onClick={() => onSelect(pr)}
              disabled={analyzingPR != null}
              className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-[#1a1c2e] transition-colors group disabled:opacity-60"
            >
              {analyzingPR === pr.number ? (
                <Loader2 className="w-4 h-4 text-[#7c3aed] mt-0.5 flex-shrink-0 animate-spin" />
              ) : (
                <GitPullRequest className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono text-[#7d84a3]">#{pr.number}</span>
                  <span className="text-sm font-medium text-[#f4f5fc] group-hover:text-[#c4b5fd] transition-colors truncate">
                    {pr.title}
                  </span>
                  {pr.draft && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full border border-[#262a3d] bg-[#1a1c2e] text-[#7d84a3]">
                      draft
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-[#7d84a3] flex-wrap">
                  <span>@{pr.author}</span>
                  <span className="inline-flex items-center gap-1 font-mono">
                    <GitBranch className="w-3 h-3" />
                    {pr.head_branch} → {pr.base_branch}
                  </span>
                  <span className="ml-auto">{timeAgo(pr.updated_at)}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
