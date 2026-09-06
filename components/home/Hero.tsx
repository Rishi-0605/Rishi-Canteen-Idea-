"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, LayoutGrid, Smartphone, Laptop, Headphones, Watch, Gamepad2, Tv } from "lucide-react";

const floaters = [
  { Icon: Smartphone, className: "left-[6%] top-[18%] animate-float", delay: 0 },
  { Icon: Laptop, className: "right-[8%] top-[10%] animate-float-delay", delay: 0.1 },
  { Icon: Headphones, className: "left-[14%] bottom-[16%] animate-float-delay", delay: 0.2 },
  { Icon: Watch, className: "right-[16%] bottom-[26%] animate-float", delay: 0.3 },
  { Icon: Gamepad2, className: "left-[42%] top-[6%] animate-float-delay", delay: 0.4 },
  { Icon: Tv, className: "right-[38%] bottom-[8%] animate-float", delay: 0.5 },
];

export default function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pb-16 pt-14 md:px-6 md:pb-24 md:pt-20">
      <div className="pointer-events-none absolute left-1/2 top-0 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-rush/20 blur-[140px]" />

      <div className="relative mx-auto max-w-4xl text-center">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-semibold text-white/70"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Delivery in 30 min – 2 hrs*
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="text-4xl font-extrabold leading-[1.08] tracking-tight text-white sm:text-5xl md:text-6xl"
        >
          TECH YOU WANT.
          <br />
          <span className="rush-underline">DELIVERED FAST.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mx-auto mt-5 max-w-xl text-base text-white/60 md:text-lg"
        >
          Shop electronics and appliances from trusted nearby retail partners and get them delivered in as little as
          30 minutes.*
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25 }}
          className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <Link
            href="/products"
            className="focus-ring group flex items-center gap-2 rounded-full bg-rush-gradient px-7 py-3.5 text-sm font-bold text-white shadow-glow transition hover:brightness-110"
          >
            SHOP NOW <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
          </Link>
          <Link
            href="/categories"
            className="focus-ring flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-7 py-3.5 text-sm font-bold text-white transition hover:border-rush-cyan/50"
          >
            <LayoutGrid className="h-4 w-4" /> EXPLORE CATEGORIES
          </Link>
        </motion.div>

        <p className="mt-4 text-xs text-white/35">*Delivery time varies by product, location and partner availability.</p>
      </div>

      <div className="relative mx-auto mt-14 hidden h-64 max-w-5xl md:block" aria-hidden="true">
        {floaters.map(({ Icon, className, delay }, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.4 + delay }}
            className={`absolute ${className} rounded-2xl border border-white/10 bg-navy-800/70 p-4 shadow-glow-sm backdrop-blur`}
          >
            <Icon className="h-8 w-8 text-rush-cyan" strokeWidth={1.5} />
          </motion.div>
        ))}
      </div>
    </section>
  );
}
