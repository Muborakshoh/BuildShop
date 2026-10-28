<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'

const { t } = useI18n()
const reviews = ref([])
const loading = ref(true)
const toast = ref('')
const toastType = ref('ok')
const filterStatus = ref('pending')

const filtered = computed(() => {
  if (filterStatus.value === 'all') return reviews.value
  return reviews.value.filter(r => r.status === filterStatus.value)
})

const counts = computed(() => ({
  pending: reviews.value.filter(r => r.status === 'pending').length,
  approved: reviews.value.filter(r => r.status === 'approved').length,
  rejected: reviews.value.filter(r => r.status === 'rejected').length,
}))

onMounted(loadReviews)

async function loadReviews() {
  loading.value = true
  try {
    // /reviews/admin/pending возвращает только pending, но для полного списка можно расширить бэкенд
    // Сейчас endpoint только /admin/pending — показываем pending
    reviews.value = await api.get('/reviews/admin/pending')
  } catch (e) {
    showToast(e.message || 'Ошибка загрузки', 'err')
  }
  loading.value = false
}

function showToast(msg, type = 'ok') {
  toast.value = msg; toastType.value = type
  setTimeout(() => { toast.value = '' }, 3000)
}

async function moderate(review, status) {
  try {
    const updated = await api.patch(`/reviews/admin/${review.id}/moderate`, { status })
    const i = reviews.value.findIndex(r => r.id === review.id)
    if (i >= 0) reviews.value[i] = updated
    showToast(status === 'approved' ? 'Отзыв одобрен' : 'Отзыв отклонён')
    // Убираем из списка pending
    if (status !== 'pending') {
      reviews.value = reviews.value.filter(r => r.id !== review.id)
    }
  } catch (e) {
    showToast(e.message || 'Ошибка', 'err')
  }
}

function stars(n) {
  return Array.from({ length: 5 }, (_, i) => i < n)
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function statusLabel(s) {
  if (s === 'pending') return 'на модерации'
  if (s === 'approved') return 'одобрен'
  if (s === 'rejected') return 'отклонён'
  return s
}
function statusClass(s) {
  if (s === 'pending') return 'status-pending'
  if (s === 'approved') return 'status-approved'
  if (s === 'rejected') return 'status-rejected'
  return ''
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('admin_reviews') || 'Отзывы' }}</h1>
        <p class="sub">{{ counts.pending }} на модерации</p>
      </div>
      <button class="btn-refresh" @click="loadReviews" :disabled="loading">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"/>
          <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
        </svg>
        <span>Обновить</span>
      </button>
    </div>

    <div v-if="loading" class="loading">Загрузка…</div>

    <div v-else-if="!filtered.length" class="empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
        <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7A8.38 8.38 0 014 11.5a8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
      </svg>
      <p>Нет отзывов на модерации</p>
    </div>

    <div v-else class="review-list">
      <div v-for="r in filtered" :key="r.id" class="review-card">
        <div class="review-top">
          <div class="review-meta">
            <div class="review-avatar">{{ (r.user?.full_name || '?')[0].toUpperCase() }}</div>
            <div class="review-info">
              <span class="review-author">{{ r.user?.full_name || 'Аноним' }}</span>
              <span class="review-date">{{ formatDate(r.created_at) }}</span>
            </div>
          </div>
          <span class="review-status" :class="statusClass(r.status)">{{ statusLabel(r.status) }}</span>
        </div>

        <div class="review-product">
          <span class="label">Товар #{{ r.product_id }}</span>
          <span class="stars">
            <span v-for="(f, i) in stars(r.rating)" :key="i" class="star" :class="{filled: f}">★</span>
          </span>
        </div>

        <p class="review-text" v-if="r.text">{{ r.text }}</p>

        <div class="review-actions">
          <button class="btn-approve" @click="moderate(r, 'approved')">✓ Одобрить</button>
          <button class="btn-reject" @click="moderate(r, 'rejected')">✕ Отклонить</button>
        </div>
      </div>
    </div>

    <Transition name="toast">
      <div v-if="toast" class="toast" :class="toastType">{{ toast }}</div>
    </Transition>
  </div>
</template>

<style scoped>
.page{max-width:900px;margin:0 auto;padding:16px 16px 100px}
.page-header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;gap:12px}
h1{font-size:20px;font-weight:800;margin:0}
.sub{font-size:12px;color:var(--muted);margin:2px 0 0}
.btn-refresh{display:flex;align-items:center;gap:6px;padding:9px 16px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:10px;font-size:13px;font-weight:700;cursor:pointer;white-space:nowrap}
.btn-refresh svg{width:16px;height:16px}
.btn-refresh:disabled{opacity:.5}
.loading{text-align:center;padding:40px;color:var(--muted)}
.empty{text-align:center;padding:60px 20px;color:var(--muted)}
.empty p{margin:12px 0 0;font-size:14px}

.review-list{display:flex;flex-direction:column;gap:10px}
.review-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px}
.review-top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}
.review-meta{display:flex;align-items:center;gap:10px}
.review-avatar{width:34px;height:34px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800}
.review-info{display:flex;flex-direction:column;gap:1px}
.review-author{font-size:14px;font-weight:700}
.review-date{font-size:11px;color:var(--muted)}
.review-status{font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:.3px}
.status-pending{background:#fef3c7;color:#92400e}
.status-approved{background:#d1fae5;color:#065f46}
.status-rejected{background:#fee2e2;color:#991b1b}

.review-product{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.review-product .label{font-size:12px;color:var(--muted);font-weight:600}
.stars{font-size:14px;letter-spacing:1px}
.star{color:#e5e7eb}
.star.filled{color:#f59e0b}

.review-text{font-size:14px;line-height:1.55;color:var(--text);margin:0 0 12px;white-space:pre-wrap}
.review-actions{display:flex;gap:8px}
.btn-approve,.btn-reject{padding:8px 16px;border:none;border-radius:10px;font-size:13px;font-weight:700;cursor:pointer}
.btn-approve{background:#059669;color:#fff}
.btn-reject{background:#ef4444;color:#fff}

.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);padding:10px 20px;border-radius:10px;font-size:13px;font-weight:600;z-index:11000;box-shadow:0 4px 16px rgba(0,0,0,.15)}
.toast.ok{background:#059669;color:#fff}
.toast.err{background:#ef4444;color:#fff}
.toast-enter-active{animation:toast-in .22s ease}
.toast-leave-active{animation:toast-in .18s ease reverse}
@keyframes toast-in{from{opacity:0;transform:translateX(-50%) translateY(10px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
</style>
