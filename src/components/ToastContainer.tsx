import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, Info, AlertTriangle, XCircle, X } from 'lucide-react'
import { useDataStore } from '../store/useDataStore'
import type { Notification } from '../store/useDataStore'
import { useSessionStore } from '../store/useSessionStore'

const ICONS = { success: CheckCircle2, info: Info, warning: AlertTriangle, error: XCircle }
const TONES = {
  success: 'text-emerald-600 bg-emerald-50 ring-emerald-100',
  info: 'text-brand-600 bg-brand-50 ring-brand-100',
  warning: 'text-amber-600 bg-amber-50 ring-amber-100',
  error: 'text-rose-600 bg-rose-50 ring-rose-100',
}

export function ToastContainer() {
  const allNotifications = useDataStore((s) => s.notifications)
  const role = useSessionStore((s) => s.role)
  const notifications = allNotifications.filter((n) => !n.audience || n.audience === role)
  const [visible, setVisible] = useState<Notification[]>([])
  const seen = useRef(new Set<string>())
  const initialized = useRef(false)

  useEffect(() => {
    if (!initialized.current) {
      notifications.forEach((n) => seen.current.add(n.id))
      initialized.current = true
      return
    }
    const fresh = notifications.filter((n) => !seen.current.has(n.id))
    fresh.forEach((n) => seen.current.add(n.id))
    if (fresh.length) {
      setVisible((v) => [...fresh, ...v].slice(0, 4))
      fresh.forEach((n) => {
        setTimeout(() => {
          setVisible((v) => v.filter((x) => x.id !== n.id))
        }, 5000)
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notifications])

  return (
    <div className="fixed top-3 sm:top-5 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 w-[calc(100%-1.5rem)] max-w-sm px-0 pointer-events-none">
      {visible.map((n) => {
        const Icon = ICONS[n.type]
        return (
          <div
            key={n.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-2xl bg-white/95 backdrop-blur p-3.5 shadow-lg shadow-slate-900/10 ring-1 ring-slate-100 animate-slide-up`}
          >
            <span className={`grid place-items-center w-8 h-8 rounded-xl shrink-0 ring-1 ${TONES[n.type]}`}>
              <Icon size={16} />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-slate-900">{n.title}</p>
              <p className="text-xs text-slate-500 mt-0.5">{n.message}</p>
            </div>
            <button
              onClick={() => setVisible((v) => v.filter((x) => x.id !== n.id))}
              className="text-slate-300 hover:text-slate-500 p-1 -m-1"
              aria-label="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
