export type Category =
  | 'All'
  | 'Main Course'
  | 'Sandwiches'
  | 'Chinese'
  | 'South Indian'
  | 'Healthy'
  | 'Juices'
  | 'Milkshakes'
  | 'Tea & Coffee'
  | 'Bakery'

export interface FoodItem {
  id: string
  name: string
  category: Exclude<Category, 'All'>
  price: number
  description: string
  veg: boolean
  emoji: string
  gradient: string
  available: boolean
  popular?: boolean
  quickPickup?: boolean
  recommended?: boolean
}

export interface CartLine {
  foodId: string
  qty: number
}

export type OrderType = 'eat-in' | 'parcel'
export type PickupMode = 'asap' | 'scheduled'
export type PaymentMethod = 'upi' | 'gpay' | 'phonepe' | 'card'
export type PaymentStatus = 'pending' | 'paid' | 'failed'
export type OrderStatus =
  | 'new'
  | 'accepted'
  | 'preparing'
  | 'ready'
  | 'completed'
  | 'cancelled'

export interface OrderLine {
  foodId: string
  name: string
  price: number
  qty: number
  veg: boolean
}

export interface StatusEvent {
  status: OrderStatus
  at: number
}

export interface Order {
  id: string
  token: string
  studentId: string
  studentName: string
  items: OrderLine[]
  total: number
  orderType: OrderType
  pickupMode: PickupMode
  pickupTime: number
  paymentMethod: PaymentMethod
  paymentStatus: PaymentStatus
  status: OrderStatus
  createdAt: number
  history: StatusEvent[]
}

export interface Student {
  id: string
  name: string
  studentId: string
  email: string
  college: string
}

export type Role = 'student' | 'staff' | 'admin' | null
