"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Phone, Mail, Loader2, ShieldCheck } from "lucide-react";
import Logo from "@/components/ui/Logo";
import { useUserStore } from "@/lib/store/userStore";
import { useToastStore } from "@/lib/store/toastStore";
import { cn } from "@/lib/utils";

type Mode = "phone" | "email";
type Stage = "form" | "otp" | "loading";

export default function LoginPage() {
  const router = useRouter();
  const login = useUserStore((s) => s.login);
  const push = useToastStore((s) => s.push);

  const [mode, setMode] = useState<Mode>("phone");
  const [stage, setStage] = useState<Stage>("form");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState<string[]>(Array(6).fill(""));
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  function completeLogin() {
    setStage("loading");
    setTimeout(() => {
      login({
        name: mode === "phone" ? "Rishi Sharma" : email.split("@")[0] || "TECHRUSH User",
        email: mode === "email" ? email : "rishi.sharma@example.com",
        phone: mode === "phone" ? phone : "+91 98765 43210",
      });
      push("Logged in successfully!", "success");
      router.push("/profile");
    }, 900);
  }

  function requestOtp(e: React.FormEvent) {
    e.preventDefault();
    if (phone.trim().length < 10) {
      push("Enter a valid 10-digit phone number", "error");
      return;
    }
    setStage("otp");
    push("OTP sent: use 1234 for this demo", "info");
  }

  function verifyOtp() {
    if (otp.some((d) => !d)) {
      push("Please enter the complete OTP", "error");
      return;
    }
    completeLogin();
  }

  function handleEmailLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!email.includes("@") || password.length < 4) {
      push("Enter a valid email and password", "error");
      return;
    }
    completeLogin();
  }

  return (
    <div className="mx-auto flex max-w-md flex-col items-center px-4 py-16 md:px-6">
      <Logo size="lg" className="mb-8" />
      <div className="w-full rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 md:p-8">
        <h1 className="mb-1 text-center text-xl font-bold text-white">Welcome back</h1>
        <p className="mb-6 text-center text-sm text-white/50">Log in to track orders and checkout faster.</p>

        {stage !== "otp" && (
          <div className="mb-5 flex rounded-full border border-white/10 bg-navy-800/60 p-1">
            {(["phone", "email"] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={cn(
                  "flex-1 rounded-full py-2 text-xs font-semibold capitalize transition",
                  mode === m ? "bg-rush-gradient text-white" : "text-white/50"
                )}
              >
                {m}
              </button>
            ))}
          </div>
        )}

        <AnimatePresence mode="wait">
          {stage === "form" && mode === "phone" && (
            <motion.form key="phone" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onSubmit={requestOtp} className="space-y-4">
              <div className="relative">
                <Phone className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                  placeholder="10-digit mobile number"
                  className="focus-ring w-full rounded-xl border border-white/10 bg-navy-800 py-3 pl-10 pr-3 text-sm text-white placeholder:text-white/30"
                />
              </div>
              <button type="submit" className="focus-ring w-full rounded-full bg-rush-gradient py-3 text-sm font-bold text-white shadow-glow-sm">
                Send OTP
              </button>
            </motion.form>
          )}

          {stage === "form" && mode === "email" && (
            <motion.form key="email" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onSubmit={handleEmailLogin} className="space-y-4">
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email address"
                  className="focus-ring w-full rounded-xl border border-white/10 bg-navy-800 py-3 pl-10 pr-3 text-sm text-white placeholder:text-white/30"
                />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="focus-ring w-full rounded-xl border border-white/10 bg-navy-800 px-3 py-3 text-sm text-white placeholder:text-white/30"
              />
              <button type="submit" className="focus-ring w-full rounded-full bg-rush-gradient py-3 text-sm font-bold text-white shadow-glow-sm">
                Log in
              </button>
            </motion.form>
          )}

          {stage === "otp" && (
            <motion.div key="otp" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <p className="flex items-center gap-1.5 text-xs text-white/50">
                <ShieldCheck className="h-3.5 w-3.5 text-rush-cyan" /> Enter the 4-digit code sent to +91 {phone} (use 1234)
              </p>
              <div className="flex justify-between gap-2">
                {otp.slice(0, 4).map((digit, i) => (
                  <input
                    key={i}
                    ref={(el) => { inputsRef.current[i] = el; }}
                    value={digit}
                    onChange={(e) => {
                      const v = e.target.value.replace(/\D/g, "").slice(-1);
                      const next = [...otp];
                      next[i] = v;
                      setOtp(next);
                      if (v && i < 3) inputsRef.current[i + 1]?.focus();
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Backspace" && !otp[i] && i > 0) inputsRef.current[i - 1]?.focus();
                    }}
                    maxLength={1}
                    inputMode="numeric"
                    className="focus-ring h-14 w-14 rounded-xl border border-white/10 bg-navy-800 text-center text-xl font-bold text-white"
                  />
                ))}
              </div>
              <button onClick={verifyOtp} className="focus-ring w-full rounded-full bg-rush-gradient py-3 text-sm font-bold text-white shadow-glow-sm">
                Verify &amp; Continue
              </button>
              <button onClick={() => setStage("form")} className="focus-ring w-full text-center text-xs text-white/40 hover:text-white">
                Change phone number
              </button>
            </motion.div>
          )}

          {stage === "loading" && (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center gap-3 py-6">
              <Loader2 className="h-8 w-8 animate-spin text-rush-cyan" />
              <p className="text-sm text-white/60">Signing you in…</p>
            </motion.div>
          )}
        </AnimatePresence>

        {stage === "form" && (
          <>
            <div className="my-5 flex items-center gap-3 text-xs text-white/30">
              <div className="h-px flex-1 bg-white/10" /> OR <div className="h-px flex-1 bg-white/10" />
            </div>
            <button
              onClick={() => push("Google login is a placeholder in this prototype.", "info")}
              className="focus-ring flex w-full items-center justify-center gap-2 rounded-full border border-white/15 bg-white/5 py-3 text-sm font-semibold text-white hover:border-white/30"
            >
              <GoogleIcon /> Continue with Google
            </button>
          </>
        )}
      </div>

      <p className="mt-6 text-sm text-white/50">
        New to TECHRUSH?{" "}
        <Link href="/signup" className="focus-ring font-semibold text-rush-cyan hover:underline">
          Create an account
        </Link>
      </p>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09A6.98 6.98 0 0 1 5.42 12c0-.73.13-1.43.36-2.09V7.07H2.18A11 11 0 0 0 1 12c0 1.77.43 3.45 1.18 4.93z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z" />
    </svg>
  );
}
