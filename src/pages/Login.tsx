import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GraduationCap, Lock, Mail, ShieldCheck, UtensilsCrossed, ChevronRight } from 'lucide-react'
import { Logo } from '../components/Logo'
import { useSessionStore } from '../store/useSessionStore'

export function Login() {
  const navigate = useNavigate()
  const loginStudent = useSessionStore((s) => s.loginStudent)
  const loginDemo = useSessionStore((s) => s.loginDemo)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [showDemoRoles, setShowDemoRoles] = useState(false)

  function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    const res = loginStudent(email, password)
    if (!res.ok) {
      setError(res.error ?? 'Something went wrong.')
      return
    }
    navigate('/app/home')
  }

  function enterDemo(role: 'student' | 'staff' | 'admin') {
    loginDemo(role)
    if (role === 'student') navigate('/app/home')
    else navigate(`/${role}`)
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-sm">
        <div className="flex justify-center mb-8">
          <Logo size="lg" />
        </div>

        <div className="rounded-3xl bg-white shadow-sm shadow-slate-200/70 ring-1 ring-slate-100 p-6 sm:p-7">
          <h1 className="font-display font-extrabold text-xl text-slate-900 text-center">Welcome to IBS Cafeteria</h1>
          <p className="text-center text-sm text-slate-400 mt-1.5">Sign in to order ahead and skip the queue.</p>

          <form onSubmit={handleLogin} className="mt-6 space-y-3.5">
            <div>
              <label className="text-xs font-semibold text-slate-500 mb-1.5 block">College Email / Student ID</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300" size={17} />
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@ibsmumbai.edu.in"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3.5 text-sm outline-none transition focus:border-brand-400 focus:bg-white focus:ring-4 focus:ring-brand-100"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-500 mb-1.5 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300" size={17} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3.5 text-sm outline-none transition focus:border-brand-400 focus:bg-white focus:ring-4 focus:ring-brand-100"
                />
              </div>
            </div>

            {error && <p className="text-xs font-medium text-rose-600 bg-rose-50 rounded-lg px-3 py-2">{error}</p>}

            <button
              type="submit"
              className="w-full rounded-xl bg-brand-600 text-white font-bold text-sm py-3.5 shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 active:scale-[0.98]"
            >
              LOGIN
            </button>
          </form>

          <div className="flex items-center gap-3 my-5">
            <span className="h-px flex-1 bg-slate-100" />
            <span className="text-[11px] font-semibold text-slate-400 uppercase">or</span>
            <span className="h-px flex-1 bg-slate-100" />
          </div>

          <button
            onClick={() => enterDemo('student')}
            className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-200 text-slate-700 font-bold text-sm py-3.5 transition hover:bg-slate-50 active:scale-[0.98]"
          >
            <GraduationCap size={17} />
            Continue with College ID
          </button>

          <p className="text-center text-xs text-slate-400 mt-5">
            Don't have an account? <span className="font-semibold text-brand-600">Contact your cafeteria admin</span>
          </p>
        </div>

        <div className="mt-5 rounded-3xl bg-gradient-to-br from-brand-600 to-brand-800 p-5 text-white shadow-lg shadow-brand-900/20">
          <p className="text-xs font-bold uppercase tracking-wide text-white/70">Prototype Demo</p>
          <p className="text-sm text-white/90 mt-1">Skip real accounts &amp; payments — jump straight into the experience.</p>
          {!showDemoRoles ? (
            <button
              onClick={() => setShowDemoRoles(true)}
              className="mt-3.5 w-full flex items-center justify-center gap-1.5 rounded-xl bg-white text-brand-700 font-bold text-sm py-3 transition hover:bg-brand-50 active:scale-[0.98]"
            >
              DEMO LOGIN <ChevronRight size={16} />
            </button>
          ) : (
            <div className="mt-3.5 grid gap-2">
              <button
                onClick={() => enterDemo('student')}
                className="flex items-center gap-2.5 rounded-xl bg-white/10 hover:bg-white/20 transition px-3.5 py-2.5 text-sm font-semibold"
              >
                <GraduationCap size={16} /> Enter Demo as Student
              </button>
              <button
                onClick={() => enterDemo('staff')}
                className="flex items-center gap-2.5 rounded-xl bg-white/10 hover:bg-white/20 transition px-3.5 py-2.5 text-sm font-semibold"
              >
                <UtensilsCrossed size={16} /> Enter Demo as Canteen Staff
              </button>
              <button
                onClick={() => enterDemo('admin')}
                className="flex items-center gap-2.5 rounded-xl bg-white/10 hover:bg-white/20 transition px-3.5 py-2.5 text-sm font-semibold"
              >
                <ShieldCheck size={16} /> Enter Demo as Admin
              </button>
            </div>
          )}
        </div>

        <button
          onClick={() => navigate('/campus-bite')}
          className="w-full text-center text-[11px] text-slate-400 mt-6 hover:text-slate-500 transition"
        >
          Built on the Campus Bite platform — multi-college version coming soon →
        </button>
      </div>
    </div>
  )
}
