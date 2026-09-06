export const adminOverviewStats = {
  gmv: 48_62_400,
  orders: 1284,
  activeUsers: 6420,
  retailPartners: 128,
  deliveryPartners: 342,
  avgDeliveryMinutes: 47,
  cancellationRate: 2.4,
};

export const topCategories = [
  { name: "Smartphones", share: 32 },
  { name: "Laptops", share: 21 },
  { name: "TVs", share: 14 },
  { name: "Audio", share: 12 },
  { name: "Appliances", share: 11 },
  { name: "Others", share: 10 },
];

export const topProducts = [
  { name: "iPhone 17", orders: 214, revenue: 1_71_19_786 },
  { name: "Galaxy S26 Ultra", orders: 132, revenue: 1_64_99_868 },
  { name: "AirPods Pro 3", orders: 301, revenue: 69_20_699 },
  { name: "MacBook Air M5", orders: 88, revenue: 1_01_11_200 },
  { name: "Smart TV 43\"", orders: 156, revenue: 42_11_844 },
];

export interface AdminOrderRow {
  id: string;
  customer: string;
  product: string;
  partner: string;
  status: "Delivered" | "On the way" | "Preparing" | "Cancelled";
  total: number;
}

export const adminOrders: AdminOrderRow[] = [
  { id: "TR10293", customer: "Aarav Sharma", product: "Samsung 55\" 4K TV", partner: "UrbanTech Retail", status: "On the way", total: 89999 },
  { id: "TR10292", customer: "Priya Menon", product: "iPhone 17 Pro", partner: "CircuitPoint Dealers", status: "Delivered", total: 129999 },
  { id: "TR10291", customer: "Rohan Kapoor", product: "MacBook Pro 14\"", partner: "Skyline Warehouse Co.", status: "Preparing", total: 189900 },
  { id: "TR10290", customer: "Ishita Desai", product: "AirPods Pro 3", partner: "PixelHub Electronics", status: "Delivered", total: 22999 },
  { id: "TR10289", customer: "Kabir Thakur", product: "Split AC 1.5 Ton", partner: "MetroTech Store", status: "Cancelled", total: 39999 },
  { id: "TR10288", customer: "Ananya Rao", product: "PlayStation 6", partner: "Quantum Gadgets", status: "On the way", total: 59999 },
];

export interface AdminPartnerRow {
  id: string;
  name: string;
  type: string;
  area: string;
  orders: number;
  rating: number;
  status: "Active" | "Pending" | "Suspended";
}

export const adminPartners: AdminPartnerRow[] = [
  { id: "p1", name: "UrbanTech Retail", type: "Retail Partner", area: "Andheri West", orders: 412, rating: 4.5, status: "Active" },
  { id: "p2", name: "CircuitPoint Dealers", type: "Authorized Dealer", area: "Bandra", orders: 298, rating: 4.3, status: "Active" },
  { id: "p3", name: "NextGen Distributors", type: "Distributor", area: "Powai", orders: 187, rating: 4.6, status: "Active" },
  { id: "p4", name: "PixelHub Electronics", type: "Retail Partner", area: "Malad", orders: 156, rating: 4.2, status: "Pending" },
  { id: "p5", name: "Skyline Warehouse Co.", type: "Brand Warehouse", area: "Bhandup", orders: 342, rating: 4.7, status: "Active" },
  { id: "p6", name: "MetroTech Store", type: "Retail Partner", area: "Dadar", orders: 64, rating: 3.9, status: "Suspended" },
];

export interface DeliveryPartnerRow {
  id: string;
  name: string;
  zone: string;
  activeDeliveries: number;
  completedToday: number;
  rating: number;
  status: "Online" | "Offline" | "On delivery";
}

export const deliveryPartners: DeliveryPartnerRow[] = [
  { id: "d1", name: "Sandeep Yadav", zone: "Bandra – Khar", activeDeliveries: 1, completedToday: 8, rating: 4.8, status: "On delivery" },
  { id: "d2", name: "Manoj Kumar", zone: "Andheri – Juhu", activeDeliveries: 0, completedToday: 6, rating: 4.6, status: "Online" },
  { id: "d3", name: "Rakesh Singh", zone: "Powai – Chandivali", activeDeliveries: 2, completedToday: 5, rating: 4.4, status: "On delivery" },
  { id: "d4", name: "Vijay Patil", zone: "Dadar – Worli", activeDeliveries: 0, completedToday: 0, rating: 4.7, status: "Offline" },
];

export interface SupportTicketRow {
  id: string;
  customer: string;
  subject: string;
  priority: "Low" | "Medium" | "High";
  status: "Open" | "Resolved";
}

export const supportTickets: SupportTicketRow[] = [
  { id: "t1", customer: "Neha Bhatt", subject: "Delivery delayed beyond estimate", priority: "High", status: "Open" },
  { id: "t2", customer: "Sai Kumar", subject: "Wrong item delivered", priority: "High", status: "Open" },
  { id: "t3", customer: "Meera Verma", subject: "Installation not scheduled", priority: "Medium", status: "Open" },
  { id: "t4", customer: "Arjun Nair", subject: "Refund status query", priority: "Low", status: "Resolved" },
];
