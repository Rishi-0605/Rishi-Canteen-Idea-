import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ClipboardList, Timer, Flame, CheckCircle2, Wallet, LogOut, Power } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { useSessionStore } from '../../store/useSessionStore'
import { StatCard } from '../../components/StatCard'
import { StaffOrderCard } from '../../components/staff/StaffOrderCard'
import { NotificationBell } from '../../components/NotificationBell'
import { EmptyState } from '../../components/EmptyState'
import { computeStaffStats } from '../../lib/analytics'
import { formatINR, formatTime } from '../../lib/format'
import type { Order } from '../../types'

export function StaffDashboard() {
  const navigate = useNavigate()
  const orders = useDataStore((s) => s.orders)
  const cafeteriaOpen = useDataStore((s) => s.cafeteriaOpen)
  const setCafeteriaOpen = useDataStore((s) => s.setCafeteriaOpen)
  const logout = useSessionStore((s) => s.logout)

  const stats = computeStaffStats(orders)

  const columns = useMemo(() => {
    const byStatus = (statuses: Order['status'][]) =>
      orders
        .filter((o) => statuses.includes(o.status))
        .sort((a, b) => b.createdAt - a.createdAt)
    return [
      { title: 'NEW', statuses: ['new', 'accepted'] as Order['status'][], items: byStatus(['new', 'accepted']) },
      { title: 'PREPARING', statuses: ['preparing'] as Order['status'][], items: byStatus(['preparing']) },
      { title: 'READY', statuses: ['ready'] as Order['status'][], items: byStatus(['ready']) },
      { title: 'COMPLETED', statuses: ['completed'] as Order['status'][], items: byStatus(['completed']).slice(0, 12) },
    ]
  }, [orders])

  const scheduled = useMemo(
    () =>
      orders
        .filter((o) => o.pickupMode === 'scheduled' && !['completed', 'cancelled'].includes(o.status))
        .sort((a, b) => a.pickupTime - b.pickupTime),
    [orders],
  )

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-100 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wide text-slate-400">IBS Cafeteria</p>
            <h1 className="font-display font-extrabold text-xl text-slate-900">Staff Dashboard</h1>
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
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <button
          onClick={() => setCafeteriaOpen(!cafeteriaOpen)}
          className={`sm:hidden mb-4 w-full flex items-center justify-center gap-1.5 rounded-2xl px-4 py-3 text-sm font-bold ${
            cafeteriaOpen ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
          }`}
        >
          <Power size={15} />
          {cafeteriaOpen ? 'Cafeteria is Open' : 'Cafeteria is Closed'}
        </button>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
          <StatCard icon={ClipboardList} label="Today's Orders" value={String(stats.todayOrders)} />
          <StatCard icon={Timer} label="Pending" value={String(stats.pending)} tone="accent" />
          <StatCard icon={Flame} label="Preparing" value={String(stats.preparing)} tone="accent" />
          <StatCard icon={CheckCircle2} label="Ready" value={String(stats.ready)} tone="green" />
          <StatCard icon={CheckCircle2} label="Completed" value={String(stats.completedToday)} />
          <StatCard icon={Wallet} label="Today's Sales" value={formatINR(stats.salesToday)} tone="green" />
        </div>

        {scheduled.length > 0 && (
          <div className="mb-8">
            <h2 className="font-display font-bold text-slate-900 mb-3">Scheduled Orders</h2>
            <div className="flex gap-3 overflow-x-auto no-scrollbar pb-1">
              {scheduled.map((o) => (
                <div key={o.id} className="shrink-0 w-64 rounded-2xl bg-white ring-1 ring-accent-500/30 p-4">
                  <div className="flex items-center justify-between">
                    <p className="font-display font-bold text-slate-900">#{o.token}</p>
                    <span className="text-[10px] font-bold uppercase text-accent-600 bg-accent-500/10 rounded-full px-2 py-1">
                      Pickup {formatTime(o.pickupTime)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2 truncate">
                    {o.items.map((l) => `${l.name} × ${l.qty}`).join(', ')}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid lg:grid-cols-4 gap-5">
          {columns.map((col) => (
            <div key={col.title} className="min-w-0">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-display font-bold text-sm tracking-wide text-slate-700">{col.title}</h3>
                <span className="text-xs font-bold text-slate-400 bg-slate-100 rounded-full px-2 py-0.5">
                  {col.items.length}
                </span>
              </div>
              <div className="space-y-3 lg:max-h-[calc(100vh-260px)] lg:overflow-y-auto lg:pr-1">
                {col.items.length === 0 ? (
                  <EmptyState emoji="📭" title="No orders" />
                ) : (
                  col.items.map((order) => <StaffOrderCard key={order.id} order={order} />)
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
