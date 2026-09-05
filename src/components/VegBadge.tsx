export function VegBadge({ veg, size = 14 }: { veg: boolean; size?: number }) {
  return (
    <span
      className={`inline-flex items-center justify-center border-2 rounded-[3px] ${
        veg ? 'border-veg-500' : 'border-nonveg-500'
      }`}
      style={{ width: size, height: size }}
      title={veg ? 'Vegetarian' : 'Non-Vegetarian'}
      aria-label={veg ? 'Vegetarian' : 'Non-Vegetarian'}
    >
      <span
        className={`rounded-full ${veg ? 'bg-veg-500' : 'bg-nonveg-500'}`}
        style={{ width: size * 0.5, height: size * 0.5 }}
      />
    </span>
  )
}
