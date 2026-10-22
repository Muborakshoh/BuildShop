<template>
  <div class="cart-page">
    <h1>{{ t('cart_title') }}</h1>

    <div v-if="cart.items.length === 0" class="empty-cart">
      <p>{{ t('cart_empty') }}</p>
      <router-link to="/products" class="btn-secondary">{{ t('cart_goShopping') }}</router-link>
    </div>

    <template v-else>
      <div class="cart-items">
        <div v-for="item in cart.items" :key="item.id" class="cart-item">
          <div class="item-info">
            <router-link :to="`/products/${item.id}`" class="item-name">{{ item.name }}</router-link>
            <span class="item-unit" v-if="item.unit">{{ item.unit }}</span>
          </div>
          <div class="item-price">{{ money(item.price) }}</div>
          <div class="item-qty">
            <button class="qty-btn" @click="cart.updateQty(item.id, item.qty - 1)">-</button>
            <span class="qty-val">{{ item.qty }}</span>
            <button class="qty-btn" @click="cart.updateQty(item.id, item.qty + 1)">+</button>
          </div>
          <div class="item-subtotal">{{ money(item.price * item.qty) }}</div>
          <button class="btn-remove" @click="cart.remove(item.id)">✕</button>
        </div>
      </div>

      <!-- Checkout section -->
      <div class="checkout-section">
        <!-- Delivery -->
        <div class="checkout-block">
          <h3>🚚 {{ t('delivery_method') || 'Тарзи интиқол' }}</h3>
          <div class="radio-group">
            <label class="radio-card" :class="{active: deliveryMethod === 'pickup'}">
              <input type="radio" v-model="deliveryMethod" value="pickup" />
              <div>
                <strong>{{ t('pickup') || 'Худ гирифтан' }}</strong>
                <span class="radio-hint">{{ t('pickup_hint') || 'Аз мағоза гиред — бепул' }}</span>
              </div>
              <span class="price-tag free">{{ t('free') || 'Бепул' }}</span>
            </label>
            <label class="radio-card" :class="{active: deliveryMethod === 'delivery'}">
              <input type="radio" v-model="deliveryMethod" value="delivery" />
              <div>
                <strong>{{ t('delivery') || 'Интиқол' }}</strong>
                <span class="radio-hint">{{ t('delivery_hint') || 'Ба суроғаи шумо' }}</span>
              </div>
            </label>
          </div>

          <template v-if="deliveryMethod === 'delivery'">
            <select v-model="selectedZone" class="input" v-if="zones.length">
              <option :value="null" disabled>{{ t('select_zone') || 'Минтақаро интихоб кунед' }}</option>
              <option v-for="z in zones" :key="z.id" :value="z">
                {{ z.name }} — {{ z.min_order_for_free && cart.total >= z.min_order_for_free ? (t('free') || 'Бепул') : money(z.price) }}
                {{ z.estimated_days ? `(${z.estimated_days})` : '' }}
              </option>
            </select>
            <input v-model="address" :placeholder="t('delivery_address') || 'Суроғаи интиқол'" class="input" />
            <input v-model="phone" :placeholder="t('phone') || 'Телефон: +992 ...'" class="input" type="tel" />
          </template>
        </div>

        <!-- Payment -->
        <div class="checkout-block">
          <h3>💳 {{ t('payment_method') || 'Тарзи пардохт' }}</h3>
          <div class="radio-group">
            <label class="radio-card" :class="{active: paymentMethod === 'cash'}">
              <input type="radio" v-model="paymentMethod" value="cash" />
              <div>
                <strong>{{ t('cash_payment') || 'Нақд' }}</strong>
                <span class="radio-hint">{{ t('cash_hint') || 'Ҳангоми гирифтан пардохт кунед' }}</span>
              </div>
            </label>
            <label class="radio-card" :class="{active: paymentMethod === 'transfer'}">
              <input type="radio" v-model="paymentMethod" value="transfer" />
              <div>
                <strong>{{ t('bank_transfer') || 'Интиқоли бонкӣ' }}</strong>
                <span class="radio-hint">{{ t('transfer_hint') || 'Ба ҳисоби бонкии мо' }}</span>
              </div>
            </label>
          </div>
        </div>

        <!-- Comment -->
        <div class="checkout-block">
          <textarea v-model="comment" :placeholder="t('order_comment') || 'Шарҳ ба фармоиш (ихтиёрӣ)'" class="input textarea" rows="2"></textarea>
        </div>

        <!-- Total -->
        <div class="cart-footer">
          <div class="total-breakdown">
            <div class="tb-row"><span>{{ t('products') || 'Маҳсулот' }}</span><span>{{ money(cart.total) }}</span></div>
            <div class="tb-row" v-if="deliveryMethod === 'delivery'">
              <span>{{ t('delivery') || 'Интиқол' }}</span>
              <span :class="{free: deliveryCost === 0}">{{ deliveryCost === 0 ? (t('free') || 'Бепул') : money(deliveryCost) }}</span>
            </div>
            <div class="tb-row total-row">
              <span>{{ t('cart_total') || 'Ҳамагӣ' }}</span>
              <strong>{{ money(cart.total + deliveryCost) }}</strong>
            </div>
          </div>
          <button class="btn-order" @click="placeOrder" :disabled="ordering || !canOrder">
            {{ ordering ? (t('common_loading') || 'Боркунӣ') + '...' : (t('cart_placeOrder') || 'Фармоиш додан') }}
          </button>
          <p v-if="error" class="error-msg">{{ error }}</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'
import { money } from '@/utils/helpers'
import { useCartStore } from '@/stores/cart'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const cart = useCartStore()
const auth = useAuthStore()

const ordering = ref(false)
const error = ref('')
const deliveryMethod = ref('pickup')
const paymentMethod = ref('cash')
const selectedZone = ref(null)
const address = ref('')
const phone = ref('')
const comment = ref('')
const zones = ref([])

onMounted(async () => {
  try {
    zones.value = await api.get('/delivery/zones')
  } catch (e) {
    zones.value = []
  }
})

const deliveryCost = computed(() => {
  if (deliveryMethod.value === 'pickup' || !selectedZone.value) return 0
  const z = selectedZone.value
  if (z.min_order_for_free && cart.total >= z.min_order_for_free) return 0
  return Number(z.price)
})

const canOrder = computed(() => {
  if (deliveryMethod.value === 'delivery' && !address.value.trim()) return false
  return true
})

async function placeOrder() {
  if (!auth.isLoggedIn) {
    router.push({ name: 'Auth', query: { redirect: '/cart' } })
    return
  }
  ordering.value = true
  error.value = ''
  try {
    const data = {
      items: cart.items.map(i => ({ product_id: i.id, quantity: i.qty })),
      delivery_method: deliveryMethod.value,
      delivery_address: deliveryMethod.value === 'delivery' ? address.value : 'Самовывоз',
      delivery_zone_id: deliveryMethod.value === 'delivery' && selectedZone.value ? selectedZone.value.id : null,
      payment_method: paymentMethod.value,
      phone: phone.value || null,
      comment: comment.value || null,
    }
    await api.post('/orders', data)
    cart.clear()
    router.push('/orders')
  } catch (e) {
    error.value = e.message || t('cart_orderError')
  } finally {
    ordering.value = false
  }
}
</script>

<style scoped>
.cart-page{max-width:800px;margin:0 auto;padding:1.5rem}
.cart-page h1{font-size:1.75rem;color:var(--text);margin-bottom:2rem}
.empty-cart{text-align:center;padding:3rem;color:var(--muted)}
.empty-cart p{font-size:1.1rem;margin-bottom:1.5rem}
.btn-secondary{display:inline-block;padding:.6rem 2rem;background:var(--surface);color:var(--accent);border:1px solid var(--accent);border-radius:8px;text-decoration:none;font-size:.95rem}
.btn-secondary:hover{background:var(--accent-bg)}
.cart-items{margin-bottom:1.5rem}
.cart-item{display:flex;align-items:center;gap:1rem;padding:1rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:.75rem}
.item-info{flex:1;min-width:0}
.item-name{font-weight:600;color:var(--text);text-decoration:none;display:block}
.item-name:hover{color:var(--accent)}
.item-unit{font-size:.8rem;color:var(--muted)}
.item-price{color:var(--muted);font-size:.9rem;white-space:nowrap}
.item-qty{display:flex;align-items:center;gap:.5rem}
.qty-btn{width:30px;height:30px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center}
.qty-btn:hover{background:var(--border)}
.qty-val{min-width:24px;text-align:center;font-weight:600}
.item-subtotal{font-weight:700;color:var(--accent);white-space:nowrap;min-width:80px;text-align:right}
.btn-remove{background:none;border:none;color:var(--muted);cursor:pointer;font-size:1.1rem;padding:.25rem}
.btn-remove:hover{color:#dc2626}

.checkout-section{display:flex;flex-direction:column;gap:1rem}
.checkout-block{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.25rem}
.checkout-block h3{font-size:1rem;color:var(--text);margin:0 0 1rem}
.radio-group{display:flex;flex-direction:column;gap:.5rem}
.radio-card{display:flex;align-items:center;gap:.75rem;padding:.75rem 1rem;border:1.5px solid var(--border);border-radius:8px;cursor:pointer;transition:all .15s}
.radio-card:hover{border-color:var(--accent)}
.radio-card.active{border-color:var(--accent);background:var(--accent-bg,rgba(37,99,235,.04))}
.radio-card input{accent-color:var(--accent)}
.radio-card strong{display:block;font-size:.95rem;color:var(--text)}
.radio-hint{display:block;font-size:.8rem;color:var(--muted);margin-top:2px}
.price-tag{margin-left:auto;font-size:.8rem;font-weight:600;padding:2px 8px;border-radius:4px}
.price-tag.free{background:#dcfce7;color:#166534}
.input{width:100%;padding:.65rem .85rem;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:.9rem;margin-top:.5rem;box-sizing:border-box}
.input:focus{outline:none;border-color:var(--accent)}
.textarea{resize:vertical;font-family:inherit}

.cart-footer{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.5rem}
.total-breakdown{margin-bottom:1rem}
.tb-row{display:flex;justify-content:space-between;padding:.35rem 0;font-size:.95rem;color:var(--text)}
.tb-row .free{color:#16a34a;font-weight:600}
.total-row{border-top:1px solid var(--border);padding-top:.75rem;margin-top:.5rem;font-size:1.15rem}
.total-row strong{color:var(--accent);font-size:1.35rem}
.btn-order{width:100%;padding:.75rem;background:var(--accent);color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;transition:opacity .15s}
.btn-order:hover{opacity:.9}
.btn-order:disabled{opacity:.5;cursor:not-allowed}
.error-msg{color:#dc2626;margin-top:.75rem;font-size:.9rem;text-align:center}

@media(max-width:640px){
  .cart-item{flex-wrap:wrap;gap:.5rem}
  .item-info{width:100%}
  .item-subtotal{min-width:auto}
}
</style>
