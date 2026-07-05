"use client";

import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot } from "lucide-react";
import type { ChatMessage } from "@/lib/hooks/useChat";
import { cn } from "@/lib/utils";

interface Props {
  message: ChatMessage;
  isLast?: boolean;
}

export function MessageBubble({ message, isLast }: Props) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn("flex gap-3 max-w-4xl", isUser ? "ml-auto flex-row-reverse" : "")}
    >
      {/* Avatar */}
      <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5", isUser ? "bg-[#0891b2]" : "bg-[#1a1c2e] border border-[#262a3d]")}>
        {isUser ? <User className="w-3.5 h-3.5 text-white" /> : <Bot className="w-3.5 h-3.5 text-[#a8adc9]" />}
      </div>

      {/* Content */}
      <div className={cn("rounded-xl px-4 py-3 max-w-[85%] text-sm leading-relaxed", isUser ? "bg-[#0891b2] text-white rounded-tr-sm" : "bg-[#1a1c2e] border border-[#262a3d] text-[#c7cbe3] rounded-tl-sm")}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              code: ({ children, className }) => {
                const isBlock = className?.includes("language-");
                return isBlock ? (
                  <pre className="bg-black/40 rounded-md p-3 overflow-x-auto text-xs font-mono my-2 text-green-300">
                    <code>{children}</code>
                  </pre>
                ) : (
                  <code className="bg-black/30 px-1 py-0.5 rounded text-xs font-mono text-[#67e8f9]">{children}</code>
                );
              },
              ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2">{children}</ol>,
              h3: ({ children }) => <h3 className="font-semibold text-[#f4f5fc] mt-3 mb-1">{children}</h3>,
              h4: ({ children }) => <h4 className="font-medium text-[#f4f5fc] mt-2 mb-1">{children}</h4>,
              strong: ({ children }) => <strong className="font-semibold text-[#f4f5fc]">{children}</strong>,
              a: ({ children, href }) => <a href={href} target="_blank" rel="noreferrer" className="text-[#22d3ee] hover:underline">{children}</a>,
            }}
          >
            {message.content || (isLast ? "▋" : "")}
          </ReactMarkdown>
        )}
      </div>
    </motion.div>
  );
}
