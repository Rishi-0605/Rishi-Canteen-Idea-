"use client";

import Link from "next/link";
import { Heart, Trash2, ShoppingCart } from "lucide-react";
import { useWishlistStore } from "@/lib/store/wishlistStore";
import { useCartStore } from "@/lib/store/cartStore";
import { getProduct } from "@/lib/data/products";
import { discountPercent, formatINR } from "@/lib/utils";
import ProductVisual from "@/components/ui/ProductVisual";
import { useToastStore } from "@/lib/store/toastStore";

export default function WishlistPage() {
  const ids = useWishlistStore((s) => s.ids);
  const remove = useWishlistStore((s) => s.remove);
  const addToCart = useCartStore((s) => s.add);
  const push = useToastStore((s) => s.push);

  const items = ids.map((id) => getProduct(id)).filter((p): p is NonNullable<typeof p> => Boolean(p));

  if (items.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center gap-4 px-4 py-24 text-center">
        <Heart className="h-14 w-14 text-white/20" />
        <h1 className="text-2xl font-bold text-white">NOTHING SAVED YET.</h1>
        <p className="text-sm text-white/50">Tap the heart on any product to save it here.</p>
        <Link href="/products" className="focus-ring rounded-full bg-rush-gradient px-7 py-3 text-sm font-bold text-white shadow-glow-sm">
          SHOP NOW
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:px-6">
      <h1 className="mb-6 text-2xl font-extrabold tracking-tight text-white">Your Wishlist ({items.length})</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((product) => {
          const discount = discountPercent(product.price, product.mrp);
          return (
            <div key={product.id} className="flex gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
              <Link href={`/products/${product.id}`}>
                <ProductVisual category={product.category} seed={product.id} className="h-20 w-20 shrink-0" iconClassName="h-8 w-8" />
              </Link>
              <div className="flex-1">
                <Link href={`/products/${product.id}`} className="focus-ring text-sm font-semibold text-white hover:text-rush-cyan">
                  {product.name}
                </Link>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="font-bold text-white">{formatINR(product.price)}</span>
                  {discount > 0 && <span className="text-xs text-emerald-400">{discount}% off</span>}
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => {
                      addToCart(product.id);
                      remove(product.id);
                      push(`${product.name} moved to cart`, "success");
                    }}
                    className="focus-ring flex items-center gap-1.5 rounded-full bg-rush-gradient px-3 py-1.5 text-xs font-semibold text-white"
                  >
                    <ShoppingCart className="h-3.5 w-3.5" /> Move to cart
                  </button>
                  <button
                    onClick={() => remove(product.id)}
                    className="focus-ring flex items-center justify-center rounded-full border border-white/15 px-2.5 py-1.5 text-white/50 hover:text-rose-400"
                    aria-label="Remove from wishlist"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
