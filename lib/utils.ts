import { ProductSize } from "@/lib/types";

export function formatINR(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function discountPercent(price: number, mrp: number): number {
  if (mrp <= price) return 0;
  return Math.round(((mrp - price) / mrp) * 100);
}

const BASE_MINUTES: Record<ProductSize, [number, number]> = {
  small: [18, 32],
  medium: [34, 55],
  large: [50, 90],
  bulky: [95, 150],
};

export function estimateDeliveryMinutes(size: ProductSize, distanceKm: number, seed = 0): number {
  const [min, max] = BASE_MINUTES[size];
  const distanceFactor = Math.min(distanceKm * 4, 40);
  const jitter = (seed * 37) % 17;
  const raw = min + distanceFactor + jitter;
  return Math.max(min, Math.min(max + 30, Math.round(raw)));
}

export function formatMinutes(mins: number): string {
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h} hr` : `${h} hr ${m} min`;
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function sizeForCategory(category: string): ProductSize {
  switch (category) {
    case "accessories":
    case "audio":
    case "wearables":
      return "small";
    case "smartphones":
    case "cameras":
    case "gaming":
      return "medium";
    case "laptops":
    case "monitors":
    case "tvs":
    case "home-appliances":
      return "large";
    case "refrigerators":
    case "appliances":
      return "bulky";
    default:
      return "medium";
  }
}

export function timeAgo(dateStr: string): string {
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}
