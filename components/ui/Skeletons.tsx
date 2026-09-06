export function ProductCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.03]">
      <div className="shimmer-bg aspect-square" />
      <div className="space-y-2 p-4">
        <div className="shimmer-bg h-2.5 w-1/3 rounded" />
        <div className="shimmer-bg h-3.5 w-4/5 rounded" />
        <div className="shimmer-bg h-3 w-1/2 rounded" />
        <div className="shimmer-bg h-8 w-full rounded-full" />
      </div>
    </div>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 md:gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function TrackingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="shimmer-bg h-40 w-full rounded-2xl" />
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="shimmer-bg h-6 w-6 shrink-0 rounded-full" />
            <div className="shimmer-bg h-3 w-1/2 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
