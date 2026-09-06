"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search as SearchIcon } from "lucide-react";
import { searchProducts } from "@/lib/data/products";
import ProductCard from "@/components/product/ProductCard";
import { ProductGridSkeleton } from "@/components/ui/Skeletons";

const trending = ["iPhone 17", "Gaming laptop", "Smart TV", "Earbuds", "Refrigerator", "PlayStation"];

export default function SearchClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") ?? "";
  const [query, setQuery] = useState(initialQ);
  const [loading, setLoading] = useState(Boolean(initialQ));

  useEffect(() => {
    setQuery(initialQ);
  }, [initialQ]);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    const t = setTimeout(() => setLoading(false), 300);
    return () => clearTimeout(t);
  }, [query]);

  function submit(q: string) {
    router.push(`/search?q=${encodeURIComponent(q)}`);
  }

  const results = query.trim() ? searchProducts(query) : [];

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:px-6">
      <div className="relative mb-6">
        <SearchIcon className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit(query)}
          placeholder="Search phones, laptops, TVs & more…"
          className="focus-ring w-full rounded-full border border-white/10 bg-white/5 py-3.5 pl-11 pr-4 text-sm text-white placeholder:text-white/40"
        />
      </div>

      {!query.trim() && (
        <div>
          <h2 className="mb-3 text-xs font-bold uppercase tracking-wider text-white/40">Trending searches</h2>
          <div className="flex flex-wrap gap-2">
            {trending.map((t) => (
              <button
                key={t}
                onClick={() => submit(t)}
                className="focus-ring rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-white/70 hover:border-rush-cyan/40 hover:text-white"
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      )}

      {query.trim() && (
        <>
          <p className="mb-4 text-sm text-white/50">
            {loading ? "Searching…" : `${results.length} results for "${query}"`}
          </p>
          {loading ? (
            <ProductGridSkeleton count={6} />
          ) : results.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-16 text-center">
              <p className="text-lg font-bold text-white">OOPS. NO MATCHES RUSHED IN.</p>
              <p className="text-sm text-white/50">Try a different search term.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 md:gap-4">
              {results.map((p, i) => (
                <ProductCard key={p.id} product={p} index={i} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
