/* eslint-disable @next/next/no-img-element */
export function Logo({ size = 28, className }: { size?: number; className?: string }) {
  return (
    <span
      className={`inline-block rounded-full overflow-hidden ring-1 ring-[#22d3ee]/40 ${className ?? ""}`}
      style={{ width: size, height: size }}
    >
      <img
        src="/brand/logo.png"
        alt="ReviewMind"
        width={size}
        height={size}
        className="w-full h-full object-cover scale-[1.18]"
      />
    </span>
  );
}
