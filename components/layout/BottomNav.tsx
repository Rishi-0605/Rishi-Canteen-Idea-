"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LayoutGrid, Search, Package, User } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home", Icon: Home },
  { href: "/categories", label: "Categories", Icon: LayoutGrid },
  { href: "/search", label: "Search", Icon: Search },
  { href: "/orders", label: "Orders", Icon: Package },
  { href: "/profile", label: "Account", Icon: User },
];

export default function BottomNav() {
  const pathname = usePathname();
  return (
    <nav
      className="glass fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t border-white/10 px-2 py-2 md:hidden"
      style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 0.4rem)" }}
      aria-label="Primary mobile"
    >
      {links.map(({ href, label, Icon }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "focus-ring flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 text-[10px] font-medium transition",
              active ? "text-rush-cyan" : "text-white/50"
            )}
          >
            <Icon className="h-5 w-5" strokeWidth={active ? 2.2 : 1.8} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
