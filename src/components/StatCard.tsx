import type { LucideIcon } from 'lucide-react'

export function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  tone = 'brand',
}: {
  icon: LucideIcon
  label: string
  value: string
  hint?: string
  tone?: 'brand' | 'accent' | 'green' | 'rose'
}) {
  const tones: Record<string, string> = {
    brand: 'bg-brand-50 text-brand-700',
    accent: 'bg-amber-50 text-amber-700',
    green: 'bg-emerald-50 text-emerald-700',
    rose: 'bg-rose-50 text-rose-700',
  }
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm shadow-slate-200/60 ring-1 ring-slate-100">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</span>
        <span className={`grid place-items-center w-8 h-8 rounded-xl ${tones[tone]}`}>
          <Icon size={16} />
        </span>
      </div>
      <p className="font-display font-extrabold text-2xl text-slate-900 mt-2">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
    </div>
  )
}
