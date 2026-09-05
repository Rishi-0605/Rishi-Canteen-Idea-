import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Minus, Plus, Trash2, Utensils, Package, Zap, CalendarClock } from 'lucide-react'
import { useSessionStore } from '../../store/useSessionStore'
import { useDataStore } from '../../store/useDataStore'
import { EmptyState } from '../../components/EmptyState'
import { formatINR, minutesFromNow, formatTimeShort } from '../../lib/format'

const PRESETS = [10, 15, 20, 30]
const TAX_RATE = 0.05

export function Cart() {
  const navigate = useNavigate()
  const cart = useSessionStore((s) => s.cart)
  const menu = useDataStore((s) => s.menu)
  const updateCartQty = useSessionStore((s) => s.updateCartQty)
  const removeFromCart = useSessionStore((s) => s.removeFromCart)
  const orderType = useSessionStore((s) => s.orderType)
  const setOrderType = useSessionStore((s) => s.setOrderType)
  const pickupMode = useSessionStore((s) => s.pickupMode)
  const scheduledTime = useSessionStore((s) => s.scheduledTime)
  const setPickup = useSessionStore((s) => s.setPickup)
  const cafeteriaOpen = useDataStore((s) => s.cafeteriaOpen)

  const [customMinutes, setCustomMinutes] = useState(15)

  const lines = useMemo(
    () =>
      cart
        .map((c) => {
          const item = menu.find((m) => m.id === c.foodId)
          return item ? { ...c, item } : null
        })
        .filter(Boolean) as { foodId: string; qty: number; item: (typeof menu)[number] }[],
    [cart, menu],
  )

  const subtotal = lines.reduce((sum, l) => sum + l.item.price * l.qty, 0)
  const tax = Math.round(subtotal * TAX_RATE)
  const total = subtotal + tax

  if (lines.length === 0) {
    return (
      <div className="pt-16">
        <EmptyState
          emoji="🛒"
          title="Your cart is waiting for something delicious."
          subtitle="Browse the menu and add your favourite items."
          action={
            <button
              onClick={() => navigate('/app/home')}
              className="rounded-xl bg-brand-600 text-white font-bold text-sm px-6 py-3 shadow-lg shadow-brand-600/25"
            >
              Browse Menu
            </button>
          }
        />
      </div>
    )
  }

  return (
    <div className="pb-8">
      <header className="px-4 sm:px-6 lg:px-8 pt-6 pb-4">
        <h1 className="font-display font-extrabold text-xl text-slate-900">Your Cart</h1>
        <p className="text-sm text-slate-400 mt-0.5">{lines.length} item{lines.length > 1 ? 's' : ''} selected</p>
      </header>

      {!cafeteriaOpen && (
        <div className="mx-4 sm:mx-6 lg:mx-8 mb-4 rounded-2xl bg-amber-50 ring-1 ring-amber-200 text-amber-700 text-sm font-semibold px-4 py-3">
          ⚠️ The cafeteria is currently closed. You can still build your cart, but payment is disabled until it reopens.
        </div>
      )}

      <div className="px-4 sm:px-6 lg:px-8 space-y-3">
        {lines.map(({ foodId, qty, item }) => (
          <div key={foodId} className="flex items-center gap-3.5 rounded-2xl bg-white ring-1 ring-slate-100 shadow-sm shadow-slate-200/50 p-3">
            <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${item.gradient} grid place-items-center text-3xl shrink-0`}>
              {item.emoji}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-slate-900 text-sm truncate">{item.name}</p>
              <p className="text-xs text-slate-400 mt-0.5">{formatINR(item.price)} each</p>
            </div>
            <div className="flex items-center gap-2.5 rounded-full bg-slate-100 px-1 py-1">
              <button
                onClick={() => (qty === 1 ? removeFromCart(foodId) : updateCartQty(foodId, qty - 1))}
                className="grid place-items-center w-7 h-7 rounded-full bg-white shadow-sm text-slate-600 active:scale-90 transition"
              >
                <Minus size={13} />
              </button>
              <span className="w-5 text-center text-sm font-bold text-slate-900">{qty}</span>
              <button
                onClick={() => updateCartQty(foodId, qty + 1)}
                className="grid place-items-center w-7 h-7 rounded-full bg-white shadow-sm text-slate-600 active:scale-90 transition"
              >
                <Plus size={13} />
              </button>
            </div>
            <div className="text-right w-16 shrink-0">
              <p className="font-display font-bold text-sm text-slate-900">{formatINR(item.price * qty)}</p>
              <button onClick={() => removeFromCart(foodId)} className="text-rose-400 hover:text-rose-600 mt-1 inline-flex">
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="px-4 sm:px-6 lg:px-8 mt-6">
        <h2 className="font-display font-bold text-slate-900 mb-3">Order Type</h2>
        <div className="grid grid-cols-2 gap-3">
          <OptionCard
            active={orderType === 'eat-in'}
            icon={<Utensils size={18} />}
            label="Eat In"
            onClick={() => setOrderType('eat-in')}
          />
          <OptionCard
            active={orderType === 'parcel'}
            icon={<Package size={18} />}
            label="Parcel"
            onClick={() => setOrderType('parcel')}
          />
        </div>
        <p className="text-xs text-slate-400 mt-2.5">
          {orderType === 'parcel'
            ? 'Your order will be packed for takeaway.'
            : 'Please collect your order and enjoy it in the cafeteria.'}
        </p>
      </div>

      <div className="px-4 sm:px-6 lg:px-8 mt-6">
        <h2 className="font-display font-bold text-slate-900 mb-3">Pickup</h2>
        <div className="grid grid-cols-2 gap-3">
          <OptionCard
            active={pickupMode === 'asap'}
            icon={<Zap size={18} />}
            label="ASAP"
            onClick={() => setPickup('asap')}
          />
          <OptionCard
            active={pickupMode === 'scheduled'}
            icon={<CalendarClock size={18} />}
            label="Schedule Pickup"
            onClick={() => setPickup('scheduled', minutesFromNow(customMinutes))}
          />
        </div>

        {pickupMode === 'scheduled' && (
          <div className="mt-3.5 rounded-2xl bg-white ring-1 ring-slate-100 p-4 animate-slide-up">
            <p className="text-xs font-semibold text-slate-500 mb-2.5">
              Perfect for ordering before your break. Pick a time and skip the line.
            </p>
            <div className="flex flex-wrap gap-2">
              {PRESETS.map((m) => (
                <button
                  key={m}
                  onClick={() => {
                    setCustomMinutes(m)
                    setPickup('scheduled', minutesFromNow(m))
                  }}
                  className={`rounded-full px-3.5 py-2 text-xs font-bold transition ${
                    customMinutes === m
                      ? 'bg-brand-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  in {m} min
                </button>
              ))}
            </div>
            <p className="text-sm font-bold text-brand-700 mt-3">
              Pickup at {scheduledTime ? formatTimeShort(scheduledTime) : formatTimeShort(minutesFromNow(customMinutes))}
            </p>
          </div>
        )}
      </div>

      <div className="px-4 sm:px-6 lg:px-8 mt-7">
        <div className="rounded-2xl bg-white ring-1 ring-slate-100 p-5 space-y-2">
          <Row label="Subtotal" value={formatINR(subtotal)} />
          <Row label="Taxes & charges (5%)" value={formatINR(tax)} />
          <div className="h-px bg-slate-100 my-1" />
          <Row label="Total" value={formatINR(total)} bold />
        </div>

        <button
          onClick={() => navigate('/app/payment')}
          disabled={!cafeteriaOpen}
          className="mt-4 w-full rounded-2xl bg-brand-600 disabled:bg-slate-300 text-white font-bold text-sm py-4 shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 active:scale-[0.98]"
        >
          PROCEED TO PAYMENT · {formatINR(total)}
        </button>
      </div>
    </div>
  )
}

function OptionCard({ active, icon, label, onClick }: { active: boolean; icon: React.ReactNode; label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-2 rounded-2xl py-4 transition ring-1 ${
        active ? 'bg-brand-50 ring-brand-300 text-brand-700' : 'bg-white ring-slate-100 text-slate-500 hover:ring-slate-200'
      }`}
    >
      {icon}
      <span className="text-sm font-bold">{label}</span>
    </button>
  )
}

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className={`text-sm ${bold ? 'font-bold text-slate-900' : 'text-slate-500'}`}>{label}</span>
      <span className={`${bold ? 'font-display font-extrabold text-lg text-slate-900' : 'text-sm font-semibold text-slate-700'}`}>
        {value}
      </span>
    </div>
  )
}
