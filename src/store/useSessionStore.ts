import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { CartLine, OrderType, PickupMode, Student, Role } from '../types'

// Per-tab identity & cart. Kept in sessionStorage (not localStorage) so that
// opening the Staff or Admin dashboard in another tab never logs out, or
// swaps the cart of, a Student tab already open in this browser — each tab
// is its own "device" in this prototype. Shared data (menu/orders) lives in
// useDataStore instead, which IS synced across tabs.
interface SessionState {
  role: Role
  student: Student | null

  cart: CartLine[]
  orderType: OrderType
  pickupMode: PickupMode
  scheduledTime: number | null
  simulatePaymentFailure: boolean

  loginDemo: (role: Exclude<Role, null>) => void
  loginStudent: (email: string, password: string) => { ok: boolean; error?: string }
  logout: () => void

  addToCart: (foodId: string, qty?: number, isAvailable?: boolean) => void
  updateCartQty: (foodId: string, qty: number) => void
  removeFromCart: (foodId: string) => void
  setCart: (cart: CartLine[]) => void
  clearCart: () => void
  setOrderType: (t: OrderType) => void
  setPickup: (mode: PickupMode, time?: number | null) => void
  setSimulatePaymentFailure: (v: boolean) => void
}

const DEMO_STUDENT: Student = {
  id: 'stu_demo',
  name: 'Aarav Shah',
  studentId: 'IBS24118',
  email: 'aarav.shah@ibsmumbai.demo',
  college: 'IBS Mumbai',
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      role: null,
      student: null,
      cart: [],
      orderType: 'parcel',
      pickupMode: 'asap',
      scheduledTime: null,
      simulatePaymentFailure: false,

      loginDemo: (role) => set({ role, student: role === 'student' ? DEMO_STUDENT : null }),

      loginStudent: (email, password) => {
        if (!email || !password) return { ok: false, error: 'Enter your college email and password.' }
        set({ role: 'student', student: { ...DEMO_STUDENT, email } })
        return { ok: true }
      },

      logout: () => set({ role: null, student: null, cart: [] }),

      addToCart: (foodId, qty = 1, isAvailable = true) => {
        if (!isAvailable) return
        set((s) => {
          const existing = s.cart.find((c) => c.foodId === foodId)
          if (existing) {
            return { cart: s.cart.map((c) => (c.foodId === foodId ? { ...c, qty: c.qty + qty } : c)) }
          }
          return { cart: [...s.cart, { foodId, qty }] }
        })
      },

      updateCartQty: (foodId, qty) => {
        if (qty <= 0) {
          get().removeFromCart(foodId)
          return
        }
        set((s) => ({ cart: s.cart.map((c) => (c.foodId === foodId ? { ...c, qty } : c)) }))
      },

      removeFromCart: (foodId) => set((s) => ({ cart: s.cart.filter((c) => c.foodId !== foodId) })),
      setCart: (cart) => set({ cart }),
      clearCart: () => set({ cart: [], orderType: 'parcel', pickupMode: 'asap', scheduledTime: null }),
      setOrderType: (t) => set({ orderType: t }),
      setPickup: (mode, time = null) => set({ pickupMode: mode, scheduledTime: mode === 'scheduled' ? (time ?? null) : null }),
      setSimulatePaymentFailure: (v) => set({ simulatePaymentFailure: v }),
    }),
    {
      name: 'ibs-cafeteria-session',
      storage: createJSONStorage(() => sessionStorage),
      version: 1,
    },
  ),
)
