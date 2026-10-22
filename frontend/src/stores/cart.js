import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCartStore = defineStore('cart', () => {
  const items = ref(JSON.parse(localStorage.getItem('cart') || '[]'))

  const count = computed(() => items.value.reduce((s, i) => s + i.qty, 0))
  const total = computed(() => items.value.reduce((s, i) => s + i.qty * i.price, 0))

  function save() { localStorage.setItem('cart', JSON.stringify(items.value)) }

  function add(product, qty = 1) {
    const existing = items.value.find(i => i.id === product.id)
    if (existing) { existing.qty += qty }
    else { items.value.push({ id: product.id, name: product.name, price: product.price, unit: product.unit, qty }) }
    save()
  }

  function remove(productId) {
    items.value = items.value.filter(i => i.id !== productId)
    save()
  }

  function updateQty(productId, qty) {
    const item = items.value.find(i => i.id === productId)
    if (item) { item.qty = Math.max(1, qty); save() }
  }

  function clear() { items.value = []; save() }

  return { items, count, total, add, remove, updateQty, clear }
})
