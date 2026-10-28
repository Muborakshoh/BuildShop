<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/utils/api'
import { money } from '@/utils/helpers'

const { t } = useI18n()
const auth = useAuthStore()

// Shift state
const shift = ref(null)
const shiftLoading = ref(true)
const openForm = ref({ register_name: 'Касса-1', opening_cash: 0 })
const closeForm = ref({ actual_cash: 0 })
const showCloseModal = ref(false)
const shiftSummary = ref(null)

// Products
const search = ref('')
const products = ref([])
const searchResults = ref([])
const popularProducts = ref([])
const categories = ref([])
const activeCategory = ref(null)
let searchTimeout = null

// Cart
const cart = ref([])
const total = computed(() => cart.value.reduce((s, i) => s + i.price * i.qty, 0))
const itemCount = computed(() => cart.value.reduce((s, i) => s + i.qty, 0))

// Payment
const showPayment = ref(false)
const payMethod = ref('cash')
const cashGiven = ref(0)
const change = computed(() => Math.max(0, cashGiven.value - total.value))
const processing = ref(false)

// Recent sales
const recentSales = ref([])
const showReceipt = ref(null)

// Отчёты
const showXReport = ref(false)
const xReport = ref(null)
const zReport = ref(null)
const closedShiftId = ref(null)

async function openXReport() {
  try {
    xReport.value = await api.get(`/cashier/shifts/${shift.value.id}/x-report`)
    showXReport.value = true
  } catch (e) { showToast(e.message, 'err') }
}

// Toast
const toast = ref('')
const toastType = ref('ok')
function showToast(msg, type='ok') {
  toast.value = msg; toastType.value = type
  setTimeout(() => toast.value = '', 3000)
}

// ── Shift management ──
onMounted(async () => {
  await loadShift()
  await loadProducts()
})

async function loadShift() {
  shiftLoading.value = true
  try {
    shift.value = await api.get('/cashier/shifts/current')
    await loadRecentSales()
  } catch {
    shift.value = null
  }
  shiftLoading.value = false
}

async function openShift() {
  try {
    shift.value = await api.post('/cashier/shifts/open', openForm.value)
    showToast(t('shift_opened') || 'Смена открыта')
  } catch (e) { showToast(e.message, 'err') }
}

async function prepareCloseShift() {
  try {
    shiftSummary.value = await api.get(`/cashier/shifts/${shift.value.id}/summary`)
    closeForm.value.actual_cash = parseFloat(shiftSummary.value.shift.expected_cash) || 0
    showCloseModal.value = true
  } catch (e) { showToast(e.message, 'err') }
}

async function closeShift() {
  try {
    const closed = await api.post(`/cashier/shifts/${shift.value.id}/close`, closeForm.value)
    closedShiftId.value = closed.id
    try {
      zReport.value = await api.get(`/cashier/shifts/${closed.id}/z-report`)
    } catch { zReport.value = null }
    shift.value = null
    showCloseModal.value = false
    shiftSummary.value = null
    cart.value = []
    recentSales.value = []
    showToast(t('shift_closed') || 'Смена закрыта')
  } catch (e) { showToast(e.message, 'err') }
}

// ── Products ──
async function loadProducts() {
  try {
    products.value = await api.get('/products?limit=500')
    // Extract unique categories
    const cats = new Set()
    products.value.forEach(p => { if (p.category?.name) cats.add(p.category.name) })
    categories.value = [...cats]
    // Popular = first 8
    popularProducts.value = products.value.slice(0, 8)
  } catch {}
}

function doSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    const q = search.value.toLowerCase()
    if (q.length < 2) { searchResults.value = []; return }
    searchResults.value = products.value.filter(p =>
      (p.name || '').toLowerCase().includes(q) ||
      (p.sku || '').toLowerCase().includes(q)
    ).slice(0, 12)
  }, 200)
}

const filteredProducts = computed(() => {
  if (search.value.length >= 2) return searchResults.value
  if (activeCategory.value) return products.value.filter(p => p.category?.name === activeCategory.value)
  return popularProducts.value
})

// ── Cart ──
function addToCart(p) {
  const ex = cart.value.find(i => i.id === p.id)
  if (ex) { ex.qty++ }
  else { cart.value.push({ id: p.id, name: p.name, price: parseFloat(p.price), unit: p.unit, qty: 1 }) }
  search.value = ''
  searchResults.value = []
}

function updateQty(item, delta) {
  item.qty += delta
  if (item.qty <= 0) cart.value = cart.value.filter(i => i.id !== item.id)
}

function removeFromCart(id) {
  cart.value = cart.value.filter(i => i.id !== id)
}

function clearCart() { cart.value = [] }

// ── Payment ──
function openPayment() {
  if (!cart.value.length) return
  payMethod.value = 'cash'
  cashGiven.value = Math.ceil(total.value)
  showPayment.value = true
}

async function processPayment() {
  if (processing.value) return
  processing.value = true
  try {
    const payload = {
      payment_method: payMethod.value,
      cash_amount: payMethod.value === 'card' ? 0 : (payMethod.value === 'mixed' ? cashGiven.value : total.value),
      card_amount: payMethod.value === 'cash' ? 0 : (payMethod.value === 'mixed' ? total.value - cashGiven.value : total.value),
      items: cart.value.map(i => ({ product_id: i.id, quantity: i.qty })),
      comment: null
    }
    const sale = await api.post('/cashier/sales', payload)
    recentSales.value.unshift(sale)
    showReceipt.value = { ...sale, cartItems: [...cart.value], changeAmount: change.value, paymentMethod: payMethod.value }
    cart.value = []
    showPayment.value = false
    showToast(t('sale_complete') || 'Фурӯш сабт шуд!')
  } catch (e) {
    showToast(e.message, 'err')
  }
  processing.value = false
}

async function loadRecentSales() {
  if (!shift.value) return
  try {
    recentSales.value = await api.get(`/cashier/shifts/${shift.value.id}/transactions?limit=20`)
  } catch {}
}

function quickCash(amount) { cashGiven.value = amount }

function formatTime(d) {
  return new Date(d).toLocaleTimeString('ru-RU', { hour:'2-digit', minute:'2-digit' })
}
</script>

<template>
  <div class="pos">
    <!-- No shift open -->
    <div v-if="shiftLoading" class="pos-loading">
      <div class="spinner"></div>
    </div>

    <div v-else-if="!shift" class="open-shift-screen">
      <div class="oss-card">
        <div class="oss-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/><line x1="6" y1="14" x2="10" y2="14"/></svg>
        </div>
        <h1>{{ t('open_shift') || 'Кушодани смена' }}</h1>
        <p>{{ t('open_shift_desc') || 'Барои оғоз кардани кор, сменаро кушоед' }}</p>
        <label class="oss-field">
          <span>{{ t('register_name') || 'Номи касса' }}</span>
          <input v-model="openForm.register_name" placeholder="Касса-1"/>
        </label>
        <label class="oss-field">
          <span>{{ t('opening_cash') || 'Пули ибтидоӣ' }}</span>
          <input type="number" v-model.number="openForm.opening_cash" min="0" step="0.01"/>
        </label>
        <button class="oss-btn" @click="openShift">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>
          {{ t('start_shift') || 'Оғоз' }}
        </button>
      </div>
    </div>

    <!-- Main POS layout -->
    <template v-else>
      <div class="pos-layout">
        <!-- LEFT: Product catalog -->
        <div class="pos-catalog">
          <!-- Search bar -->
          <div class="pos-search">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input v-model="search" @input="doSearch" :placeholder="t('search_product') || 'Ҷустуҷӯ... (ном ё артикул)'" />
          </div>

          <!-- Category pills -->
          <div class="cat-pills" v-if="categories.length">
            <button :class="['pill', {active: !activeCategory}]" @click="activeCategory=null">{{ t('all') || 'Ҳама' }}</button>
            <button v-for="cat in categories" :key="cat" :class="['pill', {active: activeCategory===cat}]" @click="activeCategory=cat">{{ cat }}</button>
          </div>

          <!-- Product grid -->
          <div class="product-grid">
            <button v-for="p in filteredProducts" :key="p.id" class="prod-card" @click="addToCart(p)">
              <div class="prod-img" v-if="p.image_url">
                <img :src="p.image_url" :alt="p.name" loading="lazy"/>
              </div>
              <div class="prod-img prod-placeholder" v-else>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
              </div>
              <div class="prod-name">{{ p.name }}</div>
              <div class="prod-price">{{ money(p.price) }}</div>
              <div class="prod-stock" v-if="p.stock_quantity <= 5" style="color:#ef4444">{{ p.stock_quantity }} {{ t('pcs') || 'шт' }}</div>
            </button>
            <div v-if="!filteredProducts.length" class="no-products">{{ t('no_results') || 'Натиҷае нест' }}</div>
          </div>
        </div>

        <!-- RIGHT: Cart + Payment -->
        <div class="pos-cart">
          <!-- Shift header -->
          <div class="shift-bar">
            <div class="shift-info">
              <div class="shift-dot"></div>
              <span>{{ shift.register_name }}</span>
            </div>
             <div class="shift-actions">
              <button class="shift-x-btn" @click="openXReport">X</button>
              <button class="shift-close-btn" @click="prepareCloseShift">{{ t('close_shift') || 'Пӯшидан' }}</button>
             </div>            
          </div>

          <!-- Cart items -->
          <div class="cart-items" :class="{'cart-empty': !cart.length}">
            <div v-if="!cart.length" class="empty-cart">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>
              <span>{{ t('cart_empty_hint') || 'Маҳсулот илова кунед' }}</span>
            </div>

            <TransitionGroup name="cart-item" tag="div">
              <div v-for="item in cart" :key="item.id" class="cart-row">
                <div class="cr-info">
                  <div class="cr-name">{{ item.name }}</div>
                  <div class="cr-unit-price">{{ money(item.price) }} × {{ item.qty }}</div>
                </div>
                <div class="cr-controls">
                  <button class="qty-btn" @click="updateQty(item, -1)">−</button>
                  <span class="qty-val">{{ item.qty }}</span>
                  <button class="qty-btn" @click="updateQty(item, 1)">+</button>
                </div>
                <div class="cr-total">{{ money(item.price * item.qty) }}</div>
                <button class="cr-del" @click="removeFromCart(item.id)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            </TransitionGroup>
          </div>

          <!-- Cart footer -->
          <div class="cart-footer" v-if="cart.length">
            <button class="clear-btn" @click="clearCart">{{ t('clear') || 'Тоза' }}</button>
            <div class="cart-total-row">
              <span>{{ itemCount }} {{ t('items') || 'адад' }}</span>
              <strong>{{ money(total) }}</strong>
            </div>
          </div>

          <!-- Pay button -->
          <button class="pay-btn" :disabled="!cart.length" @click="openPayment">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
            {{ t('pay') || 'Пардохт' }} · {{ money(total) }}
          </button>

          <!-- Recent sales ticker -->
          <div class="recent-sales" v-if="recentSales.length">
            <div class="rs-title">{{ t('recent') || 'Охирин' }}</div>
            <div class="rs-list">
              <div v-for="s in recentSales.slice(0,5)" :key="s.id" class="rs-item">
                <span class="rs-num">{{ s.receipt_number }}</span>
                <span class="rs-amount">{{ money(s.total_amount) }}</span>
                <span class="rs-time">{{ formatTime(s.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Payment modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showPayment" class="modal-overlay" @click.self="showPayment=false">
          <div class="pay-modal">
            <div class="pm-header">
              <h2>{{ t('payment') || 'Пардохт' }}</h2>
              <button class="modal-close" @click="showPayment=false">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            <div class="pm-total">{{ money(total) }}</div>

            <!-- Payment method -->
            <div class="pm-methods">
              <button :class="['pm-method', {active: payMethod==='cash'}]" @click="payMethod='cash'">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M1 10h2M21 10h2M1 14h2M21 14h2"/></svg>
                {{ t('cash') || 'Нақд' }}
              </button>
              <button :class="['pm-method', {active: payMethod==='card'}]" @click="payMethod='card'">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
                {{ t('card') || 'Корт' }}
              </button>
              <button :class="['pm-method', {active: payMethod==='mixed'}]" @click="payMethod='mixed'">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
                {{ t('mixed') || 'Омехта' }}
              </button>
            </div>

            <!-- Cash input -->
            <div v-if="payMethod !== 'card'" class="pm-cash-section">
              <label>{{ t('cash_received') || 'Пули гирифташуда' }}</label>
              <input type="number" v-model.number="cashGiven" class="cash-input" step="0.01" min="0"/>
              <div class="quick-cash">
                <button v-for="q in [Math.ceil(total), Math.ceil(total/10)*10, Math.ceil(total/50)*50, Math.ceil(total/100)*100].filter((v,i,a)=>a.indexOf(v)===i && v>=total)" :key="q" @click="quickCash(q)">{{ money(q) }}</button>
              </div>
              <div class="change-display" v-if="change > 0">
                <span>{{ t('change') || 'Баргардонӣ' }}</span>
                <strong>{{ money(change) }}</strong>
              </div>
            </div>

            <button class="pm-confirm" @click="processPayment" :disabled="processing || (payMethod!=='card' && cashGiven < total)">
              {{ processing ? '...' : (t('confirm_payment') || 'Тасдиқ') }}
            </button>
          </div>
        </div>
      </Transition>

      <!-- Receipt modal -->
      <Transition name="modal">
        <div v-if="showReceipt" class="modal-overlay" @click.self="showReceipt=null">
          <div class="receipt-modal">
            <div class="receipt-check">✓</div>
            <h2>{{ t('sale_complete') || 'Фурӯш сабт шуд!' }}</h2>
            <div class="receipt-num">{{ showReceipt.receipt_number }}</div>
            <div class="receipt-items">
              <div v-for="item in showReceipt.cartItems" :key="item.id" class="ri-row">
                <span>{{ item.name }} × {{ item.qty }}</span>
                <span>{{ money(item.price * item.qty) }}</span>
              </div>
            </div>
            <div class="receipt-total">
              <span>{{ t('total') || 'Ҷамъ' }}</span>
              <strong>{{ money(showReceipt.total_amount) }}</strong>
            </div>
            <div class="receipt-pay-info">
              <span>{{ showReceipt.paymentMethod === 'cash' ? (t('cash')||'Нақд') : showReceipt.paymentMethod === 'card' ? (t('card')||'Корт') : (t('mixed')||'Омехта') }}</span>
              <span v-if="showReceipt.changeAmount > 0">{{ t('change') || 'Баргардонӣ' }}: {{ money(showReceipt.changeAmount) }}</span>
            </div>
            <button class="receipt-close" @click="showReceipt=null">{{ t('new_sale') || 'Фурӯши нав' }}</button>
          </div>
        </div>
      </Transition>

      <!-- Close shift modal -->
      <Transition name="modal">
        <div v-if="showCloseModal" class="modal-overlay" @click.self="showCloseModal=false">
          <div class="close-shift-modal">
            <h2>{{ t('close_shift') || 'Пӯшидани смена' }}</h2>
            <div v-if="shiftSummary" class="csm-summary">
              <div class="csm-row"><span>{{ t('sales') || 'Фурӯшҳо' }}</span><strong>{{ money(shiftSummary.sales_total) }}</strong></div>
              <div class="csm-row"><span>{{ t('refunds') || 'Баргардонӣ' }}</span><strong style="color:#ef4444">{{ money(shiftSummary.refunds_total) }}</strong></div>
              <div class="csm-row"><span>{{ t('receipts') || 'Чекҳо' }}</span><strong>{{ shiftSummary.receipt_count }}</strong></div>
              <div class="csm-row"><span>{{ t('cash_total') || 'Нақд' }}</span><strong>{{ money(shiftSummary.cash_total) }}</strong></div>
              <div class="csm-row"><span>{{ t('card_total') || 'Корт' }}</span><strong>{{ money(shiftSummary.card_total) }}</strong></div>
              <div class="csm-row highlight"><span>{{ t('expected') || 'Бояд бошад' }}</span><strong>{{ money(shiftSummary.shift.expected_cash) }}</strong></div>
            </div>
            <!-- X-отчёт -->
<Transition name="modal">
  <div v-if="showXReport" class="modal-overlay" @click.self="showXReport=false">
    <div class="close-shift-modal">
      <h2>X-отчёт · {{ shift?.register_name }}</h2>
      <div class="csm-summary" v-if="xReport">
        <div class="csm-row"><span>Продаж</span><strong>{{ xReport.sales_count }}</strong></div>
        <div class="csm-row"><span>Возвратов</span><strong>{{ xReport.refunds_count }}</strong></div>
        <div class="csm-row"><span>Выручка</span><strong>{{ money(xReport.sales_total) }}</strong></div>
        <div class="csm-row"><span>Нақд</span><strong>{{ money(xReport.cash_total) }}</strong></div>
        <div class="csm-row"><span>Корт</span><strong>{{ money(xReport.card_total) }}</strong></div>
        <div class="csm-row highlight"><span>В кассе</span><strong>{{ money(xReport.net_cash) }}</strong></div>
      </div>
      <div class="csm-actions">
        <button class="btn-close-shift" @click="showXReport=false">Закрыть</button>
      </div>
    </div>
  </div>
</Transition>

<!-- Z-отчёт после закрытия -->
<Transition name="modal">
  <div v-if="zReport" class="modal-overlay" @click.self="zReport=null">
    <div class="close-shift-modal">
      <h2>Z-отчёт · смена #{{ zReport.shift.id }}</h2>
      <div class="csm-summary">
        <div class="csm-row"><span>Продаж</span><strong>{{ zReport.sales_count }}</strong></div>
        <div class="csm-row"><span>Выручка</span><strong>{{ money(zReport.sales_total) }}</strong></div>
        <div class="csm-row"><span>Нақд</span><strong>{{ money(zReport.cash_total) }}</strong></div>
        <div class="csm-row"><span>Корт</span><strong>{{ money(zReport.card_total) }}</strong></div>
        <div class="csm-row"><span>Должно быть</span><strong>{{ money(zReport.shift.expected_cash) }}</strong></div>
        <div class="csm-row"><span>Фактически</span><strong>{{ money(zReport.shift.actual_cash) }}</strong></div>
        <div class="csm-row highlight">
          <span>Расхождение</span>
          <strong :style="{color: Number(zReport.discrepancy) === 0 ? '#16a34a' : '#ef4444'}">
            {{ money(zReport.discrepancy) }}
          </strong>
        </div>
      </div>
      <div class="csm-actions">
        <button class="btn-close-shift" @click="zReport=null">Закрыть</button>
      </div>
    </div>
  </div>
</Transition>
            <label class="oss-field">
              <span>{{ t('actual_cash') || 'Пули воқеӣ дар касса' }}</span>
              <input type="number" v-model.number="closeForm.actual_cash" min="0" step="0.01"/>
            </label>
            <div class="csm-actions">
              <button class="btn-cancel" @click="showCloseModal=false">{{ t('cancel') || 'Бекор' }}</button>
              <button class="btn-close-shift" @click="closeShift">{{ t('close_shift') || 'Пӯшидан' }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" class="toast" :class="toastType">{{ toast }}</div>
    </Transition>
  </div>
</template>

<style scoped>
.pos{height:calc(100vh - 50px);overflow:hidden;display:flex;flex-direction:column}

/* Loading */
.pos-loading{display:flex;align-items:center;justify-content:center;height:100%}
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* Open shift screen */
.open-shift-screen{display:flex;align-items:center;justify-content:center;height:100%;padding:20px}
.oss-card{text-align:center;max-width:380px;width:100%;background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:32px 24px}
.oss-icon{margin:0 auto 16px}
.oss-icon svg{width:56px;height:56px;color:var(--accent)}
.oss-card h1{font-size:20px;font-weight:800;margin-bottom:6px}
.oss-card p{font-size:13px;color:var(--muted);margin-bottom:20px}
.oss-field{display:flex;flex-direction:column;gap:4px;text-align:left;margin-bottom:12px}
.oss-field span{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase}
.oss-field input{padding:10px 12px;border:1px solid var(--border);border-radius:10px;font-size:14px;background:var(--bg);color:var(--text);outline:none}
.oss-field input:focus{border-color:var(--accent)}
.oss-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:14px;background:var(--accent);color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px;transition:background .2s}
.oss-btn:hover{background:var(--accent-hover)}
.oss-btn svg{width:22px;height:22px}

/* Main POS layout */
.pos-layout{display:flex;flex:1;overflow:hidden}

/* Left: Catalog */
.pos-catalog{flex:1;display:flex;flex-direction:column;overflow:hidden;border-right:1px solid var(--border)}
.pos-search{position:relative;padding:10px 12px}
.pos-search input{width:100%;padding:10px 10px 10px 38px;border:1px solid var(--border);border-radius:10px;font-size:14px;background:var(--bg);color:var(--text);outline:none}
.pos-search input:focus{border-color:var(--accent)}
.search-icon{position:absolute;left:22px;top:50%;transform:translateY(-50%);width:18px;height:18px;color:var(--muted);pointer-events:none}

.cat-pills{display:flex;gap:6px;padding:0 12px 8px;overflow-x:auto;flex-shrink:0}
.cat-pills::-webkit-scrollbar{display:none}
.pill{padding:6px 14px;border:1px solid var(--border);border-radius:20px;background:var(--bg);color:var(--text);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap;transition:all .15s}
.pill.active{background:var(--accent);color:#fff;border-color:var(--accent)}

.product-grid{flex:1;overflow-y:auto;padding:8px 12px 80px;display:grid;grid-template-columns:repeat(auto-fill, minmax(120px, 1fr));gap:8px;align-content:start}
.prod-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:8px;cursor:pointer;transition:all .15s;text-align:center;display:flex;flex-direction:column;align-items:center;gap:4px}
.prod-card:hover{border-color:var(--accent);box-shadow:0 2px 8px rgba(37,99,235,.1);transform:translateY(-1px)}
.prod-card:active{transform:scale(.97)}
.prod-img{width:100%;aspect-ratio:1;border-radius:8px;overflow:hidden;background:var(--bg);display:flex;align-items:center;justify-content:center}
.prod-img img{max-width:90%;max-height:90%;width:auto;height:auto;object-fit:contain}
.prod-placeholder svg{width:32px;height:32px;opacity:.3}
.prod-name{font-size:12px;font-weight:600;line-height:1.3;max-height:2.6em;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.prod-price{font-size:13px;font-weight:800;color:var(--accent)}
.prod-stock{font-size:10px;font-weight:600}
.no-products{grid-column:1/-1;text-align:center;padding:40px;color:var(--muted);font-size:14px}

/* Right: Cart */
.pos-cart{width:340px;display:flex;flex-direction:column;background:var(--surface);flex-shrink:0}

.shift-bar{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-bottom:1px solid var(--border)}
.shift-info{display:flex;align-items:center;gap:8px;font-weight:700;font-size:13px}
.shift-dot{width:8px;height:8px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.shift-close-btn{padding:6px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--muted);font-size:11px;font-weight:600;cursor:pointer}
.shift-close-btn:hover{border-color:#ef4444;color:#ef4444}
.shift-actions{display:flex;gap:4px}
.shift-x-btn{padding:6px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--muted);font-size:11px;font-weight:700;cursor:pointer}
.shift-x-btn:hover{border-color:var(--accent);color:var(--accent)}

.cart-items{flex:1;overflow-y:auto;padding:8px}
.cart-empty{display:flex;align-items:center;justify-content:center;height:100%}
.empty-cart{text-align:center;color:var(--muted);opacity:.5}
.empty-cart svg{width:48px;height:48px;display:block;margin:0 auto 8px}
.empty-cart span{font-size:13px}

.cart-row{display:flex;align-items:center;gap:8px;padding:8px 10px;background:var(--bg);border-radius:10px;margin-bottom:6px}
.cr-info{flex:1;min-width:0}
.cr-name{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cr-unit-price{font-size:11px;color:var(--muted)}
.cr-controls{display:flex;align-items:center;gap:4px}
.qty-btn{width:26px;height:26px;border:1px solid var(--border);border-radius:6px;background:var(--surface);cursor:pointer;font-size:14px;font-weight:700;display:flex;align-items:center;justify-content:center;color:var(--text);transition:all .15s}
.qty-btn:hover{border-color:var(--accent);color:var(--accent)}
.qty-val{font-weight:700;font-size:13px;min-width:20px;text-align:center}
.cr-total{font-weight:700;font-size:13px;color:var(--accent);min-width:60px;text-align:right}
.cr-del{background:none;border:none;cursor:pointer;color:var(--muted);padding:2px;display:flex}
.cr-del:hover{color:#ef4444}
.cr-del svg{width:16px;height:16px}

.cart-item-enter-active{animation:slide-in .2s ease}
.cart-item-leave-active{animation:slide-in .15s ease reverse}
@keyframes slide-in{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}

.cart-footer{padding:8px 14px;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.clear-btn{padding:4px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--muted);font-size:11px;cursor:pointer}
.clear-btn:hover{border-color:#ef4444;color:#ef4444}
.cart-total-row{text-align:right}
.cart-total-row span{font-size:12px;color:var(--muted);display:block}
.cart-total-row strong{font-size:20px;color:var(--text)}

.pay-btn{display:flex;align-items:center;justify-content:center;gap:8px;margin:8px 14px 14px;padding:14px;background:#16a34a;color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:800;cursor:pointer;transition:all .2s}
.pay-btn:hover:not(:disabled){background:#15803d;transform:translateY(-1px)}
.pay-btn:disabled{opacity:.3;cursor:not-allowed}
.pay-btn svg{width:22px;height:22px}

.recent-sales{padding:8px 14px 14px;border-top:1px solid var(--border)}
.rs-title{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;margin-bottom:6px}
.rs-list{display:flex;flex-direction:column;gap:3px}
.rs-item{display:flex;align-items:center;gap:6px;font-size:11px;padding:3px 0}
.rs-num{color:var(--muted);font-family:monospace}
.rs-amount{font-weight:700;flex:1;text-align:right}
.rs-time{color:var(--muted)}

/* Payment modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:10000;padding:16px}
.pay-modal{background:var(--surface);border-radius:20px;width:100%;max-width:400px;padding:24px;box-shadow:0 16px 48px rgba(0,0,0,.25)}
.pm-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.pm-header h2{margin:0;font-size:18px;font-weight:800}
.modal-close{background:none;border:none;cursor:pointer;color:var(--muted);display:flex}
.modal-close svg{width:22px;height:22px}
.pm-total{text-align:center;font-size:36px;font-weight:900;color:var(--accent);margin-bottom:20px}
.pm-methods{display:flex;gap:8px;margin-bottom:20px}
.pm-method{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 8px;border:2px solid var(--border);border-radius:12px;background:var(--bg);cursor:pointer;font-size:12px;font-weight:700;color:var(--text);transition:all .15s}
.pm-method svg{width:28px;height:28px}
.pm-method.active{border-color:var(--accent);background:var(--accent-bg);color:var(--accent)}
.pm-cash-section{margin-bottom:20px}
.pm-cash-section label{display:block;font-size:12px;font-weight:700;color:var(--muted);margin-bottom:6px;text-transform:uppercase}
.cash-input{width:100%;padding:12px;border:2px solid var(--border);border-radius:10px;font-size:20px;font-weight:700;text-align:center;background:var(--bg);color:var(--text);outline:none}
.cash-input:focus{border-color:var(--accent)}
.quick-cash{display:flex;gap:6px;margin-top:8px}
.quick-cash button{flex:1;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--bg);font-size:12px;font-weight:700;cursor:pointer;color:var(--text);transition:all .15s}
.quick-cash button:hover{border-color:var(--accent);background:var(--accent-bg)}
.change-display{margin-top:12px;display:flex;justify-content:space-between;padding:12px;background:rgba(22,163,74,.08);border-radius:10px}
.change-display span{color:var(--muted);font-weight:600}
.change-display strong{color:#16a34a;font-size:20px;font-weight:900}
.pm-confirm{width:100%;padding:14px;background:#16a34a;color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:800;cursor:pointer}
.pm-confirm:hover:not(:disabled){background:#15803d}
.pm-confirm:disabled{opacity:.4;cursor:not-allowed}

/* Receipt modal */
.receipt-modal{background:var(--surface);border-radius:20px;width:100%;max-width:340px;padding:24px;text-align:center}
.receipt-check{width:56px;height:56px;background:#dcfce7;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:28px;color:#16a34a}
.receipt-modal h2{font-size:18px;font-weight:800;margin-bottom:4px}
.receipt-num{font-size:12px;color:var(--muted);font-family:monospace;margin-bottom:16px}
.receipt-items{text-align:left;border-top:1px dashed var(--border);border-bottom:1px dashed var(--border);padding:10px 0;margin-bottom:10px}
.ri-row{display:flex;justify-content:space-between;padding:3px 0;font-size:13px}
.receipt-total{display:flex;justify-content:space-between;padding:8px 0;font-size:16px}
.receipt-total strong{color:var(--accent)}
.receipt-pay-info{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);padding-bottom:16px}
.receipt-close{width:100%;padding:12px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer}

/* Close shift modal */
.close-shift-modal{background:var(--surface);border-radius:20px;width:100%;max-width:400px;padding:24px}
.close-shift-modal h2{font-size:18px;font-weight:800;margin-bottom:16px}
.csm-summary{display:flex;flex-direction:column;gap:4px;margin-bottom:16px;padding:12px;background:var(--bg);border-radius:12px}
.csm-row{display:flex;justify-content:space-between;font-size:13px;padding:3px 0}
.csm-row.highlight{border-top:1px solid var(--border);padding-top:8px;margin-top:4px;font-size:14px}
.csm-row.highlight strong{color:var(--accent)}
.csm-actions{display:flex;gap:8px;margin-top:16px}
.btn-cancel{flex:1;padding:12px;border:1px solid var(--border);border-radius:10px;background:var(--bg);color:var(--text);font-size:14px;font-weight:600;cursor:pointer}
.btn-close-shift{flex:1;padding:12px;border:none;border-radius:10px;background:#ef4444;color:#fff;font-size:14px;font-weight:700;cursor:pointer}

.modal-enter-active{animation:modal-in .25s ease}
.modal-leave-active{animation:modal-in .2s ease reverse}
@keyframes modal-in{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}

/* Toast */
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);padding:10px 20px;border-radius:10px;font-size:13px;font-weight:600;z-index:11000;box-shadow:0 4px 16px rgba(0,0,0,.15)}
.toast.ok{background:#059669;color:#fff}
.toast.err{background:#ef4444;color:#fff}
.toast-enter-active{animation:toast-in .3s ease}
.toast-leave-active{animation:toast-in .2s ease reverse}
@keyframes toast-in{from{opacity:0;transform:translateX(-50%) translateY(10px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}

/* Mobile */
@media(max-width:700px){
  .pos-layout{flex-direction:column}
  .pos-catalog{border-right:none;max-height:50vh}
  .pos-cart{width:100%}
  .product-grid{grid-template-columns:repeat(auto-fill, minmax(100px, 1fr))}
}
</style>
