import { Suspense } from "react";
import SearchClient from "@/components/search/SearchClient";

export const metadata = { title: "Search | TECHRUSH" };

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-5xl px-4 py-8 md:px-6" />}>
      <SearchClient />
    </Suspense>
  );
}
