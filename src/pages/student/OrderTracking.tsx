import { useNavigate, useParams } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { ArrowLeft, Users, Clock } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { StatusTimeline } from '../../components/StatusTimeline'
import { formatINR, formatTime } from '../../lib/format'
import { getOrderPosition, getQueueStats } from '../../lib/queue'

export function OrderTracking() {
  const { orderId } = useParams()
  const navigate = useNavigate()
  const order = useDataStore((s) => s.orders.find((o) => o.id === orderId))
  const orders = useDataStore((s) => s.orders)
  const cancelOrder = useDataStore((s) => s.cancelOrder)

  if (!order) {
    return (
      <div className="p-8 text-center">
        <p className="text-slate-500">Order not found.</p>
        <button onClick={() => navigate('/app/orders')} className="mt-3 text-brand-600 font-semibold text-sm">
          Back to Orders
        </button>
      </div>
    )
  }

  const position = getOrderPosition(orders, order)
  const { waitMinutes } = getQueueStats(orders)
  const isActive = ['new', 'accepted', 'preparing', 'ready'].includes(order.status)

  return (
    <div className="pb-10 max-w-xl mx-auto">
      <header className="px-4 sm:px-6 lg:px-8 pt-6 pb-4 flex items-center gap-2">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 text-slate-500">
          <ArrowLeft size={20} />
        </button>
        <h1 className="font-display font-extrabold text-xl text-slate-900">Token #{order.token}</h1>
      </header>

      {order.status === 'ready' && (
        <div className="mx-4 sm:mx-6 lg:mx-8 mb-5 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 text-white p-5 text-center shadow-lg shadow-emerald-600/30 animate-slide-up">
          <p className="text-2xl mb-1">🔔</p>
          <p className="font-display font-extrabold text-lg">YOUR ORDER IS READY!</p>
          <p className="text-sm text-white/85 mt-1">Token #{order.token} is ready for pickup.</p>
        </div>
      )}

      {isActive && order.status !== 'ready' && (
        <div className="mx-4 sm:mx-6 lg:mx-8 mb-5 rounded-2xl bg-white ring-1 ring-slate-100 p-4 flex items-center gap-4">
          <div className="flex-1 text-center">
            <div className="flex items-center justify-center gap-1.5 text-slate-400 text-[11px] font-semibold mb-0.5">
              <Users size={12} /> Your Position
            </div>
            <p className="font-display font-extrabold text-lg text-slate-900">#{position}</p>
          </div>
          <div className="w-px h-8 bg-slate-100" />
          <div className="flex-1 text-center">
            <div className="flex items-center justify-center gap-1.5 text-slate-400 text-[11px] font-semibold mb-0.5">
              <Clock size={12} /> Est. Wait
            </div>
            <p className="font-display font-extrabold text-lg text-slate-900">{waitMinutes} min</p>
          </div>
        </div>
      )}

      <div className="px-4 sm:px-6 lg:px-8 grid sm:grid-cols-[1fr,auto] gap-5">
        <div className="rounded-2xl bg-white ring-1 ring-slate-100 p-5">
          <h2 className="font-display font-bold text-slate-900 mb-4">Order Status</h2>
          <StatusTimeline order={order} />
        </div>

        <div className="rounded-2xl bg-white ring-1 ring-slate-100 p-5 flex flex-col items-center justify-center sm:w-44">
          <QRCodeSVG value={`IBS-CAFETERIA:${order.token}:${order.id}`} size={112} fgColor="#0b1f5c" />
          <p className="text-[11px] text-slate-400 text-center mt-3">Show at counter to collect</p>
        </div>
      </div>

      <div className="px-4 sm:px-6 lg:px-8 mt-5">
        <div className="rounded-2xl bg-white ring-1 ring-slate-100 p-5">
          <h2 className="font-display font-bold text-slate-900 mb-3">Order Details</h2>
          <div className="space-y-1.5">
            {order.items.map((line) => (
              <div key={line.foodId} className="flex justify-between text-sm">
                <span className="text-slate-600">{line.name} × {line.qty}</span>
                <span className="font-semibold text-slate-800">{formatINR(line.price * line.qty)}</span>
              </div>
            ))}
          </div>
          <div className="h-px bg-slate-100 my-3" />
          <div className="flex justify-between font-display font-bold text-slate-900">
            <span>Total</span>
            <span>{formatINR(order.total)}</span>
          </div>
          <p className="text-xs text-slate-400 mt-3">Placed at {formatTime(order.createdAt)} · {order.orderType === 'parcel' ? 'Parcel' : 'Eat In'}</p>
        </div>
      </div>

      {order.status === 'new' && (
        <div className="px-4 sm:px-6 lg:px-8 mt-4">
          <button
            onClick={() => cancelOrder(order.id)}
            className="w-full rounded-2xl bg-rose-50 text-rose-600 font-bold text-sm py-3.5 hover:bg-rose-100 transition"
          >
            Cancel Order
          </button>
        </div>
      )}
    </div>
  )
}
