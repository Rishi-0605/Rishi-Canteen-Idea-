"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Smartphone,
  Laptop,
  Headphones,
  Watch,
  Gamepad2,
  Tv,
  Camera,
  Keyboard,
  Mouse,
  Cable,
  Speaker,
} from "lucide-react";
import { LogoMark } from "@/components/ui/Logo";

const STORAGE_KEY = "techrush_intro_seen_v1";

const objectIcons = [
  { Icon: Smartphone, angle: 0 },
  { Icon: Laptop, angle: 33 },
  { Icon: Headphones, angle: 66 },
  { Icon: Watch, angle: 99 },
  { Icon: Gamepad2, angle: 132 },
  { Icon: Tv, angle: 165 },
  { Icon: Camera, angle: 198 },
  { Icon: Keyboard, angle: 231 },
  { Icon: Mouse, angle: 264 },
  { Icon: Cable, angle: 297 },
  { Icon: Speaker, angle: 330 },
];

// Phase durations in ms, matching the spec timeline
const PHASE_DURATIONS = [1000, 1000, 2000, 1500, 1500, 1000, 1000, 1000];
const TOTAL_MS = PHASE_DURATIONS.reduce((a, b) => a + b, 0);

function edgeOffset(angle: number) {
  const rad = (angle * Math.PI) / 180;
  return { x: Math.cos(rad) * 620, y: Math.sin(rad) * 620 };
}

export default function SplashScreen({ onDone }: { onDone: () => void }) {
  const prefersReduced = useReducedMotion();
  const [mode, setMode] = useState<"full" | "short" | null>(null);
  const [phase, setPhase] = useState(0);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    let seen = false;
    try {
      seen = localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      seen = false;
    }
    setMode(seen || prefersReduced ? "short" : "full");
  }, [prefersReduced]);

  useEffect(() => {
    if (mode === null) return;
    if (mode === "short") {
      const t = setTimeout(finish, prefersReduced ? 150 : 650);
      timers.current.push(t);
      return () => timers.current.forEach(clearTimeout);
    }
    let elapsed = 0;
    PHASE_DURATIONS.forEach((duration, idx) => {
      elapsed += duration;
      const t = setTimeout(() => setPhase(idx + 1), elapsed);
      timers.current.push(t);
    });
    const finishTimer = setTimeout(finish, TOTAL_MS + 150);
    timers.current.push(finishTimer);
    return () => timers.current.forEach(clearTimeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  function finish() {
    timers.current.forEach(clearTimeout);
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
    onDone();
  }

  if (mode === null) return <div className="fixed inset-0 z-[100] bg-navy-950" />;

  if (mode === "short") {
    return (
      <motion.div
        className="fixed inset-0 z-[100] flex items-center justify-center bg-navy-950"
        exit={{ opacity: 0 }}
        transition={{ duration: 0.4 }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: prefersReduced ? 0.15 : 0.5, ease: "easeOut" }}
          className="flex items-center gap-3"
        >
          <LogoMark size="lg" />
          <span className="text-3xl font-extrabold tracking-tight">
            <span className="text-white">TECH</span>
            <span className="rush-underline">RUSH</span>
          </span>
        </motion.div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="fixed inset-0 z-[100] overflow-hidden bg-[#04060d]"
      exit={{ opacity: 0, transition: { duration: 0.7, ease: "easeInOut" } }}
    >
      {/* ambient glow, present from phase 0 */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: phase >= 6 ? 0 : 1 }}
        transition={{ duration: 1 }}
        className="absolute left-1/2 top-1/2 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-rush-cyan/20 blur-[120px]"
      />

      {/* converging objects: phases 1-2 */}
      <AnimatePresence>
        {phase >= 1 && phase <= 2 && (
          <div className="absolute inset-0 flex items-center justify-center">
            {objectIcons.map(({ Icon, angle }, i) => {
              const { x, y } = edgeOffset(angle);
              return (
                <motion.div
                  key={i}
                  initial={{ x, y, opacity: 0, scale: 0.4 }}
                  animate={{ x: 0, y: 0, opacity: [0, 1, 1, 0.4], scale: [0.4, 1, 1, 0.3] }}
                  transition={{ duration: 3, ease: [0.16, 1, 0.3, 1], times: [0, 0.25, 0.7, 1] }}
                  className="absolute"
                >
                  <div className="rounded-2xl border border-rush/40 bg-navy-800/80 p-3 shadow-glow-sm">
                    <Icon className="h-6 w-6 text-rush-cyan md:h-7 md:w-7" strokeWidth={1.6} />
                  </div>
                </motion.div>
              );
            })}
            {/* particles */}
            {Array.from({ length: 18 }).map((_, i) => (
              <motion.span
                key={`p-${i}`}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: [0, 0.8, 0], scale: [0, 1, 0] }}
                transition={{ duration: 1.6, repeat: Infinity, delay: (i % 9) * 0.15 }}
                className="absolute h-1 w-1 rounded-full bg-rush-cyan"
                style={{
                  left: `${50 + Math.cos((i / 18) * Math.PI * 2) * 22}%`,
                  top: `${50 + Math.sin((i / 18) * Math.PI * 2) * 22}%`,
                }}
              />
            ))}
          </div>
        )}
      </AnimatePresence>

      {/* rush streak + flash: phase 3 */}
      <AnimatePresence>
        {phase === 3 && (
          <motion.div className="absolute inset-0">
            {Array.from({ length: 24 }).map((_, i) => (
              <motion.span
                key={i}
                initial={{ x: "-20vw", opacity: 0 }}
                animate={{ x: "120vw", opacity: [0, 1, 0] }}
                transition={{ duration: 0.7 + (i % 5) * 0.08, delay: i * 0.03, ease: "easeIn" }}
                className="absolute h-[1.5px] w-24 bg-gradient-to-r from-transparent via-rush-cyan to-transparent"
                style={{ top: `${(i * 41) % 100}%` }}
              />
            ))}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 0, 1, 0] }}
              transition={{ duration: 1.5, times: [0, 0.7, 0.85, 1] }}
              className="absolute inset-0 bg-white"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* logo formation: phase 4+ */}
      <AnimatePresence>
        {phase >= 4 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 flex flex-col items-center justify-center gap-5 px-6 text-center"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.6, filter: "blur(8px)" }}
              animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="drop-shadow-[0_0_35px_rgba(63,120,255,0.55)]"
            >
              <LogoMark size="xl" />
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35, duration: 0.6 }}
              className="text-4xl font-extrabold tracking-tight md:text-6xl"
            >
              <span className="text-white">TECH</span>
              <span className="rush-underline">RUSH</span>
            </motion.h1>

            {phase >= 5 && (
              <motion.p
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="text-sm font-medium uppercase tracking-[0.3em] text-white/70 md:text-base"
              >
                Technology. Delivered Faster.
              </motion.p>
            )}

            {phase >= 6 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="mt-2 flex flex-col items-center gap-4"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-rush-cyan md:text-sm">
                  Need tech? Get it fast.
                </p>
                <div className="relative h-[2px] w-56 overflow-hidden rounded-full bg-white/10 md:w-72">
                  <motion.div
                    initial={{ x: "-100%" }}
                    animate={{ x: "100%" }}
                    transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute inset-y-0 w-1/2 bg-gradient-to-r from-transparent via-rush-cyan to-transparent"
                  />
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <button
        onClick={finish}
        className="focus-ring absolute bottom-6 right-6 z-10 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs font-semibold tracking-wide text-white/80 backdrop-blur transition hover:border-rush-cyan/60 hover:text-white md:bottom-8 md:right-8"
        aria-label="Skip intro animation"
      >
        SKIP INTRO →
      </button>
    </motion.div>
  );
}
