export function formatINR(amount: number) {
  return `₹${amount.toFixed(amount % 1 === 0 ? 0 : 2)}`
}

export function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' })
}

export function formatTimeShort(ts: number) {
  return new Date(ts).toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit', hour12: true })
}

export function formatRelative(ts: number) {
  const diff = Date.now() - ts
  const min = Math.floor(diff / 60000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min} min ago`
  const hr = Math.floor(min / 60)
  return `${hr} hr ago`
}

export function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good Morning'
  if (h < 17) return 'Good Afternoon'
  return 'Good Evening'
}

export function minutesFromNow(mins: number) {
  return Date.now() + mins * 60_000
}
