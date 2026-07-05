"use client";

import { useCallback, useRef } from "react";
import Editor from "@monaco-editor/react";
import { Upload, X } from "lucide-react";
import { cn } from "@/lib/utils";

const EXT_LANG: Record<string, string> = {
  py: "python", ts: "typescript", tsx: "typescript", js: "javascript", jsx: "javascript",
  rs: "rust", go: "go", java: "java", cs: "csharp", cpp: "cpp", c: "c",
  rb: "ruby", php: "php", sh: "shell", yaml: "yaml", yml: "yaml",
  json: "json", md: "markdown", sql: "sql", html: "html", css: "css",
};

function detectLanguage(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  return EXT_LANG[ext] ?? "plaintext";
}

interface Props {
  value: string;
  onChange: (v: string) => void;
  filename?: string;
  height?: string;
  placeholder?: string;
  readOnly?: boolean;
  className?: string;
}

export function CodeEditor({ value, onChange, filename = "snippet.py", height = "300px", placeholder, readOnly = false, className }: Props) {
  const lang = detectLanguage(filename);
  const dropRef = useRef<HTMLDivElement>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => onChange(ev.target?.result as string ?? "");
    reader.readAsText(file);
  }, [onChange]);

  const handleDragOver = (e: React.DragEvent) => e.preventDefault();

  return (
    <div
      ref={dropRef}
      className={cn("relative bg-[#1e1e1e] group", className)}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#252526] border-b border-[#262a3d]">
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#a8adc9] font-mono">{filename}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#262a3d] text-[#7d84a3] uppercase tracking-wide">{lang}</span>
        </div>
        <div className="flex items-center gap-2">
          {!readOnly && (
            <>
              <span className="text-[10px] text-[#7d84a3] opacity-0 group-hover:opacity-100 transition-opacity">
                <Upload className="w-3 h-3 inline mr-1" />drop file
              </span>
              {value && (
                <button onClick={() => onChange("")} className="text-[#7d84a3] hover:text-[#f4f5fc] transition-colors">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Editor */}
      <Editor
        height={height}
        language={lang}
        value={value || (readOnly ? "" : undefined)}
        onChange={(v) => !readOnly && onChange(v ?? "")}
        theme="vs-dark"
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 13,
          lineHeight: 20,
          fontFamily: "'Geist Mono', 'Fira Code', 'Cascadia Code', monospace",
          fontLigatures: true,
          scrollBeyondLastLine: false,
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: "none",
          overviewRulerLanes: 0,
          hideCursorInOverviewRuler: true,
          scrollbar: { verticalScrollbarSize: 6, horizontalScrollbarSize: 6 },
          contextmenu: false,
          folding: true,
          lineNumbers: "on",
          glyphMargin: false,
          wordWrap: "off",
          automaticLayout: true,
          placeholder: placeholder,
        }}
        loading={
          <div className="flex items-center justify-center bg-[#1e1e1e]" style={{ height }}>
            <span className="text-xs text-[#7d84a3]">Loading editor…</span>
          </div>
        }
      />
    </div>
  );
}
