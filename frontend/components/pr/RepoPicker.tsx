"use client";

import { useEffect, useMemo, useState } from "react";
import { Search, Lock, BookMarked, RefreshCw, Loader2 } from "lucide-react";
import { listRepos, ApiError, type RepoSummary } from "@/lib/api";
import { timeAgo } from "@/lib/utils";

interface Props {
  onSelect: (repo: RepoSummary) => void;
  onReconnect: () => void;
}

export function RepoPicker({ onSelect, onReconnect }: Props) {
  const [repos, setRepos] = useState<RepoSummary[] | null>(null);
  const [error, setError] = useState<{ message: string; needsReconnect: boolean } | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    listRepos()
      .then((res) => { if (!cancelled) setRepos(res.repos); })
      .catch((err) => {
        if (cancelled) return;
        const needsReconnect =
          err instanceof ApiError &&
          (err.code === "github_permission_denied" || err.status === 403);
        setError({
          message: err instanceof Error ? err.message : "Failed to load repositories",
          needsReconnect,
        });
      });
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    if (!repos) return [];
    const q = query.trim().toLowerCase();
    if (!q) return repos;
    return repos.filter((r) => r.full_name.toLowerCase().includes(q));
  }, [repos, query]);

  if (error) {
    return (
      <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-8 text-center">
        <p className="text-[#f4f5fc] font-medium mb-1">Couldn&apos;t load your repositories</p>
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
    );
  }

  if (!repos) {
    return (
      <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-8 flex items-center justify-center gap-2 text-[#7d84a3] text-sm">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading your repositories…
      </div>
    );
  }

  return (
    <div className="bg-[#12131f] border border-[#262a3d] rounded-xl overflow-hidden">
      <div className="p-4 border-b border-[#262a3d]">
        <div className="relative">
          <Search className="w-4 h-4 text-[#7d84a3] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search repositories…"
            autoFocus
            className="w-full bg-[#1a1c2e] border border-[#262a3d] rounded-lg pl-9 pr-3 py-2 text-sm text-[#f4f5fc] placeholder:text-[#7d84a3] focus:outline-none focus:border-[#7c3aed] transition-colors"
          />
        </div>
      </div>

      <div className="max-h-[420px] overflow-y-auto divide-y divide-[#1a1c2e]">
        {filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-[#7d84a3]">
            {query
              ? "No repositories match your search."
              : "No repositories found. Org repos may need the org to approve the OAuth app on GitHub."}
          </div>
        ) : (
          filtered.map((r) => (
            <button
              key={r.full_name}
              onClick={() => onSelect(r)}
              className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-[#1a1c2e] transition-colors group"
            >
              <BookMarked className="w-4 h-4 text-[#818cf8] mt-0.5 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-[#f4f5fc] group-hover:text-[#c4b5fd] transition-colors">
                    {r.full_name}
                  </span>
                  {r.private && (
                    <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full border border-[#3d3450] bg-[#7c3aed]/10 text-[#a78bfa]">
                      <Lock className="w-2.5 h-2.5" /> private
                    </span>
                  )}
                  <span className="ml-auto text-xs text-[#7d84a3] flex-shrink-0">{timeAgo(r.pushed_at)}</span>
                </div>
                {r.description && (
                  <p className="text-xs text-[#7d84a3] mt-0.5 truncate">{r.description}</p>
                )}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
