"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  steps: string[];
  current: number;
  onStepClick?: (index: number) => void;
}

export function StepBreadcrumb({ steps, current, onStepClick }: Props) {
  return (
    <div className="flex items-center gap-0 mb-8">
      {steps.map((step, i) => {
        const done = i < current;
        const active = i === current;
        const future = i > current;

        return (
          <div key={step} className="flex items-center">
            <button
              onClick={() => done && onStepClick?.(i)}
              disabled={!done}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                active && "text-[#f9fafb] bg-[#2563eb]/15 border border-[#2563eb]/40",
                done && "text-[#60a5fa] hover:text-[#93c5fd] cursor-pointer",
                future && "text-[#4b5563] cursor-default"
              )}
            >
              <span className={cn(
                "w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 border",
                active && "bg-[#2563eb] border-[#2563eb] text-white",
                done && "bg-[#1d4ed8]/30 border-[#2563eb]/60 text-[#60a5fa]",
                future && "bg-[#1f2937] border-[#374151] text-[#4b5563]"
              )}>
                {done ? <Check className="w-3 h-3" /> : i + 1}
              </span>
              {step}
            </button>

            {i < steps.length - 1 && (
              <div className={cn("w-8 h-px mx-1", done || active ? "bg-[#2563eb]/40" : "bg-[#374151]")} />
            )}
          </div>
        );
      })}
    </div>
  );
}
