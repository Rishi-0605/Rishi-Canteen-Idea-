"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { MapPin, Search, ShoppingCart, User, ChevronDown } from "lucide-react";
import Logo from "@/components/ui/Logo";
import { useLocationStore } from "@/lib/store/locationStore";
import { useCartStore } from "@/lib/store/cartStore";
import { useUiStore } from "@/lib/store/uiStore";
import { searchProducts } from "@/lib/data/products";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/categories", label: "Categories" },
  { href: "/deals", label: "Deals" },
  { href: "/products?sort=new", label: "New Arrivals" },
  { href: "/orders", label: "Track Order" },
];

export default function Navbar() {
  const router = useRouter();
  const location = useLocationStore((s) => s.location);
  const openLocationModal = useLocationStore((s) => s.openModal);
  const openCart = useUiStore((s) => s.openCartDrawer);
  const cartCount = useCartStore((s) => s.items.filter((i) => !i.savedForLater).reduce((n, i) => n + i.quantity, 0));
  const bump = useCartStore((s) => s.lastAdded);

  const [query, setQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);
  const suggestions = query.trim().length > 0 ? searchProducts(query).slice(0, 6) : [];

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setShowSuggestions(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  function submitSearch(q: string) {
    if (!q.trim()) return;
    setShowSuggestions(false);
    router.push(`/search?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-navy-950/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 md:px-6">
        <Link href="/" className="focus-ring shrink-0" aria-label="TECHRUSH home">
          <Logo size="sm" className="md:hidden" />
          <Logo size="md" className="hidden md:flex" />
        </Link>

        <nav className="hidden items-center gap-6 lg:flex" aria-label="Primary">
          {navLinks.map((link) => (
            <Link key={link.href} href={link.href} className="focus-ring text-sm font-medium text-white/70 transition hover:text-white">
              {link.label}
            </Link>
          ))}
        </nav>

        <div ref={boxRef} className="relative ml-auto hidden max-w-md flex-1 md:block">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={(e) => e.key === "Enter" && submitSearch(query)}
            placeholder="Search phones, laptops, TVs & more…"
            className="focus-ring w-full rounded-full border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-white/40 transition focus:border-rush-cyan/50 focus:bg-white/[0.07]"
            aria-label="Search products"
          />
          {showSuggestions && suggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass absolute left-0 right-0 top-full mt-2 overflow-hidden rounded-xl border-white/10 shadow-card"
            >
              {suggestions.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    setQuery(p.name);
                    submitSearch(p.name);
                  }}
                  className="focus-ring flex w-full items-center justify-between px-4 py-2.5 text-left text-sm text-white/80 hover:bg-white/5"
                >
                  <span>{p.name}</span>
                  <span className="text-xs text-white/40">{p.brand}</span>
                </button>
              ))}
            </motion.div>
          )}
        </div>

        <button
          onClick={openLocationModal}
          className="focus-ring ml-auto hidden items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-white/80 transition hover:border-rush-cyan/40 md:ml-0 md:flex"
        >
          <MapPin className="h-3.5 w-3.5 text-rush-cyan" />
          <span className="max-w-[140px] truncate">{location ? `Deliver to ${location.city}` : "Deliver to…"}</span>
          <ChevronDown className="h-3 w-3 opacity-60" />
        </button>

        <button
          onClick={openLocationModal}
          className="focus-ring ml-auto flex items-center gap-1 text-white/80 md:hidden"
          aria-label="Choose location"
        >
          <MapPin className="h-5 w-5 text-rush-cyan" />
        </button>

        <Link href="/search" className="focus-ring text-white/80 md:hidden" aria-label="Search">
          <Search className="h-5 w-5" />
        </Link>

        <Link href="/profile" className="focus-ring hidden text-white/80 transition hover:text-white md:block" aria-label="Account">
          <User className="h-5 w-5" />
        </Link>

        <button onClick={openCart} className="focus-ring relative text-white/80 transition hover:text-white" aria-label="Cart">
          <motion.div animate={bump ? { scale: [1, 1.3, 1] } : {}} transition={{ duration: 0.35 }}>
            <ShoppingCart className="h-5 w-5" />
          </motion.div>
          {cartCount > 0 && (
            <span className="absolute -right-2 -top-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-rush-cyan px-1 text-[10px] font-bold text-navy-950">
              {cartCount}
            </span>
          )}
        </button>
      </div>

      {location && (
        <div className="border-t border-white/[0.05] bg-navy-900/60 px-4 py-1.5 text-center text-[11px] text-white/50 md:hidden">
          <MapPin className="mr-1 inline h-3 w-3 text-rush-cyan" />
          Deliver to {location.label}
        </div>
      )}
    </header>
  );
}
