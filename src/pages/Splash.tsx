import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionStore } from '../store/useSessionStore'

export function Splash() {
  const navigate = useNavigate()
  const role = useSessionStore((s) => s.role)

  useEffect(() => {
    const t = setTimeout(() => {
      if (role === 'student') navigate('/app/home', { replace: true })
      else if (role === 'staff') navigate('/staff', { replace: true })
      else if (role === 'admin') navigate('/admin', { replace: true })
      else navigate('/login', { replace: true })
    }, 1600)
    return () => clearTimeout(t)
  }, [navigate, role])

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-700 via-brand-800 to-brand-950 flex flex-col items-center justify-center text-white px-6 overflow-hidden relative">
      <div className="absolute -top-24 -right-24 w-72 h-72 rounded-full bg-brand-500/30 blur-3xl" />
      <div className="absolute -bottom-24 -left-24 w-72 h-72 rounded-full bg-accent-500/20 blur-3xl" />

      <div className="relative flex flex-col items-center animate-pop">
        <div className="w-24 h-24 rounded-[28px] bg-white/10 backdrop-blur grid place-items-center font-display font-extrabold text-4xl shadow-2xl ring-1 ring-white/20 mb-6">
          IB
        </div>
        <h1 className="font-display font-extrabold text-3xl tracking-tight">IBS CAFETERIA</h1>
        <p className="text-white/70 mt-2.5 text-sm font-medium tracking-wide">Skip the Queue. Enjoy Your Break.</p>
      </div>

      <div className="absolute bottom-14 flex flex-col items-center gap-3 animate-fade-in">
        <div className="flex gap-1.5">
          <span className="w-2 h-2 rounded-full bg-white/90 animate-pulse" />
          <span className="w-2 h-2 rounded-full bg-white/50 animate-pulse [animation-delay:150ms]" />
          <span className="w-2 h-2 rounded-full bg-white/30 animate-pulse [animation-delay:300ms]" />
        </div>
        <p className="text-[11px] text-white/40 tracking-wide">a pilot for IBS Mumbai · by Campus Bite</p>
      </div>
    </div>
  )
}
