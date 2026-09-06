import { Category } from "@/lib/types";

export const categories: Category[] = [
  { slug: "smartphones", name: "Smartphones", emoji: "📱", description: "Latest phones from top brands" },
  { slug: "laptops", name: "Laptops", emoji: "💻", description: "Work, gaming & everyday laptops" },
  { slug: "tvs", name: "TVs", emoji: "📺", description: "4K, QLED & smart TVs" },
  { slug: "audio", name: "Audio", emoji: "🎧", description: "Headphones, earbuds & speakers" },
  { slug: "wearables", name: "Wearables", emoji: "⌚", description: "Smartwatches & fitness bands" },
  { slug: "gaming", name: "Gaming", emoji: "🎮", description: "Consoles, controllers & gear" },
  { slug: "monitors", name: "Monitors", emoji: "🖥", description: "Displays for work & play" },
  { slug: "accessories", name: "Accessories", emoji: "⌨", description: "Cables, keyboards, mice & more" },
  { slug: "appliances", name: "Appliances", emoji: "🧺", description: "Everyday home appliances" },
  { slug: "refrigerators", name: "Refrigerators", emoji: "❄", description: "Single & double door fridges" },
  { slug: "home-appliances", name: "Home Appliances", emoji: "🧹", description: "Cleaning & kitchen appliances" },
  { slug: "cameras", name: "Cameras", emoji: "📷", description: "Mirrorless, DSLR & action cams" },
];

export function getCategory(slug: string) {
  return categories.find((c) => c.slug === slug);
}
