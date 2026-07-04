"use client";

import { useState } from "react";
import { Menu, MessageSquare } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-20 flex items-center gap-3 px-4 py-3 bg-[#111827] border-b border-[#374151]">
        <button
          onClick={() => setMobileNavOpen(true)}
          className="text-[#9ca3af] hover:text-[#f9fafb] transition-colors"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#2563eb] flex items-center justify-center flex-shrink-0">
            <MessageSquare className="w-3.5 h-3.5 text-white" />
          </div>
          <p className="text-sm font-bold text-[#f9fafb] leading-none">ReviewMind</p>
        </div>
      </div>

      <Sidebar open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

      <main className="flex-1 min-w-0 md:ml-60 pt-14 md:pt-0 min-h-screen overflow-auto">
        {children}
      </main>
    </>
  );
}
