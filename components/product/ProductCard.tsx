"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Heart, Plus, Star, Zap } from "lucide-react";
import { Product } from "@/lib/types";
import { discountPercent, estimateDeliveryMinutes, formatINR, formatMinutes, cn } from "@/lib/utils";
import { useCartStore } from "@/lib/store/cartStore";
import { useWishlistStore } from "@/lib/store/wishlistStore";
import { useToastStore } from "@/lib/store/toastStore";
import ProductVisual from "@/components/ui/ProductVisual";

export default function ProductCard({ product, index = 0 }: { product: Product; index?: number }) {
  const add = useCartStore((s) => s.add);
  const wishlisted = useWishlistStore((s) => s.has(product.id));
  const toggleWishlist = useWishlistStore((s) => s.toggle);
  const push = useToastStore((s) => s.push);
  const discount = discountPercent(product.price, product.mrp);
  const eta = estimateDeliveryMinutes(product.size, product.retailers[0]?.distanceKm ?? 3, index + 1);
  const outOfStock = product.retailers.every((r) => r.stock === 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.4, delay: Math.min(index, 6) * 0.04 }}
      whileHover={{ y: -4 }}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.03] shadow-card transition hover:border-rush/40"
    >
      <button
        onClick={() => {
          toggleWishlist(product.id);
          push(wishlisted ? "Removed from wishlist" : "Added to wishlist", "success");
        }}
        className="focus-ring absolute right-2.5 top-2.5 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-navy-950/60 backdrop-blur transition hover:scale-110"
        aria-label={wishlisted ? "Remove from wishlist" : "Add to wishlist"}
      >
        <motion.span animate={wishlisted ? { scale: [1, 1.3, 1] } : {}} transition={{ duration: 0.3 }}>
          <Heart className={cn("h-4 w-4", wishlisted ? "fill-rush-cyan text-rush-cyan" : "text-white/70")} />
        </motion.span>
      </button>

      <Link href={`/products/${product.id}`} className="focus-ring block">
        <div className="relative aspect-square p-6">
          <ProductVisual category={product.category} seed={product.id} className="h-full w-full" iconClassName="h-14 w-14" />
          {discount > 0 && (
            <span className="absolute left-2.5 top-2.5 rounded-md bg-emerald-500/90 px-1.5 py-0.5 text-[11px] font-bold text-white">
              {discount}% OFF
            </span>
          )}
          {outOfStock && (
            <span className="absolute inset-x-2.5 bottom-2.5 rounded-md bg-black/70 px-1.5 py-1 text-center text-[10px] font-semibold text-white">
              Currently unavailable nearby
            </span>
          )}
        </div>
      </Link>

      <div className="flex flex-1 flex-col gap-1.5 p-4 pt-0">
        <p className="text-[11px] font-medium uppercase tracking-wide text-white/40">{product.brand}</p>
        <Link href={`/products/${product.id}`} className="focus-ring line-clamp-2 text-sm font-semibold text-white hover:text-rush-cyan">
          {product.name}
        </Link>
        <div className="flex items-center gap-1 text-xs text-white/50">
          <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
          <span>{product.rating}</span>
          <span className="text-white/30">({product.reviewCount})</span>
        </div>
        <div className="mt-0.5 flex items-baseline gap-2">
          <span className="text-base font-bold text-white">{formatINR(product.price)}</span>
          {discount > 0 && <span className="text-xs text-white/40 line-through">{formatINR(product.mrp)}</span>}
        </div>
        <p className="flex items-center gap-1 text-xs font-medium text-emerald-400">
          <Zap className="h-3.5 w-3.5" /> Delivery in {formatMinutes(eta)}
        </p>

        <button
          disabled={outOfStock}
          onClick={() => {
            add(product.id);
            push(`${product.name} added to cart`, "success");
          }}
          className="focus-ring mt-2 flex items-center justify-center gap-1.5 rounded-full bg-white/[0.06] py-2 text-xs font-semibold text-white transition hover:bg-rush-gradient disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white/[0.06]"
        >
          <Plus className="h-3.5 w-3.5" /> Add to Cart
        </button>
      </div>
    </motion.div>
  );
}
