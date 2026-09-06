"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { Address, Order } from "@/lib/types";

interface UserProfile {
  name: string;
  email: string;
  phone: string;
}

interface UserState {
  user: UserProfile | null;
  addresses: Address[];
  orders: Order[];
  login: (user: UserProfile) => void;
  logout: () => void;
  addAddress: (address: Address) => void;
  addOrder: (order: Order) => void;
  updateOrderStatus: (orderId: string, status: Order["status"]) => void;
}

const defaultAddresses: Address[] = [
  {
    id: "addr-home",
    label: "Home",
    line1: "402, Silver Crest Apartments",
    line2: "Linking Road",
    city: "Mumbai",
    state: "Maharashtra",
    pincode: "400050",
    isDefault: true,
  },
];

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      user: null,
      addresses: defaultAddresses,
      orders: [],
      login: (user) => set({ user }),
      logout: () => set({ user: null }),
      addAddress: (address) => set({ addresses: [...get().addresses, address] }),
      addOrder: (order) => set({ orders: [order, ...get().orders] }),
      updateOrderStatus: (orderId, status) =>
        set({ orders: get().orders.map((o) => (o.id === orderId ? { ...o, status } : o)) }),
    }),
    { name: "techrush-user" }
  )
);
