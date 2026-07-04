"use client";

import { useState } from "react";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { CodeEditor } from "@/components/code/CodeEditor";
import { PanelRight, X } from "lucide-react";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const [attachedCode, setAttachedCode] = useState<string | undefined>();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen relative">
      {/* Main chat */}
      <div className={cn("flex flex-col flex-1 min-w-0 transition-all", sidebarOpen ? "sm:mr-[380px]" : "")}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#374151] bg-[#0a0a0a]">
          <div>
            <h1 className="font-semibold text-[#f9fafb]">AI Review Chat</h1>
            <p className="text-xs text-[#6b7280]">Claude · 14 specialized tools</p>
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs transition-all", sidebarOpen ? "bg-[#1f2937] border-[#2563eb] text-[#60a5fa]" : "border-[#374151] text-[#6b7280] hover:text-[#9ca3af]")}
          >
            <PanelRight className="w-3.5 h-3.5" />
            {attachedCode ? "Code attached" : "Attach code"}
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          <ChatPanel initialCode={attachedCode} />
        </div>
      </div>

      {/* Code panel */}
      {sidebarOpen && (
        <div className="fixed right-0 top-0 h-full w-full sm:w-[380px] bg-[#111827] border-l border-[#374151] flex flex-col z-10">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#374151]">
            <span className="text-sm font-medium text-[#f9fafb]">Attach Code</span>
            <button onClick={() => setSidebarOpen(false)} className="text-[#6b7280] hover:text-[#f9fafb] transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <CodeEditor
              value={attachedCode ?? ""}
              onChange={setAttachedCode}
              height="100%"
            />
          </div>
          {attachedCode && (
            <div className="px-4 py-3 border-t border-[#374151]">
              <button
                onClick={() => { setAttachedCode(undefined); setSidebarOpen(false); }}
                className="text-xs text-[#6b7280] hover:text-[#f9fafb] transition-colors"
              >
                Remove attachment
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
