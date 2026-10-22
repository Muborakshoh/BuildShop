<template>
  <div class="product-page">
    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <template v-else-if="product">
      <nav class="breadcrumb">
        <router-link to="/products">{{ t('products_title') }}</router-link>
        <span> / </span>
        <span v-if="product.category">{{ ml(product.category, 'name') }}</span>
        <span> / </span>
        <span>{{ ml(product, 'name') }}</span>
      </nav>

      <div class="product-detail">
        <div class="product-image">
          <img v-if="product.image_url" :src="product.image_url" :alt="ml(product, 'name')" />
          <div v-else class="img-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
          </div>
        </div>

        <div class="product-info">
          <div class="category-badge" v-if="product.category">{{ ml(product.category, 'name') }}</div>
          <h1>{{ ml(product, 'name') }}</h1>
          <p class="description" v-if="ml(product, 'description')">{{ ml(product, 'description') }}</p>

          <div class="price-block">
            <span class="price">{{ money(product.price) }}</span>
            <span class="unit" v-if="product.unit">/ {{ product.unit }}</span>
          </div>

          <!-- Rating -->
          <div class="rating-row" v-if="avgRating > 0">
            <span v-for="s in 5" :key="s" class="star" :class="{filled: s <= Math.round(avgRating)}">★</span>
            <span class="rating-text">{{ avgRating.toFixed(1) }} ({{ reviews.length }})</span>
          </div>

          <div class="stock-badge" :class="product.stock_quantity > 0 ? 'in-stock' : 'out-stock'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-if="product.stock_quantity > 0"><path d="M20 6L9 17l-5-5"/></svg>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-else><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            {{ product.stock_quantity > 0
              ? (t('in_stock') || 'Дар анбор') + ': ' + product.stock_quantity + ' ' + (product.unit || t('pcs'))
              : (t('out_of_stock') || 'Нест дар анбор') }}
          </div>

          <div class="quantity-row" v-if="product.stock_quantity > 0">
            <button class="qty-btn" @click="qty = Math.max(1, qty - 1)">−</button>
            <input type="number" v-model.number="qty" min="1" :max="product.stock_quantity" class="qty-input" />
            <button class="qty-btn" @click="qty = Math.min(product.stock_quantity, qty + 1)">+</button>
            <button class="btn-add-cart" @click="addToCart">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>
              {{ t('products_addToCart') }}
            </button>
          </div>
          <p v-if="added" class="added-msg">✓ {{ t('product_added') }}</p>

          <!-- Volume/specs -->
          <div class="specs" v-if="product.volume">
            <div class="spec-row"><span>{{ t('volume') || 'Ҳаҷм' }}</span><span>{{ product.volume }}</span></div>
          </div>
        </div>
      </div>

      <!-- Reviews section -->
      <section class="reviews-section">
        <h2>{{ t('product_reviews') }} ({{ reviews.length }})</h2>

        <!-- Write review (logged in only) -->
        <div v-if="auth.isLoggedIn && !userReview" class="review-form">
          <h3>{{ t('write_review') || 'Шарҳ навиштан' }}</h3>
          <div class="star-picker">
            <span v-for="s in 5" :key="s" class="star-pick" :class="{active: s <= newRating}" @click="newRating = s">★</span>
          </div>
          <textarea v-model="newText" :placeholder="t('review_placeholder') || 'Шарҳи шумо...'" rows="3"></textarea>
          <button class="btn-submit-review" @click="submitReview" :disabled="!newRating || submitting">
            {{ submitting ? '...' : (t('submit') || 'Фиристодан') }}
          </button>
          <p v-if="reviewError" class="review-error">{{ reviewError }}</p>
        </div>

        <div v-if="reviews.length === 0" class="no-reviews">{{ t('product_noReviews') }}</div>
        <div v-for="r in reviews" :key="r.id" class="review-card">
          <div class="review-header">
            <div class="review-avatar">{{ (r.user_name || '?')[0] }}</div>
            <div>
              <span class="review-author">{{ r.user_name || t('product_anonymous') }}</span>
              <span class="review-date">{{ formatDate(r.created_at) }}</span>
            </div>
            <span class="review-stars">
              <span v-for="s in 5" :key="s" class="star" :class="{filled: s <= r.rating}">★</span>
            </span>
          </div>
          <p class="review-text" v-if="r.text">{{ r.text }}</p>
        </div>
      </section>
    </template>

    <div v-else class="not-found">{{ t('product_notFound') }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'
import { money, ml } from '@/utils/helpers'
import { useCartStore } from '@/stores/cart'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const route = useRoute()
const cart = useCartStore()
const auth = useAuthStore()

const product = ref(null)
const reviews = ref([])
const loading = ref(true)
const qty = ref(1)
const added = ref(false)

// Review form
const newRating = ref(0)
const newText = ref('')
const submitting = ref(false)
const reviewError = ref('')
const userReview = computed(() => reviews.value.find(r => r.user_id === auth.user?.id))
const avgRating = computed(() => {
  if (!reviews.value.length) return 0
  return reviews.value.reduce((s,r) => s + r.rating, 0) / reviews.value.length
})

function addToCart() {
  if (!product.value) return
  cart.add(product.value, qty.value)
  added.value = true
  setTimeout(() => { added.value = false }, 2000)
}

async function submitReview() {
  submitting.value = true
  reviewError.value = ''
  try {
    const rev = await api.post('/reviews/', { product_id: product.value.id, rating: newRating.value, text: newText.value || null })
    reviews.value.unshift(rev)
    newRating.value = 0
    newText.value = ''
  } catch (e) {
    reviewError.value = e.message || 'Хатогӣ'
  }
  submitting.value = false
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU', { day:'2-digit', month:'short', year:'numeric' })
}

onMounted(async () => {
  try {
    const id = route.params.id
    const [prod, revs] = await Promise.all([
      api.get(`/products/${id}`),
      api.get(`/reviews/product/${id}`).catch(() => [])
    ])
    product.value = prod
    reviews.value = Array.isArray(revs) ? revs : []
  } catch (e) { console.error(e) }
  loading.value = false
})
</script>

<style scoped>
.product-page{max-width:1000px;margin:0 auto;padding:16px 16px 100px}
.loading{display:flex;justify-content:center;padding:60px}
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

.breadcrumb{margin-bottom:16px;font-size:13px;color:var(--muted)}
.breadcrumb a{color:var(--accent);text-decoration:none}

.product-detail{display:flex;gap:24px;margin-bottom:32px}
.product-image{flex:0 0 360px;height:320px;background:var(--bg);border-radius:16px;overflow:hidden;display:flex;align-items:center;justify-content:center}
.product-image img{max-width:90%;max-height:90%;width:auto;height:auto;object-fit:contain}
.img-placeholder{opacity:.15}
.img-placeholder svg{width:80px;height:80px}

.product-info{flex:1}
.category-badge{display:inline-block;padding:4px 12px;background:var(--accent-bg,rgba(37,99,235,.08));color:var(--accent);font-size:12px;font-weight:600;border-radius:20px;margin-bottom:8px}
.product-info h1{font-size:22px;font-weight:800;margin-bottom:8px;line-height:1.3}
.description{color:var(--muted);line-height:1.6;margin-bottom:16px;font-size:14px}

.price-block{margin-bottom:8px}
.price{font-size:28px;font-weight:800;color:var(--accent)}
.unit{font-size:16px;color:var(--muted)}

.rating-row{display:flex;align-items:center;gap:4px;margin-bottom:10px}
.star{font-size:16px;color:var(--border)}
.star.filled{color:#f59e0b}
.rating-text{font-size:13px;color:var(--muted);margin-left:4px}

.stock-badge{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border-radius:8px;font-size:13px;font-weight:600;margin-bottom:16px}
.stock-badge svg{width:16px;height:16px}
.in-stock{background:rgba(22,163,74,.08);color:#16a34a}
.out-stock{background:rgba(220,38,38,.08);color:#dc2626}

.quantity-row{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.qty-btn{width:40px;height:40px;border:1px solid var(--border);border-radius:10px;background:var(--surface);color:var(--text);font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.qty-btn:hover{background:var(--bg)}
.qty-input{width:56px;text-align:center;padding:8px;border:1px solid var(--border);border-radius:10px;font-size:16px;background:var(--surface);color:var(--text)}
.btn-add-cart{display:flex;align-items:center;gap:8px;padding:10px 20px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;transition:opacity .15s}
.btn-add-cart svg{width:20px;height:20px}
.btn-add-cart:hover{opacity:.9}
.added-msg{color:#16a34a;font-size:14px;font-weight:600;margin-top:4px}

.specs{margin-top:16px;border-top:1px solid var(--border);padding-top:12px}
.spec-row{display:flex;justify-content:space-between;padding:6px 0;font-size:13px;border-bottom:1px solid var(--border)}
.spec-row:last-child{border:none}
.spec-row span:first-child{color:var(--muted);font-weight:500}
.spec-row span:last-child{font-weight:600}

/* Reviews */
.reviews-section{border-top:1px solid var(--border);padding-top:24px}
.reviews-section h2{font-size:18px;font-weight:700;margin-bottom:16px}

.review-form{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:20px}
.review-form h3{font-size:14px;font-weight:700;margin-bottom:10px}
.star-picker{display:flex;gap:4px;margin-bottom:10px}
.star-pick{font-size:28px;color:var(--border);cursor:pointer;transition:color .15s}
.star-pick.active{color:#f59e0b}
.star-pick:hover{color:#f59e0b}
.review-form textarea{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:10px;background:var(--bg);color:var(--text);font-size:14px;resize:vertical;font-family:inherit}
.btn-submit-review{margin-top:10px;padding:8px 20px;background:var(--accent);color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer}
.btn-submit-review:disabled{opacity:.5}
.review-error{color:#dc2626;font-size:13px;margin-top:6px}

.review-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:10px}
.review-header{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.review-avatar{width:36px;height:36px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0}
.review-author{font-weight:600;font-size:14px;display:block}
.review-date{font-size:11px;color:var(--muted)}
.review-stars{margin-left:auto}
.review-text{color:var(--muted);font-size:14px;line-height:1.5}
.no-reviews{text-align:center;padding:24px;color:var(--muted);font-size:14px}
.not-found{text-align:center;padding:60px;color:var(--muted);font-size:16px}

@media(max-width:768px){
  .product-detail{flex-direction:column}
  .product-image{flex:none;width:100%;height:240px}
}
</style>
