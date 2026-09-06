"use client";

import { useEffect, useState } from "react";
import { Timer } from "lucide-react";

function pad(n: number) {
  return n.toString().padStart(2, "0");
}

export default function CountdownTimer({ initialSeconds = 3600 * 4 }: { initialSeconds?: number }) {
  const [seconds, setSeconds] = useState(initialSeconds);

  useEffect(() => {
    const id = setInterval(() => setSeconds((s) => (s > 0 ? s - 1 : initialSeconds)), 1000);
    return () => clearInterval(id);
  }, [initialSeconds]);

  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  return (
    <span className="flex items-center gap-1.5 rounded-full bg-black/30 px-3 py-1 text-xs font-semibold text-white" title="Demo countdown timer">
      <Timer className="h-3.5 w-3.5 text-rush-cyan" />
      {pad(h)}:{pad(m)}:{pad(s)}
    </span>
  );
}
