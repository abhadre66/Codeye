"use client";

import { useState, useCallback, useRef } from "react";
import { supabase } from "@/lib/supabase";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface ToolCallState {
  id: string;
  name: string;
  status: "running" | "done";
}

export interface ChatRequest {
  message: string;
  code?: string;
  files?: { name: string; content: string }[];
  pr?: { owner: string; repo: string; pr_number: number };
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTool, setActiveTool] = useState<ToolCallState | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (req: ChatRequest) => {
    if (isStreaming) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: req.message + (req.code ? `\n\n\`\`\`\n${req.code}\n\`\`\`` : "") + (req.pr ? `\n\nPR: ${req.pr.owner}/${req.pr.repo} #${req.pr.pr_number}` : ""),
    };
    const assistantMsg: ChatMessage = { id: crypto.randomUUID(), role: "assistant", content: "" };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);
    setActiveTool(null);

    abortRef.current = new AbortController();

    try {
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(req),
        signal: abortRef.current.signal,
      });

      const reader = res.body!.getReader();
      const dec = new TextDecoder();
      let buf = "";
      let evt = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            evt = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (evt === "token") {
                setMessages((prev) => {
                  const next = [...prev];
                  next[next.length - 1] = { ...next[next.length - 1], content: next[next.length - 1].content + data.text };
                  return next;
                });
              } else if (evt === "tool_call") {
                setActiveTool({ id: data.id, name: data.name, status: "running" });
              } else if (evt === "tool_result") {
                setActiveTool((prev) => prev ? { ...prev, status: "done" } : null);
                setTimeout(() => setActiveTool(null), 1000);
              } else if (evt === "done") {
                setActiveTool(null);
              } else if (evt === "error") {
                setMessages((prev) => {
                  const next = [...prev];
                  next[next.length - 1] = { ...next[next.length - 1], content: `Error: ${data.message}` };
                  return next;
                });
              }
            } catch (_) {}
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== "AbortError") {
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...next[next.length - 1], content: `Connection error: ${e.message}` };
          return next;
        });
      }
    } finally {
      setIsStreaming(false);
      setActiveTool(null);
    }
  }, [isStreaming]);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setIsStreaming(false);
    setActiveTool(null);
  }, []);

  return { messages, isStreaming, activeTool, sendMessage, clear };
}
