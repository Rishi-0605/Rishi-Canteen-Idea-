"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Store, BadgeCheck, Truck, Building2, Warehouse, ArrowRight } from "lucide-react";

const partnerCards = [
  { Icon: Store, label: "Retail Stores" },
  { Icon: BadgeCheck, label: "Authorized Dealers" },
  { Icon: Truck, label: "Distributors" },
  { Icon: Building2, label: "Brand Partners" },
  { Icon: Warehouse, label: "Warehouses" },
];

export default function PartnerSection() {
  return (
    <section className="px-4 py-16 md:px-6 md:py-20">
      <div className="mx-auto max-w-6xl rounded-3xl border border-white/[0.07] bg-gradient-to-br from-navy-800/60 to-navy-900/60 p-8 text-center md:p-14">
        <h2 className="text-2xl font-extrabold tracking-tight text-white md:text-3xl">POWERED BY LOCAL RETAIL.</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-white/55 md:text-base">
          We connect customers with nearby electronics inventory from independent stores, authorized dealers,
          distributors and brand warehouses.
        </p>

        <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-5">
          {partnerCards.map(({ Icon, label }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.06 }}
              className="flex flex-col items-center gap-2 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4"
            >
              <Icon className="h-6 w-6 text-rush-cyan" strokeWidth={1.6} />
              <span className="text-[11px] font-medium text-white/70">{label}</span>
            </motion.div>
          ))}
        </div>

        <Link
          href="/partner"
          className="focus-ring mt-9 inline-flex items-center gap-2 rounded-full bg-rush-gradient px-7 py-3.5 text-sm font-bold text-white shadow-glow-sm transition hover:brightness-110"
        >
          BECOME A RETAIL PARTNER <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}
