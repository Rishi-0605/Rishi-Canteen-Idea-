import type { Order } from '../types'

export function isToday(ts: number) {
  const d = new Date(ts)
  const now = new Date()
  return d.getDate() === now.getDate() && d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
}

export function computeStaffStats(orders: Order[]) {
  const today = orders.filter((o) => isToday(o.createdAt))
  const pending = orders.filter((o) => o.status === 'new' || o.status === 'accepted').length
  const preparing = orders.filter((o) => o.status === 'preparing').length
  const ready = orders.filter((o) => o.status === 'ready').length
  const completedToday = today.filter((o) => o.status === 'completed').length
  const salesToday = today.filter((o) => o.status !== 'cancelled').reduce((sum, o) => sum + o.total, 0)
  return { todayOrders: today.length, pending, preparing, ready, completedToday, salesToday }
}

export function computeAdminStats(orders: Order[]) {
  const today = orders.filter((o) => isToday(o.createdAt) && o.status !== 'cancelled')
  const revenue = today.reduce((sum, o) => sum + o.total, 0)
  const aov = today.length ? Math.round(revenue / today.length) : 0

  const itemCounts = new Map<string, number>()
  for (const o of today) {
    for (const line of o.items) {
      itemCounts.set(line.name, (itemCounts.get(line.name) ?? 0) + line.qty)
    }
  }
  let mostOrdered = '—'
  let max = 0
  for (const [name, qty] of itemCounts) {
    if (qty > max) {
      max = qty
      mostOrdered = name
    }
  }

  const hourCounts = new Array(24).fill(0)
  for (const o of today) {
    hourCounts[new Date(o.createdAt).getHours()]++
  }
  let peakHour = 0
  let peakCount = 0
  hourCounts.forEach((c, h) => {
    if (c > peakCount) {
      peakCount = c
      peakHour = h
    }
  })
  const peakLabel = peakCount > 0 ? formatHourRange(peakHour) : '—'

  return { todayOrders: today.length, revenue, aov, mostOrdered, peakLabel, hourCounts, itemCounts }
}

function formatHourRange(h: number) {
  const label = (hh: number) => {
    const period = hh < 12 ? 'AM' : 'PM'
    const hour12 = hh % 12 === 0 ? 12 : hh % 12
    return `${hour12} ${period}`
  }
  return `${label(h)} – ${label((h + 1) % 24)}`
}

export function popularItemsChartData(itemCounts: Map<string, number>) {
  return Array.from(itemCounts.entries())
    .map(([name, qty]) => ({ name, qty }))
    .sort((a, b) => b.qty - a.qty)
    .slice(0, 6)
}

export function salesByHourChartData(hourCounts: number[]) {
  return hourCounts
    .map((count, hour) => ({ hour: `${hour}:00`, orders: count }))
    .filter((_, i) => i >= 7 && i <= 20)
}
