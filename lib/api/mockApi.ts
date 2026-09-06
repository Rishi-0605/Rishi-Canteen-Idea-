import { products, getProduct as _getProduct, searchProducts as _searchProducts } from "@/lib/data/products";
import { Order, OrderStatusStep, Address, Product } from "@/lib/types";
import { estimateDeliveryMinutes } from "@/lib/utils";

function delay<T>(value: T, ms = 400): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

/** GET /products */
export async function apiGetProducts(): Promise<Product[]> {
  return delay(products, 300);
}

/** GET /products/:id */
export async function apiGetProduct(id: string): Promise<Product | undefined> {
  return delay(_getProduct(id), 250);
}

/** GET /products/search?q= */
export async function apiSearchProducts(query: string): Promise<Product[]> {
  return delay(_searchProducts(query), 200);
}

/** GET /inventory/nearby?productId= */
export interface NearbyInventoryResult {
  fastest: Product["retailers"][number];
  etaMinutes: number;
  allOptions: { retailer: Product["retailers"][number]; etaMinutes: number }[];
}

export async function apiGetNearbyInventory(productId: string): Promise<NearbyInventoryResult | null> {
  const product = _getProduct(productId);
  if (!product) return delay(null, 200);
  const options = product.retailers
    .filter((r) => r.stock > 0)
    .map((r, idx) => ({
      retailer: r,
      etaMinutes: estimateDeliveryMinutes(product.size, r.distanceKm, idx + productId.length),
    }))
    .sort((a, b) => a.etaMinutes - b.etaMinutes);
  if (options.length === 0) return delay(null, 200);
  return delay({ fastest: options[0].retailer, etaMinutes: options[0].etaMinutes, allOptions: options }, 350);
}

/** POST /orders */
export interface PlaceOrderInput {
  items: { productId: string; name: string; image: string; price: number; quantity: number }[];
  address: Address;
  paymentMethod: string;
  subtotal: number;
  deliveryFee: number;
  platformFee: number;
  discount: number;
  total: number;
  installationRequested?: boolean;
}

let orderCounter = 10293;

export async function apiPlaceOrder(input: PlaceOrderInput): Promise<Order> {
  const primaryProduct = _getProduct(input.items[0].productId);
  const retailer = primaryProduct?.retailers[0] ?? {
    id: "partner-generic",
    name: "Nearby Retail Partner",
    type: "Retail Partner" as const,
    area: "Local Area",
    distanceKm: 2.5,
    rating: 4.3,
    stock: 5,
  };
  const etaMinutes = primaryProduct
    ? estimateDeliveryMinutes(primaryProduct.size, retailer.distanceKm, orderCounter)
    : 45;
  const order: Order = {
    id: `TR${orderCounter++}`,
    createdAt: new Date().toISOString(),
    items: input.items,
    address: input.address,
    paymentMethod: input.paymentMethod,
    subtotal: input.subtotal,
    deliveryFee: input.deliveryFee,
    platformFee: input.platformFee,
    discount: input.discount,
    total: input.total,
    status: "confirmed",
    etaMinutes,
    retailer,
    installationRequested: input.installationRequested,
  };
  return delay(order, 900);
}

export const ORDER_STEPS: { key: OrderStatusStep; label: string }[] = [
  { key: "confirmed", label: "Order confirmed" },
  { key: "partner_notified", label: "Partner store notified" },
  { key: "preparing", label: "Product being prepared" },
  { key: "partner_assigned", label: "Delivery partner assigned" },
  { key: "on_the_way", label: "On the way" },
  { key: "delivered", label: "Delivered" },
];

export function nextOrderStatus(current: OrderStatusStep): OrderStatusStep {
  const idx = ORDER_STEPS.findIndex((s) => s.key === current);
  if (idx === -1 || idx === ORDER_STEPS.length - 1) return current;
  return ORDER_STEPS[idx + 1].key;
}
