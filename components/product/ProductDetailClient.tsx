"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Star, Heart, Zap, ShieldCheck, RotateCcw, MapPin, ChevronDown, Wrench, Store, Bike, Home as HomeIcon,
  CheckCircle2, CreditCard,
} from "lucide-react";
import { Product } from "@/lib/types";
import { discountPercent, estimateDeliveryMinutes, formatINR, formatMinutes, timeAgo, cn } from "@/lib/utils";
import { useCartStore } from "@/lib/store/cartStore";
import { useWishlistStore } from "@/lib/store/wishlistStore";
import { useToastStore } from "@/lib/store/toastStore";
import { useLocationStore } from "@/lib/store/locationStore";
import ProductVisual from "@/components/ui/ProductVisual";
import ProductCard from "@/components/product/ProductCard";

export default function ProductDetailClient({ product, related }: { product: Product; related: Product[] }) {
  const router = useRouter();
  const add = useCartStore((s) => s.add);
  const wishlisted = useWishlistStore((s) => s.has(product.id));
  const toggleWishlist = useWishlistStore((s) => s.toggle);
  const push = useToastStore((s) => s.push);
  const location = useLocationStore((s) => s.location);

  const [qty, setQty] = useState(1);
  const [tab, setTab] = useState<"specs" | "reviews" | "box">("specs");
  const [howOpen, setHowOpen] = useState(false);
  const [wantsInstall, setWantsInstall] = useState(false);

  const discount = discountPercent(product.price, product.mrp);
  const fastest = [...product.retailers].sort((a, b) => a.distanceKm - b.distanceKm)[0];
  const eta = estimateDeliveryMinutes(product.size, fastest?.distanceKm ?? 3, product.id.length);
  const outOfStock = product.retailers.every((r) => r.stock === 0);

  function handleAddToCart() {
    add(product.id, qty);
    push(`${product.name} added to cart`, "success");
  }

  function handleBuyNow() {
    add(product.id, qty);
    router.push("/checkout");
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-6">
      <nav className="mb-6 text-xs text-white/40">
        <Link href="/" className="hover:text-white">Home</Link> /{" "}
        <Link href={`/products?category=${product.category}`} className="hover:text-white capitalize">{product.category.replace("-", " ")}</Link> /{" "}
        <span className="text-white/60">{product.name}</span>
      </nav>

      <div className="grid grid-cols-1 gap-10 lg:grid-cols-2">
        {/* Gallery */}
        <div>
          <div className="relative aspect-square overflow-hidden rounded-3xl border border-white/10">
            <ProductVisual category={product.category} seed={product.id} className="h-full w-full" iconClassName="h-28 w-28" />
            {discount > 0 && (
              <span className="absolute left-4 top-4 rounded-md bg-emerald-500/90 px-2 py-1 text-xs font-bold text-white">
                {discount}% OFF
              </span>
            )}
          </div>
          <div className="mt-3 flex gap-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 w-16 overflow-hidden rounded-xl border border-white/10 opacity-70 transition hover:opacity-100">
                <ProductVisual category={product.category} seed={product.id + i} className="h-full w-full" iconClassName="h-6 w-6" />
              </div>
            ))}
          </div>
        </div>

        {/* Info */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-white/40">{product.brand}</p>
          <h1 className="mt-1 text-2xl font-extrabold text-white md:text-3xl">{product.name}</h1>
          <div className="mt-2 flex items-center gap-3 text-sm">
            <span className="flex items-center gap-1 rounded-md bg-emerald-500/15 px-2 py-0.5 font-semibold text-emerald-400">
              <Star className="h-3.5 w-3.5 fill-emerald-400" /> {product.rating}
            </span>
            <span className="text-white/50">{product.reviewCount} ratings</span>
            <span className="text-white/30">·</span>
            <span className="text-white/50">{product.color}</span>
          </div>

          <div className="mt-4 flex items-baseline gap-3">
            <span className="text-3xl font-extrabold text-white">{formatINR(product.price)}</span>
            {discount > 0 && (
              <>
                <span className="text-base text-white/40 line-through">{formatINR(product.mrp)}</span>
                <span className="text-sm font-semibold text-emerald-400">{discount}% off</span>
              </>
            )}
          </div>
          {product.emiFrom && (
            <p className="mt-1.5 flex items-center gap-1.5 text-xs text-white/50">
              <CreditCard className="h-3.5 w-3.5" /> EMI from {formatINR(product.emiFrom)}/month available
            </p>
          )}

          {/* Available near you */}
          <div className="mt-5 rounded-2xl border border-rush/30 bg-rush/10 p-4">
            <p className="flex items-center gap-1.5 text-sm font-bold text-rush-cyan">
              <Zap className="h-4 w-4" /> AVAILABLE NEAR YOU
            </p>
            {outOfStock ? (
              <p className="mt-1 text-sm text-white/70">This item is currently unavailable nearby. Check back soon.</p>
            ) : (
              <>
                <p className="mt-1 text-sm text-white/70">
                  Available at <span className="font-semibold text-white">{fastest.name}</span> ({fastest.type}), {fastest.distanceKm} km away
                </p>
                <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-white">
                  <MapPin className="h-3.5 w-3.5 text-rush-cyan" />
                  Estimated delivery: {formatMinutes(eta)}
                  {location && <span className="font-normal text-white/50"> to {location.city}</span>}
                </p>
              </>
            )}

            <button
              onClick={() => setHowOpen((v) => !v)}
              className="focus-ring mt-3 flex w-full items-center justify-between text-xs font-semibold text-white/70 hover:text-white"
            >
              HOW YOUR ORDER REACHES YOU
              <ChevronDown className={cn("h-4 w-4 transition", howOpen && "rotate-180")} />
            </button>
            {howOpen && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} className="mt-3 overflow-hidden">
                <div className="flex items-center justify-between text-center text-[11px] text-white/60">
                  {[
                    { Icon: Store, label: "Nearby inventory" },
                    { Icon: CheckCircle2, label: "Pick-up" },
                    { Icon: Bike, label: "Delivery" },
                    { Icon: HomeIcon, label: "Your doorstep" },
                  ].map(({ Icon, label }) => (
                    <div key={label} className="flex flex-1 flex-col items-center gap-1">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-navy-800">
                        <Icon className="h-4 w-4 text-rush-cyan" />
                      </div>
                      <span>{label}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {product.installationAvailable && (
            <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                <Zap className="mx-auto mb-1 h-4 w-4 text-rush-cyan" />
                <p className="font-semibold text-white">{formatMinutes(eta)}</p>
                <p className="text-white/40">Delivery</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                <Wrench className="mx-auto mb-1 h-4 w-4 text-rush-cyan" />
                <p className="font-semibold text-white">Available</p>
                <p className="text-white/40">Installation</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                <ShieldCheck className="mx-auto mb-1 h-4 w-4 text-rush-cyan" />
                <p className="font-semibold text-white">1 Year</p>
                <p className="text-white/40">Warranty</p>
              </div>
            </div>
          )}

          {product.installationAvailable && (
            <label className="mt-4 flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-white/[0.02] p-3 text-sm text-white/70">
              <input
                type="checkbox"
                checked={wantsInstall}
                onChange={(e) => setWantsInstall(e.target.checked)}
                className="h-4 w-4 accent-rush"
              />
              Request professional installation for this product
            </label>
          )}

          <div className="mt-5 flex items-center gap-3">
            <div className="flex items-center gap-3 rounded-full border border-white/15 px-3 py-2">
              <button onClick={() => setQty((q) => Math.max(1, q - 1))} className="focus-ring text-white/70 hover:text-white" aria-label="Decrease quantity">−</button>
              <span className="w-5 text-center text-sm font-semibold text-white">{qty}</span>
              <button onClick={() => setQty((q) => q + 1)} className="focus-ring text-white/70 hover:text-white" aria-label="Increase quantity">+</button>
            </div>
            <button
              onClick={() => toggleWishlist(product.id)}
              className="focus-ring flex h-11 w-11 items-center justify-center rounded-full border border-white/15 text-white/70 hover:text-rush-cyan"
              aria-label="Toggle wishlist"
            >
              <Heart className={cn("h-5 w-5", wishlisted && "fill-rush-cyan text-rush-cyan")} />
            </button>
          </div>

          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <button
              disabled={outOfStock}
              onClick={handleAddToCart}
              className="focus-ring flex-1 rounded-full border border-white/15 bg-white/5 py-3.5 text-sm font-bold text-white transition hover:border-rush-cyan/50 disabled:opacity-40"
            >
              ADD TO CART
            </button>
            <button
              disabled={outOfStock}
              onClick={handleBuyNow}
              className="focus-ring flex-1 rounded-full bg-rush-gradient py-3.5 text-sm font-bold text-white shadow-glow-sm transition hover:brightness-110 disabled:opacity-40"
            >
              BUY NOW
            </button>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 text-xs text-white/60">
            <p className="flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5 text-rush-cyan" /> {product.warranty}</p>
            <p className="flex items-center gap-1.5"><RotateCcw className="h-3.5 w-3.5 text-rush-cyan" /> {product.returnPolicy}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mt-14 border-b border-white/10">
        <div className="flex gap-6 text-sm font-semibold">
          {[
            { key: "specs" as const, label: "Specifications" },
            { key: "box" as const, label: "What's in the Box" },
            { key: "reviews" as const, label: `Reviews (${product.reviews.length})` },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={cn(
                "focus-ring border-b-2 pb-3 transition",
                tab === t.key ? "border-rush-cyan text-white" : "border-transparent text-white/40 hover:text-white/70"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="py-8">
        {tab === "specs" && (
          <div className="grid grid-cols-1 gap-x-10 gap-y-3 sm:grid-cols-2">
            <p className="col-span-full text-sm leading-relaxed text-white/60">{product.description}</p>
            {product.specs.map((s) => (
              <div key={s.label} className="flex justify-between border-b border-white/[0.06] py-2 text-sm">
                <span className="text-white/40">{s.label}</span>
                <span className="font-medium text-white">{s.value}</span>
              </div>
            ))}
          </div>
        )}
        {tab === "box" && (
          <ul className="space-y-2">
            {product.whatsInTheBox.map((item) => (
              <li key={item} className="flex items-center gap-2 text-sm text-white/70">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" /> {item}
              </li>
            ))}
          </ul>
        )}
        {tab === "reviews" && (
          <div className="space-y-5">
            {product.reviews.map((r) => (
              <div key={r.id} className="border-b border-white/[0.06] pb-5">
                <div className="mb-1 flex items-center gap-2">
                  <div className="flex items-center gap-0.5">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className={cn("h-3.5 w-3.5", i < r.rating ? "fill-amber-400 text-amber-400" : "text-white/15")} />
                    ))}
                  </div>
                  <span className="text-sm font-semibold text-white">{r.title}</span>
                </div>
                <p className="text-sm text-white/60">{r.body}</p>
                <p className="mt-1.5 text-xs text-white/35">
                  {r.author} {r.verified && "· Verified Purchase"} · {timeAgo(r.date)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {related.length > 0 && (
        <div className="mt-4">
          <h2 className="mb-4 text-lg font-bold text-white">You may also like</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 md:gap-4">
            {related.map((p, i) => (
              <ProductCard key={p.id} product={p} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
