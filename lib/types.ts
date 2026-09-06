export type CategorySlug =
  | "smartphones"
  | "laptops"
  | "tvs"
  | "audio"
  | "wearables"
  | "gaming"
  | "monitors"
  | "accessories"
  | "appliances"
  | "refrigerators"
  | "home-appliances"
  | "cameras";

export interface Category {
  slug: CategorySlug;
  name: string;
  emoji: string;
  description: string;
}

export type ProductSize = "small" | "medium" | "large" | "bulky";

export interface Retailer {
  id: string;
  name: string;
  type: "Retail Partner" | "Authorized Dealer" | "Distributor" | "Brand Warehouse";
  area: string;
  distanceKm: number;
  rating: number;
  stock: number;
}

export interface Review {
  id: string;
  author: string;
  rating: number;
  title: string;
  body: string;
  date: string;
  verified: boolean;
}

export interface Product {
  id: string;
  name: string;
  brand: string;
  category: CategorySlug;
  price: number;
  mrp: number;
  rating: number;
  reviewCount: number;
  images: string[];
  color: string;
  tags: string[];
  size: ProductSize;
  installationAvailable: boolean;
  warranty: string;
  returnPolicy: string;
  emiFrom?: number;
  specs: { label: string; value: string }[];
  whatsInTheBox: string[];
  description: string;
  featured?: boolean;
  dealTag?: "flash" | "under999" | "gaming" | "phones" | "laptops" | "appliances" | "weekend";
  reviews: Review[];
  retailers: Retailer[];
}

export interface CartItem {
  productId: string;
  quantity: number;
  savedForLater?: boolean;
}

export interface Address {
  id: string;
  label: string;
  line1: string;
  line2?: string;
  city: string;
  state: string;
  pincode: string;
  isDefault?: boolean;
}

export type OrderStatusStep =
  | "confirmed"
  | "partner_notified"
  | "preparing"
  | "partner_assigned"
  | "on_the_way"
  | "delivered";

export interface OrderItem {
  productId: string;
  name: string;
  image: string;
  price: number;
  quantity: number;
}

export interface Order {
  id: string;
  createdAt: string;
  items: OrderItem[];
  address: Address;
  paymentMethod: string;
  subtotal: number;
  deliveryFee: number;
  platformFee: number;
  discount: number;
  total: number;
  status: OrderStatusStep;
  etaMinutes: number;
  retailer: Retailer;
  installationRequested?: boolean;
}

export interface LocationInfo {
  label: string;
  city: string;
  state: string;
  pincode: string;
  serviceable: boolean;
}

export interface Notification {
  id: string;
  title: string;
  body: string;
  read: boolean;
  date: string;
}
