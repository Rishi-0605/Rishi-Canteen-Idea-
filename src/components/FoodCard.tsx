import { Minus, Plus } from 'lucide-react'
import type { FoodItem } from '../types'
import { VegBadge } from './VegBadge'
import { formatINR } from '../lib/format'
import { useSessionStore } from '../store/useSessionStore'
import { useNavigate } from 'react-router-dom'

export function FoodCard({ item, layout = 'grid' }: { item: FoodItem; layout?: 'grid' | 'row' }) {
  const cart = useSessionStore((s) => s.cart)
  const addToCart = useSessionStore((s) => s.addToCart)
  const updateCartQty = useSessionStore((s) => s.updateCartQty)
  const navigate = useNavigate()

  const line = cart.find((c) => c.foodId === item.id)
  const qty = line?.qty ?? 0

  if (layout === 'row') {
    return (
      <div
        className="group flex gap-3.5 rounded-2xl bg-white p-3 shadow-sm shadow-slate-200/60 ring-1 ring-slate-100 transition hover:shadow-md hover:-translate-y-0.5"
      >
        <button
          onClick={() => navigate(`/app/food/${item.id}`)}
          className={`relative shrink-0 w-24 h-24 rounded-xl bg-gradient-to-br ${item.gradient} grid place-items-center text-4xl overflow-hidden`}
        >
          {item.emoji}
          {!item.available && (
            <span className="absolute inset-0 bg-white/70 backdrop-blur-[1px] grid place-items-center text-[10px] font-bold uppercase tracking-wide text-slate-600">
              Sold Out
            </span>
          )}
        </button>
        <div className="flex-1 min-w-0 flex flex-col">
          <div className="flex items-start justify-between gap-2">
            <button onClick={() => navigate(`/app/food/${item.id}`)} className="text-left min-w-0">
              <div className="flex items-center gap-1.5">
                <VegBadge veg={item.veg} />
                <h3 className="font-semibold text-slate-900 truncate">{item.name}</h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{item.description}</p>
            </button>
          </div>
          <div className="mt-auto flex items-center justify-between pt-2">
            <span className="font-display font-bold text-brand-800">{formatINR(item.price)}</span>
            <AddControl qty={qty} disabled={!item.available} onAdd={() => addToCart(item.id)} onChange={(q) => updateCartQty(item.id, q)} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="group flex flex-col rounded-2xl bg-white shadow-sm shadow-slate-200/60 ring-1 ring-slate-100 overflow-hidden transition hover:shadow-lg hover:-translate-y-1">
      <button
        onClick={() => navigate(`/app/food/${item.id}`)}
        className={`relative w-full aspect-[4/3] bg-gradient-to-br ${item.gradient} grid place-items-center text-5xl`}
      >
        {item.emoji}
        {item.popular && item.available && (
          <span className="absolute top-2 left-2 rounded-full bg-white/90 backdrop-blur px-2 py-0.5 text-[10px] font-bold text-accent-600 shadow-sm">
            🔥 Popular
          </span>
        )}
        {!item.available && (
          <span className="absolute inset-0 bg-white/70 backdrop-blur-[1px] grid place-items-center text-xs font-bold uppercase tracking-wide text-slate-600">
            Sold Out
          </span>
        )}
      </button>
      <div className="flex flex-1 flex-col p-3.5">
        <button onClick={() => navigate(`/app/food/${item.id}`)} className="text-left flex-1">
          <div className="flex items-center gap-1.5">
            <VegBadge veg={item.veg} />
            <h3 className="font-semibold text-slate-900 text-sm leading-tight">{item.name}</h3>
          </div>
          <p className="text-xs text-slate-500 mt-1 line-clamp-2 min-h-[2.2em]">{item.description}</p>
        </button>
        <div className="mt-2.5 flex items-center justify-between">
          <span className="font-display font-bold text-brand-800">{formatINR(item.price)}</span>
          <AddControl qty={qty} disabled={!item.available} onAdd={() => addToCart(item.id)} onChange={(q) => updateCartQty(item.id, q)} />
        </div>
      </div>
    </div>
  )
}

function AddControl({
  qty,
  disabled,
  onAdd,
  onChange,
}: {
  qty: number
  disabled?: boolean
  onAdd: () => void
  onChange: (q: number) => void
}) {
  if (disabled) {
    return (
      <span className="rounded-full bg-slate-100 px-3.5 py-1.5 text-xs font-semibold text-slate-400">Unavailable</span>
    )
  }
  if (qty === 0) {
    return (
      <button
        onClick={onAdd}
        className="rounded-full bg-brand-50 px-4 py-1.5 text-xs font-bold text-brand-700 ring-1 ring-brand-200 transition hover:bg-brand-600 hover:text-white hover:ring-brand-600 active:scale-95"
      >
        ADD
      </button>
    )
  }
  return (
    <div className="flex items-center gap-2 rounded-full bg-brand-600 px-1 py-1 text-white shadow-sm shadow-brand-600/30">
      <button
        onClick={() => onChange(qty - 1)}
        className="grid h-6 w-6 place-items-center rounded-full transition hover:bg-white/20 active:scale-90"
        aria-label="Decrease quantity"
      >
        <Minus size={13} />
      </button>
      <span className="min-w-[1.1rem] text-center text-xs font-bold tabular-nums">{qty}</span>
      <button
        onClick={() => onChange(qty + 1)}
        className="grid h-6 w-6 place-items-center rounded-full transition hover:bg-white/20 active:scale-90"
        aria-label="Increase quantity"
      >
        <Plus size={13} />
      </button>
    </div>
  )
}
