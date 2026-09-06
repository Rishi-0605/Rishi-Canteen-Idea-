"use client";

import Link from "next/link";
import { Minus, Plus, ShoppingBag, Trash2, Zap, BookmarkPlus, ArrowRight } from "lucide-react";
import { cartTotals, useCartStore } from "@/lib/store/cartStore";
import { getProduct } from "@/lib/data/products";
import { estimateDeliveryMinutes, formatINR, formatMinutes } from "@/lib/utils";
import ProductVisual from "@/components/ui/ProductVisual";
import { useToastStore } from "@/lib/store/toastStore";

export default function CartPage() {
  const items = useCartStore((s) => s.items);
  const setQuantity = useCartStore((s) => s.setQuantity);
  const remove = useCartStore((s) => s.remove);
  const saveForLater = useCartStore((s) => s.saveForLater);
  const moveToCart = useCartStore((s) => s.moveToCart);
  const push = useToastStore((s) => s.push);

  const active = items.filter((i) => !i.savedForLater);
  const saved = items.filter((i) => i.savedForLater);
  const totals = cartTotals(items);

  if (items.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center gap-4 px-4 py-24 text-center">
        <ShoppingBag className="h-14 w-14 text-white/20" />
        <h1 className="text-2xl font-bold text-white">YOUR CART IS WAITING.</h1>
        <p className="text-sm text-white/50">Find something worth rushing home for.</p>
        <Link href="/products" className="focus-ring rounded-full bg-rush-gradient px-7 py-3 text-sm font-bold text-white shadow-glow-sm">
          SHOP NOW
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 md:px-6">
      <h1 className="mb-6 text-2xl font-extrabold tracking-tight text-white">Your Cart</h1>
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-4">
          {active.map((item) => {
            const product = getProduct(item.productId);
            if (!product) return null;
            const eta = estimateDeliveryMinutes(product.size, product.retailers[0]?.distanceKm ?? 3, item.quantity);
            return (
              <div key={item.productId} className="flex gap-4 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                <Link href={`/products/${product.id}`}>
                  <ProductVisual category={product.category} seed={product.id} className="h-24 w-24 shrink-0" iconClassName="h-10 w-10" />
                </Link>
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <Link href={`/products/${product.id}`} className="focus-ring font-semibold text-white hover:text-rush-cyan">
                        {product.name}
                      </Link>
                      <p className="text-xs text-white/40">{product.brand} · {product.color}</p>
                    </div>
                    <button onClick={() => remove(item.productId)} className="focus-ring text-white/40 hover:text-rose-400" aria-label="Remove item">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <p className="mt-2 flex items-center gap-1 text-xs font-medium text-emerald-400">
                    <Zap className="h-3.5 w-3.5" /> Delivery in {formatMinutes(eta)}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3 rounded-full border border-white/15 px-3 py-1.5">
                      <button onClick={() => setQuantity(item.productId, item.quantity - 1)} className="focus-ring text-white/70 hover:text-white" aria-label="Decrease quantity">
                        <Minus className="h-3.5 w-3.5" />
                      </button>
                      <span className="w-5 text-center text-sm font-semibold text-white">{item.quantity}</span>
                      <button onClick={() => setQuantity(item.productId, item.quantity + 1)} className="focus-ring text-white/70 hover:text-white" aria-label="Increase quantity">
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => {
                          saveForLater(item.productId);
                          push("Saved for later", "success");
                        }}
                        className="focus-ring flex items-center gap-1 text-xs font-medium text-white/50 hover:text-white"
                      >
                        <BookmarkPlus className="h-3.5 w-3.5" /> Save for later
                      </button>
                      <span className="text-base font-bold text-white">{formatINR(product.price * item.quantity)}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {saved.length > 0 && (
            <div className="mt-8">
              <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-white/50">Saved for later ({saved.length})</h2>
              <div className="space-y-3">
                {saved.map((item) => {
                  const product = getProduct(item.productId);
                  if (!product) return null;
                  return (
                    <div key={item.productId} className="flex items-center gap-4 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-3">
                      <ProductVisual category={product.category} seed={product.id} className="h-14 w-14 shrink-0" iconClassName="h-6 w-6" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">{product.name}</p>
                        <p className="text-xs text-white/40">{formatINR(product.price)}</p>
                      </div>
                      <button onClick={() => moveToCart(item.productId)} className="focus-ring rounded-full border border-white/15 px-3 py-1.5 text-xs font-semibold text-white hover:border-rush-cyan/50">
                        Move to cart
                      </button>
                      <button onClick={() => remove(item.productId)} className="focus-ring text-white/40 hover:text-rose-400" aria-label="Remove item">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="h-fit rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5">
          <h2 className="mb-4 text-sm font-bold uppercase tracking-wide text-white/50">Order Summary</h2>
          <div className="space-y-2 text-sm">
            <Row label={`Subtotal (${totals.itemCount} items)`} value={formatINR(totals.subtotal)} />
            <Row label="Delivery fee" value={totals.deliveryFee === 0 ? "FREE" : formatINR(totals.deliveryFee)} />
            <Row label="Platform fee" value={formatINR(totals.platformFee)} />
            {totals.discount > 0 && <Row label="Discount" value={`− ${formatINR(totals.discount)}`} highlight />}
            <div className="my-2 border-t border-white/10" />
            <Row label="Total" value={formatINR(totals.total)} bold />
          </div>
          <Link
            href="/checkout"
            className="focus-ring mt-5 flex w-full items-center justify-center gap-2 rounded-full bg-rush-gradient py-3.5 text-sm font-bold text-white shadow-glow-sm transition hover:brightness-110"
          >
            PROCEED TO CHECKOUT <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, bold, highlight }: { label: string; value: string; bold?: boolean; highlight?: boolean }) {
  return (
    <div className={`flex justify-between ${bold ? "text-base font-bold text-white" : "text-white/60"} ${highlight ? "text-emerald-400" : ""}`}>
      <span>{label}</span>
      <span>{value}</span>
    </div>
  );
}
