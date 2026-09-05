import { useMemo, useState } from 'react'
import { Plus, Pencil, Trash2, Search } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { VegBadge } from '../../components/VegBadge'
import { FoodFormModal } from '../../components/admin/FoodFormModal'
import type { FoodItem } from '../../types'

export function MenuTab() {
  const menu = useDataStore((s) => s.menu)
  const addFoodItem = useDataStore((s) => s.addFoodItem)
  const updateFoodItem = useDataStore((s) => s.updateFoodItem)
  const deleteFoodItem = useDataStore((s) => s.deleteFoodItem)
  const toggleAvailability = useDataStore((s) => s.toggleAvailability)
  const pushNotification = useDataStore((s) => s.pushNotification)

  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState<FoodItem | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<FoodItem | null>(null)

  const filtered = useMemo(
    () => menu.filter((m) => m.name.toLowerCase().includes(query.toLowerCase())),
    [menu, query],
  )

  function openAdd() {
    setEditing(null)
    setShowForm(true)
  }
  function openEdit(item: FoodItem) {
    setEditing(item)
    setShowForm(true)
  }
  function handleSave(item: FoodItem) {
    if (editing) {
      updateFoodItem(item.id, item)
      pushNotification({ title: 'Item updated', message: `${item.name} was updated.`, type: 'success', audience: 'admin' })
    } else {
      addFoodItem(item)
      pushNotification({ title: 'Item added', message: `${item.name} was added to the menu.`, type: 'success', audience: 'admin' })
    }
    setShowForm(false)
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-5">
        <div className="flex-1 flex items-center gap-2.5 rounded-2xl bg-white ring-1 ring-slate-200 px-4 py-2.5">
          <Search size={16} className="text-slate-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search menu items..."
            className="flex-1 text-sm outline-none bg-transparent"
          />
        </div>
        <button
          onClick={openAdd}
          className="flex items-center justify-center gap-1.5 rounded-2xl bg-brand-600 text-white font-bold text-sm px-4 py-2.5 hover:bg-brand-700 transition shrink-0"
        >
          <Plus size={16} /> Add Food
        </button>
      </div>

      <div className="rounded-2xl bg-white ring-1 ring-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[720px]">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs font-bold uppercase tracking-wide text-slate-400">
                <th className="px-4 py-3">Item</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Price</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${item.gradient} grid place-items-center text-lg shrink-0`}>
                        {item.emoji}
                      </div>
                      <div className="flex items-center gap-1.5 min-w-0">
                        <VegBadge veg={item.veg} />
                        <span className="font-semibold text-slate-800 truncate">{item.name}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{item.category}</td>
                  <td className="px-4 py-3">
                    <PriceEditor item={item} onChange={(p) => updateFoodItem(item.id, { price: p })} />
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleAvailability(item.id)}
                      className={`text-[11px] font-bold uppercase rounded-full px-2.5 py-1 transition ${
                        item.available ? 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100' : 'bg-rose-50 text-rose-600 hover:bg-rose-100'
                      }`}
                    >
                      {item.available ? 'Available' : 'Sold Out'}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1.5">
                      <button onClick={() => openEdit(item)} className="p-2 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-brand-600">
                        <Pencil size={15} />
                      </button>
                      <button
                        onClick={() => setConfirmDelete(item)}
                        className="p-2 rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-slate-400 text-sm">
                    No items match "{query}".
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showForm && <FoodFormModal initial={editing} onClose={() => setShowForm(false)} onSave={handleSave} />}

      {confirmDelete && (
        <div className="fixed inset-0 z-[110] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-white rounded-3xl p-6 animate-pop">
            <h3 className="font-display font-bold text-lg text-slate-900">Delete "{confirmDelete.name}"?</h3>
            <p className="text-sm text-slate-500 mt-1.5">This will remove the item from the menu permanently.</p>
            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setConfirmDelete(null)}
                className="flex-1 rounded-xl bg-slate-100 text-slate-600 font-bold text-sm py-2.5"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  deleteFoodItem(confirmDelete.id)
                  pushNotification({ title: 'Item removed', message: `${confirmDelete.name} was deleted.`, type: 'warning', audience: 'admin' })
                  setConfirmDelete(null)
                }}
                className="flex-1 rounded-xl bg-rose-600 text-white font-bold text-sm py-2.5"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function PriceEditor({ item, onChange }: { item: FoodItem; onChange: (price: number) => void }) {
  const [value, setValue] = useState(String(item.price))
  return (
    <div className="flex items-center gap-1 text-slate-800 font-semibold">
      <span className="text-slate-400">₹</span>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value.replace(/[^0-9]/g, ''))}
        onBlur={() => onChange(Number(value) || 0)}
        className="w-16 rounded-lg border border-transparent hover:border-slate-200 focus:border-brand-400 focus:ring-2 focus:ring-brand-100 px-1.5 py-1 outline-none bg-transparent"
      />
    </div>
  )
}
