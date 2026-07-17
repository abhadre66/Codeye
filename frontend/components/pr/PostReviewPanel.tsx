"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Loader2, Send, FileText, MessageSquare, ChevronLeft, RefreshCw } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { postReview, ApiError } from "@/lib/api";
import type { Finding } from "@/components/findings/FindingCard";

type ReviewEvent = "COMMENT" | "APPROVE" | "REQUEST_CHANGES";

interface InlineComment {
  path: string;
  line?: number;
  side?: string;
  body: string;
}

interface Preview {
  body: string;
  event: string;
  comments: InlineComment[];
}

interface Props {
  owner: string;
  repo: string;
  prNumber: number;
  findings: Finding[];
  body: string;
  onBodyChange: (v: string) => void;
  signedIn: boolean;
  onRequireAuth: () => void;
  onReconnect: () => void;
  onBack: () => void;
}

function findingKey(f: Finding, i: number) {
  return `${f.rule_id}:${f.file_path ?? ""}:${f.line ?? ""}:${i}`;
}

function findingToComment(f: Finding): InlineComment {
  let body = `**${f.rule_id}** (${f.severity}): ${f.message}`;
  if (f.fix_description) body += `\n\n${f.fix_description}`;
  if (f.fix_example) body += `\n\n\`\`\`\n${f.fix_example.trim()}\n\`\`\``;
  return f.file_path && f.line
    ? { path: f.file_path, line: f.line, side: "RIGHT", body }
    : { path: f.file_path ?? "", body };
}

function summarize(findings: Finding[]): string {
  if (findings.length === 0) return "";
  const security = findings.filter((f) => f.rule_id.startsWith("SEC")).length;
  const style = findings.length - security;
  const parts = [];
  if (security) parts.push(`${security} security issue${security !== 1 ? "s" : ""}`);
  if (style) parts.push(`${style} style issue${style !== 1 ? "s" : ""}`);
  return `ReviewMind reviewed this PR and found ${parts.join(" and ")}. See the inline comments for details.`;
}

export function PostReviewPanel({
  owner, repo, prNumber, findings, body, onBodyChange,
  signedIn, onRequireAuth, onReconnect, onBack,
}: Props) {
  const [event, setEvent] = useState<ReviewEvent>("COMMENT");
  const [selected, setSelected] = useState<Set<string>>(
    () => new Set(findings.flatMap((f, i) => (f.file_path && f.line ? [findingKey(f, i)] : []))),
  );
  const [preview, setPreview] = useState<Preview | null>(null);
  const [loading, setLoading] = useState(false);
  const [needsReconnect, setNeedsReconnect] = useState(false);

  const selectedFindings = useMemo(
    () => findings.filter((f, i) => selected.has(findingKey(f, i))),
    [findings, selected],
  );

  const toggle = (key: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  const effectiveBody = body.trim() || summarize(selectedFindings.length ? selectedFindings : findings);

  const handleError = (err: unknown) => {
    if (err instanceof ApiError) {
      if (err.code === "github_permission_denied") {
        setNeedsReconnect(true);
        toast.error("GitHub denied the action — your connection may be missing permissions.");
        return;
      }
      if (err.code === "cannot_approve_own_pr") {
        toast.error("GitHub doesn't allow approving your own PR — use Comment or Request Changes.");
        return;
      }
      if (err.code === "comment_line_not_in_diff") {
        toast.error("Some inline comments point at lines outside this PR's diff. Deselect them or post as summary only.");
        return;
      }
    }
    toast.error(err instanceof Error ? err.message : "Failed to post review");
  };

  const handlePreview = async () => {
    if (!signedIn) { onRequireAuth(); return; }
    if (!effectiveBody) { toast.error("Write a review body or select at least one finding."); return; }
    setLoading(true);
    try {
      const comments = selectedFindings.map(findingToComment);
      const res = await postReview(owner, repo, prNumber, effectiveBody, event, false, comments);
      const p = (res as { result?: Preview }).result ?? (res as unknown as Preview);
      setPreview(p);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setLoading(true);
    try {
      const comments = selectedFindings.map(findingToComment);
      await postReview(owner, repo, prNumber, effectiveBody, event, true, comments);
      setPreview(null);
      toast.success(
        selectedFindings.filter((f) => f.file_path && f.line).length > 0
          ? "Review posted with inline comments!"
          : "Review posted to GitHub!",
      );
    } catch (err) {
      setPreview(null);
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-6 space-y-4">
      <div className="flex items-center gap-2">
        <FileText className="w-4 h-4 text-[#22d3ee]" />
        <h3 className="font-semibold text-[#f4f5fc]">Post review to GitHub</h3>
      </div>

      {needsReconnect && (
        <div className="flex items-center justify-between gap-3 bg-[#7c3aed]/10 border border-[#7c3aed]/40 rounded-lg px-4 py-3">
          <p className="text-xs text-[#c7cbe3]">
            Your GitHub connection can&apos;t post reviews. Reconnect to grant write access.
          </p>
          <button
            onClick={onReconnect}
            className="flex items-center gap-1.5 flex-shrink-0 text-xs font-medium text-white bg-[#7c3aed] hover:bg-[#6d28d9] px-3 py-1.5 rounded-lg transition-colors"
          >
            <RefreshCw className="w-3 h-3" /> Reconnect GitHub
          </button>
        </div>
      )}

      <div>
        <label className="text-xs font-medium text-[#a8adc9] block mb-2">Review type</label>
        <div className="flex gap-2">
          {(["COMMENT", "APPROVE", "REQUEST_CHANGES"] as const).map((e) => (
            <button
              key={e}
              onClick={() => setEvent(e)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${event === e ? "bg-[#7c3aed] border-[#7c3aed] text-white" : "border-[#262a3d] text-[#a8adc9] hover:border-[#7d84a3]"}`}
            >
              {e.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {findings.length > 0 && (
        <div>
          <label className="text-xs font-medium text-[#a8adc9] block mb-2">
            <MessageSquare className="w-3 h-3 inline mr-1" />
            Post findings as inline comments ({selectedFindings.length}/{findings.length} selected)
          </label>
          <div className="max-h-48 overflow-y-auto space-y-1 border border-[#262a3d] rounded-lg p-2 bg-[#0d0e18]">
            {findings.map((f, i) => {
              const key = findingKey(f, i);
              const anchorable = Boolean(f.file_path && f.line);
              return (
                <label
                  key={key}
                  className="flex items-start gap-2 px-2 py-1.5 rounded hover:bg-[#1a1c2e] cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selected.has(key)}
                    onChange={() => toggle(key)}
                    className="mt-0.5 accent-[#7c3aed]"
                  />
                  <span className="text-xs text-[#c7cbe3] min-w-0">
                    <span className="font-mono text-[#a78bfa]">{f.rule_id}</span> {f.message}
                    <span className="block text-[#7d84a3] font-mono truncate">
                      {anchorable ? `${f.file_path}:${f.line}` : "no line — added to summary"}
                    </span>
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}

      <div>
        <label className="text-xs font-medium text-[#a8adc9] block mb-2">Review body</label>
        <textarea
          value={body}
          onChange={(e) => onBodyChange(e.target.value)}
          rows={6}
          placeholder={summarize(findings) || "Write your review comments in Markdown…"}
          className="w-full bg-[#1a1c2e] border border-[#262a3d] rounded-lg px-3 py-2.5 text-sm text-[#f4f5fc] placeholder:text-[#7d84a3] focus:outline-none focus:border-[#7c3aed] resize-none"
        />
        {!body.trim() && effectiveBody && (
          <p className="text-[11px] text-[#7d84a3] mt-1">
            Leave empty to use the auto-generated summary shown above.
          </p>
        )}
      </div>

      <div className="flex items-center justify-between">
        <button onClick={onBack} className="flex items-center gap-2 text-sm text-[#7d84a3] hover:text-[#f4f5fc] transition-colors">
          <ChevronLeft className="w-4 h-4" /> Back to findings
        </button>
        <button
          onClick={handlePreview}
          disabled={loading || !effectiveBody}
          className="flex items-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
        >
          {loading && !preview ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          {signedIn ? "Preview & Post" : "Sign in & Post"}
        </button>
      </div>

      {/* Preview-then-confirm dialog */}
      <Dialog open={preview !== null} onOpenChange={(open) => { if (!open) setPreview(null); }}>
        <DialogContent className="bg-[#12131f] border-[#262a3d] text-[#f4f5fc] max-w-xl">
          <DialogHeader>
            <DialogTitle>Confirm review</DialogTitle>
            <DialogDescription className="text-[#7d84a3]">
              This will post to {owner}/{repo}#{prNumber} as{" "}
              <span className="text-[#a78bfa] font-medium">{event.replace("_", " ")}</span>.
            </DialogDescription>
          </DialogHeader>
          {preview && (
            <div className="space-y-3 max-h-[50vh] overflow-y-auto">
              <div className="bg-[#0d0e18] border border-[#262a3d] rounded-lg p-3">
                <p className="text-xs font-medium text-[#a8adc9] mb-1">Summary</p>
                <p className="text-sm text-[#c7cbe3] whitespace-pre-wrap">{preview.body}</p>
              </div>
              {preview.comments.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-[#a8adc9]">
                    {preview.comments.length} inline comment{preview.comments.length !== 1 ? "s" : ""}
                  </p>
                  {preview.comments.map((c, i) => (
                    <div key={i} className="bg-[#0d0e18] border border-[#262a3d] rounded-lg p-3">
                      <p className="text-[11px] font-mono text-[#7d84a3] mb-1">
                        {c.path}:{c.line}
                      </p>
                      <p className="text-xs text-[#c7cbe3] whitespace-pre-wrap">{c.body}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <button
              onClick={() => setPreview(null)}
              className="text-sm text-[#7d84a3] hover:text-[#f4f5fc] px-4 py-2 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="flex items-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Post to GitHub
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
