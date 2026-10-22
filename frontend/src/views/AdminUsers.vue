<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'

const { t } = useI18n()
const users = ref([])
const search = ref('')
const loading = ref(true)
const toast = ref('')
const toastType = ref('ok')

// Modal state
const showModal = ref(false)
const modalMode = ref('add') // add | edit | password
const editUser = ref(null)
const form = ref({ full_name: '', email: '', password: '', role: 'buyer' })
const saving = ref(false)

// Delete confirm
const confirmDelete = ref(null)

const roles = ['admin', 'manager', 'seller', 'buyer', 'user']

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return users.value
  return users.value.filter(u =>
    (u.full_name || '').toLowerCase().includes(q) ||
    (u.email || '').toLowerCase().includes(q) ||
    (u.role || '').toLowerCase().includes(q)
  )
})

onMounted(async () => {
  await loadUsers()
})

async function loadUsers() {
  loading.value = true
  try { users.value = await api.get('/users') } catch (e) { console.error(e) }
  loading.value = false
}

function showToast(msg, type = 'ok') {
  toast.value = msg; toastType.value = type
  setTimeout(() => toast.value = '', 3000)
}

function openAdd() {
  modalMode.value = 'add'
  form.value = { full_name: '', email: '', password: '', role: 'buyer' }
  editUser.value = null
  showModal.value = true
}

function openEdit(u) {
  modalMode.value = 'edit'
  editUser.value = u
  form.value = { full_name: u.full_name, email: u.email, password: '', role: u.role?.toLowerCase() || 'user' }
  showModal.value = true
}

function openPassword(u) {
  modalMode.value = 'password'
  editUser.value = u
  form.value = { full_name: u.full_name, email: u.email, password: '', role: u.role }
  showModal.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (modalMode.value === 'add') {
      const created = await api.post('/users', {
        full_name: form.value.full_name,
        email: form.value.email,
        password: form.value.password,
        role: form.value.role
      })
      users.value.push(created)
      showToast(t('user_created') || 'Корбар илова шуд')
    } else if (modalMode.value === 'edit') {
      const payload = { full_name: form.value.full_name, role: form.value.role }
      const updated = await api.patch('/users/' + editUser.value.id, payload)
      Object.assign(editUser.value, updated)
      showToast(t('user_updated') || 'Тағйирот нигоҳ шуд')
    } else if (modalMode.value === 'password') {
      if (!form.value.password || form.value.password.length < 8) {
        showToast(t('password_min_8') || 'Рамз бояд ақаллан 8 аломат бошад', 'err')
        saving.value = false
        return
      }
      await api.patch('/users/' + editUser.value.id, { password: form.value.password })
      showToast(t('password_changed') || 'Рамз иваз шуд')
    }
    showModal.value = false
  } catch (e) {
    showToast(e.message || 'Хатогӣ', 'err')
  }
  saving.value = false
}

async function handleDelete(u) {
  if (confirmDelete.value !== u.id) { confirmDelete.value = u.id; return }
  try {
    await api.delete('/users/' + u.id)
    users.value = users.value.filter(x => x.id !== u.id)
    showToast(t('user_deleted') || 'Корбар нест шуд')
  } catch (e) {
    const msg = e.message || ''
    if (msg.includes('deactivated') || msg.includes('orders')) {
      u.is_active = false
      showToast(t('user_has_data_deactivated') || 'Корбар фармоишҳо дорад — ба ҷои нест кардан ғайрифаъол шуд', 'err')
    } else {
      showToast(msg || 'Хатогӣ', 'err')
    }
  }
  confirmDelete.value = null
}

async function toggleActive(u) {
  try {
    const updated = await api.patch('/users/' + u.id, { is_active: !u.is_active })
    Object.assign(u, updated)
  } catch (e) { showToast(e.message, 'err') }
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const roleColors = {
  admin: '#ef4444', ADMIN: '#ef4444',
  manager: '#2563eb', MANAGER: '#2563eb',
  seller: '#d97706', SELLER: '#d97706',
  buyer: '#059669', BUYER: '#059669',
  user: '#6b7280', USER: '#6b7280',
}
</script>

<template>
  <div class="page">
    <!-- Header -->
    <div class="page-header">
      <h1>{{ t('admin_users') }}</h1>
      <button class="btn-add" @click="openAdd">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        <span>{{ t('add') || 'Илова' }}</span>
      </button>
    </div>

    <input v-model="search" :placeholder="t('search') || 'Ҷустуҷӯ...'" class="search"/>

    <div v-if="loading" class="loading">{{ t('loading') }}</div>

    <div v-else class="user-cards">
      <div v-for="u in filtered" :key="u.id" class="user-card" :class="{'inactive': !u.is_active}">
        <div class="uc-left">
          <div class="uc-avatar" :style="{borderColor: roleColors[u.role] || '#6b7280'}">
            {{ (u.full_name || u.email || '?')[0].toUpperCase() }}
          </div>
          <div class="uc-info">
            <div class="uc-name">
              {{ u.full_name || '—' }}
              <span v-if="!u.is_active" class="uc-blocked">{{ t('blocked') || 'Баста' }}</span>
            </div>
            <div class="uc-email">{{ u.email || '—' }}</div>
            <div class="uc-meta">
              <span class="role-badge" :style="{background: (roleColors[u.role]||'#6b7280') + '18', color: roleColors[u.role]||'#6b7280'}">{{ u.role }}</span>
              <span>{{ formatDate(u.created_at) }}</span>
              <span class="uc-id">#{{ u.id }}</span>
            </div>
          </div>
        </div>
        <div class="uc-actions">
          <button class="act-btn" @click="openEdit(u)" :title="t('edit') || 'Таҳрир'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="act-btn" @click="openPassword(u)" :title="t('change_password') || 'Иваз кардани рамз'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
          </button>
          <button class="act-btn" @click="toggleActive(u)" :title="u.is_active ? 'Баста кардан' : 'Фаъол кардан'">
            <svg v-if="u.is_active" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
          </button>
          <button class="act-btn act-del" @click="handleDelete(u)">
            <svg v-if="confirmDelete !== u.id" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
            <span v-else class="del-confirm">{{ t('confirm') || '?' }}</span>
          </button>
        </div>
      </div>

      <div v-if="!filtered.length && !loading" class="empty">{{ t('no_results') || 'Натиҷае нест' }}</div>
    </div>

    <div class="total" v-if="users.length">{{ t('total') || 'Ҳамагӣ' }}: {{ users.length }}</div>

    <!-- Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModal" class="modal-overlay" @click.self="showModal=false">
          <div class="modal-card">
            <div class="modal-header">
              <h2 v-if="modalMode==='add'">{{ t('add_user') || 'Илова кардани корбар' }}</h2>
              <h2 v-else-if="modalMode==='edit'">{{ t('edit_user') || 'Таҳрири корбар' }}</h2>
              <h2 v-else>{{ t('change_password') || 'Иваз кардани рамз' }}</h2>
              <button class="modal-close" @click="showModal=false">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            <div class="modal-body">
              <template v-if="modalMode==='password'">
                <div class="field-info">{{ editUser?.full_name }} ({{ editUser?.email }})</div>
                <label class="field">
                  <span>{{ t('new_password') || 'Рамзи нав' }}</span>
                  <input type="password" v-model="form.password" placeholder="Ақаллан 8 аломат" autocomplete="new-password"/>
                </label>
              </template>

              <template v-else>
                <label class="field">
                  <span>{{ t('full_name') || 'Номи пурра' }}</span>
                  <input type="text" v-model="form.full_name" placeholder="Муборакшо"/>
                </label>
                <label class="field" v-if="modalMode==='add'">
                  <span>Email</span>
                  <input type="email" v-model="form.email" placeholder="user@example.com"/>
                </label>
                <label class="field" v-if="modalMode==='add'">
                  <span>{{ t('password') || 'Рамз' }}</span>
                  <input type="password" v-model="form.password" placeholder="Ақаллан 8 аломат" autocomplete="new-password"/>
                </label>
                <label class="field">
                  <span>{{ t('role') || 'Нақш' }}</span>
                  <select v-model="form.role">
                    <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
                  </select>
                </label>
              </template>
            </div>

            <div class="modal-footer">
              <button class="btn-cancel" @click="showModal=false">{{ t('cancel') || 'Бекор' }}</button>
              <button class="btn-save" @click="handleSave" :disabled="saving">
                {{ saving ? '...' : (t('save') || 'Нигоҳ доштан') }}
              </button>
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
.page{max-width:900px;margin:0 auto;padding:16px 16px 100px}
.page-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
h1{font-size:20px;font-weight:800;margin:0}
.btn-add{display:flex;align-items:center;gap:6px;padding:8px 16px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-size:13px;font-weight:700;cursor:pointer;transition:background .2s}
.btn-add:hover{background:var(--accent-hover)}
.btn-add svg{width:18px;height:18px}
.search{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:12px;margin-bottom:16px;font-size:14px;background:var(--bg);color:var(--text);outline:none}
.search:focus{border-color:var(--accent)}

.loading{text-align:center;padding:40px;color:var(--muted)}

.user-cards{display:flex;flex-direction:column;gap:8px}

.user-card{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:var(--surface);border:1px solid var(--border);border-radius:14px;transition:border-color .2s;gap:8px}
.user-card:hover{border-color:var(--accent)}
.user-card.inactive{opacity:.55}

.uc-left{display:flex;align-items:center;gap:12px;flex:1;min-width:0}
.uc-avatar{width:42px;height:42px;border-radius:50%;background:var(--bg);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px;flex-shrink:0;border:2px solid;color:var(--text)}
.uc-info{flex:1;min-width:0}
.uc-name{font-weight:700;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;align-items:center;gap:6px}
.uc-blocked{font-size:10px;background:rgba(239,68,68,.12);color:#ef4444;padding:1px 6px;border-radius:4px;font-weight:700}
.uc-email{font-size:12px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}
.uc-meta{display:flex;align-items:center;gap:6px;margin-top:4px;font-size:11px;color:var(--muted)}
.role-badge{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;text-transform:capitalize}
.uc-id{opacity:.5}

.uc-actions{display:flex;gap:4px;flex-shrink:0}
.act-btn{width:34px;height:34px;border:1px solid var(--border);border-radius:8px;background:var(--bg);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .15s;color:var(--text)}
.act-btn:hover{border-color:var(--accent);background:var(--accent-bg)}
.act-btn svg{width:16px;height:16px}
.act-del{color:var(--muted)}
.act-del:hover{border-color:#ef4444;background:rgba(239,68,68,.06);color:#ef4444}
.act-del:hover svg{stroke:#ef4444}
.del-confirm{font-size:11px;font-weight:800;color:#ef4444}

/* Modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:10000;padding:16px}
.modal-card{background:var(--surface);border-radius:18px;width:100%;max-width:420px;box-shadow:0 12px 48px rgba(0,0,0,.2);overflow:hidden}
.modal-header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px 14px}
.modal-header h2{margin:0;font-size:17px;font-weight:800}
.modal-close{background:none;border:none;cursor:pointer;color:var(--muted);padding:4px;display:flex}
.modal-close svg{width:22px;height:22px}
.modal-body{padding:0 20px 16px;display:flex;flex-direction:column;gap:12px}
.field-info{font-size:14px;font-weight:600;color:var(--text);padding:8px 12px;background:var(--bg);border-radius:10px}
.field{display:flex;flex-direction:column;gap:4px}
.field span{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.3px}
.field input,.field select{padding:10px 12px;border:1px solid var(--border);border-radius:10px;font-size:14px;background:var(--bg);color:var(--text);outline:none;font-family:inherit}
.field input:focus,.field select:focus{border-color:var(--accent)}
.modal-footer{display:flex;gap:8px;padding:0 20px 20px;justify-content:flex-end}
.btn-cancel{padding:8px 18px;border:1px solid var(--border);border-radius:10px;background:var(--bg);color:var(--text);font-size:13px;font-weight:600;cursor:pointer}
.btn-save{padding:8px 24px;border:none;border-radius:10px;background:var(--accent);color:#fff;font-size:13px;font-weight:700;cursor:pointer;transition:background .2s}
.btn-save:hover{background:var(--accent-hover)}
.btn-save:disabled{opacity:.5;cursor:not-allowed}

.modal-enter-active{animation:modal-in .25s ease}
.modal-leave-active{animation:modal-in .2s ease reverse}
@keyframes modal-in{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}

.empty{text-align:center;padding:40px;color:var(--muted);font-size:14px}
.total{text-align:center;margin-top:16px;font-size:13px;color:var(--muted);font-weight:600}

/* Toast */
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);padding:10px 20px;border-radius:10px;font-size:13px;font-weight:600;z-index:11000;box-shadow:0 4px 16px rgba(0,0,0,.15)}
.toast.ok{background:#059669;color:#fff}
.toast.err{background:#ef4444;color:#fff}
.toast-enter-active{animation:toast-in .3s ease}
.toast-leave-active{animation:toast-in .2s ease reverse}
@keyframes toast-in{from{opacity:0;transform:translateX(-50%) translateY(10px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
</style>
