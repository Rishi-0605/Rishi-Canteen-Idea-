import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { INITIAL_MENU } from '../data/menu'
import type { FoodItem, Order, OrderLine, OrderType, PickupMode, PaymentMethod, OrderStatus, Role } from '../types'

// Shared "backend" data — menu & orders — visible to every role. Persisted to
// localStorage and kept in sync across tabs (e.g. Student + Staff dashboard
// open side by side) via the `storage` event listener registered below.

export interface Notification {
  id: string
  title: string
  message: string
  type: 'success' | 'info' | 'warning' | 'error'
  at: number
  read: boolean
  /** Which dashboard this toast/bell entry is meant for. Omit to show everywhere. */
  audience?: Exclude<Role, null>
}

interface PlaceOrderInput {
  cart: { foodId: string; qty: number }[]
  studentId: string
  studentName: string
  orderType: OrderType
  pickupMode: PickupMode
  scheduledTime: number | null
  method: PaymentMethod
  simulateFailure: boolean
}

interface PlaceOrderResult {
  ok: boolean
  order?: Order
  reason?: string
}

interface DataState {
  menu: FoodItem[]
  orders: Order[]
  tokenSeq: number
  notifications: Notification[]
  cafeteriaOpen: boolean

  placeOrder: (input: PlaceOrderInput) => PlaceOrderResult
  updateOrderStatus: (orderId: string, status: OrderStatus) => void
  cancelOrder: (orderId: string) => void

  addFoodItem: (item: FoodItem) => void
  updateFoodItem: (id: string, patch: Partial<FoodItem>) => void
  deleteFoodItem: (id: string) => void
  toggleAvailability: (id: string) => void

  pushNotification: (n: Omit<Notification, 'id' | 'at' | 'read'>) => void
  markNotificationRead: (id: string) => void
  clearNotifications: () => void
  setCafeteriaOpen: (v: boolean) => void
}

function genId(prefix = 'id') {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`
}

export const useDataStore = create<DataState>()(
  persist(
    (set, get) => ({
      menu: INITIAL_MENU,
      orders: [],
      tokenSeq: 127,
      notifications: [],
      cafeteriaOpen: true,

      placeOrder: (input) => {
        const s = get()
        if (!s.cafeteriaOpen) {
          return { ok: false, reason: 'The cafeteria is currently closed. Please order during operating hours.' }
        }
        if (input.cart.length === 0) {
          return { ok: false, reason: 'Your cart is empty.' }
        }
        const soldOut = input.cart.find((c) => {
          const item = s.menu.find((m) => m.id === c.foodId)
          return !item || !item.available
        })
        if (soldOut) {
          return { ok: false, reason: 'One of the items in your cart just sold out. Please review your cart.' }
        }
        if (input.simulateFailure) {
          return { ok: false, reason: 'Payment could not be processed. Please try again.' }
        }

        const lines: OrderLine[] = input.cart.map((c) => {
          const item = s.menu.find((m) => m.id === c.foodId)!
          return { foodId: item.id, name: item.name, price: item.price, qty: c.qty, veg: item.veg }
        })
        const total = lines.reduce((sum, l) => sum + l.price * l.qty, 0)
        const token = `A${s.tokenSeq}`
        const now = Date.now()
        const pickupTime = input.pickupMode === 'scheduled' && input.scheduledTime ? input.scheduledTime : now

        const order: Order = {
          id: genId('order'),
          token,
          studentId: input.studentId,
          studentName: input.studentName,
          items: lines,
          total,
          orderType: input.orderType,
          pickupMode: input.pickupMode,
          pickupTime,
          paymentMethod: input.method,
          paymentStatus: 'paid',
          status: 'new',
          createdAt: now,
          history: [{ status: 'new', at: now }],
        }

        set((st) => ({ orders: [order, ...st.orders], tokenSeq: st.tokenSeq + 1 }))

        get().pushNotification({
          title: 'Payment successful',
          message: `Token #${token} confirmed. Order placed successfully.`,
          type: 'success',
          audience: 'student',
        })
        get().pushNotification({
          title: 'New order received',
          message: `Token #${token} · ${lines.map((l) => `${l.name} × ${l.qty}`).join(', ')}`,
          type: 'info',
          audience: 'staff',
        })

        return { ok: true, order }
      },

      updateOrderStatus: (orderId, status) => {
        set((s) => ({
          orders: s.orders.map((o) =>
            o.id === orderId ? { ...o, status, history: [...o.history, { status, at: Date.now() }] } : o,
          ),
        }))
        const order = get().orders.find((o) => o.id === orderId)
        if (!order) return
        const messages: Partial<Record<OrderStatus, { title: string; message: string }>> = {
          accepted: { title: 'Order accepted ✓', message: `Token #${order.token} has been accepted by the cafeteria.` },
          preparing: { title: 'Being prepared 🍴', message: `Token #${order.token} is being prepared.` },
          ready: { title: 'Order ready 🔔', message: `Token #${order.token} is ready for pickup!` },
          completed: { title: 'Order collected', message: `Token #${order.token} marked as collected. Enjoy!` },
        }
        const m = messages[status]
        if (m) {
          get().pushNotification({ title: m.title, message: m.message, type: status === 'ready' ? 'success' : 'info', audience: 'student' })
        }
      },

      cancelOrder: (orderId) => {
        set((s) => ({
          orders: s.orders.map((o) =>
            o.id === orderId ? { ...o, status: 'cancelled', history: [...o.history, { status: 'cancelled', at: Date.now() }] } : o,
          ),
        }))
      },

      addFoodItem: (item) => set((s) => ({ menu: [...s.menu, item] })),
      updateFoodItem: (id, patch) => set((s) => ({ menu: s.menu.map((m) => (m.id === id ? { ...m, ...patch } : m)) })),
      deleteFoodItem: (id) => set((s) => ({ menu: s.menu.filter((m) => m.id !== id) })),
      toggleAvailability: (id) => set((s) => ({ menu: s.menu.map((m) => (m.id === id ? { ...m, available: !m.available } : m)) })),

      pushNotification: (n) =>
        set((s) => ({
          notifications: [{ ...n, id: genId('notif'), at: Date.now(), read: false }, ...s.notifications].slice(0, 50),
        })),
      markNotificationRead: (id) =>
        set((s) => ({ notifications: s.notifications.map((n) => (n.id === id ? { ...n, read: true } : n)) })),
      clearNotifications: () => set({ notifications: [] }),
      setCafeteriaOpen: (v) => set({ cafeteriaOpen: v }),
    }),
    {
      name: 'ibs-cafeteria-data',
      version: 1,
    },
  ),
)

// Keep multiple open tabs (e.g. a Student view + the Staff dashboard) in
// sync, since this prototype uses localStorage as its shared mock backend.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key === 'ibs-cafeteria-data') {
      useDataStore.persist.rehydrate()
    }
  })
}
