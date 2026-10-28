import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/utils/api'
import { useAuthStore } from './auth'

export const useCartStore = defineStore('cart', () => {
  const items = ref(JSON.parse(localStorage.getItem('cart') || '[]'))
  const stockCache = ref({})

  const count = computed(() => items.value.reduce((s, i) => s + i.qty, 0))
  const total = computed(() => items.value.reduce((s, i) => s + i.qty * i.price, 0))

  function save() { localStorage.setItem('cart', JSON.stringify(items.value)) }

  // ✅ Синхронизация с backend при логине
  async function syncWithServer() {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) return

    try {
      // Загрузить серверную корзину
      const serverItems = await api.get('/orders/cart/me')
      
      // Объединить с локальной (локальная приоритетнее по количеству)
      const localItems = items.value
      const merged = [...localItems]

      for (const serverItem of serverItems) {
        const local = merged.find(i => i.id === serverItem.product_id)
        if (local) {
          // Обновить количество на сервере (максимум)
          const newQty = Math.max(local.qty, serverItem.quantity)
          if (newQty !== serverItem.quantity) {
            await api.put(`/orders/cart/me/${serverItem.product_id}`, {
              product_id: serverItem.product_id,
              quantity: newQty
            })
          }
          local.qty = newQty
        } else {
          merged.push({
            id: serverItem.product_id,
            name: serverItem.product_name || 'Unknown',
            price: serverItem.product_price || 0,
            qty: serverItem.quantity
          })
          // Добавить на сервер если только в локальной
          await api.post('/orders/cart/me', {
            product_id: serverItem.product_id,
            quantity: serverItem.quantity
          })
        }
      }

      // Отправить локальные товары на сервер
      for (const localItem of localItems) {
        const serverItem = serverItems.find(i => i.product_id === localItem.id)
        if (!serverItem) {
          await api.post('/orders/cart/me', {
            product_id: localItem.id,
            quantity: localItem.qty
          })
        }
      }

      items.value = merged
      save()
    } catch (e) {
      console.error('Cart sync failed:', e)
    }
  }

  // ✅ Сохранить на сервер при изменении (если залогинен)
  async function syncItem(productId, quantity) {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) return
    try {
      const existing = await api.get('/orders/cart/me').then(items => 
        items.find(i => i.product_id === productId)
      )
      if (existing) {
        await api.put(`/orders/cart/me/${productId}`, { product_id: productId, quantity })
      } else {
        await api.post('/orders/cart/me', { product_id: productId, quantity })
      }
    } catch (e) {
      console.error('Cart item sync failed:', e)
    }
  }

  async function refreshStock() {
    const ids = items.value.map(i => i.id)
    if (!ids.length) return
    try {
      const products = await api.get(`/products?limit=100`)
      stockCache.value = {}
      for (const p of products) {
        if (ids.includes(p.id)) {
          stockCache.value[p.id] = p.stock_quantity || 0
        }
      }
    } catch (e) {
      console.error('Failed to refresh stock:', e)
    }
  }

  function add(product, qty = 1) {
    const available = stockCache.value[product.id]
    if (available !== undefined && qty > available) {
      throw new Error(`Only ${available} items available`)
    }
    const existing = items.value.find(i => i.id === product.id)
    if (existing) {
      const newQty = existing.qty + qty
      if (available !== undefined && newQty > available) {
        throw new Error(`Only ${available} items available. You have ${existing.qty} in cart.`)
      }
      existing.qty = newQty
      syncItem(product.id, newQty)  // ✅ синхронизация
    } else {
      items.value.push({ id: product.id, name: product.name, price: product.price, unit: product.unit, qty })
      syncItem(product.id, qty)  // ✅ синхронизация
    }
    save()
  }

  function remove(productId) {
    items.value = items.value.filter(i => i.id !== productId)
    save()
    const auth = useAuthStore()
    if (auth.isLoggedIn) {
      api.delete(`/orders/cart/me/${productId}`).catch(() => {})  // ✅ синхронизация
    }
  }

  function updateQty(productId, qty) {
    const item = items.value.find(i => i.id === productId)
    if (!item) return
    const available = stockCache.value[productId]
    if (available !== undefined && qty > available) {
      throw new Error(`Only ${available} items available`)
    }
    item.qty = Math.max(1, qty)
    save()
    syncItem(productId, qty)  // ✅ синхронизация
  }

  function clear() { 
    items.value = []
    save()
    const auth = useAuthStore()
    if (auth.isLoggedIn) {
      api.delete('/orders/cart/me').catch(() => {})  // ✅ синхронизация
    }
  }

  return { 
    items, count, total, stockCache,
    add, remove, updateQty, clear,
    refreshStock, syncWithServer, syncItem
  }
})
