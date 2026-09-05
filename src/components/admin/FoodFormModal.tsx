import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { CATEGORIES } from '../../data/menu'
import type { FoodItem } from '../../types'

const EMOJI_CHOICES = ['🍛', '🫓', '🍲', '🍚', '🧀', '🌶️', '🍞', '🥪', '🍜', '🥟', '🍥', '🍩', '🌽', '🍎', '🥗', '🍉', '🍈', '🥤', '☕', '🍵', '🥐']
const GRADIENT_CHOICES = [
  'from-amber-200 via-orange-200 to-rose-200',
  'from-emerald-200 via-teal-200 to-cyan-200',
  'from-orange-300 via-amber-200 to-yellow-200',
  'from-lime-200 via-emerald-200 to-teal-200',
  'from-yellow-100 via-amber-100 to-orange-200',
  'from-sky-200 via-blue-200 to-indigo-200',
  'from-amber-300 via-orange-300 to-stone-300',
  'from-pink-200 via-rose-200 to-red-200',
]

function slugify(name: string) {
  return name.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}

export function FoodFormModal({
  initial,
  onClose,
  onSave,
}: {
  initial: FoodItem | null
  onClose: () => void
  onSave: (item: FoodItem) => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [category, setCategory] = useState<FoodItem['category']>(initial?.category ?? 'Main Course')
  const [price, setPrice] = useState(initial?.price ?? 50)
  const [description, setDescription] = useState(initial?.description ?? '')
  const [veg, setVeg] = useState(initial?.veg ?? true)
  const [emoji, setEmoji] = useState(initial?.emoji ?? EMOJI_CHOICES[0])
  const [gradient, setGradient] = useState(initial?.gradient ?? GRADIENT_CHOICES[0])

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    const item: FoodItem = {
      id: initial?.id ?? `${slugify(name)}-${Date.now().toString(36)}`,
      name: name.trim(),
      category,
      price: Math.max(0, Math.round(price)),
      description: description.trim() || 'A cafeteria favourite.',
      veg,
      emoji,
      gradient,
      available: initial?.available ?? true,
      popular: initial?.popular,
      quickPickup: initial?.quickPickup,
      recommended: initial?.recommended,
    }
    onSave(item)
  }

  return (
    <div className="fixed inset-0 z-[110] bg-slate-900/40 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full sm:max-w-md bg-white rounded-t-3xl sm:rounded-3xl max-h-[92vh] overflow-y-auto animate-slide-up"
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 sticky top-0 bg-white">
          <h2 className="font-display font-bold text-lg text-slate-900">{initial ? 'Edit Item' : 'Add Food Item'}</h2>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-700 p-1">
            <X size={18} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <Field label="Name">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
              placeholder="e.g. Veg Frankie"
            />
          </Field>

          <Field label="Category">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as FoodItem['category'])}
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
            >
              {CATEGORIES.filter((c) => c !== 'All').map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Price (₹) — Demo Price">
            <input
              type="number"
              min={0}
              value={price}
              onChange={(e) => setPrice(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
            />
          </Field>

          <Field label="Description">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-4 focus:ring-brand-100 resize-none"
              placeholder="Short appetising description"
            />
          </Field>

          <Field label="Icon">
            <div className="flex flex-wrap gap-2">
              {EMOJI_CHOICES.map((em) => (
                <button
                  type="button"
                  key={em}
                  onClick={() => setEmoji(em)}
                  className={`w-9 h-9 rounded-lg grid place-items-center text-lg ring-2 transition ${
                    emoji === em ? 'ring-brand-500' : 'ring-transparent bg-slate-50'
                  }`}
                >
                  {em}
                </button>
              ))}
            </div>
          </Field>

          <Field label="Card color">
            <div className="flex flex-wrap gap-2">
              {GRADIENT_CHOICES.map((g) => (
                <button
                  type="button"
                  key={g}
                  onClick={() => setGradient(g)}
                  className={`w-9 h-9 rounded-lg bg-gradient-to-br ${g} ring-2 transition ${
                    gradient === g ? 'ring-brand-500' : 'ring-transparent'
                  }`}
                />
              ))}
            </div>
          </Field>

          <label className="flex items-center gap-2.5 text-sm font-semibold text-slate-700">
            <input type="checkbox" checked={veg} onChange={(e) => setVeg(e.target.checked)} className="accent-veg-500 w-4 h-4" />
            Vegetarian item
          </label>
        </div>

        <div className="p-5 pt-0 sticky bottom-0 bg-white">
          <button
            type="submit"
            className="w-full rounded-2xl bg-brand-600 text-white font-bold text-sm py-3.5 shadow-lg shadow-brand-600/25 hover:bg-brand-700 transition"
          >
            {initial ? 'Save Changes' : 'Add Item'}
          </button>
        </div>
      </form>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-xs font-semibold text-slate-500 mb-1.5 block">{label}</label>
      {children}
    </div>
  )
}
