import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Rocket } from 'lucide-react'
import { useDataStore } from '../store/useDataStore'

const COLLEGES = ['IBS Mumbai', 'NMIMS', 'Somaiya', 'Hinduja College', 'Mithibai College', 'Jai Hind College', 'HR College', 'KC College']

export function CampusBiteTeaser() {
  const navigate = useNavigate()
  const pushNotification = useDataStore((s) => s.pushNotification)

  function pick(college: string) {
    if (college === 'IBS Mumbai') {
      navigate('/login')
      return
    }
    pushNotification({
      title: 'Coming soon',
      message: `${college} isn't live on Campus Bite yet. This pilot currently runs only for IBS Mumbai.`,
      type: 'info',
    })
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-sm">
        <button onClick={() => navigate('/login')} className="flex items-center gap-1.5 text-sm font-semibold text-slate-500 mb-6 hover:text-slate-800">
          <ArrowLeft size={16} /> Back to IBS Cafeteria
        </button>

        <div className="flex flex-col items-center text-center mb-7">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent-400 to-accent-600 grid place-items-center text-white mb-4 shadow-lg shadow-accent-500/30">
            <Rocket size={24} />
          </div>
          <h1 className="font-display font-extrabold text-2xl text-slate-900">Campus Bite</h1>
          <p className="text-sm text-slate-400 mt-1.5">Your Campus. Your Food. One App.</p>
          <p className="text-xs text-slate-400 mt-3 max-w-xs">
            Choose your college. <span className="font-semibold text-slate-500">Note:</span> these colleges are shown only
            as examples of future expansion and are not currently partnered with Campus Bite.
          </p>
        </div>

        <div className="grid gap-2">
          {COLLEGES.map((c) => (
            <button
              key={c}
              onClick={() => pick(c)}
              className={`flex items-center justify-between rounded-2xl px-4 py-3.5 text-sm font-semibold transition ${
                c === 'IBS Mumbai'
                  ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/25 hover:bg-brand-700'
                  : 'bg-white text-slate-600 ring-1 ring-slate-100 hover:bg-slate-50'
              }`}
            >
              {c}
              {c === 'IBS Mumbai' && <span className="text-[10px] font-bold uppercase bg-white/20 rounded-full px-2 py-0.5">Live Pilot</span>}
              {c !== 'IBS Mumbai' && <span className="text-[10px] font-bold uppercase text-slate-300">Coming soon</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
