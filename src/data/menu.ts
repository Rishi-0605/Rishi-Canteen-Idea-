import type { FoodItem } from '../types'

// DEMO PRICES ONLY — not the actual cafeteria prices.
// Admins can edit name / price / availability from the Admin Dashboard.
// To add real photos later, replace the `emoji` + `gradient` pair with an
// <img> based FoodCard (see components/FoodCard.tsx) without touching data shape.

export const CATEGORIES = [
  'All',
  'Main Course',
  'Sandwiches',
  'Chinese',
  'South Indian',
  'Healthy',
  'Juices',
  'Milkshakes',
  'Tea & Coffee',
  'Bakery',
] as const

const G = {
  warm: 'from-amber-200 via-orange-200 to-rose-200',
  green: 'from-emerald-200 via-teal-200 to-cyan-200',
  spice: 'from-orange-300 via-amber-200 to-yellow-200',
  fresh: 'from-lime-200 via-emerald-200 to-teal-200',
  cream: 'from-yellow-100 via-amber-100 to-orange-200',
  cool: 'from-sky-200 via-blue-200 to-indigo-200',
  choco: 'from-amber-300 via-orange-300 to-stone-300',
  berry: 'from-pink-200 via-rose-200 to-red-200',
}

export const INITIAL_MENU: FoodItem[] = [
  // MAIN COURSE / INDIAN
  { id: 'paneer-biryani', name: 'Paneer Biryani', category: 'Main Course', price: 120, description: 'Flavourful paneer biryani prepared with aromatic rice and spices.', veg: true, emoji: '🍛', gradient: G.spice, available: true, popular: true, recommended: true },
  { id: 'chole-bhature', name: 'Chole Bhature', category: 'Main Course', price: 90, description: 'Spiced chickpea curry served with fluffy deep-fried bhature.', veg: true, emoji: '🫓', gradient: G.warm, available: true, popular: true },
  { id: 'roti', name: 'Roti', category: 'Main Course', price: 15, description: 'Soft whole-wheat tawa roti, made fresh to order.', veg: true, emoji: '🫓', gradient: G.cream, available: true, quickPickup: true },
  { id: 'paratha', name: 'Paratha', category: 'Main Course', price: 35, description: 'Layered, lightly crisp tawa paratha served hot.', veg: true, emoji: '🫓', gradient: G.cream, available: true, quickPickup: true },
  { id: 'daal-tadka', name: 'Daal Tadka', category: 'Main Course', price: 60, description: 'Yellow lentils tempered with ghee, cumin and spices.', veg: true, emoji: '🍲', gradient: G.spice, available: true },
  { id: 'daal-fry', name: 'Daal Fry', category: 'Main Course', price: 60, description: 'Classic pan-fried lentils finished with a garlic tadka.', veg: true, emoji: '🍲', gradient: G.spice, available: true },
  { id: 'daal-tadka-jeera-rice', name: 'Daal Tadka with Jeera Rice', category: 'Main Course', price: 90, description: 'Daal tadka paired with fragrant cumin-tempered rice.', veg: true, emoji: '🍚', gradient: G.spice, available: true, recommended: true },
  { id: 'paneer-spcl', name: 'Paneer Spcl', category: 'Main Course', price: 110, description: "Chef's special paneer preparation in a rich house gravy.", veg: true, emoji: '🧀', gradient: G.warm, available: true, popular: true },
  { id: 'misal-pav', name: 'Misal Pav', category: 'Main Course', price: 70, description: 'Spicy sprouted-lentil curry topped with farsan, served with pav.', veg: true, emoji: '🌶️', gradient: G.spice, available: true, popular: true, quickPickup: true },
  { id: 'pav-bhaji', name: 'Pav Bhaji', category: 'Main Course', price: 80, description: 'Buttery mashed vegetable bhaji served with toasted pav.', veg: true, emoji: '🍞', gradient: G.warm, available: true, popular: true, quickPickup: true },
  { id: 'paneer-bhurji', name: 'Paneer Bhurji', category: 'Main Course', price: 100, description: 'Scrambled crumbled paneer sautéed with onion, tomato and spices.', veg: true, emoji: '🧀', gradient: G.warm, available: true },
  { id: 'daal-makhni', name: 'Daal Makhni', category: 'Main Course', price: 95, description: 'Slow-simmered black lentils finished with cream and butter.', veg: true, emoji: '🍲', gradient: G.choco, available: true, recommended: true },
  { id: 'pulaw', name: 'Pulaw', category: 'Main Course', price: 85, description: 'Fragrant rice pulaw tossed with whole spices and vegetables.', veg: true, emoji: '🍚', gradient: G.fresh, available: true },

  // SANDWICHES
  { id: 'sandwich', name: 'Sandwich', category: 'Sandwiches', price: 45, description: 'Fresh vegetable sandwich layered with chutney and masala.', veg: true, emoji: '🥪', gradient: G.fresh, available: true, quickPickup: true },
  { id: 'toast-sandwich', name: 'Toast Sandwich', category: 'Sandwiches', price: 50, description: 'Golden-toasted sandwich with a crisp buttery finish.', veg: true, emoji: '🥪', gradient: G.cream, available: true, quickPickup: true },
  { id: 'grill-sandwich', name: 'Grill Sandwich', category: 'Sandwiches', price: 60, description: 'Cheesy grilled sandwich pressed till golden and crunchy.', veg: true, emoji: '🥪', gradient: G.warm, available: true, popular: true, quickPickup: true },

  // CHINESE
  { id: 'schezwan-rice', name: 'Schezwan Rice', category: 'Chinese', price: 80, description: 'Wok-tossed rice in a fiery Schezwan sauce.', veg: true, emoji: '🍜', gradient: G.spice, available: true },
  { id: 'manchurian', name: 'Manchurian', category: 'Chinese', price: 75, description: 'Crispy vegetable balls tossed in tangy Manchurian sauce.', veg: true, emoji: '🥟', gradient: G.spice, available: true, popular: true },
  { id: 'noodles', name: 'Noodles', category: 'Chinese', price: 75, description: 'Stir-fried hakka noodles loaded with crunchy vegetables.', veg: true, emoji: '🍜', gradient: G.fresh, available: true, popular: true, quickPickup: true },
  { id: 'paneer-chilly', name: 'Paneer Chilly', category: 'Chinese', price: 100, description: 'Crispy paneer tossed in a spicy chilli-garlic sauce.', veg: true, emoji: '🌶️', gradient: G.spice, available: true, recommended: true },

  // SOUTH INDIAN
  { id: 'idli-wada', name: 'Idli Wada', category: 'South Indian', price: 55, description: 'Steamed idli paired with crispy medu wada, sambar and chutney.', veg: true, emoji: '🍥', gradient: G.cream, available: true, quickPickup: true },
  { id: 'medu-wada', name: 'Medu Wada', category: 'South Indian', price: 45, description: 'Crispy golden lentil doughnuts served with sambar and chutney.', veg: true, emoji: '🍩', gradient: G.warm, available: true, quickPickup: true },

  // HEALTHY / SNACKS
  { id: 'corn-chat', name: 'Corn Chat', category: 'Healthy', price: 50, description: 'Tangy spiced sweet-corn chaat, light and refreshing.', veg: true, emoji: '🌽', gradient: G.fresh, available: true, recommended: true },
  { id: 'fruit-dish', name: 'Fruit Dish', category: 'Healthy', price: 60, description: 'A fresh seasonal fruit bowl, cut and served chilled.', veg: true, emoji: '🍎', gradient: G.berry, available: true, recommended: true },
  { id: 'salad-dish', name: 'Salad Dish', category: 'Healthy', price: 50, description: 'Crisp fresh vegetable salad tossed with a light dressing.', veg: true, emoji: '🥗', gradient: G.fresh, available: true, recommended: true },

  // FRESH JUICES
  { id: 'watermelon-juice', name: 'Water Melon Juice', category: 'Juices', price: 45, description: 'Chilled fresh watermelon juice, naturally sweet and hydrating.', veg: true, emoji: '🍉', gradient: G.berry, available: true, quickPickup: true },
  { id: 'mosambi-juice', name: 'Mosambi Juice', category: 'Juices', price: 45, description: 'Freshly squeezed sweet-lime juice, light and refreshing.', veg: true, emoji: '🍈', gradient: G.fresh, available: true, quickPickup: true },

  // MILKSHAKES
  { id: 'chocolate-milkshake', name: 'Chocolate Milkshake', category: 'Milkshakes', price: 65, description: 'Rich and creamy chocolate milkshake, chilled to perfection.', veg: true, emoji: '🥤', gradient: G.choco, available: true, popular: true },
  { id: 'cold-coffee', name: 'Cold Coffee', category: 'Milkshakes', price: 60, description: 'Frothy chilled cold coffee blended with ice cream.', veg: true, emoji: '🥤', gradient: G.choco, available: true, popular: true, quickPickup: true },

  // TEA & COFFEE
  { id: 'coffee', name: 'Coffee', category: 'Tea & Coffee', price: 25, description: 'Hot filter coffee, brewed fresh and served piping hot.', veg: true, emoji: '☕', gradient: G.cream, available: true, quickPickup: true },
  { id: 'tea', name: 'Tea', category: 'Tea & Coffee', price: 20, description: 'Classic masala chai, brewed strong with milk and spices.', veg: true, emoji: '🍵', gradient: G.cream, available: true, quickPickup: true },

  // BAKERY / BREAKFAST
  { id: 'bun-maska', name: 'Bun Maska', category: 'Bakery', price: 35, description: 'Soft bakery bun generously slathered with butter.', veg: true, emoji: '🥐', gradient: G.warm, available: true, quickPickup: true },
  { id: 'bun-maska-jam', name: 'Bun Maska with Jam', category: 'Bakery', price: 40, description: 'Soft bakery bun with butter and a sweet fruit jam.', veg: true, emoji: '🥐', gradient: G.warm, available: true, quickPickup: true },
]
