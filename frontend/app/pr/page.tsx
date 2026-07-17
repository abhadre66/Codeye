"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PRInput } from "@/components/pr/PRInput";
import { RepoPicker } from "@/components/pr/RepoPicker";
import { PRPicker } from "@/components/pr/PRPicker";
import { PostReviewPanel } from "@/components/pr/PostReviewPanel";
import { FindingsList } from "@/components/findings/FindingsList";
import { AuthModal } from "@/components/auth/AuthModal";
import { StepBreadcrumb } from "@/components/analyze/StepBreadcrumb";
import { ScanStats } from "@/components/analyze/ScanStats";
import { PipelineStrip } from "@/components/analyze/PipelineStrip";
import type { Finding } from "@/components/findings/FindingCard";
import { analyzePR, getReviewers, getPRFilesContent, ApiError, type PRFileContent, type RepoSummary, type PRListItem } from "@/lib/api";
import { useUser } from "@/lib/hooks/useUser";
import { toast } from "sonner";
import {
  GitPullRequest, ChevronLeft, Users, GitBranch,
  ShieldCheck, Wand2, GitCompare,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import dynamic from "next/dynamic";

const DiffEditor = dynamic(
  () => import("@monaco-editor/react").then((m) => m.DiffEditor),
  { ssr: false, loading: () => <div className="h-[500px] bg-[#08080f] rounded-lg animate-pulse" /> }
);

interface PRCoords { owner: string; repo: string; pr_number: number }

interface PRResult {
  summary?: string;
  security_findings?: Finding[];
  style_findings?: Finding[];
  files_changed?: number;
  additions?: number;
  deletions?: number;
}

interface Reviewer { login: string; reason?: string; score?: number }

type Stage = "repos" | "pulls" | "findings" | "diff";

const STAGE_INDEX: Record<Stage, number> = { repos: 0, pulls: 1, findings: 2, diff: 3 };

function isGenericFix(fix: string) {
  return ["# Instead of", "# Use", "// Instead of", "// Use", "# Bad:", "# Good:"].some(m => fix.includes(m));
}

function applyFixes(original: string, findings: Finding[]): string {
  let result = original;
  for (const f of findings) {
    if (f.snippet && f.fix_example && !isGenericFix(f.fix_example)) {
      const trimmed = f.snippet.trim();
      if (result.includes(trimmed)) {
        result = result.replace(trimmed, f.fix_example.trim());
      }
    }
  }
  return result;
}

export default function PRPage() {
  const [stage, setStage] = useState<Stage>("repos");
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [selectedRepo, setSelectedRepo] = useState<RepoSummary | null>(null);
  const [analyzingPR, setAnalyzingPR] = useState<number | null>(null);
  const [result, setResult] = useState<PRResult | null>(null);
  const [coords, setCoords] = useState<PRCoords | null>(null);
  const [reviewers, setReviewers] = useState<Reviewer[] | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [prFiles, setPrFiles] = useState<PRFileContent[]>([]);
  const [selectedFile, setSelectedFile] = useState<PRFileContent | null>(null);
  const [fixedContent, setFixedContent] = useState<string>("");
  const [appliedFindings, setAppliedFindings] = useState<Finding[]>([]);
  const [reviewBody, setReviewBody] = useState("");
  const { user, signInWithGitHub, signOut } = useUser();
  const [authOpen, setAuthOpen] = useState(false);

  const isGitHubUser = user?.app_metadata?.provider === "github";

  // Re-runs the OAuth flow so a token with the newly requested scopes
  // ("repo read:org") replaces an old read-only one.
  const reconnectGitHub = async () => {
    await signOut();
    signInWithGitHub();
  };

  const handleResult = async (r: unknown, c: PRCoords) => {
    const inner = (r as { result?: PRResult }).result ?? (r as PRResult);
    setResult(inner);
    setCoords(c);
    const all = [...(inner.security_findings ?? []), ...(inner.style_findings ?? [])];
    setFindings(all);
    setAppliedFindings([]);
    setReviewBody("");
    setStage("findings");

    try {
      const rv = await getReviewers(c.owner, c.repo, c.pr_number);
      const inner2 = (rv as { result?: { reviewers?: Reviewer[] } }).result ?? rv;
      setReviewers((inner2 as { reviewers?: Reviewer[] }).reviewers ?? []);
    } catch { /* optional */ }

    try {
      const fc = await getPRFilesContent(c.owner, c.repo, c.pr_number);
      setPrFiles(fc.files);
      if (fc.files.length > 0) {
        setSelectedFile(fc.files[0]);
        setFixedContent(fc.files[0].after);
      }
    } catch { /* optional */ }
  };

  const handleSelectRepo = (r: RepoSummary) => {
    setSelectedRepo(r);
    setOwner(r.owner);
    setRepo(r.name);
    setStage("pulls");
  };

  const handleSelectPR = async (pr: PRListItem) => {
    if (!selectedRepo) return;
    setAnalyzingPR(pr.number);
    try {
      const res = await analyzePR(selectedRepo.owner, selectedRepo.name, pr.number);
      await handleResult(res, {
        owner: selectedRepo.owner,
        repo: selectedRepo.name,
        pr_number: pr.number,
      });
    } catch (err) {
      if (err instanceof ApiError && err.code === "github_permission_denied") {
        toast.error("GitHub denied access — try reconnecting GitHub.");
      } else {
        toast.error(err instanceof Error ? err.message : "Failed to analyze PR");
      }
    } finally {
      setAnalyzingPR(null);
    }
  };

  const handleApplyFix = (finding: Finding) => {
    if (!selectedFile) return;
    const nextFixed = applyFixes(fixedContent, [finding]);
    setFixedContent(nextFixed);
    setFindings(prev => prev.filter(f => f !== finding));
    setAppliedFindings(prev => [...prev, finding]);

    const comment = `**${finding.rule_id}** — ${finding.message}\n\`\`\`\n${finding.fix_example ?? ""}\n\`\`\``;
    setReviewBody(prev => prev ? prev + "\n\n" + comment : comment);
    toast.success(`Fix applied — ${finding.rule_id}`);
  };

  const handleApplyAll = () => {
    if (!selectedFile) return;
    const fixable = findings.filter(f => f.fix_example && !isGenericFix(f.fix_example) && f.snippet);
    const nextFixed = applyFixes(fixedContent, fixable);
    setFixedContent(nextFixed);
    setAppliedFindings(prev => [...prev, ...fixable]);
    setFindings(prev => prev.filter(f => !fixable.includes(f)));
    const comments = fixable.map(f => `**${f.rule_id}** — ${f.message}\n\`\`\`\n${f.fix_example ?? ""}\n\`\`\``).join("\n\n");
    setReviewBody(prev => prev ? prev + "\n\n" + comments : comments);
    toast.success(`${fixable.length} fixes applied`);
  };

  const goToDiff = () => setStage("diff");

  const allFindings = [...(result?.security_findings ?? []), ...(result?.style_findings ?? [])];
  const fixableCount = findings.filter(f => f.fix_example && !isGenericFix(f.fix_example) && f.snippet).length;

  return (
    <div className="px-4 sm:px-8 py-6 sm:py-8 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold font-display tracking-tight text-[#f4f5fc] mb-1">PR Review</h1>
        <p className="text-[#7d84a3] text-sm">Pick a repo, choose a pull request, review it, and post the findings back to GitHub.</p>
      </div>

      {/* ── Not connected with GitHub ── */}
      {!isGitHubUser ? (
        <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-10 text-center">
          <GitBranch className="w-10 h-10 text-[#818cf8] mx-auto mb-4" />
          <h2 className="font-semibold text-[#f4f5fc] mb-1">Connect GitHub</h2>
          <p className="text-sm text-[#7d84a3] mb-5 max-w-md mx-auto">
            Sign in with GitHub to browse your repositories, pick a pull request to review,
            and post findings back as review comments.
          </p>
          <button
            onClick={() => signInWithGitHub()}
            className="inline-flex items-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] text-white font-medium px-5 py-2.5 rounded-lg text-sm transition-colors"
          >
            <GitBranch className="w-4 h-4" /> Continue with GitHub
          </button>
          {user && (
            <p className="text-xs text-[#7d84a3] mt-4">
              You&apos;re signed in with {user.app_metadata?.provider ?? "another provider"} —
              GitHub is required for PR reviews.
            </p>
          )}
        </div>
      ) : (
        <>
          <div className="mb-6">
            <StepBreadcrumb
              steps={["Pick Repo", "Pick PR", "Findings", "Diff & Post"]}
              current={STAGE_INDEX[stage]}
              onStepClick={(i) => {
                if (i === 0) setStage("repos");
                if (i === 1 && selectedRepo) setStage("pulls");
                if (i === 2 && result) setStage("findings");
              }}
            />
          </div>

          <AnimatePresence mode="wait">
            {/* ── Stage 1: Pick a repo (or enter manually) ── */}
            {stage === "repos" && (
              <motion.div key="repos" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                <Tabs defaultValue="browse">
                  <TabsList className="mb-4 bg-[#12131f] border border-[#262a3d]">
                    <TabsTrigger value="browse">Browse repos</TabsTrigger>
                    <TabsTrigger value="manual">Enter manually</TabsTrigger>
                  </TabsList>
                  <TabsContent value="browse">
                    <RepoPicker onSelect={handleSelectRepo} onReconnect={reconnectGitHub} />
                  </TabsContent>
                  <TabsContent value="manual">
                    <PRInput
                      onResult={handleResult}
                      owner={owner}
                      repo={repo}
                      prNumber={prNumber}
                      onOwnerChange={setOwner}
                      onRepoChange={setRepo}
                      onPrNumberChange={setPrNumber}
                    />
                  </TabsContent>
                </Tabs>
              </motion.div>
            )}

            {/* ── Stage 2: Pick an open PR ── */}
            {stage === "pulls" && selectedRepo && (
              <motion.div key="pulls" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }}>
                <PRPicker
                  owner={selectedRepo.owner}
                  repo={selectedRepo.name}
                  onSelect={handleSelectPR}
                  onBack={() => setStage("repos")}
                  onReconnect={reconnectGitHub}
                  analyzingPR={analyzingPR}
                />
                {analyzingPR !== null && (
                  <div className="mt-6">
                    <PipelineStrip />
                  </div>
                )}
              </motion.div>
            )}

            {/* ── Stage 3: Findings ── */}
            {stage === "findings" && (
              <motion.div key="findings" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }}>
                {/* Scan stats */}
                <div className="mb-6">
                  <ScanStats filesScanned={result?.files_changed ?? 0} findings={allFindings} />
                </div>

                {/* Summary */}
                {result?.summary && (
                  <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-5 mb-5">
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      <GitPullRequest className="w-4 h-4 text-[#818cf8]" />
                      <h3 className="font-semibold text-[#f4f5fc]">PR #{coords?.pr_number} — {coords?.owner}/{coords?.repo}</h3>
                      <span className="ml-auto font-mono text-xs">
                        <span className="text-green-400">+{result?.additions ?? 0}</span>{" "}
                        <span className="text-red-400">-{result?.deletions ?? 0}</span>
                      </span>
                    </div>
                    <p className="text-sm text-[#c7cbe3] leading-relaxed whitespace-pre-wrap">{result.summary}</p>
                  </div>
                )}

                {/* Reviewers */}
                {reviewers && reviewers.length > 0 && (
                  <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-5 mb-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Users className="w-4 h-4 text-[#22d3ee]" />
                      <h3 className="font-semibold text-[#f4f5fc]">Suggested Reviewers</h3>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {reviewers.map(r => (
                        <span key={r.login} className="text-xs px-2.5 py-1 bg-[#1a1c2e] border border-[#262a3d] rounded-full text-[#c7cbe3]">
                          @{r.login}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Findings */}
                {findings.length > 0 ? (
                  <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-[#f97316]" />
                        <span className="text-sm font-medium text-[#f4f5fc]">{findings.length} issue{findings.length !== 1 ? "s" : ""} found</span>
                      </div>
                      <div className="flex gap-2 flex-wrap">
                        <button
                          onClick={goToDiff}
                          className="flex items-center gap-1.5 text-sm text-[#a8adc9] border border-[#262a3d] hover:border-[#7d84a3] px-3 py-1.5 rounded-lg transition-all"
                        >
                          <GitCompare className="w-3.5 h-3.5" /> See Diff
                        </button>
                        {fixableCount > 0 && (
                          <button
                            onClick={handleApplyAll}
                            className="flex items-center gap-1.5 text-sm font-medium text-white bg-[#7c3aed] hover:bg-[#6d28d9] px-3 py-1.5 rounded-lg transition-all"
                          >
                            <Wand2 className="w-3.5 h-3.5" /> Apply all fixes ({fixableCount})
                          </button>
                        )}
                      </div>
                    </div>
                    <FindingsList findings={findings} onApplyFix={handleApplyFix} applyFixLabel="Apply fix" />
                  </div>
                ) : (
                  <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-8 text-center">
                    <p className="text-[#f4f5fc] font-medium mb-1">No issues remaining</p>
                    <p className="text-sm text-[#7d84a3]">All fixes applied — ready to post review.</p>
                  </div>
                )}

                <div className="flex justify-between mt-6">
                  <button onClick={() => setStage(selectedRepo ? "pulls" : "repos")} className="flex items-center gap-2 text-sm text-[#7d84a3] hover:text-[#f4f5fc] transition-colors">
                    <ChevronLeft className="w-4 h-4" /> Back
                  </button>
                  <button
                    onClick={goToDiff}
                    className="flex items-center gap-2 text-sm font-medium text-white bg-[#7c3aed] hover:bg-[#6d28d9] px-4 py-2 rounded-lg transition-colors"
                  >
                    <GitCompare className="w-4 h-4" /> See Diff & Post Review
                  </button>
                </div>

                <div className="mt-6">
                  <PipelineStrip />
                </div>
              </motion.div>
            )}

            {/* ── Stage 4: Diff + Post Review ── */}
            {stage === "diff" && (
              <motion.div key="diff" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} className="space-y-5">

                {/* File selector */}
                {prFiles.length > 1 && (
                  <div className="flex gap-2 flex-wrap">
                    {prFiles.map(f => (
                      <button
                        key={f.filename}
                        onClick={() => { setSelectedFile(f); setFixedContent(applyFixes(f.after, appliedFindings)); }}
                        className={`text-xs font-mono px-3 py-1.5 rounded-lg border transition-all ${selectedFile?.filename === f.filename ? "bg-[#7c3aed] border-[#7c3aed] text-white" : "border-[#262a3d] text-[#a8adc9] hover:border-[#7d84a3]"}`}
                      >
                        {f.filename}
                      </button>
                    ))}
                  </div>
                )}

                {/* Diff editor */}
                {selectedFile ? (
                  <div className="rounded-xl overflow-hidden border border-[#262a3d]">
                    <div className="flex items-center justify-between px-4 py-2 bg-[#12131f] border-b border-[#262a3d]">
                      <span className="text-xs font-mono text-[#a8adc9]">{selectedFile.filename}</span>
                      <div className="flex gap-3 text-xs">
                        <span className="text-green-400">+{selectedFile.additions}</span>
                        <span className="text-red-400">-{selectedFile.deletions}</span>
                        {appliedFindings.length > 0 && <span className="text-[#22d3ee]">{appliedFindings.length} fix{appliedFindings.length !== 1 ? "es" : ""} applied</span>}
                      </div>
                    </div>
                    <DiffEditor
                      height="500px"
                      theme="vs-dark"
                      original={selectedFile.before}
                      modified={fixedContent}
                      options={{ readOnly: true, fontSize: 12, minimap: { enabled: false }, scrollBeyondLastLine: false }}
                    />
                  </div>
                ) : (
                  <div className="bg-[#12131f] border border-[#262a3d] rounded-xl p-8 text-center">
                    <p className="text-sm text-[#7d84a3]">No file content available for this PR.</p>
                  </div>
                )}

                {/* Post Review */}
                {coords && (
                  <PostReviewPanel
                    owner={coords.owner}
                    repo={coords.repo}
                    prNumber={coords.pr_number}
                    findings={allFindings}
                    body={reviewBody}
                    onBodyChange={setReviewBody}
                    signedIn={Boolean(user)}
                    onRequireAuth={() => setAuthOpen(true)}
                    onReconnect={reconnectGitHub}
                    onBack={() => setStage("findings")}
                  />
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}

      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} onSuccess={() => setAuthOpen(false)} />
    </div>
  );
}
