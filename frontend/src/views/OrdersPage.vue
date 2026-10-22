<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/utils/api'
import { money } from '@/utils/helpers'

const { t } = useI18n()
const auth = useAuthStore()

const orders = ref([])
const loading = ref(true)
const expanded = reactive(new Set())
const toast = ref('')
const toastType = ref('ok')

const statusFlow = ['created','confirmed','assembling','delivering','delivered','completed','cancelled']
const statusColors = {
  created: { bg: '#dbeafe', color: '#1d4ed8', bar: '#3b82f6' },
  confirmed: { bg: '#dcfce7', color: '#15803d', bar: '#22c55e' },
  assembling: { bg: '#fef9c3', color: '#a16207', bar: '#eab308' },
  delivering: { bg: '#f3e8ff', color: '#7c3aed', bar: '#a855f7' },
  delivered: { bg: '#e0e7ff', color: '#4338ca', bar: '#6366f1' },
  completed: { bg: '#dcfce7', color: '#15803d', bar: '#22c55e' },
  cancelled: { bg: '#fee2e2', color: '#dc2626', bar: '#ef4444' },
}
const statusProgress = { created:15, confirmed:30, assembling:50, delivering:70, delivered:85, completed:100, cancelled:100 }

const statusLabels = {
  created: 'order_status_created',
  confirmed: 'order_status_confirmed',
  assembling: 'order_status_assembling',
  delivering: 'order_status_delivering',
  delivered: 'order_status_delivered',
  completed: 'order_status_completed',
  cancelled: 'order_status_cancelled',
}

function statusLabel(s) {
  const key = statusLabels[s?.toLowerCase()] || ''
  const translated = key ? t(key) : ''
  return translated || s || ''
}

// Valid transitions (mirrors backend)
const validTransitions = {
  created: ['confirmed','cancelled'],
  confirmed: ['assembling','cancelled'],
  assembling: ['delivering','cancelled'],
  delivering: ['delivered','cancelled'],
  delivered: ['completed'],
  completed: [],
  cancelled: [],
}

function getStatusColor(s) { return statusColors[s?.toLowerCase()] || statusColors.created }
function getProgress(s) { return (statusProgress[s?.toLowerCase()] || 0) + '%' }

function canCancel(status) {
  const s = status?.toLowerCase()
  return ['created','confirmed','assembling','delivering'].includes(s)
}

function getAllowedTransitions(status) {
  const s = status?.toLowerCase()
  return validTransitions[s] || []
}

function showToast(msg, type='ok') {
  toast.value = msg; toastType.value = type
  setTimeout(() => toast.value = '', 3000)
}

function toggle(id) {
  if (expanded.has(id)) { expanded.delete(id) }
  else { expanded.add(id); loadHistory(id) }
}

async function loadHistory(orderId) {
  try {
    const history = await api.get(`/orders/${orderId}/history`)
    const order = orders.value.find(o => o.id === orderId)
    if (order) order.history = Array.isArray(history) ? history : []
  } catch (e) { console.error(e) }
}

async function changeStatus(orderId, newStatus, comment) {
  try {
    const updated = await api.patch(`/orders/${orderId}/status`, { status: newStatus, comment: comment || null })
    const order = orders.value.find(o => o.id === orderId)
    if (order) {
      order.status = updated.status
      loadHistory(orderId)
    }
    showToast(t('status_updated') || 'Статус иваз шуд')
  } catch (e) {
    showToast(e.message || 'Хатогӣ', 'err')
  }
}

async function cancelOrder(orderId) {
  await changeStatus(orderId, 'cancelled', 'Cancelled by user')
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('ru-RU', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })
}

onMounted(async () => {
  try {
    const data = await api.get('/orders')
    orders.value = Array.isArray(data) ? data : data.items || []
  } catch (e) { console.error(e) }
  loading.value = false
})
</script>

<template>
  <div class="page">
    <h1>{{ t('orders') }}</h1>

    <div v-if="loading" class="loading">{{ t('loading') }}</div>

    <div v-else-if="!orders.length" class="empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
      <p>{{ t('orders_empty') || 'Фармоишҳо нест' }}</p>
      <router-link to="/products" class="btn-shop">{{ t('go_shopping') || 'Ба харидорӣ' }}</router-link>
    </div>

    <div v-else class="orders-list">
      <div v-for="order in orders" :key="order.id" class="order-card">
        <!-- Header -->
        <div class="order-header" @click="toggle(order.id)">
          <div class="oh-left">
            <span class="order-id">#{{ order.id }}</span>
            <span class="status-badge" :style="{background: getStatusColor(order.status).bg, color: getStatusColor(order.status).color}">
              {{ statusLabel(order.status) }}
            </span>
          </div>
          <div class="oh-right">
            <span class="order-total">{{ money(order.total_amount) }}</span>
            <span class="order-date">{{ formatDate(order.created_at) }}</span>
            <svg :class="['chevron', {open: expanded.has(order.id)}]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>

        <!-- Progress -->
        <div class="progress-bar">
          <div class="progress-fill" :style="{width: getProgress(order.status), background: getStatusColor(order.status).bar}"></div>
        </div>

        <!-- Expanded body -->
        <Transition name="slide-body">
          <div v-if="expanded.has(order.id)" class="order-body">
            <!-- Items -->
            <div class="order-items">
              <div v-for="item in order.items" :key="item.id" class="oi-row">
                <span class="oi-name">{{ item.product_name || (item.product_id ? 'Product #' + item.product_id : 'Маҳсулоти нест шуда') }}</span>
                <span class="oi-qty">×{{ item.quantity }}</span>
                <span class="oi-price">{{ money(item.unit_price * item.quantity) }}</span>
              </div>
            </div>

            <!-- Delivery info -->
            <div class="order-info" v-if="order.delivery_address || order.phone">
              <div v-if="order.delivery_method" class="info-row">
                <span>{{ t('delivery') || 'Расонидан' }}</span>
                <strong>{{ order.delivery_method === 'delivery' ? (t('delivery') || 'Расонидан') : (t('pickup') || 'Самовывоз') }}</strong>
              </div>
              <div v-if="order.delivery_address" class="info-row">
                <span>{{ t('address') || 'Суроға' }}</span>
                <strong>{{ order.delivery_address }}</strong>
              </div>
              <div v-if="order.phone" class="info-row">
                <span>{{ t('phone') || 'Телефон' }}</span>
                <strong>{{ order.phone }}</strong>
              </div>
              <div v-if="order.comment" class="info-row">
                <span>{{ t('comment') || 'Шарҳ' }}</span>
                <strong>{{ order.comment }}</strong>
              </div>
            </div>

            <!-- Admin: change status -->
            <div v-if="auth.isAdmin && getAllowedTransitions(order.status).length" class="admin-status">
              <span class="admin-label">{{ t('change_status') || 'Иваз кардани статус' }}:</span>
              <div class="status-btns">
                <button v-for="s in getAllowedTransitions(order.status)" :key="s"
                  class="status-btn"
                  :style="{background: getStatusColor(s).bg, color: getStatusColor(s).color, borderColor: getStatusColor(s).color + '40'}"
                  @click.stop="changeStatus(order.id, s)">
                  {{ s }}
                </button>
              </div>
            </div>

            <!-- Regular user: cancel button -->
            <button v-else-if="!auth.isAdmin && canCancel(order.status)" class="btn-cancel" @click.stop="cancelOrder(order.id)">
              {{ t('cancel_order') || 'Бекор кардан' }}
            </button>

            <!-- History -->
            <div v-if="order.history && order.history.length" class="order-history">
              <h4>{{ t('order_history') || 'Таърих' }}</h4>
              <div v-for="h in order.history" :key="h.id" class="hist-row">
                <span class="hist-badge" :style="{background: getStatusColor(h.new_status).bg, color: getStatusColor(h.new_status).color}">
                  {{ statusLabel(h.new_status) }}
                </span>
                <span class="hist-date">{{ formatDate(h.changed_at) }}</span>
                <span v-if="h.comment" class="hist-comment">{{ h.comment }}</span>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" class="toast" :class="toastType">{{ toast }}</div>
    </Transition>
  </div>
</template>

<style scoped>
.page{max-width:800px;margin:0 auto;padding:16px 16px 100px}
h1{font-size:20px;font-weight:800;margin-bottom:16px}

.loading{text-align:center;padding:40px;color:var(--muted)}
.empty{text-align:center;padding:60px 16px;color:var(--muted)}
.empty-icon{width:48px;height:48px;margin:0 auto 12px;display:block;opacity:.4}
.empty p{margin-bottom:12px}
.btn-shop{display:inline-block;padding:8px 20px;background:var(--accent);color:#fff;border-radius:10px;text-decoration:none;font-size:14px;font-weight:600}

.orders-list{display:flex;flex-direction:column;gap:10px}

.order-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:border-color .2s}
.order-card:hover{border-color:var(--accent)}

.order-header{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;cursor:pointer;transition:background .15s;gap:8px}
.order-header:hover{background:var(--bg)}
.oh-left{display:flex;align-items:center;gap:8px}
.oh-right{display:flex;align-items:center;gap:10px}
.order-id{font-weight:800;font-size:14px;color:var(--text)}
.status-badge{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;white-space:nowrap;text-transform:capitalize}
.order-total{font-weight:700;font-size:14px;color:var(--accent)}
.order-date{font-size:11px;color:var(--muted);white-space:nowrap}
.chevron{width:18px;height:18px;color:var(--muted);transition:transform .2s;flex-shrink:0}
.chevron.open{transform:rotate(180deg)}

.progress-bar{height:3px;background:var(--border)}
.progress-fill{height:100%;transition:width .4s ease;border-radius:3px}

.order-body{padding:14px 16px;border-top:1px solid var(--border)}

.order-items{margin-bottom:12px}
.oi-row{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.oi-row:last-child{border:none}
.oi-name{flex:1;font-weight:500;color:var(--text)}
.oi-qty{color:var(--muted);font-size:12px}
.oi-price{font-weight:700;color:var(--text)}

.order-info{background:var(--bg);border-radius:10px;padding:10px 12px;margin-bottom:12px}
.info-row{display:flex;justify-content:space-between;padding:3px 0;font-size:12px}
.info-row span{color:var(--muted)}
.info-row strong{color:var(--text);font-weight:600}

/* Admin status change */
.admin-status{margin-bottom:12px;padding:10px 12px;background:var(--bg);border-radius:10px}
.admin-label{font-size:12px;font-weight:700;color:var(--muted);display:block;margin-bottom:8px}
.status-btns{display:flex;flex-wrap:wrap;gap:6px}
.status-btn{padding:6px 14px;border:1px solid;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;transition:all .15s;text-transform:capitalize}
.status-btn:hover{opacity:.85;transform:scale(1.03)}

.btn-cancel{padding:8px 18px;background:#fee2e2;color:#dc2626;border:1px solid #fca5a5;border-radius:10px;cursor:pointer;font-size:13px;font-weight:600;margin-bottom:12px}
.btn-cancel:hover{background:#fecaca}

.order-history{padding-top:12px;border-top:1px solid var(--border)}
.order-history h4{font-size:13px;font-weight:700;margin-bottom:8px}
.hist-row{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12px}
.hist-badge{padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700;text-transform:capitalize}
.hist-date{color:var(--muted)}
.hist-comment{color:var(--text);font-style:italic}

.slide-body-enter-active,.slide-body-leave-active{transition:all .25s ease;overflow:hidden}
.slide-body-enter-from,.slide-body-leave-to{max-height:0;opacity:0;padding-top:0;padding-bottom:0}
.slide-body-enter-to,.slide-body-leave-from{max-height:1000px;opacity:1}

/* Toast */
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);padding:10px 20px;border-radius:10px;font-size:13px;font-weight:600;z-index:11000;box-shadow:0 4px 16px rgba(0,0,0,.15)}
.toast.ok{background:#059669;color:#fff}
.toast.err{background:#ef4444;color:#fff}
.toast-enter-active{animation:toast-in .3s ease}
.toast-leave-active{animation:toast-in .2s ease reverse}
@keyframes toast-in{from{opacity:0;transform:translateX(-50%) translateY(10px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}

@media(max-width:500px){
  .oh-right{flex-direction:column;align-items:flex-end;gap:2px}
  .order-date{font-size:10px}
}
</style>
