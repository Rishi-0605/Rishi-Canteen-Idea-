import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LayoutDashboard, UtensilsCrossed, Receipt, LogOut, Power } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { useSessionStore } from '../../store/useSessionStore'
import { NotificationBell } from '../../components/NotificationBell'
import { OverviewTab } from './OverviewTab'
import { MenuTab } from './MenuTab'
import { OrdersTab } from './OrdersTab'

const TABS = [
  { key: 'overview', label: 'Overview', icon: LayoutDashboard },
  { key: 'menu', label: 'Menu Management', icon: UtensilsCrossed },
  { key: 'orders', label: 'Orders', icon: Receipt },
] as const

type TabKey = (typeof TABS)[number]['key']

export function AdminDashboard() {
  const navigate = useNavigate()
  const logout = useSessionStore((s) => s.logout)
  const cafeteriaOpen = useDataStore((s) => s.cafeteriaOpen)
  const setCafeteriaOpen = useDataStore((s) => s.setCafeteriaOpen)
  const [tab, setTab] = useState<TabKey>('overview')

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-100 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wide text-slate-400">IBS Cafeteria</p>
            <h1 className="font-display font-extrabold text-xl text-slate-900">Admin Dashboard</h1>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setCafeteriaOpen(!cafeteriaOpen)}
              className={`hidden sm:flex items-center gap-1.5 rounded-full px-3.5 py-2 text-xs font-bold transition ${
                cafeteriaOpen ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
              }`}
            >
              <Power size={13} />
              {cafeteriaOpen ? 'Cafeteria Open' : 'Cafeteria Closed'}
            </button>
            <NotificationBell />
            <button
              onClick={() => {
                logout()
                navigate('/login')
              }}
              className="grid place-items-center w-10 h-10 rounded-full bg-slate-100 text-slate-500 hover:bg-rose-50 hover:text-rose-600 transition"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-1 overflow-x-auto no-scrollbar">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-bold border-b-2 transition shrink-0 ${
                tab === key ? 'border-brand-600 text-brand-700' : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {tab === 'overview' && <OverviewTab />}
        {tab === 'menu' && <MenuTab />}
        {tab === 'orders' && <OrdersTab />}
      </main>
    </div>
  )
}
