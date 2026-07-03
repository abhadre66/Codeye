"use client";

import { useRef, useEffect, useState, KeyboardEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Send, Loader2, Zap, Trash2, Wrench } from "lucide-react";
import { useChat, type ChatRequest } from "@/lib/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { cn } from "@/lib/utils";

interface Props {
  initialCode?: string;
  initialPr?: { owner: string; repo: string; pr_number: number };
}

export function ChatPanel({ initialCode, initialPr }: Props) {
  const { messages, isStreaming, activeTool, sendMessage, clear } = useChat();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeTool]);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || isStreaming) return;
    const req: ChatRequest = { message: msg };
    if (initialCode) req.code = initialCode;
    if (initialPr) req.pr = initialPr;
    setInput("");
    sendMessage(req);
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {isEmpty ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center py-20"
          >
            <div className="w-12 h-12 rounded-2xl bg-[#2563eb]/20 border border-[#2563eb]/30 flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-[#2563eb]" />
            </div>
            <h2 className="text-xl font-bold text-[#f9fafb] mb-2">Start a review</h2>
            <p className="text-[#6b7280] text-sm max-w-md mb-6">
              Ask me to review a PR, analyze pasted code, find security issues, or suggest reviewers.
            </p>
            <div className="grid grid-cols-1 gap-2 w-full max-w-md">
              {[
                "Review PR #42 on owner/repo for security issues",
                "Analyze this code for SQL injection vulnerabilities",
                "Who should review this PR based on recent commits?",
                "Compare the before/after code and show what changed",
              ].map((s) => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="text-left px-4 py-2.5 rounded-lg bg-[#111827] border border-[#374151] text-sm text-[#9ca3af] hover:text-[#f9fafb] hover:border-[#6b7280] transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </motion.div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <MessageBubble key={msg.id} message={msg} isLast={i === messages.length - 1 && isStreaming} />
            ))}
            {/* Tool call indicator */}
            <AnimatePresence>
              {activeTool && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1f2937] border border-[#374151] w-fit"
                >
                  <Wrench className="w-3.5 h-3.5 text-[#2563eb]" />
                  <span className="text-xs text-[#9ca3af]">
                    {activeTool.status === "running" ? `Calling` : `Done`}:{" "}
                    <span className="text-[#60a5fa] font-mono">{activeTool.name}</span>
                  </span>
                  {activeTool.status === "running" && (
                    <span className="flex gap-0.5">
                      {[0, 1, 2].map((i) => (
                        <motion.span
                          key={i}
                          className="w-1 h-1 rounded-full bg-[#2563eb]"
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                        />
                      ))}
                    </span>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[#374151] px-4 py-4 bg-[#0a0a0a]">
        {!isEmpty && (
          <div className="flex justify-end mb-2">
            <button onClick={clear} className="flex items-center gap-1.5 text-xs text-[#6b7280] hover:text-[#9ca3af] transition-colors">
              <Trash2 className="w-3 h-3" /> Clear
            </button>
          </div>
        )}
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask ReviewMind anything… (⌘+Enter to send)"
            rows={1}
            className={cn(
              "flex-1 resize-none bg-[#111827] border border-[#374151] rounded-xl px-4 py-3",
              "text-sm text-[#f9fafb] placeholder:text-[#6b7280]",
              "focus:outline-none focus:border-[#2563eb] transition-colors",
              "max-h-40 overflow-y-auto scrollbar-thin"
            )}
            style={{ height: "auto", minHeight: "48px" }}
            onInput={(e) => {
              const t = e.currentTarget;
              t.style.height = "auto";
              t.style.height = Math.min(t.scrollHeight, 160) + "px";
            }}
            disabled={isStreaming}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all",
              input.trim() && !isStreaming
                ? "bg-[#2563eb] hover:bg-[#1d4ed8] text-white"
                : "bg-[#1f2937] text-[#6b7280] cursor-not-allowed"
            )}
          >
            {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-[10px] text-[#6b7280] mt-2 text-right">⌘+Enter to send</p>
      </div>
    </div>
  );
}
