"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { Minus, Plus, ShoppingBag, Trash2, X, Zap } from "lucide-react";
import { useUiStore } from "@/lib/store/uiStore";
import { cartTotals, useCartStore } from "@/lib/store/cartStore";
import { getProduct } from "@/lib/data/products";
import { estimateDeliveryMinutes, formatINR, formatMinutes } from "@/lib/utils";
import ProductVisual from "@/components/ui/ProductVisual";

export default function CartDrawer() {
  const open = useUiStore((s) => s.cartDrawerOpen);
  const close = useUiStore((s) => s.closeCartDrawer);
  const items = useCartStore((s) => s.items.filter((i) => !i.savedForLater));
  const setQuantity = useCartStore((s) => s.setQuantity);
  const remove = useCartStore((s) => s.remove);
  const totals = cartTotals(items);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[85] bg-black/70 backdrop-blur-sm"
            onClick={close}
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="fixed right-0 top-0 z-[86] flex h-full w-full max-w-md flex-col border-l border-white/10 bg-navy-900"
            role="dialog"
            aria-label="Shopping cart"
          >
            <div className="flex items-center justify-between border-b border-white/10 p-5">
              <h2 className="flex items-center gap-2 text-lg font-bold text-white">
                <ShoppingBag className="h-5 w-5 text-rush-cyan" /> Your Cart
              </h2>
              <button onClick={close} className="focus-ring rounded-full p-1.5 hover:bg-white/10" aria-label="Close cart">
                <X className="h-5 w-5" />
              </button>
            </div>

            {items.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 px-8 text-center">
                <ShoppingBag className="h-12 w-12 text-white/20" />
                <p className="text-lg font-bold text-white">YOUR CART IS WAITING.</p>
                <p className="text-sm text-white/50">Find something worth rushing home for.</p>
                <Link
                  href="/products"
                  onClick={close}
                  className="focus-ring mt-2 rounded-full bg-rush-gradient px-6 py-2.5 text-sm font-semibold text-white shadow-glow-sm"
                >
                  SHOP NOW
                </Link>
              </div>
            ) : (
              <>
                <div className="flex-1 space-y-4 overflow-y-auto p-5">
                  {items.map((item) => {
                    const product = getProduct(item.productId);
                    if (!product) return null;
                    const eta = estimateDeliveryMinutes(product.size, product.retailers[0]?.distanceKm ?? 3, item.quantity);
                    return (
                      <div key={item.productId} className="flex gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
                        <ProductVisual category={product.category} seed={product.id} className="h-16 w-16" iconClassName="h-7 w-7" />
                        <div className="flex-1 min-w-0">
                          <Link href={`/products/${product.id}`} onClick={close} className="focus-ring line-clamp-1 text-sm font-semibold text-white hover:text-rush-cyan">
                            {product.name}
                          </Link>
                          <p className="mt-0.5 text-sm font-bold text-white">{formatINR(product.price * item.quantity)}</p>
                          <p className="mt-0.5 flex items-center gap-1 text-xs text-emerald-400">
                            <Zap className="h-3 w-3" /> {formatMinutes(eta)}
                          </p>
                          <div className="mt-2 flex items-center justify-between">
                            <div className="flex items-center gap-2 rounded-full border border-white/10 px-2 py-1">
                              <button
                                onClick={() => setQuantity(item.productId, item.quantity - 1)}
                                className="focus-ring text-white/70 hover:text-white"
                                aria-label="Decrease quantity"
                              >
                                <Minus className="h-3.5 w-3.5" />
                              </button>
                              <span className="w-4 text-center text-xs font-semibold text-white">{item.quantity}</span>
                              <button
                                onClick={() => setQuantity(item.productId, item.quantity + 1)}
                                className="focus-ring text-white/70 hover:text-white"
                                aria-label="Increase quantity"
                              >
                                <Plus className="h-3.5 w-3.5" />
                              </button>
                            </div>
                            <button
                              onClick={() => remove(item.productId)}
                              className="focus-ring text-white/40 hover:text-rose-400"
                              aria-label={`Remove ${product.name}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="border-t border-white/10 p-5">
                  <div className="mb-3 space-y-1.5 text-sm">
                    <div className="flex justify-between text-white/60">
                      <span>Subtotal</span>
                      <span>{formatINR(totals.subtotal)}</span>
                    </div>
                    <div className="flex justify-between text-white/60">
                      <span>Delivery fee</span>
                      <span>{totals.deliveryFee === 0 ? "FREE" : formatINR(totals.deliveryFee)}</span>
                    </div>
                    <div className="flex justify-between font-bold text-white">
                      <span>Total</span>
                      <span>{formatINR(totals.total)}</span>
                    </div>
                  </div>
                  <Link
                    href="/checkout"
                    onClick={close}
                    className="focus-ring block w-full rounded-full bg-rush-gradient py-3 text-center text-sm font-bold text-white shadow-glow-sm transition hover:brightness-110"
                  >
                    PROCEED TO CHECKOUT
                  </Link>
                  <Link
                    href="/cart"
                    onClick={close}
                    className="focus-ring mt-2 block text-center text-xs font-medium text-white/50 hover:text-white"
                  >
                    View full cart
                  </Link>
                </div>
              </>
            )}
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
