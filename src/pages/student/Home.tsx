import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { useSessionStore } from '../../store/useSessionStore'
import type { FoodItem } from '../../types'
import { CategoryPills } from '../../components/CategoryPills'
import { FoodCard } from '../../components/FoodCard'
import { LiveQueueCard } from '../../components/LiveQueueCard'
import { NotificationBell } from '../../components/NotificationBell'
import { EmptyState } from '../../components/EmptyState'
import { greeting } from '../../lib/format'

export function Home() {
  const menu = useDataStore((s) => s.menu)
  const student = useSessionStore((s) => s.student)
  const navigate = useNavigate()
  const [category, setCategory] = useState('All')

  const firstName = student?.name.split(' ')[0] ?? 'Student'

  function goCategory(c: string) {
    setCategory(c)
    if (c !== 'All') navigate(`/app/explore?category=${encodeURIComponent(c)}`)
  }

  const popular = useMemo(() => menu.filter((m) => m.popular), [menu])
  const quick = useMemo(() => menu.filter((m) => m.quickPickup), [menu])
  const recommended = useMemo(() => menu.filter((m) => m.recommended), [menu])

  return (
    <div className="pb-4">
      <header className="px-4 sm:px-6 lg:px-8 pt-6 pb-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="font-display font-extrabold text-xl text-slate-900">
            {greeting()}, {firstName} 👋
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">What's your craving?</p>
        </div>
        <NotificationBell />
      </header>

      <div className="px-4 sm:px-6 lg:px-8 mb-5">
        <button
          onClick={() => navigate('/app/explore')}
          className="w-full flex items-center gap-3 rounded-2xl bg-white ring-1 ring-slate-200 px-4 py-3.5 text-sm text-slate-400 shadow-sm shadow-slate-200/50 transition hover:ring-slate-300"
        >
          <Search size={17} />
          Search food...
        </button>
      </div>

      <div className="mb-5">
        <LiveQueueCard />
      </div>

      <div className="mb-6">
        <CategoryPills active={category} onChange={goCategory} />
      </div>

      <Section title="Popular Today" items={popular} />
      <Section title="Quick Pickup" subtitle="Ready in under 5 minutes" items={quick} />
      <Section title="Recommended for You" items={recommended} />

      {menu.length === 0 && (
        <EmptyState emoji="🍽️" title="No food found" subtitle="The menu is being updated. Please check back shortly." />
      )}
    </div>
  )
}

function Section({ title, subtitle, items }: { title: string; subtitle?: string; items: FoodItem[] }) {
  if (items.length === 0) return null
  return (
    <section className="mb-7">
      <div className="px-4 sm:px-6 lg:px-8 flex items-baseline justify-between mb-3">
        <h2 className="font-display font-bold text-slate-900">{title}</h2>
        {subtitle && <span className="text-xs text-slate-400">{subtitle}</span>}
      </div>
      <div className="flex gap-3.5 overflow-x-auto no-scrollbar px-4 sm:px-6 lg:px-8 pb-1">
        {items.map((item) => (
          <div key={item.id} className="w-[168px] sm:w-[190px] shrink-0">
            <FoodCard item={item} />
          </div>
        ))}
      </div>
    </section>
  )
}
