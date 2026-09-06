import { Suspense } from "react";
import ProductListingClient from "@/components/product/ProductListingClient";
import { ProductGridSkeleton } from "@/components/ui/Skeletons";

export const metadata = {
  title: "Shop Electronics | TECHRUSH",
  description: "Browse smartphones, laptops, TVs, appliances and more with fast local delivery from TECHRUSH.",
};

export default function ProductsPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-7xl px-4 py-8 md:px-6"><ProductGridSkeleton /></div>}>
      <ProductListingClient />
    </Suspense>
  );
}
