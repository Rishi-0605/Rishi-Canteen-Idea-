"use client";

import Link from "next/link";
import {
  User, MapPin, Package, Heart, CreditCard, Bell, HelpCircle, LogOut, ChevronRight, LogIn,
} from "lucide-react";
import { useUserStore } from "@/lib/store/userStore";
import { useWishlistStore } from "@/lib/store/wishlistStore";
import { useToastStore } from "@/lib/store/toastStore";

export default function ProfilePage() {
  const user = useUserStore((s) => s.user);
  const addresses = useUserStore((s) => s.addresses);
  const orders = useUserStore((s) => s.orders);
  const logout = useUserStore((s) => s.logout);
  const wishlistCount = useWishlistStore((s) => s.ids.length);
  const push = useToastStore((s) => s.push);

  if (!user) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-4 px-4 py-24 text-center">
        <User className="h-14 w-14 text-white/20" />
        <h1 className="text-xl font-bold text-white">You&apos;re not signed in</h1>
        <p className="text-sm text-white/50">Log in to view your profile, orders and saved addresses.</p>
        <Link href="/login" className="focus-ring flex items-center gap-2 rounded-full bg-rush-gradient px-6 py-3 text-sm font-bold text-white shadow-glow-sm">
          <LogIn className="h-4 w-4" /> Log in
        </Link>
      </div>
    );
  }

  const menu = [
    { icon: Package, label: "My Orders", value: `${orders.length}`, href: "/orders" },
    { icon: Heart, label: "Wishlist", value: `${wishlistCount}`, href: "/wishlist" },
    { icon: MapPin, label: "Saved Addresses", value: `${addresses.length}`, href: "/profile#addresses" },
    { icon: CreditCard, label: "Payment Methods", value: "", href: "/profile#payments" },
    { icon: Bell, label: "Notifications", value: "", href: "/profile#notifications" },
    { icon: HelpCircle, label: "Support", value: "", href: "/support" },
  ];

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-6">
      <div className="mb-8 flex items-center gap-4 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-rush-gradient text-lg font-bold text-white">
          {user.name.charAt(0).toUpperCase()}
        </div>
        <div>
          <p className="text-lg font-bold text-white">{user.name}</p>
          <p className="text-sm text-white/50">{user.email}</p>
          <p className="text-sm text-white/50">{user.phone}</p>
        </div>
      </div>

      <div className="space-y-2">
        {menu.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className="focus-ring flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3.5 transition hover:border-rush/40"
          >
            <item.icon className="h-4.5 w-4.5 text-rush-cyan" />
            <span className="flex-1 text-sm font-medium text-white">{item.label}</span>
            {item.value && <span className="text-xs text-white/40">{item.value}</span>}
            <ChevronRight className="h-4 w-4 text-white/30" />
          </Link>
        ))}
      </div>

      <div id="addresses" className="mt-8">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-white/50">Saved Addresses</h2>
        <div className="space-y-2">
          {addresses.map((addr) => (
            <div key={addr.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5 text-sm">
              <p className="font-semibold text-white">{addr.label}{addr.isDefault && <span className="ml-2 rounded-full bg-rush/15 px-2 py-0.5 text-[10px] text-rush-cyan">DEFAULT</span>}</p>
              <p className="text-xs text-white/50">{addr.line1}, {addr.city}, {addr.state} - {addr.pincode}</p>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={() => {
          logout();
          push("Logged out successfully", "info");
        }}
        className="focus-ring mt-8 flex w-full items-center justify-center gap-2 rounded-full border border-rose-500/30 bg-rose-500/10 py-3 text-sm font-semibold text-rose-300 hover:bg-rose-500/20"
      >
        <LogOut className="h-4 w-4" /> Log out
      </button>
    </div>
  );
}
