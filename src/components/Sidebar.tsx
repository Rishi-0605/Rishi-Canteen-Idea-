import { NavLink, useNavigate } from 'react-router-dom'
import { Home, Search, ShoppingCart, Receipt, User, LogOut } from 'lucide-react'
import { Logo } from './Logo'
import { useSessionStore } from '../store/useSessionStore'

const ITEMS = [
  { to: '/app/home', icon: Home, label: 'Home' },
  { to: '/app/explore', icon: Search, label: 'Explore' },
  { to: '/app/cart', icon: ShoppingCart, label: 'Cart' },
  { to: '/app/orders', icon: Receipt, label: 'My Orders' },
  { to: '/app/profile', icon: User, label: 'Profile' },
]

export function Sidebar() {
  const cartCount = useSessionStore((s) => s.cart.reduce((sum, c) => sum + c.qty, 0))
  const logout = useSessionStore((s) => s.logout)
  const navigate = useNavigate()

  return (
    <aside className="hidden lg:flex flex-col w-64 shrink-0 border-r border-slate-200 bg-white h-screen sticky top-0 px-4 py-6">
      <div className="px-2 mb-8">
        <Logo />
      </div>
      <nav className="flex-1 flex flex-col gap-1">
        {ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition ${
                isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
              }`
            }
          >
            <Icon size={18} />
            <span className="flex-1">{label}</span>
            {label === 'Cart' && cartCount > 0 && (
              <span className="min-w-[20px] h-5 px-1 rounded-full bg-brand-600 text-white text-[10px] font-bold grid place-items-center">
                {cartCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      <button
        onClick={() => {
          logout()
          navigate('/login')
        }}
        className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
      >
        <LogOut size={18} />
        Logout
      </button>
    </aside>
  )
}
