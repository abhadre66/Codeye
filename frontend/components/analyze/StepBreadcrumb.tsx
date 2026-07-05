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
                active && "text-[#f4f5fc] bg-[#7c3aed]/15 border border-[#7c3aed]/40",
                done && "text-[#22d3ee] hover:text-[#67e8f9] cursor-pointer",
                future && "text-[#363a52] cursor-default"
              )}
            >
              <span className={cn(
                "w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 border",
                active && "bg-[#7c3aed] border-[#7c3aed] text-white",
                done && "bg-[#6d28d9]/30 border-[#7c3aed]/60 text-[#22d3ee]",
                future && "bg-[#1a1c2e] border-[#262a3d] text-[#363a52]"
              )}>
                {done ? <Check className="w-3 h-3" /> : i + 1}
              </span>
              {step}
            </button>

            {i < steps.length - 1 && (
              <div className={cn("w-8 h-px mx-1", done || active ? "bg-[#7c3aed]/40" : "bg-[#262a3d]")} />
            )}
          </div>
        );
      })}
    </div>
  );
}
