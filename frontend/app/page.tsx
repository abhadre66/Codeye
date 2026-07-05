import Link from "next/link";
import { Zap, Code2, GitPullRequest, ShieldCheck, Sparkles, ArrowRight } from "lucide-react";
import { Logo } from "@/components/layout/Logo";

const features = [
  { href: "/chat",    icon: Zap,            title: "AI Chat",          desc: "Stream a full code review with Claude calling 14 specialized tools automatically.", ring: "from-[#22d3ee] to-[#0891b2]" },
  { href: "/analyze", icon: Code2,          title: "Analyze Code",     desc: "Paste or upload code. Get plain-English findings, fix suggestions, and a before/after diff — all in one flow.", ring: "from-[#f97316] to-[#eab308]" },
  { href: "/pr",      icon: GitPullRequest, title: "PR Review",        desc: "Full GitHub PR analysis: diff, security, style, reviewer suggestions, and one-click posting.", ring: "from-[#818cf8] to-[#22d3ee]" },
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
    <div className="relative px-4 sm:px-8 py-8 sm:py-10 max-w-5xl overflow-hidden ambient-glow">
      <div className="mb-14">
        <div className="flex items-center gap-3 mb-5">
          <Logo size={40} className="drop-shadow-[0_0_20px_rgba(34,211,238,0.3)]" />
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0891b2]/10 border border-[#0891b2]/30 text-[#22d3ee] text-xs font-medium">
            <Sparkles className="w-3 h-3" />
            Phase 7 — Production Ready
          </div>
        </div>
        <h1 className="text-3xl sm:text-5xl font-bold font-display tracking-tight text-[#f4f5fc] mb-3 leading-[1.1]">
          AI-native code review<br className="hidden sm:block" />{" "}
          <span className="gradient-text">that actually catches things</span>
        </h1>
        <p className="text-[#a8adc9] text-lg max-w-2xl">
          ReviewMind runs 11 rules across security and style, powered by Claude&apos;s tool loop.
          Works on GitHub PRs, pasted code, and uploaded files.
        </p>
        <div className="flex gap-3 mt-6">
          <Link href="/chat" className="flex items-center gap-2 bg-[#0891b2] hover:bg-[#0e7490] text-white font-medium px-5 py-2.5 rounded-xl text-sm transition-colors">
            <Zap className="w-4 h-4" /> Start a review
          </Link>
          <Link href="/analyze" className="flex items-center gap-2 bg-[#12131f] hover:bg-[#1a1c2e] border border-[#262a3d] text-[#c7cbe3] font-medium px-5 py-2.5 rounded-xl text-sm transition-colors">
            <Code2 className="w-4 h-4" /> Paste code
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
        {features.map((f) => (
          <Link
            key={f.href}
            href={f.href}
            className="group relative rounded-2xl border border-[#262a3d] bg-[#12131f] p-5 transition-all hover:-translate-y-0.5 hover:border-[#363a52] overflow-hidden"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${f.ring} p-[1.5px]`}>
                <div className="w-full h-full rounded-[10px] bg-[#12131f] flex items-center justify-center">
                  <f.icon className="w-4.5 h-4.5 text-[#f4f5fc]" />
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-[#7d84a3] group-hover:text-[#22d3ee] group-hover:translate-x-0.5 transition-all" />
            </div>
            <h3 className="font-semibold font-display text-[#f4f5fc] mb-1">{f.title}</h3>
            <p className="text-sm text-[#7d84a3] leading-relaxed">{f.desc}</p>
          </Link>
        ))}
      </div>

      <div className="bg-[#12131f] border border-[#262a3d] rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="w-4 h-4 text-[#22c55e]" />
          <h2 className="font-semibold font-display text-[#f4f5fc]">11 built-in rules</h2>
          <span className="text-xs text-[#7d84a3] ml-auto">15 languages supported</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {rules.map((r) => (
            <span key={r.id} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#1a1c2e] border border-[#262a3d] text-xs">
              <span className="font-mono text-[#22d3ee]">{r.id}</span>
              <span className="text-[#a8adc9]">{r.label}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
