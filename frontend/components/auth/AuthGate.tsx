"use client";

import { useState } from "react";
import { Loader2, GitBranch } from "lucide-react";
import { useUser } from "@/lib/hooks/useUser";
import { Logo } from "@/components/layout/Logo";

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.47c-.28 1.5-1.13 2.78-2.4 3.63v3h3.88c2.27-2.09 3.57-5.17 3.57-8.82z" fill="#4285F4"/>
      <path d="M12 24c3.24 0 5.96-1.07 7.95-2.91l-3.88-3c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.96H1.27v3.11C3.25 21.3 7.31 24 12 24z" fill="#34A853"/>
      <path d="M5.27 14.28A7.2 7.2 0 0 1 4.9 12c0-.79.14-1.56.37-2.28V6.61H1.27A11.98 11.98 0 0 0 0 12c0 1.94.46 3.77 1.27 5.39l4-3.11z" fill="#FBBC05"/>
      <path d="M12 4.77c1.77 0 3.35.61 4.6 1.8l3.44-3.44C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.27 6.61l4 3.11C6.22 6.88 8.87 4.77 12 4.77z" fill="#EA4335"/>
    </svg>
  );
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading, signInWithGitHub, signInWithGoogle } = useUser();
  const [signingIn, setSigningIn] = useState<"github" | "google" | null>(null);

  if (loading) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-[#08080f]">
        <Loader2 className="w-6 h-6 text-[#7d84a3] animate-spin" />
      </div>
    );
  }

  if (!user) {
    const handleSignIn = async (provider: "github" | "google") => {
      setSigningIn(provider);
      if (provider === "github") await signInWithGitHub();
      else await signInWithGoogle();
    };

    return (
      <div className="relative h-full w-full flex items-center justify-center bg-[#08080f] px-4 overflow-hidden ambient-glow">
        <div className="w-full max-w-sm">
          <div className="flex flex-col items-center text-center mb-8">
            <Logo size={104} className="mb-5 drop-shadow-[0_0_40px_rgba(34,211,238,0.45)] float-slow" />
            <h1 className="text-3xl font-bold font-display tracking-tight gradient-text">ReviewMind</h1>
            <p className="text-sm text-[#7d84a3] mt-2">
              Sign in to analyze PRs, review code, and get AI-powered fixes.
            </p>
          </div>

          <div className="flex flex-col gap-2.5 bg-[#12131f]/80 border border-[#262a3d] rounded-2xl p-5 backdrop-blur-sm">
            <button
              onClick={() => handleSignIn("github")}
              disabled={signingIn !== null}
              className="w-full bg-[#7c3aed] hover:bg-[#6d28d9] disabled:opacity-50 text-white font-medium py-3 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
            >
              {signingIn === "github" ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitBranch className="w-4 h-4" />}
              {signingIn === "github" ? "Redirecting…" : "Continue with GitHub"}
            </button>
            <button
              onClick={() => handleSignIn("google")}
              disabled={signingIn !== null}
              className="w-full bg-white hover:bg-gray-100 disabled:opacity-50 text-[#1a1c2e] font-medium py-3 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
            >
              {signingIn === "google" ? <Loader2 className="w-4 h-4 animate-spin" /> : <GoogleIcon className="w-4 h-4" />}
              {signingIn === "google" ? "Redirecting…" : "Continue with Google"}
            </button>
          </div>

          <p className="text-center text-[10px] text-[#363a52] mt-6">
            By continuing you agree to connect your account for PR analysis and review posting.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
