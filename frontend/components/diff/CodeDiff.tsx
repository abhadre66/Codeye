"use client";

import { DiffEditor } from "@monaco-editor/react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  original: string;
  modified: string;
  filename?: string;
  complexityDelta?: number;
  height?: string;
}

export function CodeDiff({ original, modified, filename = "snippet.py", complexityDelta = 0, height = "380px" }: Props) {
  const additions = (modified.split("\n").length - original.split("\n").length);

  return (
    <div className="bg-[#1e1e1e] rounded-xl overflow-hidden border border-[#262a3d]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#252526] border-b border-[#262a3d]">
        <span className="text-xs text-[#a8adc9] font-mono">{filename} — diff</span>
        <div className="flex items-center gap-3">
          {additions !== 0 && (
            <span className={cn("text-xs font-mono", additions > 0 ? "text-green-400" : "text-red-400")}>
              {additions > 0 ? "+" : ""}{additions} lines
            </span>
          )}
          {complexityDelta !== 0 && (
            <span className={cn("inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-md border", complexityDelta > 0 ? "text-red-400 border-red-900 bg-red-950/30" : "text-green-400 border-green-900 bg-green-950/30")}>
              {complexityDelta > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {complexityDelta > 0 ? "+" : ""}{complexityDelta} complexity
            </span>
          )}
          {complexityDelta === 0 && (
            <span className="inline-flex items-center gap-1 text-xs text-[#7d84a3] border border-[#262a3d] px-2 py-0.5 rounded-md">
              <Minus className="w-3 h-3" /> no complexity change
            </span>
          )}
        </div>
      </div>

      <DiffEditor
        height={height}
        original={original}
        modified={modified}
        language={filename.split(".").pop() ?? "plaintext"}
        theme="vs-dark"
        options={{
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 13,
          lineHeight: 20,
          fontFamily: "'Geist Mono', 'Fira Code', monospace",
          scrollBeyondLastLine: false,
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: "none",
          scrollbar: { verticalScrollbarSize: 6, horizontalScrollbarSize: 6 },
          glyphMargin: false,
          folding: false,
          automaticLayout: true,
          renderSideBySide: true,
        }}
        loading={
          <div className="flex items-center justify-center bg-[#1e1e1e]" style={{ height }}>
            <span className="text-xs text-[#7d84a3]">Loading diff editor…</span>
          </div>
        }
      />
    </div>
  );
}
