"use client";

import { motion } from "framer-motion";
import { User, Zap, Store, Bike, Home as HomeIcon, ArrowDown } from "lucide-react";

const flow = [
  { Icon: User, label: "CUSTOMER", desc: "Places an order on TECHRUSH" },
  { Icon: Zap, label: "TECHRUSH", desc: "Matches the fastest nearby source" },
  { Icon: Store, label: "NEARBY RETAIL PARTNER", desc: "Prepares the product for pickup" },
  { Icon: Bike, label: "DELIVERY PARTNER", desc: "Picks up and heads your way" },
  { Icon: HomeIcon, label: "CUSTOMER", desc: "Receives it at their doorstep" },
];

export default function DeliveredFast() {
  return (
    <section className="relative overflow-hidden px-4 py-16 md:px-6 md:py-24">
      <div className="pointer-events-none absolute inset-x-0 top-1/2 h-72 -translate-y-1/2 bg-rush/10 blur-[120px]" />
      <div className="relative mx-auto max-w-5xl text-center">
        <h2 className="text-3xl font-extrabold leading-tight tracking-tight text-white md:text-4xl">
          YOUR NEAREST TECH.
          <br />
          <span className="rush-underline">NOW DELIVERED TO YOU.</span>
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-white/60">
          TECHRUSH doesn&apos;t need to own every piece of inventory. Instead, we connect nearby available stock from
          participating retailers, distributors and authorized sellers — making the marketplace asset-light and
          delivery fast.
        </p>

        <div className="mt-14 flex flex-col items-center gap-2 md:flex-row md:justify-between md:gap-3">
          {flow.map(({ Icon, label, desc }, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className="flex flex-col items-center gap-2 md:flex-1"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-rush/30 bg-navy-800/70 shadow-glow-sm">
                <Icon className="h-7 w-7 text-rush-cyan" strokeWidth={1.6} />
              </div>
              <p className="text-xs font-bold tracking-wide text-white">{label}</p>
              <p className="max-w-[9rem] text-[11px] text-white/45">{desc}</p>
              {i < flow.length - 1 && (
                <>
                  <ArrowDown className="h-4 w-4 text-rush/50 md:hidden" />
                  <motion.div
                    initial={{ scaleX: 0 }}
                    whileInView={{ scaleX: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: i * 0.1 + 0.2 }}
                    className="hidden h-px flex-1 origin-left bg-gradient-to-r from-rush/60 to-rush-cyan/20 md:block"
                  />
                </>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
