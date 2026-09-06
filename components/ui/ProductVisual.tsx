import { iconForCategory } from "@/lib/icons";
import { cn } from "@/lib/utils";

const gradients = [
  "from-[#1c3a8f] via-[#2f6bff] to-[#3ee8ff]",
  "from-[#1a2444] via-[#243063] to-[#3ee8ff]",
  "from-[#122045] via-[#2f6bff] to-[#7fd9ff]",
  "from-[#0d1326] via-[#1c48d1] to-[#5b8bff]",
];

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) hash = (hash * 31 + str.charCodeAt(i)) >>> 0;
  return hash;
}

interface ProductVisualProps {
  category: string;
  seed: string;
  className?: string;
  iconClassName?: string;
}

export default function ProductVisual({ category, seed, className, iconClassName }: ProductVisualProps) {
  const Icon = iconForCategory(category);
  const gradient = gradients[hashString(seed) % gradients.length];
  return (
    <div
      className={cn(
        "relative flex items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br",
        gradient,
        className
      )}
    >
      <div className="absolute inset-0 opacity-20 [background-image:radial-gradient(circle_at_30%_20%,white,transparent_45%)]" />
      <Icon className={cn("relative text-white/90 drop-shadow-lg", iconClassName)} strokeWidth={1.4} />
    </div>
  );
}
