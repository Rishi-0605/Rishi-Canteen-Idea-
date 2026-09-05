import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ClipboardList, Wallet, Calculator, Flame, Clock } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { StatCard } from '../../components/StatCard'
import { computeAdminStats, popularItemsChartData, salesByHourChartData } from '../../lib/analytics'
import { formatINR } from '../../lib/format'

export function OverviewTab() {
  const orders = useDataStore((s) => s.orders)
  const stats = computeAdminStats(orders)
  const popularData = popularItemsChartData(stats.itemCounts)
  const hourlyData = salesByHourChartData(stats.hourCounts)

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-8">
        <StatCard icon={ClipboardList} label="Today's Orders" value={String(stats.todayOrders)} />
        <StatCard icon={Wallet} label="Today's Revenue" value={formatINR(stats.revenue)} tone="green" />
        <StatCard icon={Calculator} label="Avg Order Value" value={formatINR(stats.aov)} tone="accent" />
        <StatCard icon={Flame} label="Most Ordered" value={stats.mostOrdered} tone="accent" />
        <StatCard icon={Clock} label="Peak Time" value={stats.peakLabel} tone="brand" />
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        <div className="rounded-2xl bg-white ring-1 ring-slate-100 p-5">
          <h3 className="font-display font-bold text-slate-900 mb-1">Popular Items Today</h3>
          <p className="text-xs text-slate-400 mb-4">Units sold, based on today's paid orders</p>
          {popularData.length === 0 ? (
            <ChartEmpty />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={popularData} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef1f7" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} interval={0} angle={-20} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} allowDecimals={false} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: 12, border: '1px solid #eef1f7', fontSize: 12 }} />
                <Bar dataKey="qty" fill="#2f5df5" radius={[8, 8, 0, 0]} maxBarSize={36} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-2xl bg-white ring-1 ring-slate-100 p-5">
          <h3 className="font-display font-bold text-slate-900 mb-1">Orders by Hour</h3>
          <p className="text-xs text-slate-400 mb-4">Peak ordering time helps plan staffing</p>
          {hourlyData.every((d) => d.orders === 0) ? (
            <ChartEmpty />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={hourlyData} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef1f7" />
                <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} allowDecimals={false} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: 12, border: '1px solid #eef1f7', fontSize: 12 }} />
                <Bar dataKey="orders" fill="#ff9d2e" radius={[8, 8, 0, 0]} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

function ChartEmpty() {
  return (
    <div className="h-[260px] grid place-items-center text-center">
      <p className="text-sm text-slate-400">No orders yet today.<br />Charts will populate as orders come in.</p>
    </div>
  )
}
