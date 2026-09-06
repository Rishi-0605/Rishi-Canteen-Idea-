export type PartnerOrderStatus = "new" | "accepted" | "packed" | "ready" | "picked_up" | "rejected";

export interface PartnerOrder {
  id: string;
  product: string;
  customerArea: string;
  deliveryStatus: string;
  pickupStatus: PartnerOrderStatus;
  value: number;
}

export interface PartnerInventoryItem {
  id: string;
  product: string;
  sku: string;
  price: number;
  stock: number;
  available: boolean;
  deliveryRadiusKm: number;
}

export const initialPartnerOrders: PartnerOrder[] = [
  { id: "TR10281", product: "iPhone 17", customerArea: "Bandra West", deliveryStatus: "Awaiting pickup", pickupStatus: "new", value: 79999 },
  { id: "TR10282", product: "WH-1000XM6", customerArea: "Khar", deliveryStatus: "Awaiting pickup", pickupStatus: "new", value: 29999 },
  { id: "TR10276", product: "Galaxy S26 Ultra", customerArea: "Andheri West", deliveryStatus: "Preparing", pickupStatus: "accepted", value: 124999 },
  { id: "TR10270", product: "MacBook Air M5", customerArea: "Juhu", deliveryStatus: "Packed", pickupStatus: "packed", value: 114900 },
  { id: "TR10265", product: "Smart TV 43\"", customerArea: "Vile Parle", deliveryStatus: "Ready for pickup", pickupStatus: "ready", value: 26999 },
  { id: "TR10250", product: "AirPods Pro 3", customerArea: "Bandra East", deliveryStatus: "Picked up", pickupStatus: "picked_up", value: 22999 },
  { id: "TR10248", product: "PlayStation 6", customerArea: "Santacruz", deliveryStatus: "Delivered", pickupStatus: "picked_up", value: 59999 },
];

export const initialPartnerInventory: PartnerInventoryItem[] = [
  { id: "inv-1", product: "iPhone 17", sku: "TR-IP17-256", price: 79999, stock: 6, available: true, deliveryRadiusKm: 8 },
  { id: "inv-2", product: "Galaxy S26 Ultra", sku: "TR-GS26U-256", price: 124999, stock: 3, available: true, deliveryRadiusKm: 8 },
  { id: "inv-3", product: "MacBook Air M5", sku: "TR-MBA5-512", price: 114900, stock: 4, available: true, deliveryRadiusKm: 10 },
  { id: "inv-4", product: "Smart TV 43\"", sku: "TR-STV43", price: 26999, stock: 0, available: false, deliveryRadiusKm: 12 },
  { id: "inv-5", product: "WH-1000XM6", sku: "TR-WHXM6", price: 29999, stock: 11, available: true, deliveryRadiusKm: 8 },
  { id: "inv-6", product: "AirPods Pro 3", sku: "TR-APP3", price: 22999, stock: 15, available: true, deliveryRadiusKm: 8 },
  { id: "inv-7", product: "PlayStation 6", sku: "TR-PS6-1TB", price: 59999, stock: 2, available: true, deliveryRadiusKm: 10 },
];
