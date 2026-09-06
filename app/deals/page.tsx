import { getDealsByTag } from "@/lib/data/products";
import { Product } from "@/lib/types";
import ProductCard from "@/components/product/ProductCard";
import CountdownTimer from "@/components/deals/CountdownTimer";
import { Flame } from "lucide-react";

export const metadata = { title: "Deals | TECHRUSH" };

const sections: { tag: NonNullable<Product["dealTag"]>; title: string; seconds: number }[] = [
  { tag: "flash", title: "⚡ Flash Deals", seconds: 3600 * 3 },
  { tag: "under999", title: "TECH UNDER ₹999 & MORE", seconds: 3600 * 8 },
  { tag: "gaming", title: "GAMING DEALS", seconds: 3600 * 12 },
  { tag: "phones", title: "SMARTPHONE DEALS", seconds: 3600 * 6 },
  { tag: "laptops", title: "LAPTOP DEALS", seconds: 3600 * 10 },
  { tag: "appliances", title: "HOME APPLIANCE DEALS", seconds: 3600 * 24 },
  { tag: "weekend", title: "WEEKEND RUSH", seconds: 3600 * 30 },
];

export default function DealsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
      <div className="mb-2 flex items-center gap-2">
        <Flame className="h-6 w-6 text-rush-cyan" />
        <h1 className="text-2xl font-extrabold tracking-tight text-white md:text-3xl">TECHRUSH Deals</h1>
      </div>
      <p className="mb-2 text-sm text-white/50">Limited-time offers from nearby retail partners.</p>
      <p className="mb-10 text-xs text-white/30">Countdown timers shown are for prototype/demo purposes only.</p>

      {sections.map(({ tag, title, seconds }) => {
        const products = getDealsByTag(tag);
        if (products.length === 0) return null;
        return (
          <section key={tag} className="mb-12">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-bold text-white md:text-xl">{title}</h2>
              <CountdownTimer initialSeconds={seconds} />
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 md:gap-4">
              {products.map((p, i) => (
                <ProductCard key={p.id} product={p} index={i} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
