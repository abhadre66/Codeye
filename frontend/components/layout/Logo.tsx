export function Logo({ size = 28, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="rm-logo-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#22d3ee" />
          <stop offset="1" stopColor="#818cf8" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#rm-logo-grad)" />
      {/* Connecting lines — a small "neural network" glyph */}
      <g stroke="#f4f5fc" strokeWidth="1.3" strokeLinecap="round" opacity="0.9">
        <line x1="16" y1="17" x2="11" y2="10" />
        <line x1="16" y1="17" x2="21" y2="9" />
        <line x1="16" y1="17" x2="10.5" y2="22.5" />
        <line x1="16" y1="17" x2="22.5" y2="21" />
      </g>
      {/* Nodes */}
      <circle cx="16" cy="17" r="2.8" fill="#f4f5fc" />
      <circle cx="11" cy="10" r="2" fill="#f4f5fc" opacity="0.95" />
      <circle cx="21" cy="9" r="1.7" fill="#f4f5fc" opacity="0.85" />
      <circle cx="10.5" cy="22.5" r="1.6" fill="#f4f5fc" opacity="0.85" />
      <circle cx="22.5" cy="21" r="1.8" fill="#f4f5fc" opacity="0.9" />
    </svg>
  );
}
