import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, X, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useDataStore } from '../../store/useDataStore'
import { CategoryPills } from '../../components/CategoryPills'
import { FoodCard } from '../../components/FoodCard'
import { EmptyState } from '../../components/EmptyState'

export function Explore() {
  const menu = useDataStore((s) => s.menu)
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState(params.get('q') ?? '')
  const category = params.get('category') ?? 'All'
  const [vegOnly, setVegOnly] = useState(false)

  function setCategory(c: string) {
    const next = new URLSearchParams(params)
    if (c === 'All') next.delete('category')
    else next.set('category', c)
    setParams(next, { replace: true })
  }

  const results = useMemo(() => {
    return menu.filter((item) => {
      if (category !== 'All' && item.category !== category) return false
      if (vegOnly && !item.veg) return false
      if (query.trim() && !item.name.toLowerCase().includes(query.trim().toLowerCase())) return false
      return true
    })
  }, [menu, category, vegOnly, query])

  return (
    <div className="pb-4">
      <header className="px-4 sm:px-6 lg:px-8 pt-6 pb-4">
        <div className="flex items-center gap-2 mb-4">
          <button onClick={() => navigate(-1)} className="lg:hidden p-2 -ml-2 text-slate-500">
            <ArrowLeft size={20} />
          </button>
          <h1 className="font-display font-extrabold text-xl text-slate-900">Explore Menu</h1>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="flex-1 flex items-center gap-3 rounded-2xl bg-white ring-1 ring-slate-200 px-4 py-3 shadow-sm shadow-slate-200/50 focus-within:ring-brand-300">
            <Search size={17} className="text-slate-400" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search food..."
              className="flex-1 outline-none text-sm bg-transparent"
            />
            {query && (
              <button onClick={() => setQuery('')} className="text-slate-300 hover:text-slate-500">
                <X size={15} />
              </button>
            )}
          </div>
          <button
            onClick={() => setVegOnly((v) => !v)}
            className={`shrink-0 flex items-center gap-1.5 rounded-2xl px-3.5 py-3 text-xs font-bold transition ${
              vegOnly ? 'bg-veg-500 text-white' : 'bg-white ring-1 ring-slate-200 text-slate-600'
            }`}
          >
            <span className={`inline-block w-2.5 h-2.5 rounded-full border-2 ${vegOnly ? 'border-white' : 'border-veg-500'}`}>
              <span className={`block w-1 h-1 m-auto rounded-full ${vegOnly ? 'bg-white' : 'bg-veg-500'}`} />
            </span>
            Veg
          </button>
        </div>
      </header>

      <div className="mb-5">
        <CategoryPills active={category} onChange={setCategory} />
      </div>

      <div className="px-4 sm:px-6 lg:px-8">
        {results.length === 0 ? (
          <EmptyState emoji="🔍" title="No food found" subtitle="Try a different search term or category." />
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3.5">
            {results.map((item) => (
              <FoodCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
