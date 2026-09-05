import { Package, Utensils, Clock, CalendarClock } from 'lucide-react'
import type { Order } from '../../types'
import { formatINR, formatTime } from '../../lib/format'
import { useDataStore } from '../../store/useDataStore'

const NEXT_ACTION: Partial<Record<Order['status'], { label: string; next: Order['status'] }>> = {
  new: { label: 'ACCEPT', next: 'accepted' },
  accepted: { label: 'START PREPARING', next: 'preparing' },
  preparing: { label: 'MARK READY', next: 'ready' },
  ready: { label: 'COMPLETED', next: 'completed' },
}

export function StaffOrderCard({ order }: { order: Order }) {
  const updateOrderStatus = useDataStore((s) => s.updateOrderStatus)
  const action = NEXT_ACTION[order.status]
  const isScheduledFuture = order.pickupMode === 'scheduled' && order.pickupTime > Date.now()

  return (
    <div className="rounded-2xl bg-white ring-1 ring-slate-100 shadow-sm shadow-slate-200/50 p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="font-display font-extrabold text-lg text-slate-900">#{order.token}</p>
        <span className="text-[10px] font-bold uppercase tracking-wide bg-emerald-50 text-emerald-600 rounded-full px-2 py-1">
          PAID ✓
        </span>
      </div>

      <div className="mt-2 space-y-0.5">
        {order.items.map((line) => (
          <p key={line.foodId} className="text-sm text-slate-600">
            {line.name} <span className="text-slate-400">× {line.qty}</span>
          </p>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-1.5 mt-3">
        <Tag icon={order.orderType === 'parcel' ? <Package size={11} /> : <Utensils size={11} />}>
          {order.orderType === 'parcel' ? 'Parcel' : 'Eat In'}
        </Tag>
        <Tag icon={<Clock size={11} />}>{formatTime(order.createdAt)}</Tag>
        {order.pickupMode === 'scheduled' && (
          <Tag icon={<CalendarClock size={11} />} highlight={isScheduledFuture}>
            Pickup {formatTime(order.pickupTime)}
          </Tag>
        )}
      </div>

      <div className="flex items-center justify-between mt-3.5">
        <span className="font-display font-bold text-slate-900">{formatINR(order.total)}</span>
        {action && (
          <button
            onClick={() => updateOrderStatus(order.id, action.next)}
            className="rounded-full bg-brand-600 text-white text-xs font-bold px-4 py-2 hover:bg-brand-700 transition active:scale-95"
          >
            {action.label}
          </button>
        )}
        {order.status === 'completed' && (
          <span className="text-xs font-bold text-slate-400">Collected</span>
        )}
      </div>
    </div>
  )
}

function Tag({ children, icon, highlight }: { children: React.ReactNode; icon: React.ReactNode; highlight?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold ${
        highlight ? 'bg-accent-500/10 text-accent-600' : 'bg-slate-100 text-slate-500'
      }`}
    >
      {icon}
      {children}
    </span>
  )
}
