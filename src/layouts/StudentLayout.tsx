import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ShoppingBag, ChevronRight } from 'lucide-react'
import { Sidebar } from '../components/Sidebar'
import { BottomNav } from '../components/BottomNav'
import { useSessionStore } from '../store/useSessionStore'
import { useDataStore } from '../store/useDataStore'
import { formatINR } from '../lib/format'

export function StudentLayout() {
  const cart = useSessionStore((s) => s.cart)
  const menu = useDataStore((s) => s.menu)
  const location = useNavigate()
  const path = useLocation().pathname

  const cartCount = cart.reduce((sum, c) => sum + c.qty, 0)
  const cartTotal = cart.reduce((sum, c) => {
    const item = menu.find((m) => m.id === c.foodId)
    return sum + (item ? item.price * c.qty : 0)
  }, 0)

  const showCartBar = cartCount > 0 && !['/app/cart', '/app/payment'].includes(path) && !path.startsWith('/app/token')

  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <div className="max-w-6xl mx-auto pb-24 lg:pb-10">
          <Outlet />
        </div>
      </div>
      {showCartBar && (
        <button
          onClick={() => location('/app/cart')}
          className="fixed bottom-20 lg:bottom-6 left-1/2 -translate-x-1/2 z-40 w-[calc(100%-1.5rem)] max-w-md lg:max-w-sm flex items-center justify-between gap-3 rounded-2xl bg-brand-600 text-white px-5 py-3.5 shadow-xl shadow-brand-900/30 animate-slide-up active:scale-[0.98] transition"
        >
          <span className="flex items-center gap-2.5">
            <ShoppingBag size={18} />
            <span className="text-sm font-bold">
              {cartCount} item{cartCount > 1 ? 's' : ''} · {formatINR(cartTotal)}
            </span>
          </span>
          <span className="flex items-center gap-1 text-sm font-bold">
            View Cart <ChevronRight size={16} />
          </span>
        </button>
      )}
      <BottomNav />
    </div>
  )
}
