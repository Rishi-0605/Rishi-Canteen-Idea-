"use client";

import { motion } from "framer-motion";
import { Zap, ShieldCheck, MapPinned, Wrench } from "lucide-react";

const cards = [
  { Icon: Zap, title: "FAST", desc: "Get eligible electronics delivered in as little as 30 minutes." },
  { Icon: ShieldCheck, title: "TRUSTED", desc: "Products sourced from participating retailers and authorized sellers." },
  { Icon: MapPinned, title: "NEARBY", desc: "Inventory from nearby retail partners close to you." },
  { Icon: Wrench, title: "COMPLETE", desc: "Delivery, installation and support for eligible products." },
];

export default function WhyTechrush() {
  return (
    <section className="px-4 py-16 md:px-6 md:py-20">
      <div className="mx-auto max-w-7xl">
        <h2 className="mb-10 text-center text-2xl font-extrabold tracking-tight text-white md:text-3xl">Why TECHRUSH?</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-5">
          {cards.map(({ Icon, title, desc }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 transition hover:-translate-y-1 hover:border-rush/40 md:p-6"
            >
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-rush-gradient/15">
                <Icon className="h-5 w-5 text-rush-cyan" />
              </div>
              <h3 className="mb-1.5 text-sm font-bold tracking-wide text-white">{title}</h3>
              <p className="text-xs leading-relaxed text-white/50">{desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
