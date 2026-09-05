import { Users, Clock } from 'lucide-react'
import { useDataStore } from '../store/useDataStore'
import { getQueueStats } from '../lib/queue'

export function LiveQueueCard() {
  const orders = useDataStore((s) => s.orders)
  const { totalQueue, waitMinutes } = getQueueStats(orders)

  return (
    <div className="mx-4 sm:mx-6 lg:mx-8 rounded-2xl bg-gradient-to-r from-brand-700 to-brand-900 text-white p-4 flex items-center gap-4 shadow-lg shadow-brand-900/20 relative overflow-hidden">
      <div className="absolute -right-8 -top-8 w-28 h-28 rounded-full bg-white/5" />
      <div className="flex items-center gap-1.5 relative">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
        </span>
        <span className="text-[10px] font-bold uppercase tracking-wide text-white/70">Live</span>
      </div>
      <div className="flex-1 flex items-center justify-around relative">
        <div className="text-center">
          <div className="flex items-center justify-center gap-1.5 text-white/70 text-[11px] font-semibold mb-0.5">
            <Users size={12} /> Current Orders
          </div>
          <p className="font-display font-extrabold text-lg leading-none">{totalQueue}</p>
        </div>
        <div className="w-px h-8 bg-white/15" />
        <div className="text-center">
          <div className="flex items-center justify-center gap-1.5 text-white/70 text-[11px] font-semibold mb-0.5">
            <Clock size={12} /> Est. Wait
          </div>
          <p className="font-display font-extrabold text-lg leading-none">{waitMinutes} min</p>
        </div>
      </div>
    </div>
  )
}
