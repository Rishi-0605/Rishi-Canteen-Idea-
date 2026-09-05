import { useMemo, useState } from 'react'
import { useDataStore } from '../../store/useDataStore'
import { EmptyState } from '../../components/EmptyState'
import { formatINR, formatTime } from '../../lib/format'
import type { Order } from '../../types'

const FILTERS: { key: 'all' | Order['status']; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'new', label: 'New' },
  { key: 'accepted', label: 'Accepted' },
  { key: 'preparing', label: 'Preparing' },
  { key: 'ready', label: 'Ready' },
  { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' },
]

const STATUS_TONE: Record<Order['status'], string> = {
  new: 'bg-slate-100 text-slate-600',
  accepted: 'bg-brand-50 text-brand-700',
  preparing: 'bg-amber-50 text-amber-700',
  ready: 'bg-emerald-50 text-emerald-700',
  completed: 'bg-slate-100 text-slate-500',
  cancelled: 'bg-rose-50 text-rose-600',
}

export function OrdersTab() {
  const orders = useDataStore((s) => s.orders)
  const [filter, setFilter] = useState<'all' | Order['status']>('all')

  const filtered = useMemo(() => {
    const list = filter === 'all' ? orders : orders.filter((o) => o.status === filter)
    return [...list].sort((a, b) => b.createdAt - a.createdAt)
  }, [orders, filter])

  return (
    <div>
      <div className="flex gap-2 overflow-x-auto no-scrollbar mb-5">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`shrink-0 rounded-full px-4 py-2 text-xs font-bold transition ${
              filter === f.key ? 'bg-brand-600 text-white' : 'bg-white ring-1 ring-slate-200 text-slate-600'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState emoji="🧾" title="No orders" subtitle="Orders will appear here as students place them." />
      ) : (
        <div className="rounded-2xl bg-white ring-1 ring-slate-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[720px]">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs font-bold uppercase tracking-wide text-slate-400">
                  <th className="px-4 py-3">Token</th>
                  <th className="px-4 py-3">Items</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Total</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((o) => (
                  <tr key={o.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                    <td className="px-4 py-3 font-display font-bold text-slate-900">#{o.token}</td>
                    <td className="px-4 py-3 text-slate-500 max-w-xs truncate">
                      {o.items.map((l) => `${l.name} × ${l.qty}`).join(', ')}
                    </td>
                    <td className="px-4 py-3 text-slate-500 capitalize">{o.orderType.replace('-', ' ')}</td>
                    <td className="px-4 py-3 text-slate-500">{formatTime(o.createdAt)}</td>
                    <td className="px-4 py-3 font-semibold text-slate-800">{formatINR(o.total)}</td>
                    <td className="px-4 py-3">
                      <span className={`text-[11px] font-bold uppercase rounded-full px-2.5 py-1 ${STATUS_TONE[o.status]}`}>
                        {o.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
