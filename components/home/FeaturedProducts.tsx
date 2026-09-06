import Link from "next/link";
import { getFeaturedProducts } from "@/lib/data/products";
import ProductCard from "@/components/product/ProductCard";

export default function FeaturedProducts() {
  const products = getFeaturedProducts();
  return (
    <section className="px-4 py-10 md:px-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-5 flex items-end justify-between">
          <h2 className="text-xl font-bold text-white md:text-2xl">Featured This Week</h2>
          <Link href="/products" className="focus-ring text-sm font-medium text-rush-cyan hover:underline">
            View all
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 md:gap-4">
          {products.map((p, i) => (
            <ProductCard key={p.id} product={p} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
