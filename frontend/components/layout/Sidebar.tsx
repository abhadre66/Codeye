"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  Code2,
  GitPullRequest,
  Zap,
  GitBranch,
  LogOut,
  Loader2,
  Clock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUser } from "@/lib/hooks/useUser";

const nav = [
  { label: "System", items: [] },
  { href: "/chat",    icon: Zap,            label: "Chat" },
  { label: "Analysis", items: [] },
  { href: "/analyze", icon: Code2,          label: "Analyze Code" },
  { label: "Pull Request", items: [] },
  { href: "/pr",      icon: GitPullRequest, label: "PR Review" },
  { label: "Memory", items: [] },
  { href: "/history", icon: Clock,          label: "History" },
];

interface Props {
  open?: boolean;
  onClose?: () => void;
}

export function Sidebar({ open = false, onClose }: Props) {
  const path = usePathname();
  const { user, loading, signInWithGitHub, signOut } = useUser();

  const githubUsername = user?.user_metadata?.user_name as string | undefined;
  const avatarUrl = user?.user_metadata?.avatar_url as string | undefined;

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 z-30 md:hidden"
        />
      )}

      <aside
        className={cn(
          "fixed top-0 left-0 bottom-0 w-60 bg-[#111827] border-r border-[#374151] flex flex-col z-40",
          "transition-transform duration-200 md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo */}
        <div className="px-5 py-5 border-b border-[#374151]">
          <Link href="/" onClick={onClose} className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 rounded-lg bg-[#2563eb] flex items-center justify-center flex-shrink-0">
              <MessageSquare className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-[#f9fafb] leading-none">ReviewMind</p>
              <p className="text-[10px] text-[#6b7280] mt-0.5">AI Code Review</p>
            </div>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          {nav.map((item, i) => {
            if ("items" in item) {
              return (
                <p key={i} className="px-2 py-2 text-[10px] font-semibold tracking-widest text-[#6b7280] uppercase mt-2 first:mt-0">
                  {item.label}
                </p>
              );
            }
            const Icon = item.icon;
            const active = path === item.href || (item.href !== "/" && path.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150 mb-0.5",
                  active
                    ? "bg-[#2563eb]/15 text-[#f9fafb] font-medium"
                    : "text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#1f2937]"
                )}
              >
                <Icon className={cn("w-4 h-4 flex-shrink-0", active ? "text-[#2563eb]" : "")} />
                {item.label}
              </Link>
            );
          })}
        </nav>

      {/* User / Auth */}
      <div className="px-4 py-3 border-t border-[#374151]">
        {loading ? (
          <div className="flex items-center gap-2 text-[#6b7280]">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-xs">Loading…</span>
          </div>
        ) : user ? (
          <div className="flex items-center gap-2.5">
            {avatarUrl ? (
              <img src={avatarUrl} alt={githubUsername} className="w-7 h-7 rounded-full flex-shrink-0" />
            ) : (
              <div className="w-7 h-7 rounded-full bg-[#374151] flex items-center justify-center flex-shrink-0">
                <GitBranch className="w-4 h-4 text-[#9ca3af]" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-[#f9fafb] truncate">{githubUsername ?? "GitHub User"}</p>
              <p className="text-[10px] text-[#6b7280]">Connected</p>
            </div>
            <button
              onClick={() => signOut()}
              className="text-[#6b7280] hover:text-[#f9fafb] transition-colors"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => signInWithGitHub()}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#1f2937] transition-all"
          >
            <GitBranch className="w-4 h-4 flex-shrink-0" />
            Sign in with GitHub
          </button>
        )}
      </div>
      </aside>
    </>
  );
}
