import { Check } from 'lucide-react'
import type { Order, OrderStatus } from '../types'
import { formatTime } from '../lib/format'

const STEPS: { key: OrderStatus; label: string }[] = [
  { key: 'new', label: 'Order Placed' },
  { key: 'accepted', label: 'Order Accepted' },
  { key: 'preparing', label: 'Preparing' },
  { key: 'ready', label: 'Ready' },
  { key: 'completed', label: 'Collected' },
]

const ORDER_RANK: Record<OrderStatus, number> = {
  new: 0,
  accepted: 1,
  preparing: 2,
  ready: 3,
  completed: 4,
  cancelled: -1,
}

export function StatusTimeline({ order }: { order: Order }) {
  const currentRank = ORDER_RANK[order.status]

  if (order.status === 'cancelled') {
    return (
      <div className="rounded-2xl bg-rose-50 ring-1 ring-rose-200 p-4 text-rose-700 text-sm font-medium">
        This order was cancelled.
      </div>
    )
  }

  return (
    <div>
      <TimelineRow
        label="Payment Confirmed"
        done
        at={order.createdAt}
        isFirst
      />
      {STEPS.map((step, i) => {
        const rank = ORDER_RANK[step.key]
        const done = rank <= currentRank
        const active = rank === currentRank
        const event = order.history.find((h) => h.status === step.key)
        return (
          <TimelineRow
            key={step.key}
            label={step.label}
            done={done}
            active={active}
            at={event?.at}
            isLast={i === STEPS.length - 1}
          />
        )
      })}
    </div>
  )
}

function TimelineRow({
  label,
  done,
  active,
  at,
  isFirst,
  isLast,
}: {
  label: string
  done: boolean
  active?: boolean
  at?: number
  isFirst?: boolean
  isLast?: boolean
}) {
  return (
    <div className="flex gap-3.5">
      <div className="flex flex-col items-center">
        <div
          className={`grid place-items-center w-7 h-7 rounded-full shrink-0 transition-all ${
            done
              ? 'bg-brand-600 text-white'
              : active
                ? 'bg-white text-brand-600 ring-2 ring-brand-500 animate-pulse-ring'
                : 'bg-slate-100 text-slate-300 ring-1 ring-slate-200'
          }`}
        >
          {done && !active ? <Check size={15} strokeWidth={3} /> : <span className="w-2 h-2 rounded-full bg-current" />}
        </div>
        {!isLast && <div className={`w-0.5 flex-1 min-h-[28px] ${done ? 'bg-brand-500' : 'bg-slate-200'}`} />}
      </div>
      <div className={`${isFirst ? '' : 'pb-6'} pt-0.5`}>
        <p className={`text-sm font-semibold ${done || active ? 'text-slate-900' : 'text-slate-400'}`}>{label}</p>
        {at && <p className="text-xs text-slate-400 mt-0.5">{formatTime(at)}</p>}
        {active && !at && <p className="text-xs text-brand-600 font-medium mt-0.5">In progress…</p>}
      </div>
    </div>
  )
}
