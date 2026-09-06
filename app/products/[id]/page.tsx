import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getProduct, getProductsByCategory, products } from "@/lib/data/products";
import ProductDetailClient from "@/components/product/ProductDetailClient";

export function generateStaticParams() {
  return products.map((p) => ({ id: p.id }));
}

export function generateMetadata({ params }: { params: { id: string } }): Metadata {
  const product = getProduct(params.id);
  if (!product) return { title: "Product not found | TECHRUSH" };
  return {
    title: `${product.name} | TECHRUSH`,
    description: product.description,
  };
}

export default function ProductDetailPage({ params }: { params: { id: string } }) {
  const product = getProduct(params.id);
  if (!product) notFound();
  const related = getProductsByCategory(product.category).filter((p) => p.id !== product.id).slice(0, 4);
  return <ProductDetailClient product={product} related={related} />;
}
