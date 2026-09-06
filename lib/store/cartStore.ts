"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { CartItem } from "@/lib/types";
import { getProduct } from "@/lib/data/products";

interface CartState {
  items: CartItem[];
  lastAdded: string | null;
  add: (productId: string, quantity?: number) => void;
  remove: (productId: string) => void;
  setQuantity: (productId: string, quantity: number) => void;
  saveForLater: (productId: string) => void;
  moveToCart: (productId: string) => void;
  clear: () => void;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      lastAdded: null,
      add: (productId, quantity = 1) => {
        const items = [...get().items];
        const existing = items.find((i) => i.productId === productId && !i.savedForLater);
        if (existing) {
          existing.quantity += quantity;
        } else {
          items.push({ productId, quantity });
        }
        set({ items, lastAdded: productId });
        setTimeout(() => set({ lastAdded: null }), 1200);
      },
      remove: (productId) => set({ items: get().items.filter((i) => i.productId !== productId) }),
      setQuantity: (productId, quantity) => {
        if (quantity <= 0) {
          set({ items: get().items.filter((i) => i.productId !== productId) });
          return;
        }
        set({ items: get().items.map((i) => (i.productId === productId ? { ...i, quantity } : i)) });
      },
      saveForLater: (productId) =>
        set({ items: get().items.map((i) => (i.productId === productId ? { ...i, savedForLater: true } : i)) }),
      moveToCart: (productId) =>
        set({ items: get().items.map((i) => (i.productId === productId ? { ...i, savedForLater: false } : i)) }),
      clear: () => set({ items: [] }),
    }),
    { name: "techrush-cart" }
  )
);

export function cartTotals(items: CartItem[]) {
  const active = items.filter((i) => !i.savedForLater);
  let subtotal = 0;
  let totalMrp = 0;
  let itemCount = 0;
  for (const item of active) {
    const product = getProduct(item.productId);
    if (!product) continue;
    subtotal += product.price * item.quantity;
    totalMrp += product.mrp * item.quantity;
    itemCount += item.quantity;
  }
  const discount = Math.max(0, totalMrp - subtotal);
  const deliveryFee = subtotal === 0 ? 0 : subtotal >= 999 ? 0 : 49;
  const platformFee = subtotal === 0 ? 0 : 9;
  const total = subtotal + deliveryFee + platformFee;
  return { subtotal, totalMrp, discount, deliveryFee, platformFee, total, itemCount };
}
