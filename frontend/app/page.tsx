/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { Zap, Code2, GitPullRequest, ArrowRight, ShieldAlert, Wand2 } from "lucide-react";

const features = [
  { href: "/chat",    icon: Zap,            title: "AI Chat",      desc: "Claude reviews your code live, wielding 14 specialized tools.", accent: "#22d3ee" },
  { href: "/analyze", icon: Code2,          title: "Analyze Code", desc: "Paste or drop a file. Findings, fixes, and a diff — one flow.", accent: "#f97316" },
  { href: "/pr",      icon: GitPullRequest, title: "PR Review",    desc: "Point at any GitHub PR. Review it, fix it, post it back.", accent: "#818cf8" },
];

const rules = [
  "SEC001 Hardcoded Secrets", "SEC002 SQL Injection", "SEC003 Insecure Dependencies",
  "SEC004 Missing Validation", "SEC005 Unsafe Deserialization", "STY001 Function Length",
  "STY002 Missing Docstrings", "STY003 Naming Conventions", "STY004 Forbidden Imports",
  "STY005 Line Length", "STY006 TODO without Ticket",
];

export default function Home() {
  return (
    <div className="relative overflow-hidden">
      {/* Backdrop: grid + glow */}
      <div className="absolute inset-0 grid-bg pointer-events-none" />
      <div className="absolute -top-40 -right-40 w-[560px] h-[560px] rounded-full bg-[#0891b2]/20 blur-[140px] pointer-events-none" />
      <div className="absolute top-96 -left-40 w-[420px] h-[420px] rounded-full bg-[#818cf8]/15 blur-[120px] pointer-events-none" />

      <div className="relative px-4 sm:px-8 py-10 sm:py-16 max-w-6xl">
        {/* ── Hero ─────────────────────────────────────────── */}
        <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center mb-20">
          <div>
            <p className="font-mono text-xs text-[#22d3ee] tracking-[0.3em] uppercase mb-4">
              $ reviewmind --scan
            </p>
            <h1 className="text-4xl sm:text-6xl font-bold font-display tracking-tight text-[#f4f5fc] leading-[1.05] mb-5">
              Your code has
              <br />
              <span className="gradient-text">secrets.</span>
              <br />
              We find them.
            </h1>
            <p className="text-[#a8adc9] text-lg max-w-md mb-8">
              AI-native review that reads every diff like a security engineer —
              on PRs, pasted snippets, and uploaded files.
            </p>
            <div className="flex gap-3 flex-wrap">
              <Link href="/analyze" className="group flex items-center gap-2 bg-gradient-to-r from-[#0891b2] to-[#6366f1] hover:opacity-90 text-white font-semibold px-6 py-3 rounded-xl text-sm transition-all">
                Scan my code
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link href="/pr" className="flex items-center gap-2 bg-[#12131f]/80 hover:bg-[#1a1c2e] border border-[#262a3d] text-[#c7cbe3] font-medium px-6 py-3 rounded-xl text-sm transition-colors backdrop-blur-sm">
                <GitPullRequest className="w-4 h-4" /> Review a PR
              </Link>
            </div>

            {/* Stats strip */}
            <div className="flex gap-8 mt-10">
              {[["11", "built-in rules"], ["15", "languages"], ["14", "AI tools"], ["<1s", "static scan"]].map(([n, l]) => (
                <div key={l}>
                  <p className="text-2xl font-bold font-display gradient-text">{n}</p>
                  <p className="text-xs text-[#7d84a3] mt-0.5">{l}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Artwork — the emblem, floating */}
          <div className="relative hidden lg:flex items-center justify-center">
            <div className="absolute w-[420px] h-[420px] rounded-full bg-[#22d3ee]/10 blur-3xl" />
            <img
              src="/brand/hero.png"
              alt="ReviewMind emblem"
              className="relative w-[420px] h-[420px] object-cover rounded-full ring-1 ring-[#22d3ee]/30 shadow-[0_0_80px_rgba(34,211,238,0.25)] float-slow"
            />
          </div>
        </div>

        {/* ── Terminal-style live finding ──────────────────── */}
        <div className="mb-20 max-w-3xl mx-auto">
          <div className="rounded-2xl border border-[#262a3d] bg-[#0c0d16]/90 backdrop-blur-sm overflow-hidden shadow-2xl">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[#262a3d] bg-[#12131f]">
              <span className="w-3 h-3 rounded-full bg-[#ff5f57]" />
              <span className="w-3 h-3 rounded-full bg-[#febc2e]" />
              <span className="w-3 h-3 rounded-full bg-[#28c840]" />
              <span className="ml-3 font-mono text-xs text-[#7d84a3]">payment_service.py — reviewmind scan</span>
            </div>
            <div className="p-5 font-mono text-sm space-y-2">
              <p className="text-[#7d84a3]">$ reviewmind scan payment_service.py</p>
              <p className="text-[#c7cbe3]">Parsing 3 semantic chunks… <span className="text-[#28c840]">done</span></p>
              <div className="flex items-start gap-2 pt-1">
                <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <p><span className="text-red-400 font-semibold">SEC001 · critical</span> <span className="text-[#a8adc9]">line 8 — hardcoded secret</span></p>
              </div>
              <p className="pl-6 text-red-300/80 bg-red-950/30 rounded px-2 py-1 w-fit">DB_PASSWORD = &quot;prod_password_2024&quot;</p>
              <div className="flex items-start gap-2">
                <Wand2 className="w-4 h-4 text-[#22d3ee] mt-0.5 flex-shrink-0" />
                <p className="text-[#22d3ee]">fix available → move to environment variable</p>
              </div>
              <p className="pl-6 text-green-300/90 bg-green-950/30 rounded px-2 py-1 w-fit">DB_PASSWORD = os.environ[&quot;DB_PASSWORD&quot;]</p>
              <p className="text-[#7d84a3] pt-1">6 findings · 4 auto-fixable · <span className="text-[#22d3ee]">apply all? [Y/n]</span><span className="cursor-blink">▌</span></p>
            </div>
          </div>
        </div>

        {/* ── Features ─────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-16">
          {features.map((f) => (
            <Link
              key={f.href}
              href={f.href}
              className="group relative rounded-2xl border border-[#262a3d] bg-[#12131f]/80 backdrop-blur-sm p-6 transition-all hover:-translate-y-1 hover:shadow-[0_8px_40px_rgba(34,211,238,0.08)]"
              style={{ ["--fa" as string]: f.accent }}
            >
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[var(--fa)] to-transparent opacity-40 group-hover:opacity-100 transition-opacity" />
              <f.icon className="w-6 h-6 mb-4" style={{ color: f.accent }} />
              <h3 className="font-semibold font-display text-lg text-[#f4f5fc] mb-1.5">{f.title}</h3>
              <p className="text-sm text-[#7d84a3] leading-relaxed">{f.desc}</p>
              <ArrowRight className="w-4 h-4 text-[#7d84a3] group-hover:text-[var(--fa)] group-hover:translate-x-1 transition-all mt-4" />
            </Link>
          ))}
        </div>

        {/* ── Rules marquee ────────────────────────────────── */}
        <div className="relative overflow-hidden py-4 border-y border-[#262a3d]/60 marquee-mask">
          <div className="flex gap-3 marquee w-max">
            {[...rules, ...rules].map((r, i) => (
              <span key={i} className="whitespace-nowrap font-mono text-xs px-3 py-1.5 rounded-full bg-[#12131f] border border-[#262a3d] text-[#a8adc9]">
                <span className="text-[#22d3ee]">{r.split(" ")[0]}</span> {r.split(" ").slice(1).join(" ")}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
