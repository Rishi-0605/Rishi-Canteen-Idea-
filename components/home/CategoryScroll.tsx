"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { categories } from "@/lib/data/categories";

export default function CategoryScroll() {
  return (
    <section className="px-4 py-10 md:px-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-5 flex items-end justify-between">
          <h2 className="text-xl font-bold text-white md:text-2xl">Shop by Category</h2>
          <Link href="/categories" className="focus-ring text-sm font-medium text-rush-cyan hover:underline">
            View all
          </Link>
        </div>
        <div className="no-scrollbar -mx-4 flex gap-3 overflow-x-auto px-4 pb-2 md:mx-0 md:grid md:grid-cols-6 md:gap-4 md:px-0">
          {categories.slice(0, 12).map((cat, i) => {
            return (
              <motion.div
                key={cat.slug}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: i * 0.03 }}
              >
                <Link
                  href={`/products?category=${cat.slug}`}
                  className="focus-ring group flex w-24 shrink-0 flex-col items-center gap-2 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 text-center transition hover:-translate-y-1 hover:border-rush/40 hover:bg-white/[0.06] md:w-auto"
                >
                  <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-rush-gradient/10 text-2xl transition group-hover:scale-110" aria-hidden="true">
                    {cat.emoji}
                  </span>
                  <span className="text-xs font-semibold leading-tight text-white/80">{cat.name}</span>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
