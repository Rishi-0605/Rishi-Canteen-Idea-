import { useState, useRef, useEffect } from 'react'
import { Bell, CheckCircle2, Info, AlertTriangle, XCircle } from 'lucide-react'
import { useDataStore } from '../store/useDataStore'
import { useSessionStore } from '../store/useSessionStore'
import { formatRelative } from '../lib/format'

const ICONS = { success: CheckCircle2, info: Info, warning: AlertTriangle, error: XCircle }
const TONES = {
  success: 'text-emerald-600 bg-emerald-50',
  info: 'text-brand-600 bg-brand-50',
  warning: 'text-amber-600 bg-amber-50',
  error: 'text-rose-600 bg-rose-50',
}

export function NotificationBell({ dark = false }: { dark?: boolean }) {
  const allNotifications = useDataStore((s) => s.notifications)
  const markNotificationRead = useDataStore((s) => s.markNotificationRead)
  const role = useSessionStore((s) => s.role)
  const notifications = allNotifications.filter((n) => !n.audience || n.audience === role)
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const unread = notifications.filter((n) => !n.read).length

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => {
          setOpen((o) => !o)
          if (!open) notifications.forEach((n) => markNotificationRead(n.id))
        }}
        className={`relative grid place-items-center w-10 h-10 rounded-full transition ${
          dark ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
        }`}
        aria-label="Notifications"
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-accent-500 ring-2 ring-white" />
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 max-w-[85vw] rounded-2xl bg-white shadow-xl shadow-slate-900/15 ring-1 ring-slate-100 overflow-hidden z-50 animate-slide-up">
          <div className="px-4 py-3 border-b border-slate-100 font-display font-bold text-slate-800 text-sm">
            Notifications
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="text-center text-sm text-slate-400 py-8">No notifications yet.</p>
            ) : (
              notifications.map((n) => {
                const Icon = ICONS[n.type]
                return (
                  <div key={n.id} className="flex gap-3 px-4 py-3 border-b border-slate-50 last:border-0">
                    <span className={`grid place-items-center w-8 h-8 rounded-xl shrink-0 ${TONES[n.type]}`}>
                      <Icon size={15} />
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-800">{n.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{n.message}</p>
                      <p className="text-[10px] text-slate-400 mt-1">{formatRelative(n.at)}</p>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
