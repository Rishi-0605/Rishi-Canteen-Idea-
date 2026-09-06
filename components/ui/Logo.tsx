import { cn } from "@/lib/utils";

interface LogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  showWordmark?: boolean;
  className?: string;
}

const markSizes = { sm: 28, md: 36, lg: 52, xl: 84 };
const textSizes = { sm: "text-lg", md: "text-xl", lg: "text-3xl", xl: "text-5xl md:text-6xl" };

export function LogoMark({ size = "md", className }: { size?: LogoProps["size"]; className?: string }) {
  const px = markSizes[size ?? "md"];
  return (
    <svg
      width={px}
      height={px}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("shrink-0", className)}
      role="img"
      aria-label="TECHRUSH logo mark"
    >
      <defs>
        <linearGradient id="trGrad" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop stopColor="#3ee8ff" />
          <stop offset="1" stopColor="#2f6bff" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="46" height="46" rx="13" fill="#0a0f1e" stroke="url(#trGrad)" strokeWidth="1.5" />
      <path d="M8 16h9M8 21h5" stroke="url(#trGrad)" strokeWidth="2.4" strokeLinecap="round" opacity="0.65" />
      <text
        x="24"
        y="31"
        textAnchor="middle"
        fontFamily="Inter, system-ui, sans-serif"
        fontWeight="800"
        fontSize="19"
        fill="url(#trGrad)"
      >
        TR
      </text>
      <path d="M31 33h9M35 38h5" stroke="url(#trGrad)" strokeWidth="2.4" strokeLinecap="round" opacity="0.65" />
    </svg>
  );
}

export default function Logo({ size = "md", showWordmark = true, className }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <LogoMark size={size} />
      {showWordmark && (
        <span className={cn("font-extrabold tracking-tight", textSizes[size])}>
          <span className="text-white">TECH</span>
          <span className="rush-underline">RUSH</span>
        </span>
      )}
    </div>
  );
}
