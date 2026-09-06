"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, LayoutDashboard, TrendingUp, Users, Zap } from "lucide-react";
import { categories } from "@/lib/data/categories";
import { useToastStore } from "@/lib/store/toastStore";

const stats = [
  { Icon: Users, label: "Retail partners onboarded", value: "500+" },
  { Icon: TrendingUp, label: "Avg. new demand for partners", value: "+18%" },
  { Icon: Zap, label: "Avg. order-to-pickup time", value: "12 min" },
];

export default function PartnerOnboardingPage() {
  const push = useToastStore((s) => s.push);
  const [submitted, setSubmitted] = useState(false);
  const [categoriesSelected, setCategoriesSelected] = useState<string[]>([]);

  function toggleCategory(slug: string) {
    setCategoriesSelected((prev) => (prev.includes(slug) ? prev.filter((c) => c !== slug) : [...prev, slug]));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitted(true);
    push("Application received! Our team will reach out within 2 business days.", "success");
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-14 md:px-6">
      <div className="mb-12 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">Become a Retail Partner</h1>
        <p className="mx-auto mt-3 max-w-xl text-white/55">
          List your electronics inventory on TECHRUSH and reach customers looking for fast local delivery — without
          changing how you run your store.
        </p>
        <Link
          href="/partner/dashboard"
          className="focus-ring mt-5 inline-flex items-center gap-2 text-sm font-semibold text-rush-cyan hover:underline"
        >
          <LayoutDashboard className="h-4 w-4" /> View demo partner dashboard
        </Link>
      </div>

      <div className="mb-12 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map(({ Icon, label, value }) => (
          <div key={label} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 text-center">
            <Icon className="mx-auto mb-2 h-5 w-5 text-rush-cyan" />
            <p className="text-xl font-extrabold text-white">{value}</p>
            <p className="mt-1 text-xs text-white/45">{label}</p>
          </div>
        ))}
      </div>

      {submitted ? (
        <div className="flex flex-col items-center gap-3 rounded-3xl border border-emerald-500/30 bg-emerald-500/[0.06] p-12 text-center">
          <CheckCircle2 className="h-12 w-12 text-emerald-400" />
          <h2 className="text-xl font-bold text-white">Application Submitted</h2>
          <p className="max-w-sm text-sm text-white/60">
            Thanks for your interest in TECHRUSH. Our partnerships team will review your application and reach out
            within 2 business days.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5 rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 md:p-8">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Business name" name="business" required />
            <Field label="Owner name" name="owner" required />
            <Field label="Phone number" name="phone" type="tel" required />
            <Field label="Email address" name="email" type="email" required />
            <Field label="Store location / address" name="location" required className="sm:col-span-2" />
            <Field label="GST / business registration number" name="gst" required />
            <Field label="Inventory capacity (approx. units)" name="capacity" type="number" required />
          </div>

          <div>
            <label className="mb-2 block text-xs font-bold uppercase tracking-wide text-white/40">Product categories you sell</label>
            <div className="flex flex-wrap gap-2">
              {categories.map((c) => (
                <button
                  type="button"
                  key={c.slug}
                  onClick={() => toggleCategory(c.slug)}
                  className={`focus-ring rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
                    categoriesSelected.includes(c.slug)
                      ? "border-rush bg-rush/15 text-rush-cyan"
                      : "border-white/10 bg-white/[0.02] text-white/60 hover:border-white/25"
                  }`}
                >
                  {c.emoji} {c.name}
                </button>
              ))}
            </div>
          </div>

          <button type="submit" className="focus-ring w-full rounded-full bg-rush-gradient py-3.5 text-sm font-bold text-white shadow-glow-sm">
            SUBMIT APPLICATION
          </button>
          <p className="text-center text-[11px] text-white/35">
            This is a prototype form. No data is submitted to a live server or third party.
          </p>
        </form>
      )}
    </div>
  );
}

function Field({
  label,
  name,
  type = "text",
  required,
  className = "",
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  className?: string;
}) {
  return (
    <div className={className}>
      <label htmlFor={name} className="mb-1.5 block text-xs font-medium text-white/50">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        required={required}
        className="focus-ring w-full rounded-lg border border-white/10 bg-navy-800 px-3 py-2.5 text-sm text-white placeholder:text-white/30"
      />
    </div>
  );
}
