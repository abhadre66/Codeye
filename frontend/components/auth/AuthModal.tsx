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

export function AuthModal({ open, onClose, onSuccess }: Props) {
  const { signInWithGitHub } = useUser();
  const [loading, setLoading] = useState(false);

  const handleSignIn = async () => {
    setLoading(true);
    await signInWithGitHub();
    onSuccess();
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="bg-[#111827] border-[#374151] text-[#f9fafb] max-w-sm">
        <DialogHeader>
          <div className="w-10 h-10 rounded-xl bg-[#2563eb]/20 border border-[#2563eb]/30 flex items-center justify-center mb-3">
            <GitBranch className="w-5 h-5 text-[#2563eb]" />
          </div>
          <DialogTitle className="text-[#f9fafb]">Sign in to ReviewMind</DialogTitle>
          <DialogDescription className="text-[#6b7280]">
            Connect your GitHub account to post reviews and analyze your PRs.
          </DialogDescription>
        </DialogHeader>
        <button
          onClick={handleSignIn}
          disabled={loading}
          className="w-full mt-2 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <GitBranch className="w-4 h-4" />
          )}
          {loading ? "Redirecting…" : "Continue with GitHub"}
        </button>
      </DialogContent>
    </Dialog>
  );
}
