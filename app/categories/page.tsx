import Link from "next/link";
import { categories } from "@/lib/data/categories";
import { getProductsByCategory } from "@/lib/data/products";

export const metadata = { title: "Categories | TECHRUSH" };

export default function CategoriesPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
      <h1 className="text-2xl font-extrabold tracking-tight text-white md:text-3xl">Shop by Category</h1>
      <p className="mt-2 text-sm text-white/50">Browse electronics and appliances from nearby retail partners.</p>

      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
        {categories.map((cat) => (
          <Link
            key={cat.slug}
            href={`/products?category=${cat.slug}`}
            className="focus-ring group flex flex-col gap-2 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 transition hover:-translate-y-1 hover:border-rush/40"
          >
            <span className="text-3xl transition group-hover:scale-110">{cat.emoji}</span>
            <span className="text-sm font-bold text-white">{cat.name}</span>
            <span className="text-xs text-white/45">{cat.description}</span>
            <span className="mt-1 text-xs font-medium text-rush-cyan">{getProductsByCategory(cat.slug).length} products</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
