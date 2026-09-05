export function Logo({ size = 'md', mono = false }: { size?: 'sm' | 'md' | 'lg'; mono?: boolean }) {
  const dims = { sm: 'w-8 h-8 text-sm', md: 'w-11 h-11 text-lg', lg: 'w-16 h-16 text-2xl' }[size]
  const text = { sm: 'text-base', md: 'text-xl', lg: 'text-3xl' }[size]
  return (
    <div className="inline-flex items-center gap-2.5">
      <div
        className={`${dims} shrink-0 rounded-2xl grid place-items-center font-display font-extrabold text-white shadow-lg shadow-brand-600/30 ${
          mono ? 'bg-white/15 backdrop-blur' : 'bg-gradient-to-br from-brand-500 to-brand-700'
        }`}
      >
        IB
      </div>
      <div className="leading-tight">
        <p className={`font-display font-extrabold tracking-tight ${text} ${mono ? 'text-white' : 'text-brand-900'}`}>
          IBS Cafeteria
        </p>
        {size !== 'sm' && (
          <p className={`text-[11px] font-medium tracking-wide uppercase ${mono ? 'text-white/70' : 'text-slate-400'}`}>
            Powered by Campus Bite
          </p>
        )}
      </div>
    </div>
  )
}
