"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, User, Mail, Phone, Lock } from "lucide-react";
import Logo from "@/components/ui/Logo";
import { useUserStore } from "@/lib/store/userStore";
import { useToastStore } from "@/lib/store/toastStore";

export default function SignupPage() {
  const router = useRouter();
  const login = useUserStore((s) => s.login);
  const push = useToastStore((s) => s.push);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !email.includes("@") || phone.length < 10 || password.length < 4) {
      push("Please fill all fields correctly", "error");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      login({ name, email, phone: `+91 ${phone}` });
      push("Account created! Welcome to TECHRUSH.", "success");
      router.push("/profile");
    }, 900);
  }

  return (
    <div className="mx-auto flex max-w-md flex-col items-center px-4 py-16 md:px-6">
      <Logo size="lg" className="mb-8" />
      <div className="w-full rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 md:p-8">
        <h1 className="mb-1 text-center text-xl font-bold text-white">Create your account</h1>
        <p className="mb-6 text-center text-sm text-white/50">Join TECHRUSH for faster checkout and order tracking.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <IconInput icon={User} value={name} onChange={setName} placeholder="Full name" />
          <IconInput icon={Mail} value={email} onChange={setEmail} placeholder="Email address" type="email" />
          <IconInput
            icon={Phone}
            value={phone}
            onChange={(v) => setPhone(v.replace(/\D/g, "").slice(0, 10))}
            placeholder="10-digit mobile number"
          />
          <IconInput icon={Lock} value={password} onChange={setPassword} placeholder="Create a password" type="password" />

          <button
            type="submit"
            disabled={loading}
            className="focus-ring flex w-full items-center justify-center gap-2 rounded-full bg-rush-gradient py-3 text-sm font-bold text-white shadow-glow-sm disabled:opacity-60"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Creating account…
              </>
            ) : (
              "Create Account"
            )}
          </button>
        </form>
        <p className="mt-4 text-center text-[11px] text-white/35">
          By signing up you agree to TECHRUSH&apos;s Terms and Privacy Policy. This is a simulated signup for
          prototype purposes.
        </p>
      </div>

      <p className="mt-6 text-sm text-white/50">
        Already have an account?{" "}
        <Link href="/login" className="focus-ring font-semibold text-rush-cyan hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}

function IconInput({
  icon: Icon,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  icon: React.ElementType;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  type?: string;
}) {
  return (
    <div className="relative">
      <Icon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="focus-ring w-full rounded-xl border border-white/10 bg-navy-800 py-3 pl-10 pr-3 text-sm text-white placeholder:text-white/30"
      />
    </div>
  );
}
