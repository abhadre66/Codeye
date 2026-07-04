"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, Play, GitCompare, ArrowLeft, RotateCcw, Wand2, UploadCloud, FileCode } from "lucide-react";
import { suggestFixes, compare } from "@/lib/api";
import { isGenericExample } from "@/lib/utils";
import { CodeEditor } from "@/components/code/CodeEditor";
import { FindingsList } from "@/components/findings/FindingsList";
import { CodeDiff } from "@/components/diff/CodeDiff";
import { StepBreadcrumb } from "@/components/analyze/StepBreadcrumb";
import type { Finding } from "@/components/findings/FindingCard";
import { toast } from "sonner";

// Raw shapes from backend
interface RawFinding { rule_id: string; severity: string; file_path?: string; line?: number; message: string; snippet?: string }
interface FixSuggestion { rule_id: string; severity: string; file_path?: string; line?: number; problem: string; fix_description: string; fix_example: string }
interface FixReport { analysis?: { security_findings?: RawFinding[]; style_findings?: RawFinding[] }; suggestions?: FixSuggestion[] }

function mergeFindings(suggestions: FixSuggestion[], rawFindings: RawFinding[]): Finding[] {
  if (suggestions.length > 0) {
    return suggestions.map((s) => ({
      rule_id: s.rule_id,
      severity: s.severity as Finding["severity"],
      file_path: s.file_path,
      line: s.line,
      message: s.problem,
      snippet: rawFindings.find((f) => f.rule_id === s.rule_id && f.line === s.line)?.snippet,
      fix_description: s.fix_description,
      fix_example: s.fix_example || undefined,
    }));
  }
  // Fallback: use raw findings if no suggestions returned
  return rawFindings.map((f) => ({
    rule_id: f.rule_id,
    severity: f.severity as Finding["severity"],
    file_path: f.file_path,
    line: f.line,
    message: f.message,
    snippet: f.snippet,
  }));
}

function applyFixes(original: string, findings: Finding[]): string {
  let result = original;
  for (const f of findings) {
    if (!f.snippet || !f.fix_example) continue;
    if (isGenericExample(f.fix_example)) continue;       // skip educational patterns
    const snippet = f.snippet.trim();
    if (!result.includes(snippet)) continue;              // skip if not an exact match
    result = result.replace(snippet, f.fix_example.trim());
  }
  return result;
}

const STEPS = ["Add Code", "Review Findings", "See Diff"];

type Stage = "input" | "findings" | "diff";

const slideIn = (dir: number) => ({ initial: { opacity: 0, x: dir * 40 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: -dir * 40 }, transition: { duration: 0.22 } });

export default function AnalyzePage() {
  const [code, setCode] = useState("");
  const [filename, setFilename] = useState("snippet.py");
  const [findings, setFindings] = useState<Finding[]>([]);
  const [currentCode, setCurrentCode] = useState(""); // accumulates applied fixes
  const [fixedCode, setFixedCode] = useState("");
  const [complexityDelta, setComplexityDelta] = useState(0);
  const [stage, setStage] = useState<Stage>("input");
  const [loading, setLoading] = useState(false);
  const [diffLoading, setDiffLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [inputMode, setInputMode] = useState<"paste" | "upload">("paste");

  const stageIndex = stage === "input" ? 0 : stage === "findings" ? 1 : 2;

  const analyzeFile = (file: File) => {
    setFilename(file.name);
    const reader = new FileReader();
    reader.onload = async (ev) => {
      const content = ev.target?.result as string;
      if (!content) return;
      setCode(content);
      setLoading(true);
      try {
        const resp = await suggestFixes(content, file.name);
        const result = (resp as { result?: FixReport }).result ?? {};
        const raw = [
          ...((result.analysis?.security_findings ?? []) as RawFinding[]),
          ...((result.analysis?.style_findings ?? []) as RawFinding[]),
        ];
        const merged = mergeFindings(result.suggestions ?? [], raw);
        setFindings(merged);
        setCurrentCode(content);
        setStage("findings");
        if (merged.length === 0) toast.success("No issues found — clean code!");
        else toast.info(`Found ${merged.length} issue${merged.length !== 1 ? "s" : ""} in ${file.name}`);
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Analysis failed");
      } finally {
        setLoading(false);
      }
    };
    reader.readAsText(file);
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) analyzeFile(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) analyzeFile(file);
  };

  const handleAnalyze = async () => {
    if (!code.trim()) return;
    setLoading(true);
    try {
      const resp = await suggestFixes(code, filename);
      const result = (resp as { result?: FixReport }).result ?? {};
      const raw = [
        ...((result.analysis?.security_findings ?? []) as RawFinding[]),
        ...((result.analysis?.style_findings ?? []) as RawFinding[]),
      ];
      const merged = mergeFindings(result.suggestions ?? [], raw);
      setFindings(merged);
      setCurrentCode(code); // reset accumulator on new analysis
      setStage("findings");
      if (merged.length === 0) toast.success("No issues found — clean code!");
      else toast.info(`Found ${merged.length} issue${merged.length !== 1 ? "s" : ""}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const goToDiff = async (nextCode: string) => {
    if (nextCode === code) {
      toast.info("No auto-fix available for this finding.");
      return;
    }
    setDiffLoading(true);
    try {
      const resp = await compare(code, nextCode, filename);
      const result = (resp as { result?: { complexity_delta?: number } }).result ?? {};
      setComplexityDelta(result.complexity_delta ?? 0);
    } catch {
      setComplexityDelta(0);
    } finally {
      setDiffLoading(false);
    }
    setFixedCode(nextCode);
    setStage("diff");
  };

  // "Apply all fixes" — apply every remaining fix, clear the list, go to diff
  const handleApplyAll = () => {
    const nextCode = applyFixes(currentCode, findings);
    setCurrentCode(nextCode);
    setFindings([]);
    toast.success(`All ${findings.length} fix${findings.length !== 1 ? "es" : ""} applied`);
    goToDiff(nextCode);
  };

  // "See Full Diff" — apply all remaining fixes on top of whatever's already been fixed
  const handleSeeDiff = () => goToDiff(applyFixes(currentCode, findings));

  // "Apply fix" on a single card — layer on top of currentCode, persist that state
  const handleApplyFix = (finding: Finding) => {
    const nextCode = applyFixes(currentCode, [finding]);
    setCurrentCode(nextCode);                                        // persist for next fix
    setFindings((prev) => prev.filter((f) => f !== finding));        // remove from list
    toast.success(`Fix applied — ${finding.rule_id} resolved`);
    goToDiff(nextCode);
  };

  const goTo = (s: Stage) => setStage(s);
  const reset = () => { setStage("input"); setFindings([]); setFixedCode(""); setCurrentCode(""); setComplexityDelta(0); };

  const secCount = findings.filter((f) => f.rule_id.startsWith("SEC")).length;
  const styCount = findings.filter((f) => f.rule_id.startsWith("STY")).length;

  return (
    <div className="px-4 sm:px-8 py-6 sm:py-8 max-w-5xl">
      <StepBreadcrumb
        steps={STEPS}
        current={stageIndex}
        onStepClick={(i) => {
          if (i === 0) goTo("input");
          if (i === 1) goTo("findings");
        }}
      />

      <AnimatePresence mode="wait">

        {/* ── Stage 1: Input ─────────────────────────────────── */}
        {stage === "input" && (
          <motion.div key="input" {...slideIn(1)}>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-[#f9fafb] mb-1">Analyze Code</h1>
              <p className="text-[#6b7280] text-sm">We&apos;ll explain every issue in plain English and show you exactly how to fix it.</p>
            </div>

            {/* Mode tabs */}
            <div className="flex gap-1 mb-4 bg-[#111827] border border-[#374151] rounded-lg p-1 w-fit">
              <button
                onClick={() => setInputMode("paste")}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  inputMode === "paste" ? "bg-[#2563eb] text-white" : "text-[#9ca3af] hover:text-[#f9fafb]"
                }`}
              >
                <FileCode className="w-4 h-4" /> Paste Code
              </button>
              <button
                onClick={() => setInputMode("upload")}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  inputMode === "upload" ? "bg-[#2563eb] text-white" : "text-[#9ca3af] hover:text-[#f9fafb]"
                }`}
              >
                <UploadCloud className="w-4 h-4" /> Upload File
              </button>
            </div>

            {inputMode === "paste" ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 text-[#6b7280]">
                    <FileCode className="w-4 h-4" />
                    <input
                      type="text"
                      value={filename}
                      onChange={(e) => setFilename(e.target.value)}
                      placeholder="filename.py"
                      className="bg-[#111827] border border-[#374151] rounded-lg px-3 py-2 text-sm text-[#f9fafb] placeholder:text-[#6b7280] focus:outline-none focus:border-[#2563eb] transition-colors w-44"
                    />
                  </div>
                  <button
                    onClick={handleAnalyze}
                    disabled={loading || !code.trim()}
                    className="flex items-center gap-2 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    {loading ? "Analyzing…" : "Run Analysis"}
                  </button>
                </div>

                <div className="rounded-xl overflow-hidden border border-[#374151]">
                  <CodeEditor
                    value={code}
                    onChange={setCode}
                    filename={filename}
                    height="360px"
                    placeholder="// Paste your code here…"
                  />
                </div>
              </div>
            ) : (
              <label
                onDrop={handleFileDrop}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                className={`flex flex-col items-center justify-center gap-3 w-full py-16 rounded-xl border-2 border-dashed cursor-pointer transition-all ${
                  dragging
                    ? "border-[#2563eb] bg-[#2563eb]/10"
                    : "border-[#374151] bg-[#111827] hover:border-[#4b5563] hover:bg-[#111827]/80"
                }`}
              >
                <input type="file" className="hidden" onChange={handleFileInput} accept=".py,.ts,.tsx,.js,.jsx,.go,.rs,.java,.cs,.cpp,.c,.rb,.php,.sh,.sql,.html,.css,.json,.yaml,.yml,.md" />
                {loading ? (
                  <>
                    <Loader2 className="w-8 h-8 text-[#2563eb] animate-spin" />
                    <p className="text-sm text-[#6b7280]">Analyzing <span className="text-[#f9fafb] font-medium">{filename}</span>…</p>
                  </>
                ) : (
                  <>
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${dragging ? "bg-[#2563eb]/20" : "bg-[#1f2937]"}`}>
                      <UploadCloud className={`w-6 h-6 ${dragging ? "text-[#2563eb]" : "text-[#6b7280]"}`} />
                    </div>
                    <div className="text-center">
                      <p className="text-sm font-medium text-[#f9fafb]">
                        {dragging ? "Drop to analyze" : "Drop a file here"}
                      </p>
                      <p className="text-xs text-[#6b7280] mt-1">
                        or <span className="text-[#60a5fa] underline underline-offset-2">click to browse</span> — auto-detects language, runs analysis instantly
                      </p>
                    </div>
                    <div className="flex flex-wrap justify-center gap-1.5 max-w-md">
                      {["py", "ts", "js", "go", "rs", "java", "cs", "cpp", "rb", "sql"].map((ext) => (
                        <span key={ext} className="text-[10px] px-1.5 py-0.5 rounded bg-[#1f2937] border border-[#374151] text-[#6b7280] font-mono">.{ext}</span>
                      ))}
                    </div>
                  </>
                )}
              </label>
            )}
          </motion.div>
        )}

        {/* ── Stage 2: Findings ──────────────────────────────── */}
        {stage === "findings" && (
          <motion.div key="findings" {...slideIn(1)}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-2xl font-bold text-[#f9fafb] mb-1">Review Findings</h1>
                <div className="flex items-center gap-2 text-sm">
                  {secCount > 0 && <span className="text-red-400">{secCount} security issue{secCount !== 1 ? "s" : ""}</span>}
                  {secCount > 0 && styCount > 0 && <span className="text-[#6b7280]">·</span>}
                  {styCount > 0 && <span className="text-yellow-400">{styCount} style issue{styCount !== 1 ? "s" : ""}</span>}
                  {findings.length === 0 && <span className="text-green-400">No issues found</span>}
                </div>
              </div>
              <button
                onClick={() => goTo("input")}
                className="flex items-center gap-1.5 text-sm text-[#6b7280] hover:text-[#f9fafb] transition-colors"
              >
                <ArrowLeft className="w-4 h-4" /> Edit code
              </button>
            </div>

            <div className="bg-[#111827] border border-[#374151] rounded-xl p-6 mb-4">
              <FindingsList findings={findings} onApplyFix={handleApplyFix} />
            </div>

            {findings.length > 0 && (
              <div className="flex items-center justify-end gap-3 flex-wrap">
                <button
                  onClick={handleSeeDiff}
                  disabled={diffLoading}
                  className="flex items-center gap-2 border border-[#374151] hover:border-[#6b7280] text-[#9ca3af] hover:text-[#f9fafb] disabled:opacity-50 font-medium px-5 py-2.5 rounded-xl text-sm transition-colors"
                >
                  {diffLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
                  {diffLoading ? "Building diff…" : "See Full Diff"}
                </button>
                <button
                  onClick={handleApplyAll}
                  disabled={diffLoading}
                  className="flex items-center gap-2 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-xl text-sm transition-colors"
                >
                  <Wand2 className="w-4 h-4" />
                  Apply all fixes
                </button>
              </div>
            )}
          </motion.div>
        )}

        {/* ── Stage 3: Diff ──────────────────────────────────── */}
        {stage === "diff" && (
          <motion.div key="diff" {...slideIn(1)}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-[#f9fafb] mb-1">Before / After</h1>
                <p className="text-[#6b7280] text-sm">Original code on the left — suggested fixes applied on the right.</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => goTo("findings")}
                  className="flex items-center gap-1.5 text-sm text-[#6b7280] hover:text-[#f9fafb] border border-[#374151] px-3 py-1.5 rounded-lg transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to findings
                </button>
                <button
                  onClick={reset}
                  className="flex items-center gap-1.5 text-sm text-[#6b7280] hover:text-[#f9fafb] border border-[#374151] px-3 py-1.5 rounded-lg transition-colors"
                >
                  <RotateCcw className="w-4 h-4" /> Start over
                </button>
              </div>
            </div>

            <CodeDiff
              original={code}
              modified={fixedCode}
              filename={filename}
              complexityDelta={complexityDelta}
              height="500px"
            />
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
