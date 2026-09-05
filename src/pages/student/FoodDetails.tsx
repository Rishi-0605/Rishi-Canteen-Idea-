import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Minus, Plus } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { useSessionStore } from '../../store/useSessionStore'
import { VegBadge } from '../../components/VegBadge'
import { formatINR } from '../../lib/format'

export function FoodDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const menu = useDataStore((s) => s.menu)
  const addToCart = useSessionStore((s) => s.addToCart)
  const cart = useSessionStore((s) => s.cart)
  const [qty, setQty] = useState(1)
  const [justAdded, setJustAdded] = useState(false)

  const item = menu.find((m) => m.id === id)

  if (!item) {
    return (
      <div className="p-8 text-center">
        <p className="text-slate-500">This item could not be found.</p>
        <button onClick={() => navigate('/app/home')} className="mt-3 text-brand-600 font-semibold text-sm">
          Back to Home
        </button>
      </div>
    )
  }

  const inCart = cart.find((c) => c.foodId === item.id)?.qty ?? 0

  function handleAdd() {
    addToCart(item!.id, qty)
    setJustAdded(true)
    setTimeout(() => setJustAdded(false), 1600)
  }

  return (
    <div className="pb-10">
      <div className={`relative w-full aspect-[5/4] sm:aspect-[16/9] bg-gradient-to-br ${item.gradient} grid place-items-center text-[7rem] sm:text-[9rem]`}>
        <button
          onClick={() => navigate(-1)}
          className="absolute top-5 left-4 sm:left-6 w-10 h-10 rounded-full bg-white/80 backdrop-blur grid place-items-center text-slate-700 shadow-sm"
        >
          <ArrowLeft size={18} />
        </button>
        <span className="animate-pop">{item.emoji}</span>
        {!item.available && (
          <span className="absolute inset-0 bg-white/70 backdrop-blur-[1px] grid place-items-center text-sm font-bold uppercase tracking-wide text-slate-600">
            Sold Out
          </span>
        )}
      </div>

      <div className="px-5 sm:px-8 max-w-2xl mx-auto -mt-6 relative">
        <div className="rounded-3xl bg-white shadow-lg shadow-slate-200/70 ring-1 ring-slate-100 p-5 sm:p-7">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <VegBadge veg={item.veg} size={16} />
                <span className="text-[11px] font-bold uppercase tracking-wide text-slate-400">{item.category}</span>
              </div>
              <h1 className="font-display font-extrabold text-2xl text-slate-900 mt-1.5">{item.name}</h1>
            </div>
            <span className="font-display font-extrabold text-xl text-brand-700 shrink-0">{formatINR(item.price)}</span>
          </div>

          <p className="text-sm text-slate-500 mt-3 leading-relaxed">"{item.description}"</p>

          <div className="flex flex-wrap gap-2 mt-4">
            {item.popular && <Tag label="🔥 Popular" />}
            {item.quickPickup && <Tag label="⚡ Quick Pickup" />}
            {item.recommended && <Tag label="⭐ Recommended" />}
          </div>

          <p className="text-[11px] text-slate-400 mt-4">Demo Price — for prototype purposes only.</p>

          {item.available ? (
            <>
              <div className="mt-6 flex items-center justify-between">
                <span className="text-sm font-bold text-slate-700">Quantity</span>
                <div className="flex items-center gap-4 rounded-full bg-slate-100 px-2 py-1.5">
                  <button
                    onClick={() => setQty((q) => Math.max(1, q - 1))}
                    className="grid place-items-center w-8 h-8 rounded-full bg-white shadow-sm text-slate-600 active:scale-90 transition"
                  >
                    <Minus size={15} />
                  </button>
                  <span className="w-6 text-center font-display font-bold text-slate-900">{qty}</span>
                  <button
                    onClick={() => setQty((q) => q + 1)}
                    className="grid place-items-center w-8 h-8 rounded-full bg-white shadow-sm text-slate-600 active:scale-90 transition"
                  >
                    <Plus size={15} />
                  </button>
                </div>
              </div>

              <button
                onClick={handleAdd}
                className={`mt-6 w-full rounded-2xl py-4 font-bold text-sm tracking-wide transition active:scale-[0.98] ${
                  justAdded ? 'bg-emerald-500 text-white' : 'bg-brand-600 text-white shadow-lg shadow-brand-600/30 hover:bg-brand-700'
                }`}
              >
                {justAdded ? 'ADDED TO CART ✓' : `ADD TO CART · ${formatINR(item.price * qty)}`}
              </button>
              {inCart > 0 && <p className="text-center text-xs text-slate-400 mt-2.5">{inCart} already in your cart</p>}
            </>
          ) : (
            <div className="mt-6 rounded-2xl bg-slate-100 text-slate-400 font-bold text-sm text-center py-4">
              Currently Sold Out
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Tag({ label }: { label: string }) {
  return <span className="text-[11px] font-bold text-brand-700 bg-brand-50 rounded-full px-2.5 py-1">{label}</span>
}
