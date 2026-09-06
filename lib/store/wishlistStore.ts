"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface WishlistState {
  ids: string[];
  toggle: (productId: string) => void;
  remove: (productId: string) => void;
  has: (productId: string) => boolean;
}

export const useWishlistStore = create<WishlistState>()(
  persist(
    (set, get) => ({
      ids: [],
      toggle: (productId) => {
        const ids = get().ids;
        set({ ids: ids.includes(productId) ? ids.filter((id) => id !== productId) : [...ids, productId] });
      },
      remove: (productId) => set({ ids: get().ids.filter((id) => id !== productId) }),
      has: (productId) => get().ids.includes(productId),
    }),
    { name: "techrush-wishlist" }
  )
);
