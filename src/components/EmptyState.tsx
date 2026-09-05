import type { ReactNode } from 'react'

export function EmptyState({
  emoji,
  title,
  subtitle,
  action,
}: {
  emoji: string
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center px-8 py-16 animate-fade-in">
      <div className="text-6xl mb-4 animate-pop">{emoji}</div>
      <h3 className="font-display font-bold text-slate-800 text-lg">{title}</h3>
      {subtitle && <p className="text-sm text-slate-500 mt-1.5 max-w-xs">{subtitle}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
