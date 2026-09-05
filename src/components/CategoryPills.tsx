import { CATEGORIES } from '../data/menu'

const EMOJI: Record<string, string> = {
  All: '🍽️',
  'Main Course': '🍛',
  Sandwiches: '🥪',
  Chinese: '🥡',
  'South Indian': '🍥',
  Healthy: '🥗',
  Juices: '🍉',
  Milkshakes: '🥤',
  'Tea & Coffee': '☕',
  Bakery: '🥐',
}

export function CategoryPills({ active, onChange }: { active: string; onChange: (c: string) => void }) {
  return (
    <div className="flex gap-2.5 overflow-x-auto no-scrollbar px-4 sm:px-6 lg:px-8 pb-1">
      {CATEGORIES.map((c) => (
        <button
          key={c}
          onClick={() => onChange(c)}
          className={`shrink-0 flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-bold transition ${
            active === c
              ? 'bg-brand-600 text-white shadow-md shadow-brand-600/25'
              : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:ring-slate-300'
          }`}
        >
          <span>{EMOJI[c]}</span>
          {c}
        </button>
      ))}
    </div>
  )
}
