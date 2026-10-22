<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/utils/api'
import { money, ml } from '@/utils/helpers'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const products = ref([])
const categories = ref([])
const showForm = ref(false)
const editing = ref(null)
const error = ref('')
const uploading = ref(false)
const form = ref(getEmptyForm())

function getEmptyForm() {
  return { name:'', description:'', price:1, unit:'шт', initial_stock:0, category_id:null, image_url:null,
    translations_ru_name:'', translations_en_name:'' }
}

onMounted(async () => {
  products.value = await api.get('/products?limit=500')
  categories.value = await api.get('/categories')
})

function openAdd() {
  editing.value = null; error.value = ''
  form.value = { ...getEmptyForm(), category_id: categories.value[0]?.id || null }
  showForm.value = true
}

function openEdit(p) {
  editing.value = p.id; error.value = ''
  let tr = {}
  if (p.translations) {
    try { tr = typeof p.translations === 'string' ? JSON.parse(p.translations) : p.translations } catch {}
  }
  form.value = {
    name: p.name, description: p.description || '', price: p.price, unit: p.unit,
    initial_stock: p.stock_quantity || 0,
    category_id: p.category?.id || p.category_id,
    image_url: p.image_url || null,
    translations_ru_name: tr.ru_name || '', translations_en_name: tr.en_name || '',
  }
  showForm.value = true
}

async function uploadImage(event) {
  const file = event.target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch('/api/upload-image', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${auth.token}` },
      body: fd
    })
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Upload failed') }
    const data = await res.json()
    form.value.image_url = data.url
  } catch (e) {
    error.value = e.message || 'Хатогии боркунии сурат'
  }
  uploading.value = false
}

function buildPayload() {
  const translations = {}
  if (form.value.translations_ru_name) translations.ru_name = form.value.translations_ru_name
  if (form.value.translations_en_name) translations.en_name = form.value.translations_en_name
  const payload = {
    name: form.value.name,
    description: form.value.description || '—',
    price: Number(form.value.price),
    unit: form.value.unit || 'шт',
    category_id: form.value.category_id,
    image_url: form.value.image_url || null,
    translations: Object.keys(translations).length ? JSON.stringify(translations) : null,
  }
  if (!editing.value) payload.initial_stock = Number(form.value.initial_stock) || 0
  return payload
}

async function save() {
  error.value = ''
  if (!form.value.name.trim()) { error.value = 'Номро ворид кунед'; return }
  if (!form.value.price || form.value.price <= 0) { error.value = 'Нарх бояд аз 0 зиёд бошад'; return }
  if (!form.value.category_id) { error.value = 'Категорияро интихоб кунед'; return }
  try {
    const payload = buildPayload()
    if (editing.value) {
      await api.patch('/products/' + editing.value, payload)
      // Update inventory separately
      const newQty = Number(form.value.initial_stock)
      if (!isNaN(newQty) && newQty >= 0) {
        await api.put('/inventory/' + editing.value, { quantity: newQty })
      }
    } else {
      await api.post('/products', payload)
    }
    products.value = await api.get('/products?limit=500')
    showForm.value = false
  } catch (e) { error.value = e.message || 'Хатогӣ' }
}

async function remove(id) {
  if (!confirm('Нест кардан?')) return
  try {
    await api.delete('/products/' + id)
    products.value = products.value.filter(p => p.id !== id)
  } catch (e) {
    alert(e.message || 'Хатогӣ дар нест кардан')
  }
}
</script>

<template>
  <div class="page">
    <div class="hdr">
      <h1>{{ t('admin_products') }}</h1>
      <button class="btn-add" @click="openAdd">+ {{ t('add') || 'Илова' }}</button>
    </div>

    <div class="products-list">
      <div v-for="p in products" :key="p.id" class="p-card">
        <div class="p-img">
          <img v-if="p.image_url" :src="p.image_url" :alt="p.name" />
          <div v-else class="p-img-ph">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
          </div>
        </div>
        <div class="p-info">
          <h3>{{ ml(p, 'name') }}</h3>
          <div class="p-meta">
            <span class="p-price">{{ money(p.price) }}</span>
            <span class="p-unit">/ {{ p.unit }}</span>
            <span class="p-stock" :class="{'low': p.stock_quantity <= 5}">{{ p.stock_quantity }} {{ t('pcs') || 'дона' }}</span>
          </div>
          <span class="p-cat" v-if="p.category">{{ ml(p.category, 'name') }}</span>
        </div>
        <div class="p-actions">
          <button class="btn-edit" @click="openEdit(p)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="btn-del" @click="remove(p.id)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
          </button>
        </div>
      </div>
      <div v-if="!products.length" class="empty">{{ t('no_results') || 'Мол нест' }}</div>
    </div>

    <Teleport to="body">
      <div v-if="showForm" class="modal-overlay" @click.self="showForm=false">
        <div class="modal">
          <h2>{{ editing ? (t('edit') || 'Таҳрир') : (t('add') || 'Илова кардан') }}</h2>

          <!-- Image upload -->
          <div class="img-upload-area">
            <div class="img-preview" v-if="form.image_url">
              <img :src="form.image_url" />
              <button class="img-remove" @click="form.image_url = null">✕</button>
            </div>
            <label v-else class="img-upload-btn" :class="{uploading}">
              <input type="file" accept="image/*" @change="uploadImage" hidden />
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
              <span v-if="uploading">{{ t('common_loading') || '...' }}</span>
              <span v-else>{{ t('upload_image') || 'Сурат илова кунед' }}</span>
            </label>
          </div>

          <div class="field">
            <label>{{ t('product_name') || 'Ном' }} (TJ) *</label>
            <input v-model="form.name" required />
          </div>
          <div class="field">
            <label>{{ t('description') || 'Тавсиф' }} (TJ)</label>
            <textarea v-model="form.description" rows="2"></textarea>
          </div>

          <div class="row3">
            <div class="field">
              <label>{{ t('price') || 'Нарх' }} *</label>
              <input v-model.number="form.price" type="number" min="0.01" step="0.01" required />
            </div>
            <div class="field">
              <label>{{ t('unit') || 'Воҳид' }}</label>
              <input v-model="form.unit" />
            </div>
            <div class="field">
              <label>{{ t('stock') || 'Анбор' }}</label>
              <input v-model.number="form.initial_stock" type="number" min="0" />
            </div>
          </div>

          <div class="field">
            <label>{{ t('category') || 'Категория' }} *</label>
            <select v-model="form.category_id">
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ ml(c,'name') }}</option>
            </select>
          </div>

          <div class="translations-block">
            <h4>{{ t('translations') || 'Тарҷумаҳо' }}</h4>
            <div class="row2">
              <div class="field"><label>{{ t('product_name') || 'Ном' }} (RU)</label><input v-model="form.translations_ru_name" /></div>
              <div class="field"><label>{{ t('product_name') || 'Ном' }} (EN)</label><input v-model="form.translations_en_name" /></div>
            </div>
          </div>

          <p v-if="error" class="error-msg">{{ error }}</p>

          <div class="btn-row">
            <button class="btn-save" @click="save">{{ t('save') || 'Сабт' }}</button>
            <button class="btn-cancel" @click="showForm=false">{{ t('cancel') || 'Бекор' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.page{max-width:900px;margin:0 auto;padding:16px 16px 100px}
.hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
h1{font-size:20px;font-weight:800}
.btn-add{background:var(--accent);color:#fff;border:none;padding:10px 18px;border-radius:10px;font-weight:600;cursor:pointer;font-size:14px}

.products-list{display:flex;flex-direction:column;gap:8px}
.p-card{display:flex;align-items:center;gap:12px;padding:12px;background:var(--surface);border:1px solid var(--border);border-radius:14px;transition:box-shadow .2s}
.p-card:hover{box-shadow:0 2px 12px rgba(0,0,0,.06)}
.p-img{width:56px;height:56px;border-radius:10px;overflow:hidden;background:var(--bg);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.p-img img{max-width:90%;max-height:90%;width:auto;height:auto;object-fit:contain}
.p-img-ph{opacity:.15}
.p-img-ph svg{width:28px;height:28px}
.p-info{flex:1;min-width:0}
.p-info h3{font-size:14px;font-weight:600;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.p-meta{display:flex;align-items:center;gap:6px;font-size:13px}
.p-price{font-weight:700;color:var(--accent)}
.p-unit{color:var(--muted)}
.p-stock{margin-left:auto;font-weight:600;color:#059669;font-size:12px}
.p-stock.low{color:#ef4444}
.p-cat{font-size:11px;color:var(--muted);background:var(--bg);padding:2px 8px;border-radius:6px;display:inline-block;margin-top:2px}

.p-actions{display:flex;gap:4px;flex-shrink:0}
.btn-edit,.btn-del{width:36px;height:36px;border-radius:10px;border:1px solid var(--border);background:var(--bg);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .15s}
.btn-edit svg,.btn-del svg{width:16px;height:16px}
.btn-edit:hover{border-color:var(--accent);color:var(--accent)}
.btn-del:hover{border-color:#ef4444;color:#ef4444}
.btn-del:hover svg{stroke:#ef4444}

/* Modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:20000;display:flex;align-items:center;justify-content:center;padding:16px}
.modal{background:var(--surface);border-radius:16px;padding:24px;width:100%;max-width:500px;max-height:90vh;overflow-y:auto}
.modal h2{margin:0 0 16px;font-size:18px;font-weight:700}

/* Image upload */
.img-upload-area{margin-bottom:16px}
.img-preview{position:relative;width:100%;height:160px;border-radius:12px;overflow:hidden;background:var(--bg)}
.img-preview img{width:100%;height:100%;object-fit:cover}
.img-remove{position:absolute;top:8px;right:8px;width:28px;height:28px;border-radius:50%;background:rgba(0,0,0,.6);color:#fff;border:none;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.img-upload-btn{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;width:100%;height:120px;border:2px dashed var(--border);border-radius:12px;cursor:pointer;color:var(--muted);font-size:13px;font-weight:500;transition:all .2s}
.img-upload-btn:hover{border-color:var(--accent);color:var(--accent);background:var(--accent-bg,rgba(37,99,235,.04))}
.img-upload-btn.uploading{opacity:.5;pointer-events:none}
.img-upload-btn svg{width:32px;height:32px}

.field{margin-bottom:12px}
.field label{display:block;font-size:12px;font-weight:600;color:var(--muted);margin-bottom:4px}
.field input,.field textarea,.field select{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:10px;background:var(--bg);color:var(--text);font-size:14px;font-family:inherit;box-sizing:border-box}
.field input:focus,.field textarea:focus,.field select:focus{outline:none;border-color:var(--accent)}
.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.translations-block{margin-top:8px;padding-top:12px;border-top:1px solid var(--border)}
.translations-block h4{font-size:13px;font-weight:700;color:var(--muted);margin-bottom:8px}
.error-msg{color:#dc2626;font-size:13px;padding:8px 12px;background:rgba(220,38,38,.06);border-radius:8px;margin-bottom:12px}
.btn-row{display:flex;gap:8px;margin-top:16px}
.btn-save{flex:1;padding:12px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-weight:600;cursor:pointer;font-size:15px}
.btn-cancel{flex:1;padding:12px;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:10px;cursor:pointer;font-size:15px}
.empty{text-align:center;padding:40px;color:var(--muted);font-size:14px}
</style>
