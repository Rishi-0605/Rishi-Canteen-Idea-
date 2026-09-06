"use client";

import { useMemo, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { SlidersHorizontal, X, ChevronDown, Zap } from "lucide-react";
import { products as allProducts } from "@/lib/data/products";
import { categories } from "@/lib/data/categories";
import { Product } from "@/lib/types";
import { discountPercent, estimateDeliveryMinutes, cn } from "@/lib/utils";
import ProductCard from "@/components/product/ProductCard";
import { ProductGridSkeleton } from "@/components/ui/Skeletons";

type SortKey = "relevance" | "price-asc" | "price-desc" | "rating" | "delivery" | "deals";

const sortOptions: { key: SortKey; label: string }[] = [
  { key: "relevance", label: "Relevance" },
  { key: "price-asc", label: "Price: Low → High" },
  { key: "price-desc", label: "Price: High → Low" },
  { key: "rating", label: "Rating" },
  { key: "delivery", label: "Fastest delivery" },
  { key: "deals", label: "Best deals" },
];

const priceBuckets = [
  { label: "Under ₹5,000", min: 0, max: 5000 },
  { label: "₹5,000 – ₹25,000", min: 5000, max: 25000 },
  { label: "₹25,000 – ₹75,000", min: 25000, max: 75000 },
  { label: "Above ₹75,000", min: 75000, max: Infinity },
];

export default function ProductListingClient() {
  const searchParams = useSearchParams();
  const initialCategory = searchParams.get("category") ?? "";

  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState<SortKey>("relevance");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string[]>(initialCategory ? [initialCategory] : []);
  const [brandFilter, setBrandFilter] = useState<string[]>([]);
  const [priceBucket, setPriceBucket] = useState<number | null>(null);
  const [minRating, setMinRating] = useState(0);
  const [maxDelivery, setMaxDelivery] = useState<number | null>(null);
  const [inStockOnly, setInStockOnly] = useState(false);
  const [minDiscount, setMinDiscount] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 450);
    return () => clearTimeout(t);
  }, []);

  const brands = useMemo(() => Array.from(new Set(allProducts.map((p) => p.brand))).sort(), []);

  const withMeta = useMemo(
    () =>
      allProducts.map((p, i) => ({
        product: p,
        discount: discountPercent(p.price, p.mrp),
        eta: estimateDeliveryMinutes(p.size, p.retailers[0]?.distanceKm ?? 3, i + 1),
        inStock: p.retailers.some((r) => r.stock > 0),
      })),
    []
  );

  const filtered = useMemo(() => {
    let list = withMeta;
    if (categoryFilter.length) list = list.filter((x) => categoryFilter.includes(x.product.category));
    if (brandFilter.length) list = list.filter((x) => brandFilter.includes(x.product.brand));
    if (priceBucket !== null) {
      const b = priceBuckets[priceBucket];
      list = list.filter((x) => x.product.price >= b.min && x.product.price < b.max);
    }
    if (minRating > 0) list = list.filter((x) => x.product.rating >= minRating);
    if (maxDelivery !== null) list = list.filter((x) => x.eta <= maxDelivery);
    if (inStockOnly) list = list.filter((x) => x.inStock);
    if (minDiscount > 0) list = list.filter((x) => x.discount >= minDiscount);

    const sorted = [...list];
    switch (sort) {
      case "price-asc":
        sorted.sort((a, b) => a.product.price - b.product.price);
        break;
      case "price-desc":
        sorted.sort((a, b) => b.product.price - a.product.price);
        break;
      case "rating":
        sorted.sort((a, b) => b.product.rating - a.product.rating);
        break;
      case "delivery":
        sorted.sort((a, b) => a.eta - b.eta);
        break;
      case "deals":
        sorted.sort((a, b) => b.discount - a.discount);
        break;
      default:
        break;
    }
    return sorted.map((x) => x.product);
  }, [withMeta, categoryFilter, brandFilter, priceBucket, minRating, maxDelivery, inStockOnly, minDiscount, sort]);

  function toggle(list: string[], value: string, setter: (v: string[]) => void) {
    setter(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  }

  function clearAll() {
    setCategoryFilter([]);
    setBrandFilter([]);
    setPriceBucket(null);
    setMinRating(0);
    setMaxDelivery(null);
    setInStockOnly(false);
    setMinDiscount(0);
  }

  const activeCount =
    categoryFilter.length +
    brandFilter.length +
    (priceBucket !== null ? 1 : 0) +
    (minRating > 0 ? 1 : 0) +
    (maxDelivery !== null ? 1 : 0) +
    (inStockOnly ? 1 : 0) +
    (minDiscount > 0 ? 1 : 0);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white">All Products</h1>
          <p className="text-sm text-white/50">{filtered.length} products found</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFiltersOpen(true)}
            className="focus-ring flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/80 hover:border-rush-cyan/40 lg:hidden"
          >
            <SlidersHorizontal className="h-4 w-4" /> Filters {activeCount > 0 && `(${activeCount})`}
          </button>
          <div className="relative">
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortKey)}
              className="focus-ring appearance-none rounded-full border border-white/10 bg-white/5 py-2 pl-4 pr-9 text-sm font-medium text-white/80 hover:border-rush-cyan/40"
              aria-label="Sort products"
            >
              {sortOptions.map((o) => (
                <option key={o.key} value={o.key} className="bg-navy-900">
                  Sort: {o.label}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/50" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[240px_1fr]">
        <aside className="hidden lg:block">
          <FilterPanel
            {...{
              categoryFilter, setCategoryFilter: (v) => setCategoryFilter(v), toggle, brands, brandFilter, setBrandFilter,
              priceBucket, setPriceBucket, minRating, setMinRating, maxDelivery, setMaxDelivery, inStockOnly, setInStockOnly,
              minDiscount, setMinDiscount, clearAll, activeCount,
            }}
          />
        </aside>

        <AnimatePresence>
          {filtersOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[70] flex bg-black/70 backdrop-blur-sm lg:hidden"
              onClick={() => setFiltersOpen(false)}
            >
              <motion.div
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ type: "spring", damping: 28, stiffness: 320 }}
                onClick={(e) => e.stopPropagation()}
                className="h-full w-full max-w-xs overflow-y-auto bg-navy-900 p-5"
              >
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-bold text-white">Filters</h2>
                  <button onClick={() => setFiltersOpen(false)} className="focus-ring rounded-full p-1.5 hover:bg-white/10" aria-label="Close filters">
                    <X className="h-5 w-5" />
                  </button>
                </div>
                <FilterPanel
                  {...{
                    categoryFilter, setCategoryFilter: (v) => setCategoryFilter(v), toggle, brands, brandFilter, setBrandFilter,
                    priceBucket, setPriceBucket, minRating, setMinRating, maxDelivery, setMaxDelivery, inStockOnly, setInStockOnly,
                    minDiscount, setMinDiscount, clearAll, activeCount,
                  }}
                />
                <button
                  onClick={() => setFiltersOpen(false)}
                  className="focus-ring mt-4 w-full rounded-full bg-rush-gradient py-3 text-sm font-bold text-white"
                >
                  Show {filtered.length} results
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <div>
          {loading ? (
            <ProductGridSkeleton count={8} />
          ) : filtered.length === 0 ? (
            <EmptyResults onClear={clearAll} />
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 md:gap-4">
              {filtered.map((p, i) => (
                <ProductCard key={p.id} product={p} index={i} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface FilterPanelProps {
  categoryFilter: string[];
  setCategoryFilter: (v: string[]) => void;
  toggle: (list: string[], value: string, setter: (v: string[]) => void) => void;
  brands: string[];
  brandFilter: string[];
  setBrandFilter: (v: string[]) => void;
  priceBucket: number | null;
  setPriceBucket: (v: number | null) => void;
  minRating: number;
  setMinRating: (v: number) => void;
  maxDelivery: number | null;
  setMaxDelivery: (v: number | null) => void;
  inStockOnly: boolean;
  setInStockOnly: (v: boolean) => void;
  minDiscount: number;
  setMinDiscount: (v: number) => void;
  clearAll: () => void;
  activeCount: number;
}

function FilterPanel(p: FilterPanelProps) {
  return (
    <div className="space-y-6 text-sm">
      {p.activeCount > 0 && (
        <button onClick={p.clearAll} className="focus-ring text-xs font-semibold text-rush-cyan hover:underline">
          Clear all filters
        </button>
      )}

      <FilterGroup title="Category">
        {categories.map((c) => (
          <CheckRow
            key={c.slug}
            label={`${c.emoji} ${c.name}`}
            checked={p.categoryFilter.includes(c.slug)}
            onChange={() => p.toggle(p.categoryFilter, c.slug, p.setCategoryFilter)}
          />
        ))}
      </FilterGroup>

      <FilterGroup title="Brand">
        {p.brands.map((b) => (
          <CheckRow key={b} label={b} checked={p.brandFilter.includes(b)} onChange={() => p.toggle(p.brandFilter, b, p.setBrandFilter)} />
        ))}
      </FilterGroup>

      <FilterGroup title="Price">
        {priceBuckets.map((b, i) => (
          <CheckRow
            key={b.label}
            label={b.label}
            checked={p.priceBucket === i}
            onChange={() => p.setPriceBucket(p.priceBucket === i ? null : i)}
          />
        ))}
      </FilterGroup>

      <FilterGroup title="Delivery time">
        {[
          { label: "Under 30 min", val: 30 },
          { label: "Under 1 hour", val: 60 },
          { label: "Under 2 hours", val: 120 },
        ].map((d) => (
          <CheckRow key={d.val} label={d.label} checked={p.maxDelivery === d.val} onChange={() => p.setMaxDelivery(p.maxDelivery === d.val ? null : d.val)} />
        ))}
      </FilterGroup>

      <FilterGroup title="Rating">
        {[4, 3, 2].map((r) => (
          <CheckRow key={r} label={`${r}★ & above`} checked={p.minRating === r} onChange={() => p.setMinRating(p.minRating === r ? 0 : r)} />
        ))}
      </FilterGroup>

      <FilterGroup title="Discount">
        {[10, 20, 30].map((d) => (
          <CheckRow key={d} label={`${d}% or more`} checked={p.minDiscount === d} onChange={() => p.setMinDiscount(p.minDiscount === d ? 0 : d)} />
        ))}
      </FilterGroup>

      <FilterGroup title="Availability">
        <CheckRow label="In stock nearby" checked={p.inStockOnly} onChange={() => p.setInStockOnly(!p.inStockOnly)} />
      </FilterGroup>
    </div>
  );
}

function FilterGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-white/40">{title}</h3>
      <div className="max-h-40 space-y-1.5 overflow-y-auto pr-1">{children}</div>
    </div>
  );
}

function CheckRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-white/70 hover:text-white">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="focus-ring h-3.5 w-3.5 rounded border-white/20 bg-transparent text-rush accent-rush"
      />
      <span className="text-xs">{label}</span>
    </label>
  );
}

function EmptyResults({ onClear }: { onClear: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-white/10 bg-white/[0.02] py-20 text-center">
      <Zap className="h-10 w-10 text-white/20" />
      <p className="text-lg font-bold text-white">OOPS. THIS SEARCH JUST RUSHED OUT.</p>
      <p className="max-w-xs text-sm text-white/50">No products match your current filters nearby.</p>
      <button onClick={onClear} className="focus-ring rounded-full bg-rush-gradient px-6 py-2.5 text-sm font-semibold text-white">
        Clear filters
      </button>
    </div>
  );
}

export { priceBuckets, sortOptions };
export type { SortKey, Product };
