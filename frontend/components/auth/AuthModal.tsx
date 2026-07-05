"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Loader2, GitBranch } from "lucide-react";
import { useUser } from "@/lib/hooks/useUser";
import { useState } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

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

export function AuthModal({ open, onClose, onSuccess }: Props) {
  const { signInWithGitHub, signInWithGoogle } = useUser();
  const [loading, setLoading] = useState<"github" | "google" | null>(null);

  const handleSignIn = async (provider: "github" | "google") => {
    setLoading(provider);
    if (provider === "github") await signInWithGitHub();
    else await signInWithGoogle();
    onSuccess();
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="bg-[#12131f] border-[#262a3d] text-[#f4f5fc] max-w-sm">
        <DialogHeader>
          <div className="w-10 h-10 rounded-xl bg-[#7c3aed]/20 border border-[#7c3aed]/30 flex items-center justify-center mb-3">
            <GitBranch className="w-5 h-5 text-[#7c3aed]" />
          </div>
          <DialogTitle className="text-[#f4f5fc]">Sign in to ReviewMind</DialogTitle>
          <DialogDescription className="text-[#7d84a3]">
            Connect an account to post reviews and analyze your PRs.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-2 mt-2">
          <button
            onClick={() => handleSignIn("github")}
            disabled={loading !== null}
            className="w-full bg-[#7c3aed] hover:bg-[#6d28d9] disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
          >
            {loading === "github" ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitBranch className="w-4 h-4" />}
            {loading === "github" ? "Redirecting…" : "Continue with GitHub"}
          </button>
          <button
            onClick={() => handleSignIn("google")}
            disabled={loading !== null}
            className="w-full bg-white hover:bg-gray-100 disabled:opacity-50 text-[#1a1c2e] font-medium py-2.5 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
          >
            {loading === "google" ? <Loader2 className="w-4 h-4 animate-spin" /> : <GoogleIcon className="w-4 h-4" />}
            {loading === "google" ? "Redirecting…" : "Continue with Google"}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
