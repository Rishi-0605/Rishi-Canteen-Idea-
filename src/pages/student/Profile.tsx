import { useNavigate } from 'react-router-dom'
import { Receipt, Heart, Bell, HelpCircle, LogOut, ChevronRight, BadgeCheck } from 'lucide-react'
import { useSessionStore } from '../../store/useSessionStore'
import { useDataStore } from '../../store/useDataStore'

export function Profile() {
  const navigate = useNavigate()
  const student = useSessionStore((s) => s.student)
  const logout = useSessionStore((s) => s.logout)
  const pushNotification = useDataStore((s) => s.pushNotification)

  function comingSoon(label: string) {
    pushNotification({ title: label, message: `${label} isn't wired up in this prototype yet.`, type: 'info', audience: 'student' })
  }

  return (
    <div className="pb-8">
      <header className="px-4 sm:px-6 lg:px-8 pt-6 pb-4">
        <h1 className="font-display font-extrabold text-xl text-slate-900">Profile</h1>
      </header>

      <div className="px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-gradient-to-br from-brand-700 to-brand-900 text-white p-5 flex items-center gap-4 shadow-lg shadow-brand-900/20">
          <div className="w-14 h-14 rounded-full bg-white/15 grid place-items-center font-display font-extrabold text-xl shrink-0">
            {student?.name.charAt(0) ?? 'S'}
          </div>
          <div className="min-w-0">
            <p className="font-display font-bold text-lg truncate">{student?.name ?? 'Demo Student'}</p>
            <p className="text-xs text-white/70 mt-0.5 flex items-center gap-1">
              <BadgeCheck size={13} /> {student?.college ?? 'IBS Mumbai'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-4">
          <InfoBox label="Student ID" value={student?.studentId ?? '—'} />
          <InfoBox label="Email" value={student?.email ?? '—'} truncate />
        </div>

        <div className="mt-6 rounded-2xl bg-white ring-1 ring-slate-100 overflow-hidden">
          <MenuRow icon={<Receipt size={17} />} label="Order History" onClick={() => navigate('/app/orders')} />
          <MenuRow icon={<Heart size={17} />} label="Saved Preferences" onClick={() => comingSoon('Saved Preferences')} />
          <MenuRow icon={<Bell size={17} />} label="Notifications" onClick={() => comingSoon('Notification Settings')} />
          <MenuRow icon={<HelpCircle size={17} />} label="Help & Support" onClick={() => comingSoon('Help & Support')} last />
        </div>

        <button
          onClick={() => {
            logout()
            navigate('/login')
          }}
          className="mt-5 w-full flex items-center justify-center gap-2 rounded-2xl bg-rose-50 text-rose-600 font-bold text-sm py-3.5 hover:bg-rose-100 transition"
        >
          <LogOut size={16} /> Logout
        </button>

        <p className="text-center text-[11px] text-slate-400 mt-6">IBS Cafeteria Pilot · Powered by Campus Bite</p>
      </div>
    </div>
  )
}

function InfoBox({ label, value, truncate }: { label: string; value: string; truncate?: boolean }) {
  return (
    <div className="rounded-2xl bg-white ring-1 ring-slate-100 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`text-sm font-bold text-slate-900 mt-1 ${truncate ? 'truncate' : ''}`}>{value}</p>
    </div>
  )
}

function MenuRow({ icon, label, onClick, last }: { icon: React.ReactNode; label: string; onClick: () => void; last?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3.5 px-4 py-3.5 text-left transition hover:bg-slate-50 ${!last ? 'border-b border-slate-50' : ''}`}
    >
      <span className="grid place-items-center w-9 h-9 rounded-xl bg-slate-100 text-slate-500">{icon}</span>
      <span className="flex-1 text-sm font-semibold text-slate-800">{label}</span>
      <ChevronRight size={16} className="text-slate-300" />
    </button>
  )
}
