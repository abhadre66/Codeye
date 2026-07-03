import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const GENERIC_MARKERS = ["# Instead of", "# Use", "// Instead of", "// Use", "# Bad:", "# Good:", "// Bad:", "// Good:"];

export function isGenericExample(fixExample: string): boolean {
  return GENERIC_MARKERS.some((m) => fixExample.includes(m));
}
