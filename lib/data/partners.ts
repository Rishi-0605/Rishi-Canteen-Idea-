import { Retailer } from "@/lib/types";

export const partnerPool: Omit<Retailer, "id" | "distanceKm" | "stock">[] = [
  { name: "UrbanTech Retail", type: "Retail Partner", area: "Andheri West", rating: 4.5 },
  { name: "CircuitPoint Dealers", type: "Authorized Dealer", area: "Bandra", rating: 4.3 },
  { name: "NextGen Distributors", type: "Distributor", area: "Powai", rating: 4.6 },
  { name: "PixelHub Electronics", type: "Retail Partner", area: "Malad", rating: 4.2 },
  { name: "Skyline Warehouse Co.", type: "Brand Warehouse", area: "Bhandup", rating: 4.7 },
  { name: "MetroTech Store", type: "Retail Partner", area: "Dadar", rating: 4.1 },
  { name: "Quantum Gadgets", type: "Authorized Dealer", area: "Kurla", rating: 4.4 },
  { name: "Coastal Electronics Hub", type: "Distributor", area: "Chembur", rating: 4.0 },
];

export const partnerTypes = ["Retail Partner", "Authorized Dealer", "Distributor", "Brand Warehouse"] as const;

let idCounter = 1;
export function makeRetailers(count = 3, seed = 1): Retailer[] {
  const result: Retailer[] = [];
  for (let i = 0; i < count; i++) {
    const base = partnerPool[(seed + i) % partnerPool.length];
    const distance = Number((0.8 + ((seed * 13 + i * 7) % 45) / 10).toFixed(1));
    const stock = 1 + ((seed * 3 + i * 5) % 12);
    result.push({
      id: `partner-${idCounter++}`,
      ...base,
      distanceKm: distance,
      stock,
    });
  }
  return result.sort((a, b) => a.distanceKm - b.distanceKm);
}
