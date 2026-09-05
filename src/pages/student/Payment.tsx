import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Smartphone, CreditCard, ShieldCheck, XCircle, Loader2 } from 'lucide-react'
import { useSessionStore } from '../../store/useSessionStore'
import { useDataStore } from '../../store/useDataStore'
import { formatINR } from '../../lib/format'
import type { PaymentMethod } from '../../types'

const METHODS: { id: PaymentMethod; label: string; hint: string; icon: React.ReactNode }[] = [
  { id: 'upi', label: 'UPI', hint: 'Pay via any UPI app', icon: <Smartphone size={18} /> },
  { id: 'gpay', label: 'Google Pay', hint: 'Fast & secure', icon: <Smartphone size={18} /> },
  { id: 'phonepe', label: 'PhonePe', hint: 'Fast & secure', icon: <Smartphone size={18} /> },
  { id: 'card', label: 'Credit / Debit Card', hint: 'Visa, Mastercard, RuPay', icon: <CreditCard size={18} /> },
]

const TAX_RATE = 0.05

export function Payment() {
  const navigate = useNavigate()
  const cart = useSessionStore((s) => s.cart)
  const orderType = useSessionStore((s) => s.orderType)
  const pickupMode = useSessionStore((s) => s.pickupMode)
  const scheduledTime = useSessionStore((s) => s.scheduledTime)
  const student = useSessionStore((s) => s.student)
  const clearCart = useSessionStore((s) => s.clearCart)
  const simulateFail = useSessionStore((s) => s.simulatePaymentFailure)
  const setSimulateFail = useSessionStore((s) => s.setSimulatePaymentFailure)
  const menu = useDataStore((s) => s.menu)
  const placeOrder = useDataStore((s) => s.placeOrder)

  const [method, setMethod] = useState<PaymentMethod>('upi')
  const [status, setStatus] = useState<'idle' | 'processing' | 'failed'>('idle')
  const [error, setError] = useState('')

  const lines = useMemo(
    () =>
      cart
        .map((c) => {
          const item = menu.find((m) => m.id === c.foodId)
          return item ? { qty: c.qty, item } : null
        })
        .filter(Boolean) as { qty: number; item: (typeof menu)[number] }[],
    [cart, menu],
  )
  const subtotal = lines.reduce((sum, l) => sum + l.item.price * l.qty, 0)
  const tax = Math.round(subtotal * TAX_RATE)
  const total = subtotal + tax

  if (lines.length === 0 && status === 'idle') {
    navigate('/app/cart', { replace: true })
    return null
  }

  function handlePay() {
    setStatus('processing')
    setError('')
    setTimeout(() => {
      const result = placeOrder({
        cart,
        studentId: student?.studentId ?? 'GUEST',
        studentName: student?.name ?? 'Student',
        orderType,
        pickupMode,
        scheduledTime,
        method,
        simulateFailure: simulateFail,
      })
      if (!result.ok) {
        setStatus('failed')
        setError(result.reason ?? 'Payment failed. Please try again.')
        return
      }
      clearCart()
      navigate(`/app/token/${result.order!.id}`, { replace: true })
    }, 1500)
  }

  return (
    <div className="pb-10 max-w-xl mx-auto">
      <header className="px-4 sm:px-6 lg:px-8 pt-6 pb-4 flex items-center gap-2">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 text-slate-500">
          <ArrowLeft size={20} />
        </button>
        <h1 className="font-display font-extrabold text-xl text-slate-900">Payment</h1>
      </header>

      <div className="px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-white ring-1 ring-slate-100 p-5 mb-5">
          <h2 className="font-display font-bold text-slate-900 mb-3">Order Summary</h2>
          <div className="space-y-1.5 mb-3">
            {lines.map(({ qty, item }) => (
              <div key={item.id} className="flex justify-between text-sm">
                <span className="text-slate-500">
                  {item.name} × {qty}
                </span>
                <span className="font-semibold text-slate-700">{formatINR(item.price * qty)}</span>
              </div>
            ))}
          </div>
          <div className="h-px bg-slate-100 mb-3" />
          <div className="flex justify-between text-sm text-slate-500 mb-1">
            <span>Subtotal</span>
            <span>{formatINR(subtotal)}</span>
          </div>
          <div className="flex justify-between text-sm text-slate-500 mb-2">
            <span>Taxes & charges</span>
            <span>{formatINR(tax)}</span>
          </div>
          <div className="flex justify-between font-display font-extrabold text-slate-900">
            <span>Total</span>
            <span>{formatINR(total)}</span>
          </div>
          <div className="flex gap-2 mt-3 text-xs font-semibold text-slate-400">
            <span className="rounded-full bg-slate-100 px-2.5 py-1 capitalize">{orderType.replace('-', ' ')}</span>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 capitalize">{pickupMode}</span>
          </div>
        </div>

        <h2 className="font-display font-bold text-slate-900 mb-3">Payment Method</h2>
        <div className="space-y-2.5 mb-3">
          {METHODS.map((m) => (
            <button
              key={m.id}
              onClick={() => setMethod(m.id)}
              className={`w-full flex items-center gap-3.5 rounded-2xl px-4 py-3.5 ring-1 transition ${
                method === m.id ? 'bg-brand-50 ring-brand-300' : 'bg-white ring-slate-100 hover:ring-slate-200'
              }`}
            >
              <span className={`grid place-items-center w-10 h-10 rounded-xl ${method === m.id ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                {m.icon}
              </span>
              <span className="text-left flex-1">
                <p className="text-sm font-bold text-slate-900">{m.label}</p>
                <p className="text-xs text-slate-400">{m.hint}</p>
              </span>
              <span
                className={`w-5 h-5 rounded-full border-2 grid place-items-center ${method === m.id ? 'border-brand-600' : 'border-slate-200'}`}
              >
                {method === m.id && <span className="w-2.5 h-2.5 rounded-full bg-brand-600" />}
              </span>
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-400 flex items-center gap-1.5 mb-6">
          <ShieldCheck size={13} /> Cash is not accepted — this pilot requires pre-payment for every order.
        </p>

        {status === 'failed' && (
          <div className="mb-5 rounded-2xl bg-rose-50 ring-1 ring-rose-200 p-4 flex items-start gap-3 animate-slide-up">
            <XCircle className="text-rose-500 shrink-0 mt-0.5" size={18} />
            <div>
              <p className="text-sm font-bold text-rose-700">Payment Failed</p>
              <p className="text-xs text-rose-600 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        <button
          onClick={handlePay}
          disabled={status === 'processing'}
          className="w-full rounded-2xl bg-brand-600 text-white font-bold text-sm py-4 shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 active:scale-[0.98] disabled:opacity-70 flex items-center justify-center gap-2"
        >
          {status === 'processing' ? (
            <>
              <Loader2 size={16} className="animate-spin" /> Processing Payment…
            </>
          ) : (
            `PAY NOW · ${formatINR(total)}`
          )}
        </button>

        <label className="flex items-center gap-2 justify-center mt-4 text-[11px] text-slate-400 select-none">
          <input
            type="checkbox"
            checked={simulateFail}
            onChange={(e) => setSimulateFail(e.target.checked)}
            className="accent-brand-600"
          />
          Simulate a failed payment (for demo purposes)
        </label>
      </div>
    </div>
  )
}
