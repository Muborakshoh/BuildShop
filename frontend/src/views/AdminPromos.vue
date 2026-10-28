<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'
import { money } from '@/utils/helpers'

const { t } = useI18n()
const promos = ref([])
const loading = ref(true)
const saving = ref(false)
const search = ref('')
const toast = ref('')
const toastType = ref('ok')
const showForm = ref(false)
const editingId = ref(null)
const confirmDelete = ref(null)

const emptyForm = () => ({
  code: '', user_id: null,
  discount_percent: 10, discount_amount: null,
  min_order_amount: 0, max_discount: null,
  usage_limit: null, is_active: true,
  valid_from: '', valid_to: '',
})
const form = ref(emptyForm())

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return promos.value
  return promos.value.filter(p => (p.code || '').toLowerCase().includes(q))
})
const activeCount = computed(() => promos.value.filter(p => p.is_active).length)

onMounted(loadPromos)

async function loadPromos() {
  loading.value = true
  try { promos.value = await api.get('/promos/') }
  catch (e) { showToast(e.message, 'err') }
  loading.value = false
}

function showToast(msg, type = 'ok') {
  toast.value = msg; toastType.value = type
  setTimeout(() => { toast.value = '' }, 3000)
}

function openAdd() {
  form.value = emptyForm()
  editingId.value = null
  showForm.value = true
}

function openEdit(p) {
  form.value = {
    code: p.code,
    user_id: p.user_id ?? null,
    discount_percent: p.discount_percent != null ? Number(p.discount_percent) : null,
    discount_amount: p.discount_amount != null ? Number(p.discount_amount) : null,
    min_order_amount: Number(p.min_order_amount || 0),
    max_discount: p.max_discount != null ? Number(p.max_discount) : null,
    usage_limit: p.usage_limit ?? null,
    is_active: p.is_active,
    valid_from: p.valid_from ? String(p.valid_from).slice(0, 16) : '',
    valid_to: p.valid_to ? String(p.valid_to).slice(0, 16) : '',
  }
  editingId.value = p.id
  showForm.value = true
}

function buildPayload() {
  const pct = form.value.discount_percent
  const payload = {
    user_id: form.value.user_id || null,
    discount_percent: pct ? Number(pct) : null,
    discount_amount: !pct && form.value.discount_amount ? Number(form.value.discount_amount) : null,
    min_order_amount: Number(form.value.min_order_amount) || 0,
    max_discount: form.value.max_discount ? Number(form.value.max_discount) : null,
    usage_limit: form.value.usage_limit ? Number(form.value.usage_limit) : null,
    is_active: !!form.value.is_active,
    valid_from: form.value.valid_from ? new Date(form.value.valid_from).toISOString() : null,
    valid_to: form.value.valid_to ? new Date(form.value.valid_to).toISOString() : null,
  }
  return payload
}

async function save() {
  if (!form.value.code.trim()) { showToast('Введите код', 'err'); return }
  if (!form.value.discount_percent && !form.value.discount_amount) {
    showToast('Укажите скидку: % или сумму', 'err'); return
  }
  saving.value = true
  try {
    const payload = buildPayload()
    if (editingId.value) {
      const updated = await api.patch('/promos/' + editingId.value, payload)
      const i = promos.value.findIndex(p => p.id === editingId.value)
      if (i >= 0) promos.value[i] = updated
      showToast('Промокод обновлён')
    } else {
      const created = await api.post('/promos/', { ...payload, code: form.value.code.trim().toUpperCase() })
      promos.value.unshift(created)
      showToast('Промокод создан')
    }
    showForm.value = false
  } catch (e) { showToast(e.message, 'err') }
  saving.value = false
}

async function toggleActive(p) {
  try {
    const updated = await api.patch('/promos/' + p.id, { is_active: !p.is_active })
    Object.assign(p, updated)
  } catch (e) { showToast(e.message, 'err') }
}

async function remove(p) {
  if (confirmDelete.value !== p.id) { confirmDelete.value = p.id; return }
  try {
    await api.delete('/promos/' + p.id)
    promos.value = promos.value.filter(x => x.id !== p.id)
    showToast('Промокод удалён')
  } catch (e) { showToast(e.message, 'err') }
  confirmDelete.value = null
}

function usageLabel(p) {
  if (!p.usage_limit) return `${p.usage_count} / ∞`
  return `${p.usage_count} / ${p.usage_limit}`
}
function usagePercent(p) {
  if (!p.usage_limit) return 0
  return Math.min(100, Math.round((p.usage_count / p.usage_limit) * 100))
}
function discountLabel(p) {
  if (p.discount_percent) return `−${Number(p.discount_percent)}%`
  if (p.discount_amount) return `−${money(p.discount_amount)}`
  return '—'
}
function periodLabel(p) {
  const f = p.valid_from ? new Date(p.valid_from).toLocaleDateString('ru-RU') : null
  const to = p.valid_to ? new Date(p.valid_to).toLocaleDateString('ru-RU') : null
  if (!f && !to) return 'бессрочно'
  return `${f || '…'} — ${to || '…'}`
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('admin_promos') || 'Промокоды' }}</h1>
        <p class="sub">{{ activeCount }} активных из {{ promos.length }}</p>
      </div>
      <button class="btn-add" @click="openAdd">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>Создать</span>
      </button>
    </div>

    <input v-model="search" class="search" placeholder="Поиск по коду…"/>

    <div v-if="loading" class="loading">Загрузка…</div>

    <div v-else class="promo-list">
      <div v-for="p in filtered" :key="p.id" class="promo-card" :class="{ inactive: !p.is_active }">
        <div class="pc-code">
          <span class="code-text">{{ p.code }}</span>
          <span v-if="p.user_id" class="badge personal">персональный #{{ p.user_id }}</span>
        </div>

        <div class="pc-discount">{{ discountLabel(p) }}</div>

        <div class="pc-meta">
          <span class="meta-item">от {{ money(p.min_order_amount) }}</span>
          <span v-if="p.max_discount" class="meta-item">макс. {{ money(p.max_discount) }}</span>
          <span class="meta-item">{{ periodLabel(p) }}</span>
        </div>

        <div class="pc-usage">
          <div class="usage-bar"><div class="usage-fill" :style="{ width: usagePercent(p) + '%' }"></div></div>
          <span class="usage-text">{{ usageLabel(p) }}</span>
        </div>

        <div class="pc-actions">
          <button class="act-btn" @click="toggleActive(p)" :title="p.is_active ? 'Отключить' : 'Включить'">
            <svg v-if="p.is_active" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
            </svg>
          </button>
          <button class="act-btn" @click="openEdit(p)" title="Редактировать">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="act-btn act-del" @click="remove(p)">
            <svg v-if="confirmDelete !== p.id" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
            </svg>
            <span v-else class="del-confirm">?</span>
          </button>
        </div>
      </div>

      <div v-if="!filtered.length" class="empty">Промокодов нет</div>
    </div>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showForm" class="modal-overlay" @click.self="showForm=false">
          <div class="modal-card">
            <div class="modal-header">
              <h2>{{ editingId ? 'Редактировать промокод' : 'Новый промокод' }}</h2>
              <button class="modal-close" @click="showForm=false">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div class="modal-body">
              <label class="field">
                <span>Код</span>
                <input v-model="form.code" :disabled="!!editingId" placeholder="SALE10" class="mono"/>
              </label>

              <label class="field">
                <span>ID пользователя (пусто = для всех)</span>
                <input type="number" v-model.number="form.user_id" min="1" placeholder="—"/>
              </label>

              <div class="row2">
                <label class="field">
                  <span>Скидка, %</span>
                  <input type="number" v-model.number="form.discount_percent" min="0" max="100" step="0.5"/>
                </label>
                <label class="field">
                  <span>или сумма, TJS</span>
                  <input type="number" v-model.number="form.discount_amount" min="0" step="0.01" placeholder="—"/>
                </label>
              </div>

              <div class="row2">
                <label class="field">
                  <span>Мин. сумма заказа</span>
                  <input type="number" v-model.number="form.min_order_amount" min="0" step="0.01"/>
                </label>
                <label class="field">
                  <span>Макс. скидка</span>
                  <input type="number" v-model.number="form.max_discount" min="0" step="0.01" placeholder="—"/>
                </label>
              </div>

              <label class="field">
                <span>Лимит использований</span>
                <input type="number" v-model.number="form.usage_limit" min="1" placeholder="без лимита"/>
              </label>

              <div class="row2">
                <label class="field">
                  <span>Действует с</span>
                  <input type="datetime-local" v-model="form.valid_from"/>
                </label>
                <label class="field">
                  <span>Действует до</span>
                  <input type="datetime-local" v-model="form.valid_to"/>
                </label>
              </div>

              <label class="switch-row">
                <input type="checkbox" v-model="form.is_active"/>
                <span>Активен</span>
              </label>
            </div>

            <div class="modal-footer">
              <button class="btn-cancel" @click="showForm=false">Отмена</button>
              <button class="btn-save" @click="save" :disabled="saving">
                {{ saving ? '…' : 'Сохранить' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

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
.btn-add{display:flex;align-items:center;gap:6px;padding:9px 16px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-size:13px;font-weight:700;cursor:pointer;white-space:nowrap}
.btn-add svg{width:18px;height:18px}
.search{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:12px;margin-bottom:16px;font-size:14px;background:var(--bg);color:var(--text);outline:none;box-sizing:border-box}
.search:focus{border-color:var(--accent)}
.loading{text-align:center;padding:40px;color:var(--muted)}

.promo-list{display:flex;flex-direction:column;gap:8px}
.promo-card{display:grid;grid-template-columns:1fr auto;gap:6px 12px;padding:14px;background:var(--surface);border:1px solid var(--border);border-radius:14px}
.promo-card.inactive{opacity:.55}
.pc-code{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.code-text{font-family:monospace;font-size:15px;font-weight:800;letter-spacing:.5px}
.badge{font-size:10px;font-weight:700;padding:2px 7px;border-radius:5px}
.badge.personal{background:rgba(139,92,246,.12);color:#8b5cf6}
.pc-discount{font-size:16px;font-weight:800;color:#16a34a;text-align:right;grid-row:1}
.pc-meta{display:flex;gap:10px;flex-wrap:wrap;font-size:11px;color:var(--muted);grid-column:1/-1}
.pc-usage{display:flex;align-items:center;gap:8px;grid-column:1/-1}
.usage-bar{flex:1;height:5px;background:var(--bg);border-radius:3px;overflow:hidden}
.usage-fill{height:100%;background:var(--accent);border-radius:3px;transition:width .3s}
.usage-text{font-size:11px;color:var(--muted);font-weight:600;min-width:64px;text-align:right}
.pc-actions{display:flex;gap:4px;grid-column:2;grid-row:2/4;align-self:center}
.act-btn{width:32px;height:32px;border:1px solid var(--border);border-radius:8px;background:var(--bg);display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--text)}
.act-btn svg{width:15px;height:15px}
.act-btn:hover{border-color:var(--accent);color:var(--accent)}
.act-del:hover{border-color:#ef4444;color:#ef4444}
.del-confirm{font-size:12px;font-weight:800;color:#ef4444}

.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:10000;padding:16px}
.modal-card{background:var(--surface);border-radius:18px;width:100%;max-width:440px;max-height:90vh;overflow-y:auto}
.modal-header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px 12px}
.modal-header h2{margin:0;font-size:17px;font-weight:800}
.modal-close{background:none;border:none;cursor:pointer;color:var(--muted);display:flex}
.modal-close svg{width:22px;height:22px}
.modal-body{padding:0 20px 12px;display:flex;flex-direction:column;gap:10px}
.field{display:flex;flex-direction:column;gap:4px}
.field span{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.3px}
.field input{padding:9px 12px;border:1px solid var(--border);border-radius:10px;font-size:14px;background:var(--bg);color:var(--text);outline:none;font-family:inherit;width:100%;box-sizing:border-box}
.field input:focus{border-color:var(--accent)}
.field input:disabled{opacity:.6}
.mono{font-family:monospace;letter-spacing:.5px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.switch-row{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600}
.switch-row input{width:18px;height:18px;accent-color:var(--accent)}
.modal-footer{display:flex;gap:8px;padding:0 20px 20px;justify-content:flex-end}
.btn-cancel{padding:9px 18px;border:1px solid var(--border);border-radius:10px;background:var(--bg);color:var(--text);font-size:13px;font-weight:600;cursor:pointer}
.btn-save{padding:9px 24px;border:none;border-radius:10px;background:var(--accent);color:#fff;font-size:13px;font-weight:700;cursor:pointer}
.btn-save:disabled{opacity:.5}

.empty{text-align:center;padding:40px;color:var(--muted);font-size:14px}
.modal-enter-active{animation:modal-in .22s ease}
.modal-leave-active{animation:modal-in .18s ease reverse}
@keyframes modal-in{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:scale(1)}}
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);padding:10px 20px;border-radius:10px;font-size:13px;font-weight:600;z-index:11000;box-shadow:0 4px 16px rgba(0,0,0,.15)}
.toast.ok{background:#059669;color:#fff}
.toast.err{background:#ef4444;color:#fff}
</style>
