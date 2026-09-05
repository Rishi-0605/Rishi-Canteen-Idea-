import type { Order } from '../types'

const ACTIVE: Order['status'][] = ['new', 'accepted', 'preparing']

// A stable-but-slowly-changing baseline so the "live queue" feels alive
// even before any real demo orders exist. Recomputed every 10 minutes.
function baselineQueue() {
  const bucket = Math.floor(Date.now() / (10 * 60_000))
  const pseudo = Math.abs(Math.sin(bucket) * 10000) % 1
  return 10 + Math.floor(pseudo * 18)
}

export function getQueueStats(orders: Order[]) {
  const activeReal = orders.filter((o) => ACTIVE.includes(o.status)).length
  const totalQueue = baselineQueue() + activeReal
  const waitMinutes = Math.max(4, Math.round(totalQueue * 0.35))
  return { totalQueue, waitMinutes }
}

export function getOrderPosition(orders: Order[], order: Order) {
  if (!ACTIVE.includes(order.status)) return 0
  const ahead = orders.filter((o) => ACTIVE.includes(o.status) && o.createdAt < order.createdAt).length
  return baselineQueue() % 6 + ahead + 1
}
