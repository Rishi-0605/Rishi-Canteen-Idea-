import { Review } from "@/lib/types";

const names = [
  "Aarav S.", "Priya M.", "Rohan K.", "Ishita D.", "Kabir T.", "Ananya R.",
  "Vivaan J.", "Diya P.", "Arjun N.", "Meera V.", "Sai Kumar", "Neha B.",
];

const titles = [
  "Great value for money",
  "Delivered faster than expected",
  "Exactly as described",
  "Works flawlessly",
  "Good but packaging could improve",
  "Impressed with the speed",
  "Solid build quality",
  "Would buy again",
];

const bodies = [
  "Ordered in the evening and it showed up before I finished dinner. Product quality matches the listing.",
  "The nearby partner had it in stock and delivery was smooth. No complaints so far.",
  "Performance is exactly what I expected for the price. Setup was easy.",
  "Battery life and build quality are solid. Slightly noisy fan under load but otherwise great.",
  "Customer support was responsive when I had a question about installation.",
  "Great first impression, been using it for two weeks without issues.",
];

export function makeReviews(seed: number, count = 4): Review[] {
  const reviews: Review[] = [];
  for (let i = 0; i < count; i++) {
    const idx = (seed + i * 5) % names.length;
    const rating = 3 + ((seed + i) % 3);
    reviews.push({
      id: `rev-${seed}-${i}`,
      author: names[idx],
      rating: Math.min(5, rating),
      title: titles[(seed + i) % titles.length],
      body: bodies[(seed + i * 2) % bodies.length],
      date: new Date(Date.now() - (i + 1) * 86400000 * ((seed % 5) + 1)).toISOString(),
      verified: (seed + i) % 3 !== 0,
    });
  }
  return reviews;
}
