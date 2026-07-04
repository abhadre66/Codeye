import Link from "next/link";
import { Zap, Code2, GitPullRequest, ShieldCheck, Sparkles, ArrowRight } from "lucide-react";

const features = [
  { href: "/chat",    icon: Zap,            title: "AI Chat",          desc: "Stream a full code review with Claude calling 14 specialized tools automatically.", color: "text-[#2563eb]", border: "border-blue-900/50", bg: "bg-blue-950/20" },
  { href: "/analyze", icon: Code2,          title: "Analyze Code",     desc: "Paste or upload code. Get plain-English findings, fix suggestions, and a before/after diff — all in one flow.", color: "text-[#f97316]", border: "border-orange-900/50", bg: "bg-orange-950/20" },
  { href: "/pr",      icon: GitPullRequest, title: "PR Review",        desc: "Full GitHub PR analysis: diff, security, style, reviewer suggestions, and one-click posting.", color: "text-[#a855f7]", border: "border-purple-900/50", bg: "bg-purple-950/20" },
];

const rules = [
  { id: "SEC001", label: "Hardcoded Secrets" },
  { id: "SEC002", label: "SQL Injection" },
  { id: "SEC003", label: "Insecure Dependencies" },
  { id: "SEC004", label: "Missing Validation" },
  { id: "SEC005", label: "Unsafe Deserialization" },
  { id: "STY001", label: "Function Length" },
  { id: "STY002", label: "Missing Docstrings" },
  { id: "STY003", label: "Naming Conventions" },
  { id: "STY004", label: "Forbidden Imports" },
  { id: "STY005", label: "Line Length" },
  { id: "STY006", label: "TODO without Ticket" },
];

export default function Home() {
  return (
    <div className="px-4 sm:px-8 py-8 sm:py-10 max-w-5xl">
      <div className="mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#2563eb]/10 border border-[#2563eb]/30 text-[#60a5fa] text-xs font-medium mb-4">
          <Sparkles className="w-3 h-3" />
          Phase 7 — Production Ready
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-[#f9fafb] mb-3 leading-tight">
          AI-native code review<br className="hidden sm:block" />{" "}
          <span className="text-[#2563eb]">that actually catches things</span>
        </h1>
        <p className="text-[#9ca3af] text-lg max-w-2xl">
          ReviewMind runs 11 rules across security and style, powered by Claude&apos;s tool loop.
          Works on GitHub PRs, pasted code, and uploaded files.
        </p>
        <div className="flex gap-3 mt-6">
          <Link href="/chat" className="flex items-center gap-2 bg-[#2563eb] hover:bg-[#1d4ed8] text-white font-medium px-5 py-2.5 rounded-xl text-sm transition-colors">
            <Zap className="w-4 h-4" /> Start a review
          </Link>
          <Link href="/analyze" className="flex items-center gap-2 bg-[#111827] hover:bg-[#1f2937] border border-[#374151] text-[#d1d5db] font-medium px-5 py-2.5 rounded-xl text-sm transition-colors">
            <Code2 className="w-4 h-4" /> Paste code
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
        {features.map((f) => (
          <Link key={f.href} href={f.href} className={`group rounded-xl border p-5 transition-all hover:scale-[1.01] ${f.border} ${f.bg} hover:border-opacity-80`}>
            <div className="flex items-start justify-between mb-3">
              <f.icon className={`w-5 h-5 ${f.color}`} />
              <ArrowRight className="w-4 h-4 text-[#6b7280] group-hover:text-[#9ca3af] transition-colors" />
            </div>
            <h3 className="font-semibold text-[#f9fafb] mb-1">{f.title}</h3>
            <p className="text-sm text-[#6b7280] leading-relaxed">{f.desc}</p>
          </Link>
        ))}
      </div>

      <div className="bg-[#111827] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="w-4 h-4 text-[#22c55e]" />
          <h2 className="font-semibold text-[#f9fafb]">11 built-in rules</h2>
          <span className="text-xs text-[#6b7280] ml-auto">15 languages supported</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {rules.map((r) => (
            <span key={r.id} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#1f2937] border border-[#374151] text-xs">
              <span className="font-mono text-[#60a5fa]">{r.id}</span>
              <span className="text-[#9ca3af]">{r.label}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
