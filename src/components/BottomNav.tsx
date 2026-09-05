import { NavLink } from 'react-router-dom'
import { Home, Search, ShoppingCart, Receipt, User } from 'lucide-react'
import { useDataStore } from '../store/useDataStore'
import { useSessionStore } from '../store/useSessionStore'

const ITEMS = [
  { to: '/app/home', icon: Home, label: 'Home' },
  { to: '/app/explore', icon: Search, label: 'Explore' },
  { to: '/app/cart', icon: ShoppingCart, label: 'Cart' },
  { to: '/app/orders', icon: Receipt, label: 'Orders' },
  { to: '/app/profile', icon: User, label: 'Profile' },
]

export function BottomNav() {
  const cartCount = useSessionStore((s) => s.cart.reduce((sum, c) => sum + c.qty, 0))
  const studentId = useSessionStore((s) => s.student?.studentId)
  const activeOrders = useDataStore((s) =>
    s.orders.filter((o) => o.studentId === studentId && !['completed', 'cancelled'].includes(o.status)).length,
  )

  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 glass border-t border-slate-200/70 safe-bottom">
      <div className="flex items-stretch justify-around max-w-lg mx-auto">
        {ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `relative flex flex-col items-center gap-1 py-2.5 px-3 flex-1 transition ${
                isActive ? 'text-brand-600' : 'text-slate-400'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span className="relative">
                  <Icon size={22} strokeWidth={isActive ? 2.4 : 2} />
                  {label === 'Cart' && cartCount > 0 && (
                    <span className="absolute -top-1.5 -right-2.5 min-w-[16px] h-4 px-1 rounded-full bg-accent-500 text-white text-[9px] font-bold grid place-items-center">
                      {cartCount}
                    </span>
                  )}
                  {label === 'Orders' && activeOrders > 0 && (
                    <span className="absolute -top-1 -right-2 w-2 h-2 rounded-full bg-brand-500" />
                  )}
                </span>
                <span className={`text-[10px] font-semibold ${isActive ? 'text-brand-600' : 'text-slate-400'}`}>
                  {label}
                </span>
                {isActive && <span className="absolute -top-px left-1/2 -translate-x-1/2 w-8 h-0.5 rounded-full bg-brand-600" />}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
