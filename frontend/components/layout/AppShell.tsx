"use client";

import { useState } from "react";
import { Menu } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Logo } from "@/components/layout/Logo";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-20 flex items-center gap-3 px-4 py-3 bg-[#12131f] border-b border-[#262a3d]">
        <button
          onClick={() => setMobileNavOpen(true)}
          className="text-[#a8adc9] hover:text-[#f4f5fc] transition-colors"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <Logo size={24} className="flex-shrink-0" />
          <p className="text-sm font-bold text-[#f4f5fc] leading-none font-display tracking-tight">ReviewMind</p>
        </div>
      </div>

      <Sidebar open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

      <main className="flex-1 min-w-0 md:ml-60 pt-14 md:pt-0 min-h-screen overflow-auto">
        {children}
      </main>
    </>
  );
}
