import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { CheckCircle2, Package, Utensils, Clock } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { formatINR, formatTimeShort } from '../../lib/format'

const STATUS_LABEL: Record<string, string> = {
  new: 'ORDER RECEIVED',
  accepted: 'ACCEPTED',
  preparing: 'PREPARING',
  ready: 'READY',
  completed: 'COMPLETED',
  cancelled: 'CANCELLED',
}

export function TokenScreen() {
  const { orderId } = useParams()
  const navigate = useNavigate()
  const order = useDataStore((s) => s.orders.find((o) => o.id === orderId))
  const [showSuccess, setShowSuccess] = useState(true)

  useEffect(() => {
    const t = setTimeout(() => setShowSuccess(false), 1400)
    return () => clearTimeout(t)
  }, [])

  if (!order) {
    return (
      <div className="p-8 text-center">
        <p className="text-slate-500">Order not found.</p>
        <button onClick={() => navigate('/app/home')} className="mt-3 text-brand-600 font-semibold text-sm">
          Back to Home
        </button>
      </div>
    )
  }

  if (showSuccess) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center px-6 text-center animate-fade-in">
        <div className="w-20 h-20 rounded-full bg-emerald-500 grid place-items-center text-white shadow-xl shadow-emerald-500/30 animate-pop">
          <CheckCircle2 size={40} />
        </div>
        <h1 className="font-display font-extrabold text-2xl text-slate-900 mt-5">Payment Successful ✓</h1>
        <p className="text-slate-400 text-sm mt-1.5">Generating your token…</p>
      </div>
    )
  }

  return (
    <div className="pb-10 max-w-md mx-auto px-4 sm:px-6">
      <div className="pt-8 text-center animate-slide-up">
        <p className="inline-flex items-center gap-1.5 text-emerald-600 font-bold text-sm bg-emerald-50 rounded-full px-3.5 py-1.5">
          <CheckCircle2 size={15} /> ORDER CONFIRMED
        </p>
      </div>

      <div className="mt-6 rounded-3xl bg-gradient-to-br from-brand-700 to-brand-900 text-white p-7 text-center shadow-xl shadow-brand-900/25 animate-slide-up">
        <p className="text-xs font-bold uppercase tracking-widest text-white/60">Your Token</p>
        <p className="font-display font-extrabold text-5xl mt-2 tracking-tight">#{order.token}</p>
        <div className="mt-5 bg-white rounded-2xl p-3 inline-block">
          <QRCodeSVG value={`IBS-CAFETERIA:${order.token}:${order.id}`} size={140} bgColor="#ffffff" fgColor="#0b1f5c" />
        </div>
        <p className="text-xs text-white/70 mt-4 max-w-[240px] mx-auto">
          Show this token / QR code at the cafeteria counter to collect your order.
        </p>
      </div>

      <div className="mt-5 rounded-2xl bg-white ring-1 ring-slate-100 p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display font-bold text-slate-900">Order</h2>
          <span className="text-[11px] font-bold uppercase tracking-wide text-brand-600 bg-brand-50 rounded-full px-2.5 py-1">
            {STATUS_LABEL[order.status]}
          </span>
        </div>
        <div className="space-y-1.5">
          {order.items.map((line) => (
            <div key={line.foodId} className="flex justify-between text-sm">
              <span className="text-slate-600">
                {line.name} × {line.qty}
              </span>
              <span className="font-semibold text-slate-800">{formatINR(line.price * line.qty)}</span>
            </div>
          ))}
        </div>
        <div className="h-px bg-slate-100 my-3" />
        <div className="flex justify-between font-display font-bold text-slate-900 mb-4">
          <span>Total Paid</span>
          <span>{formatINR(order.total)}</span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <InfoTile
            icon={order.orderType === 'parcel' ? <Package size={16} /> : <Utensils size={16} />}
            label="Order Type"
            value={order.orderType === 'parcel' ? 'Parcel' : 'Eat In'}
          />
          <InfoTile
            icon={<Clock size={16} />}
            label={order.pickupMode === 'scheduled' ? 'Scheduled Pickup' : 'Est. Preparation'}
            value={order.pickupMode === 'scheduled' ? formatTimeShort(order.pickupTime) : '8–10 minutes'}
          />
        </div>
      </div>

      <button
        onClick={() => navigate(`/app/orders/${order.id}`)}
        className="mt-5 w-full rounded-2xl bg-brand-600 text-white font-bold text-sm py-4 shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 active:scale-[0.98]"
      >
        TRACK MY ORDER
      </button>
      <button onClick={() => navigate('/app/home')} className="mt-3 w-full text-center text-sm font-semibold text-slate-400 py-2">
        Back to Home
      </button>
    </div>
  )
}

function InfoTile({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <div className="flex items-center gap-1.5 text-slate-400 text-[11px] font-semibold mb-1">
        {icon}
        {label}
      </div>
      <p className="text-sm font-bold text-slate-900">{value}</p>
    </div>
  )
}
