<template>
  <div class="products-page">
    <div class="page-header">
      <h1>{{ t('products_title') }}</h1>
      <div class="search-bar">
        <input
          v-model="search"
          type="text"
          :placeholder="t('products_search')"
          @input="onSearch"
        />
      </div>
    </div>

    <div class="content-layout">
      <aside class="sidebar">
        <h3>{{ t('products_categories') }}</h3>
        <button
          class="cat-chip"
          :class="{ active: !selectedCategory }"
          @click="selectedCategory = null; loadProducts()"
        >
          {{ t('products_all') }}
        </button>
        <button
          v-for="cat in categories"
          :key="cat.id"
          class="cat-chip"
          :class="{ active: selectedCategory === cat.id }"
          @click="selectedCategory = cat.id; loadProducts()"
        >
          {{ ml(cat, 'name') }}
        </button>
      </aside>

      <main class="products-main">
        <div v-if="loading" class="loading">{{ t('common_loading') }}...</div>

        <div v-else-if="products.length === 0" class="empty">
          {{ t('products_empty') }}
        </div>

        <div v-else class="products-grid">
          <div v-for="p in products" :key="p.id" class="product-card">
            <router-link :to="`/products/${p.id}`" class="card-link">
              <div class="product-img">
                <img v-if="p.image_url" :src="p.image_url" :alt="ml(p, 'name')" />
                <div v-else class="img-placeholder">🏗️</div>
              </div>
              <div class="product-info">
                <h3>{{ ml(p, 'name') }}</h3>
                <p class="price">{{ money(p.price) }}</p>
                <span class="unit" v-if="p.unit">/ {{ p.unit }}</span>
                <span class="stock" :class="p.stock_quantity > 0 ? 'in-stock' : 'out-stock'">
                  {{ p.stock_quantity > 0 ? t('products_inStock') : t('products_outOfStock') }}
                </span>
              </div>
            </router-link>
            <button
              class="btn-add"
              :disabled="p.stock_quantity <= 0"
              @click="addToCart(p)"
            >
              {{ t('products_addToCart') }}
            </button>
          </div>
        </div>

        <div v-if="hasMore" class="load-more">
          <button class="btn-secondary" @click="loadMore" :disabled="loadingMore">
            {{ loadingMore ? t('common_loading') + '...' : t('products_loadMore') }}
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'
import { money, ml, debounce } from '@/utils/helpers'
import { useCartStore } from '@/stores/cart'

const { t } = useI18n()
const route = useRoute()
const cart = useCartStore()

const products = ref([])
const categories = ref([])
const search = ref('')
const selectedCategory = ref(null)
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(false)
const page = ref(1)
const limit = 12

async function loadProducts(reset = true) {
  if (reset) { page.value = 1 }
  loading.value = reset
  loadingMore.value = !reset

  try {
    let url = `/products?limit=${limit}&offset=${(page.value - 1) * limit}`
    if (search.value) url += `&search=${encodeURIComponent(search.value)}`
    if (selectedCategory.value) url += `&category_id=${selectedCategory.value}`

    const data = await api.get(url)
    const items = Array.isArray(data) ? data : data.items || []

    if (reset) {
      products.value = items
    } else {
      products.value.push(...items)
    }

    const total = data.total || 0
    hasMore.value = products.value.length < total
  } catch (e) {
    console.error('Failed to load products:', e)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  page.value++
  loadProducts(false)
}

const onSearch = debounce(() => loadProducts(), 400)

function addToCart(product) {
  cart.add(product)
}

onMounted(async () => {
  if (route.query.category) {
    selectedCategory.value = Number(route.query.category)
  }
  try {
    const cats = await api.get('/categories')
    categories.value = Array.isArray(cats) ? cats : cats.items || []
  } catch (e) {
    console.error('Failed to load categories:', e)
  }
  loadProducts()
})
</script>

<style scoped>
.products-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.page-header h1 {
  font-size: 1.75rem;
  color: var(--text);
}

.search-bar input {
  padding: 0.6rem 1rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.95rem;
  background: var(--surface);
  color: var(--text);
  width: 280px;
}

.search-bar input:focus {
  outline: none;
  border-color: var(--accent);
}

.content-layout {
  display: flex;
  gap: 2rem;
}

.sidebar {
  flex-shrink: 0;
  width: 200px;
}

.sidebar h3 {
  font-size: 1rem;
  margin-bottom: 0.75rem;
  color: var(--text);
}

.cat-chip {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.25rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.15s;
}

.cat-chip:hover {
  background: var(--border);
}

.cat-chip.active {
  background: var(--accent);
  color: #fff;
}

.products-main {
  flex: 1;
  min-width: 0;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.25rem;
}

.product-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card-link {
  text-decoration: none;
  color: var(--text);
  flex: 1;
}

.product-img {
  height: 150px;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.product-img img {
  max-width: 90%;
  max-height: 90%;
  width: auto;
  height: auto;
  object-fit: contain;
}

.img-placeholder {
  font-size: 2.5rem;
  opacity: 0.3;
}

.product-info {
  padding: 0.75rem 1rem;
}

.product-info h3 {
  font-size: 0.95rem;
  margin-bottom: 0.4rem;
  line-height: 1.3;
}

.price {
  font-weight: 700;
  color: var(--accent);
}

.unit {
  font-size: 0.8rem;
  color: var(--muted);
}

.stock {
  display: block;
  font-size: 0.8rem;
  margin-top: 0.3rem;
}

.in-stock { color: #16a34a; }
.out-stock { color: #dc2626; }

.btn-add {
  margin: 0.5rem 1rem 1rem;
  padding: 0.5rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: opacity 0.15s;
}

.btn-add:hover { opacity: 0.9; }
.btn-add:disabled { opacity: 0.4; cursor: not-allowed; }

.load-more {
  text-align: center;
  margin-top: 2rem;
}

.btn-secondary {
  padding: 0.6rem 2rem;
  background: var(--surface);
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
}

.btn-secondary:hover { background: var(--accent-bg); }
.btn-secondary:disabled { opacity: 0.5; }

.loading, .empty {
  text-align: center;
  padding: 3rem;
  color: var(--muted);
  font-size: 1.1rem;
}

@media (max-width: 768px) {
  .content-layout {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .sidebar h3 { width: 100%; }
  .cat-chip { width: auto; }
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  .search-bar input { width: 100%; }
}
</style>
