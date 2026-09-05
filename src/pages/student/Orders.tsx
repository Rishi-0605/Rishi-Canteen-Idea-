import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { RotateCcw, ChevronRight } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { useSessionStore } from '../../store/useSessionStore'
import { EmptyState } from '../../components/EmptyState'
import { formatINR, formatTime } from '../../lib/format'
import type { Order } from '../../types'

const ACTIVE_STATUSES: Order['status'][] = ['new', 'accepted', 'preparing', 'ready']

const STATUS_META: Record<Order['status'], { label: string; tone: string }> = {
  new: { label: 'New', tone: 'bg-slate-100 text-slate-600' },
  accepted: { label: 'Accepted', tone: 'bg-brand-50 text-brand-700' },
  preparing: { label: 'Preparing', tone: 'bg-amber-50 text-amber-700' },
  ready: { label: 'Ready', tone: 'bg-emerald-50 text-emerald-700' },
  completed: { label: 'Completed', tone: 'bg-slate-100 text-slate-500' },
  cancelled: { label: 'Cancelled', tone: 'bg-rose-50 text-rose-600' },
}

export function Orders() {
  const navigate = useNavigate()
  const allOrders = useDataStore((s) => s.orders)
  const menu = useDataStore((s) => s.menu)
  const student = useSessionStore((s) => s.student)
  const cart = useSessionStore((s) => s.cart)
  const setCart = useSessionStore((s) => s.setCart)
  const setOrderType = useSessionStore((s) => s.setOrderType)
  const [tab, setTab] = useState<'active' | 'history'>('active')

  function reorder(order: Order) {
    let next = [...cart]
    for (const line of order.items) {
      const menuItem = menu.find((m) => m.id === line.foodId)
      if (!menuItem || !menuItem.available) continue
      const existing = next.find((c) => c.foodId === line.foodId)
      next = existing
        ? next.map((c) => (c.foodId === line.foodId ? { ...c, qty: c.qty + line.qty } : c))
        : [...next, { foodId: line.foodId, qty: line.qty }]
    }
    setCart(next)
    setOrderType(order.orderType)
  }

  const mine = useMemo(
    () => allOrders.filter((o) => !student || o.studentId === student.studentId),
    [allOrders, student],
  )
  const active = mine.filter((o) => ACTIVE_STATUSES.includes(o.status))
  const history = mine.filter((o) => o.status === 'completed' || o.status === 'cancelled')
  const list = tab === 'active' ? active : history

  return (
    <div className="pb-8">
      <header className="px-4 sm:px-6 lg:px-8 pt-6 pb-4">
        <h1 className="font-display font-extrabold text-xl text-slate-900">My Orders</h1>
        <div className="flex gap-2 mt-4">
          <TabButton active={tab === 'active'} onClick={() => setTab('active')} label={`Active (${active.length})`} />
          <TabButton active={tab === 'history'} onClick={() => setTab('history')} label="History" />
        </div>
      </header>

      <div className="px-4 sm:px-6 lg:px-8 space-y-3.5">
        {list.length === 0 ? (
          <EmptyState
            emoji={tab === 'active' ? '🧾' : '📦'}
            title={tab === 'active' ? 'No active orders' : 'No orders yet.'}
            subtitle={tab === 'active' ? 'Place an order and track it here in real time.' : 'Your completed orders will show up here.'}
            action={
              <button onClick={() => navigate('/app/home')} className="rounded-xl bg-brand-600 text-white font-bold text-sm px-6 py-3">
                Order Now
              </button>
            }
          />
        ) : (
          list.map((order) => (
            <div
              key={order.id}
              className={`rounded-2xl bg-white ring-1 p-4 shadow-sm shadow-slate-200/50 transition ${
                order.status === 'ready' ? 'ring-emerald-300 animate-pulse-ring' : 'ring-slate-100'
              }`}
            >
              <button onClick={() => navigate(`/app/orders/${order.id}`)} className="w-full text-left">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-display font-extrabold text-slate-900">Token #{order.token}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{formatTime(order.createdAt)} · {order.orderType === 'parcel' ? 'Parcel' : 'Eat In'}</p>
                  </div>
                  <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full ${STATUS_META[order.status].tone}`}>
                    {STATUS_META[order.status].label}
                  </span>
                </div>
                <p className="text-sm text-slate-600 mt-2.5 truncate">
                  {order.items.map((l) => `${l.name} × ${l.qty}`).join(', ')}
                </p>
                <div className="flex items-center justify-between mt-3">
                  <span className="font-display font-bold text-slate-900">{formatINR(order.total)}</span>
                  <span className="flex items-center gap-1 text-xs font-bold text-brand-600">
                    {tab === 'active' ? 'Track Order' : 'View Details'} <ChevronRight size={14} />
                  </span>
                </div>
              </button>
              {tab === 'history' && order.status === 'completed' && (
                <button
                  onClick={() => {
                    reorder(order)
                    navigate('/app/cart')
                  }}
                  className="mt-3 w-full flex items-center justify-center gap-1.5 rounded-xl bg-brand-50 text-brand-700 font-bold text-xs py-2.5 hover:bg-brand-100 transition"
                >
                  <RotateCcw size={13} /> REORDER
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function TabButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-4 py-2 text-xs font-bold transition ${
        active ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-500'
      }`}
    >
      {label}
    </button>
  )
}
