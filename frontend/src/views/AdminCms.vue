<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'

const { t } = useI18n()
const currentTab = ref('pages')
const loading = ref(false)

/* ─── State ─── */
const pages = ref([])
const news = ref([])
const menus = ref([])
const settings_list = ref([])
const media = ref([])
const audit = ref([])

/* ─── Modal state ─── */
const modal = ref(null)
const editing = ref(null)
const toast = ref('')
const toastType = ref('ok')

/* ─── Settings filter ─── */
const settingsFilter = ref('all')

/* ─── Setting groups definition ─── */
const settingGroups = [
  { key: 'general', i18n: 'cms_group_general', icon: '⚙️' },
  { key: 'contacts', i18n: 'cms_group_contacts', icon: '📞' },
  { key: 'identity', i18n: 'cms_group_identity', icon: '🏷️' },
  { key: 'social', i18n: 'cms_group_social', icon: '🌐' },
  { key: 'payment', i18n: 'cms_group_payment', icon: '💳' },
  { key: 'delivery', i18n: 'cms_group_delivery', icon: '🚚' },
  { key: 'seo', i18n: 'cms_group_seo', icon: '🔍' },
  { key: 'appearance', i18n: 'cms_group_appearance', icon: '🎨' },
  { key: 'notifications', i18n: 'cms_group_notifications', icon: '🔔' },
  { key: 'custom', i18n: 'cms_group_custom', icon: '📦' },
]

function groupLabel(key) {
  const g = settingGroups.find(g => g.key === key)
  return g ? t(g.i18n) : key
}

function groupIcon(key) {
  const g = settingGroups.find(g => g.key === key)
  return g ? g.icon : '📦'
}

/* ─── Filtered settings by group ─── */
const filteredSettings = computed(() => {
  if (settingsFilter.value === 'all') return settings_list.value
  return settings_list.value.filter(s => s.group_name === settingsFilter.value)
})

/* ─── Groups that have settings ─── */
const activeGroups = computed(() => {
  const groups = new Set(settings_list.value.map(s => s.group_name))
  return ['all', ...settingGroups.map(g => g.key).filter(k => groups.has(k))]
})

/* ─── Grouped settings for display ─── */
const groupedSettings = computed(() => {
  if (settingsFilter.value !== 'all') return null
  const groups = {}
  for (const s of settings_list.value) {
    if (!groups[s.group_name]) groups[s.group_name] = []
    groups[s.group_name].push(s)
  }
  return groups
})

/* ─── Quick Setup presets ─── */
const QUICK_SETUP_PRESETS = [
  { key: 'site_name', label: 'Номи сайт / Название сайта', group: 'general', type: 'text', placeholder: 'СохтМатериал' },
  { key: 'site_description', label: 'Тавсифи сайт / Описание сайта', group: 'general', type: 'text', placeholder: 'Мағозаи масолеҳи сохтмонӣ' },
  { key: 'phone', label: 'Телефон', group: 'contacts', type: 'text', placeholder: '+992 XX XXX XX XX' },
  { key: 'email', label: 'Email', group: 'contacts', type: 'text', placeholder: 'info@example.com' },
  { key: 'address', label: 'Суроға / Адрес', group: 'contacts', type: 'text', placeholder: 'ш. Душанбе, к. Рудакӣ 1' },
  { key: 'work_hours', label: 'Соатҳои корӣ / Время работы', group: 'contacts', type: 'text', placeholder: 'Пн-Сб: 08:00-18:00' },
]

const quickSetupValues = ref({})
const showQuickSetup = ref(false)

function initQuickSetup() {
  const vals = {}
  for (const p of QUICK_SETUP_PRESETS) {
    const existing = settings_list.value.find(s => s.key === p.key)
    vals[p.key] = existing?.value || ''
  }
  quickSetupValues.value = vals
  showQuickSetup.value = true
}

async function saveQuickSetup() {
  try {
    const promises = []
    for (const p of QUICK_SETUP_PRESETS) {
      const val = quickSetupValues.value[p.key]
      if (val && val.trim()) {
        promises.push(apiCall('POST', '/settings', {
          key: p.key,
          value: val.trim(),
          value_type: p.type,
          label: p.label,
          group_name: p.group,
        }))
      }
    }
    await Promise.all(promises)
    showQuickSetup.value = false
    showToast(t('cms_save') + ' ✓')
    await loadSettings()
  } catch (e) { showToast(e.message, 'err') }
}

/* ─── Page form ─── */
const pf = ref(emptyPageForm())
function emptyPageForm() {
  return { title:'', slug:'', description:'', status:'draft', show_in_nav:false, meta_title:'', meta_description:'', robots_index:true, blocks:[],
    tr_ru_title:'', tr_ru_description:'', tr_en_title:'', tr_en_description:'' }
}

/* ─── News form ─── */
const nf = ref(emptyNewsForm())
function emptyNewsForm() {
  return { title:'', slug:'', summary:'', content:'', image_url:'', status:'draft', pinned:false,
    tr_ru_title:'', tr_ru_summary:'', tr_ru_content:'', tr_en_title:'', tr_en_summary:'', tr_en_content:'' }
}

/* ─── Menu form ─── */
const mf = ref(emptyMenuForm())
function emptyMenuForm() {
  return { label:'', url:'', location:'footer', sort_order:0, is_active:true, open_new_tab:false, icon:'' }
}

/* ─── Setting form ─── */
const sf = ref(emptySettingForm())
function emptySettingForm() {
  return { key:'', value:'', value_type:'text', label:'', group_name:'general' }
}

/* ─── Toast ─── */
function showToast(msg, type='ok') {
  toast.value = msg; toastType.value = type
  setTimeout(() => toast.value = '', 3000)
}

/* ─── API (uses api.js with auto token refresh on 401) ─── */
async function apiCall(method, path, body) {
  const fullPath = '/cms' + path
  if (method === 'GET') return api.get(fullPath)
  if (method === 'POST') return api.post(fullPath, body)
  if (method === 'PATCH') return api.patch(fullPath, body)
  if (method === 'PUT') return api.put(fullPath, body)
  if (method === 'DELETE') return api.delete(fullPath)
}

/* ─── Load data ─── */
async function loadPages() { try { pages.value = await apiCall('GET', '/pages') } catch(e) { showToast(e.message, 'err') } }
async function loadNews() { try { news.value = await apiCall('GET', '/news') } catch(e) { showToast(e.message, 'err') } }
async function loadMenus() { try { menus.value = await apiCall('GET', '/menus') } catch(e) { showToast(e.message, 'err') } }
async function loadSettings() { try { settings_list.value = await apiCall('GET', '/settings') } catch(e) { showToast(e.message, 'err') } }
async function loadMedia() { try { media.value = await apiCall('GET', '/media') } catch(e) { showToast(e.message, 'err') } }
async function loadAudit() { try { audit.value = await apiCall('GET', '/audit?limit=50') } catch(e) { showToast(e.message, 'err') } }

onMounted(async () => {
  loading.value = true
  await Promise.all([loadPages(), loadNews()]).catch(()=>{})
  loading.value = false
})

async function switchTab(tab) {
  currentTab.value = tab
  loading.value = true
  try {
    if (tab === 'pages') await loadPages()
    else if (tab === 'news') await loadNews()
    else if (tab === 'menus') await loadMenus()
    else if (tab === 'settings') await loadSettings()
    else if (tab === 'media') await loadMedia()
    else if (tab === 'audit') await loadAudit()
  } catch {}
  loading.value = false
}

/* ─── Translations ─── */
function parseTranslations(trStr) {
  if (!trStr) return {}
  try { return typeof trStr === 'string' ? JSON.parse(trStr) : trStr } catch { return {} }
}

function buildTranslationsJson(fields) {
  const result = {}
  for (const [lang, obj] of Object.entries(fields)) {
    const cleaned = {}
    for (const [k, v] of Object.entries(obj)) {
      if (v && v.trim()) cleaned[k] = v.trim()
    }
    if (Object.keys(cleaned).length) result[lang] = cleaned
  }
  return Object.keys(result).length ? JSON.stringify(result) : null
}

/* ─── Pages CRUD ─── */
function openPageForm(p) {
  if (p) {
    editing.value = p.id
    const tr = parseTranslations(p.translations)
    pf.value = {
      title: p.title, slug: p.slug, description: p.description||'', status: p.status,
      show_in_nav: p.show_in_nav, meta_title: p.meta_title||'', meta_description: p.meta_description||'',
      robots_index: p.robots_index!==false, blocks: [],
      tr_ru_title: tr.ru?.title||'', tr_ru_description: tr.ru?.description||'',
      tr_en_title: tr.en?.title||'', tr_en_description: tr.en?.description||'',
    }
  } else { editing.value = null; pf.value = emptyPageForm() }
  modal.value = 'page'
}

async function savePage() {
  try {
    const translations = buildTranslationsJson({
      ru: { title: pf.value.tr_ru_title, description: pf.value.tr_ru_description },
      en: { title: pf.value.tr_en_title, description: pf.value.tr_en_description },
    })
    const payload = {
      title: pf.value.title, slug: pf.value.slug || undefined, description: pf.value.description || null,
      status: pf.value.status, show_in_nav: pf.value.show_in_nav,
      meta_title: pf.value.meta_title || null, meta_description: pf.value.meta_description || null,
      robots_index: pf.value.robots_index, translations,
    }
    if (!editing.value) payload.blocks = pf.value.blocks
    if (editing.value) await apiCall('PATCH', '/pages/'+editing.value, payload)
    else await apiCall('POST', '/pages', payload)
    modal.value = null; showToast(t('cms_save') + ' ✓'); await loadPages()
  } catch(e) { showToast(e.message, 'err') }
}

async function deletePage(id) { if(confirm(t('cms_delete_confirm'))) { try { await apiCall('DELETE','/pages/'+id); await loadPages(); showToast(t('cms_delete')+' ✓') } catch(e) { showToast(e.message,'err') } } }

async function togglePageStatus(p) {
  const ns = p.status === 'published' ? 'draft' : 'published'
  try { await apiCall('PATCH','/pages/'+p.id,{status:ns}); showToast('✓'); await loadPages() } catch(e) { showToast(e.message,'err') }
}

/* ─── News CRUD ─── */
function openNewsForm(n) {
  if (n) {
    editing.value = n.id
    const tr = parseTranslations(n.translations)
    nf.value = {
      title:n.title, slug:n.slug, summary:n.summary||'', content:n.content||'',
      image_url:n.image_url||'', status:n.status, pinned:n.pinned,
      tr_ru_title:tr.ru?.title||'', tr_ru_summary:tr.ru?.summary||'', tr_ru_content:tr.ru?.content||'',
      tr_en_title:tr.en?.title||'', tr_en_summary:tr.en?.summary||'', tr_en_content:tr.en?.content||'',
    }
  } else { editing.value = null; nf.value = emptyNewsForm() }
  modal.value = 'news'
}

async function saveNews() {
  try {
    const translations = buildTranslationsJson({
      ru: { title:nf.value.tr_ru_title, summary:nf.value.tr_ru_summary, content:nf.value.tr_ru_content },
      en: { title:nf.value.tr_en_title, summary:nf.value.tr_en_summary, content:nf.value.tr_en_content },
    })
    const payload = {
      title:nf.value.title, slug:nf.value.slug||undefined,
      summary:nf.value.summary||null, content:nf.value.content||'',
      image_url:nf.value.image_url||null, status:nf.value.status, pinned:nf.value.pinned, translations,
    }
    if (editing.value) await apiCall('PATCH','/news/'+editing.value, payload)
    else await apiCall('POST','/news', payload)
    modal.value = null; showToast(t('cms_save')+' ✓'); await loadNews()
  } catch(e) { showToast(e.message,'err') }
}

async function deleteNews(id) { if(confirm(t('cms_delete_confirm'))) { try { await apiCall('DELETE','/news/'+id); await loadNews(); showToast(t('cms_delete')+' ✓') } catch(e) { showToast(e.message,'err') } } }

/* ─── Menu CRUD ─── */
function openMenuForm(m) {
  if (m) {
    editing.value = m.id
    mf.value = { label:m.label, url:m.url, location:m.location, sort_order:m.sort_order, is_active:m.is_active, open_new_tab:m.open_new_tab, icon:m.icon||'' }
  } else { editing.value = null; mf.value = emptyMenuForm() }
  modal.value = 'menu'
}

async function saveMenu() {
  try {
    const payload = { ...mf.value, icon:mf.value.icon||null }
    if (editing.value) await apiCall('PATCH','/menus/'+editing.value, payload)
    else await apiCall('POST','/menus', payload)
    modal.value = null; showToast(t('cms_save')+' ✓'); await loadMenus()
  } catch(e) { showToast(e.message,'err') }
}

async function deleteMenu(id) { if(confirm(t('cms_delete_confirm'))) { try { await apiCall('DELETE','/menus/'+id); await loadMenus(); showToast(t('cms_delete')+' ✓') } catch(e) { showToast(e.message,'err') } } }

/* ─── Settings CRUD ─── */
function openSettingForm(s) {
  if (s) {
    editing.value = s.id
    sf.value = { key:s.key, value:s.value||'', value_type:s.value_type, label:s.label||'', group_name:s.group_name }
  } else { editing.value = null; sf.value = emptySettingForm() }
  modal.value = 'setting'
}

async function saveSetting() {
  try {
    await apiCall('POST','/settings', sf.value)
    modal.value = null; showToast(t('cms_save')+' ✓'); await loadSettings()
  } catch(e) { showToast(e.message,'err') }
}

async function deleteSetting(key) { if(confirm(t('cms_delete_confirm'))) { try { await apiCall('DELETE','/settings/'+encodeURIComponent(key)); await loadSettings(); showToast(t('cms_delete')+' ✓') } catch(e) { showToast(e.message,'err') } } }

/* ─── Media ─── */
const fileInput = ref(null)
async function uploadMedia() {
  const f = fileInput.value?.files?.[0]; if (!f) return
  const fd = new FormData(); fd.append('file', f)
  try {
    const { useAuthStore } = await import('@/stores/auth')
    const auth = useAuthStore()
    const headers = {}
    if (auth.token) headers['Authorization'] = 'Bearer ' + auth.token
    let r = await fetch('/api/cms/media', { method:'POST', headers, body:fd })
    if (r.status === 401 && auth.refreshToken) {
      const ok = await auth.refresh()
      if (ok) {
        headers['Authorization'] = 'Bearer ' + auth.token
        r = await fetch('/api/cms/media', { method:'POST', headers, body:fd })
      }
    }
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'Error') }
    fileInput.value.value = ''; showToast(t('cms_upload_file')+' ✓'); await loadMedia()
  } catch(e) { showToast(e.message,'err') }
}

async function deleteMedia(id) { if(confirm(t('cms_delete_confirm'))) { try { await apiCall('DELETE','/media/'+id); await loadMedia(); showToast(t('cms_delete')+' ✓') } catch(e) { showToast(e.message,'err') } } }
function copyUrl(url) { navigator.clipboard.writeText(url); showToast(t('cms_copy_url')+' ✓') }

/* ─── Helpers ─── */
function fmtDate(d) { return new Date(d).toLocaleDateString('ru-RU',{day:'numeric',month:'short',year:'numeric'}) }
function sBadge(s) { return s==='published'?'badge-pub':'badge-draft' }
function sLabel(s) { return s==='published'?t('cms_status_published'):s==='archived'?t('cms_status_archived'):t('cms_status_draft') }
function locLabel(l) { return l==='header'?t('cms_loc_header'):l==='footer'?t('cms_loc_footer'):t('cms_loc_sidebar') }
function vtLabel(vt) { return t('cms_value_type_'+vt) || vt }

/* ─── Menu count by location ─── */
const headerMenus = computed(() => menus.value.filter(m => m.location === 'header'))
const footerMenus = computed(() => menus.value.filter(m => m.location === 'footer'))
const sidebarMenus = computed(() => menus.value.filter(m => m.location === 'sidebar'))

const tabs = [
  { k:'pages', l:'cms_pages', icon:'📄' },
  { k:'news', l:'cms_news', icon:'📰' },
  { k:'menus', l:'cms_menus', icon:'☰' },
  { k:'settings', l:'cms_settings', icon:'⚙️' },
  { k:'media', l:'cms_media', icon:'🖼️' },
  { k:'audit', l:'cms_audit', icon:'📋' },
]
</script>

<template>
  <div class="page">
    <h1>CMS — {{ t('cms_admin_title') }}</h1>

    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.k" :class="['tab',{active:currentTab===tab.k}]" @click="switchTab(tab.k)">
        <span class="tab-icon">{{ tab.icon }}</span> {{ t(tab.l) }}
      </button>
    </div>

    <div v-if="loading" class="loading">{{ t('cms_loading') }}</div>

    <!-- ═══ PAGES ═══ -->
    <template v-if="currentTab==='pages' && !loading">
      <div class="tab-help">
        <div class="help-icon">📄</div>
        <div>
          <strong>{{ t('cms_pages_help_title') }}</strong>
          <p>{{ t('cms_pages_help_text') }}</p>
        </div>
      </div>

      <button class="btn-add" @click="openPageForm(null)">+ {{ t('cms_new_page') }}</button>
      <div class="card-list">
        <div v-for="p in pages" :key="p.id" class="card">
          <div class="card-top">
            <div><strong>{{ p.title }}</strong><span class="slug">/{{ p.slug }}</span></div>
            <span :class="['badge',sBadge(p.status)]">{{ sLabel(p.status) }}</span>
          </div>
          <div class="card-meta">
            <span>{{ p.blocks_count }} {{ t('cms_page_blocks_count') }}</span>
            <span v-if="p.show_in_nav" class="tag">{{ t('cms_page_nav_badge') }}</span>
            <span>{{ fmtDate(p.created_at) }}</span>
          </div>
          <div class="card-actions">
            <button @click="togglePageStatus(p)" class="btn-sm">{{ p.status==='published'?t('cms_hide'):t('cms_publish') }}</button>
            <button @click="openPageForm(p)" class="btn-sm">{{ t('cms_edit') }}</button>
            <button @click="deletePage(p.id)" class="btn-sm btn-danger">{{ t('cms_delete') }}</button>
          </div>
        </div>
      </div>
      <div v-if="!pages.length" class="empty-state">
        <div class="empty-icon">📄</div>
        <p class="empty-title">{{ t('cms_empty_pages') }}</p>
        <p class="empty-hint">{{ t('cms_pages_empty_hint') }}</p>
        <button class="btn-add" @click="openPageForm(null)">+ {{ t('cms_new_page') }}</button>
      </div>
    </template>

    <!-- ═══ NEWS ═══ -->
    <template v-if="currentTab==='news' && !loading">
      <div class="tab-help">
        <div class="help-icon">📰</div>
        <div>
          <strong>{{ t('cms_news_help_title') }}</strong>
          <p>{{ t('cms_news_help_text') }}</p>
        </div>
      </div>

      <button class="btn-add" @click="openNewsForm(null)">+ {{ t('cms_new_news') }}</button>
      <div class="card-list">
        <div v-for="n in news" :key="n.id" class="card">
          <div class="card-top">
            <div><strong>{{ n.title }}</strong><span v-if="n.pinned" class="pin">📌</span></div>
            <span :class="['badge',sBadge(n.status)]">{{ sLabel(n.status) }}</span>
          </div>
          <div class="card-meta">
            <span v-if="n.summary" class="summary">{{ n.summary.slice(0,80) }}...</span>
            <span>{{ fmtDate(n.created_at) }}</span>
          </div>
          <div class="card-actions">
            <button @click="openNewsForm(n)" class="btn-sm">{{ t('cms_edit') }}</button>
            <button @click="deleteNews(n.id)" class="btn-sm btn-danger">{{ t('cms_delete') }}</button>
          </div>
        </div>
      </div>
      <div v-if="!news.length" class="empty-state">
        <div class="empty-icon">📰</div>
        <p class="empty-title">{{ t('cms_empty_news') }}</p>
        <p class="empty-hint">{{ t('cms_news_empty_hint') }}</p>
        <button class="btn-add" @click="openNewsForm(null)">+ {{ t('cms_new_news') }}</button>
      </div>
    </template>

    <!-- ═══ MENUS ═══ -->
    <template v-if="currentTab==='menus' && !loading">
      <div class="tab-help">
        <div class="help-icon">☰</div>
        <div>
          <strong>{{ t('cms_menus_help_title') }}</strong>
          <p>{{ t('cms_menus_help_text') }}</p>
        </div>
      </div>

      <div class="menu-locations-hint">
        <div class="loc-hint">
          <span class="loc-badge loc-header">{{ t('cms_loc_header') }}</span>
          <span>{{ t('cms_menu_header_hint') }}</span>
          <span class="loc-count">{{ headerMenus.length }}</span>
        </div>
        <div class="loc-hint">
          <span class="loc-badge loc-footer">{{ t('cms_loc_footer') }}</span>
          <span>{{ t('cms_menu_footer_hint') }}</span>
          <span class="loc-count">{{ footerMenus.length }}</span>
        </div>
        <div class="loc-hint">
          <span class="loc-badge loc-sidebar">{{ t('cms_loc_sidebar') }}</span>
          <span>{{ t('cms_menu_sidebar_hint') }}</span>
          <span class="loc-count">{{ sidebarMenus.length }}</span>
        </div>
      </div>

      <button class="btn-add" @click="openMenuForm(null)">+ {{ t('cms_new_menu') }}</button>
      <div class="card-list">
        <div v-for="m in menus" :key="m.id" class="card">
          <div class="card-top">
            <div>
              <span v-if="m.icon" class="menu-icon-preview">{{ m.icon }}</span>
              <strong>{{ m.label }}</strong> → <span class="slug">{{ m.url }}</span>
            </div>
            <span :class="['badge','badge-loc','loc-' + m.location]">{{ locLabel(m.location) }}</span>
          </div>
          <div class="card-meta">
            <span>{{ t('cms_menu_sort') }}: {{ m.sort_order }}</span>
            <span :class="m.is_active?'tag':'tag-off'">{{ m.is_active?t('cms_menu_active'):t('cms_menu_inactive') }}</span>
            <span v-if="m.open_new_tab">↗ {{ t('cms_menu_new_tab') }}</span>
          </div>
          <div class="card-actions">
            <button @click="openMenuForm(m)" class="btn-sm">{{ t('cms_edit') }}</button>
            <button @click="deleteMenu(m.id)" class="btn-sm btn-danger">{{ t('cms_delete') }}</button>
          </div>
        </div>
      </div>
      <div v-if="!menus.length" class="empty-state">
        <div class="empty-icon">☰</div>
        <p class="empty-title">{{ t('cms_empty_menus') }}</p>
        <p class="empty-hint">{{ t('cms_menus_empty_hint') }}</p>
        <button class="btn-add" @click="openMenuForm(null)">+ {{ t('cms_new_menu') }}</button>
      </div>
    </template>

    <!-- ═══ SETTINGS (grouped) ═══ -->
    <template v-if="currentTab==='settings' && !loading">
      <div class="tab-help">
        <div class="help-icon">⚙️</div>
        <div>
          <strong>{{ t('cms_settings_help_title') }}</strong>
          <p>{{ t('cms_settings_help_text') }}</p>
        </div>
      </div>

      <div class="settings-top">
        <button class="btn-add btn-quick" @click="initQuickSetup">⚡ {{ t('cms_quick_setup') }}</button>
        <button class="btn-add" @click="openSettingForm(null)">+ {{ t('cms_new_setting') }}</button>
      </div>

      <!-- Group filter chips -->
      <div class="group-chips">
        <button v-for="gk in activeGroups" :key="gk"
          :class="['chip', {active: settingsFilter===gk}]"
          @click="settingsFilter=gk">
          <span v-if="gk!=='all'" class="chip-icon">{{ groupIcon(gk) }}</span>
          {{ gk==='all' ? t('cms_filter_all') : groupLabel(gk) }}
          <span class="chip-count">{{ gk==='all' ? settings_list.length : settings_list.filter(s=>s.group_name===gk).length }}</span>
        </button>
      </div>

      <!-- Grouped display -->
      <template v-if="settingsFilter==='all' && groupedSettings">
        <div v-for="(items, gName) in groupedSettings" :key="gName" class="settings-group">
          <div class="group-header">
            <span class="group-icon">{{ groupIcon(gName) }}</span>
            <span class="group-title">{{ groupLabel(gName) }}</span>
            <span class="group-count">{{ items.length }}</span>
          </div>
          <div class="card-list">
            <div v-for="s in items" :key="s.key" class="card card-flat">
              <div class="card-top">
                <div><code>{{ s.key }}</code> <span v-if="s.label" class="slug">— {{ s.label }}</span></div>
                <span class="badge badge-type">{{ vtLabel(s.value_type) }}</span>
              </div>
              <div class="card-meta">
                <span class="setting-val">{{ s.value?.slice(0,120) || '—' }}</span>
              </div>
              <div class="card-actions">
                <button @click="openSettingForm(s)" class="btn-sm">{{ t('cms_edit') }}</button>
                <button @click="deleteSetting(s.key)" class="btn-sm btn-danger">{{ t('cms_delete') }}</button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Filtered display (single group) -->
      <template v-else>
        <div class="card-list">
          <div v-for="s in filteredSettings" :key="s.key" class="card card-flat">
            <div class="card-top">
              <div><code>{{ s.key }}</code> <span v-if="s.label" class="slug">— {{ s.label }}</span></div>
              <span class="badge badge-type">{{ vtLabel(s.value_type) }}</span>
            </div>
            <div class="card-meta">
              <span class="setting-val">{{ s.value?.slice(0,120) || '—' }}</span>
            </div>
            <div class="card-actions">
              <button @click="openSettingForm(s)" class="btn-sm">{{ t('cms_edit') }}</button>
              <button @click="deleteSetting(s.key)" class="btn-sm btn-danger">{{ t('cms_delete') }}</button>
            </div>
          </div>
        </div>
        <p v-if="!filteredSettings.length" class="empty">{{ t('cms_no_settings_in_group') }}</p>
      </template>

      <div v-if="!settings_list.length" class="empty-state">
        <div class="empty-icon">⚙️</div>
        <p class="empty-title">{{ t('cms_empty_settings') }}</p>
        <p class="empty-hint">{{ t('cms_settings_empty_hint') }}</p>
        <button class="btn-add btn-quick" @click="initQuickSetup">⚡ {{ t('cms_quick_setup') }}</button>
      </div>
    </template>

    <!-- ═══ MEDIA ═══ -->
    <template v-if="currentTab==='media' && !loading">
      <div class="tab-help">
        <div class="help-icon">🖼️</div>
        <div>
          <strong>{{ t('cms_media_help_title') }}</strong>
          <p>{{ t('cms_media_help_text') }}</p>
        </div>
      </div>

      <div class="upload-bar"><input type="file" ref="fileInput" accept="image/*,video/*,.pdf,.svg" @change="uploadMedia" /></div>
      <div class="media-grid">
        <div v-for="m in media" :key="m.id" class="media-card">
          <div class="media-preview">
            <img v-if="m.content_type?.startsWith('image')" :src="m.url" :alt="m.alt_text||m.filename" />
            <div v-else class="media-file-icon">📄</div>
          </div>
          <div class="media-info">
            <span class="media-name">{{ m.filename }}</span>
            <span class="media-size">{{ (m.size_bytes/1024).toFixed(1) }}KB</span>
          </div>
          <div class="card-actions"><button class="btn-sm btn-copy" @click="copyUrl(m.url)">{{ t('cms_copy_url') }}</button><button @click="deleteMedia(m.id)" class="btn-sm btn-danger">{{ t('cms_delete') }}</button></div>
        </div>
      </div>
      <div v-if="!media.length" class="empty-state">
        <div class="empty-icon">🖼️</div>
        <p class="empty-title">{{ t('cms_empty_media') }}</p>
        <p class="empty-hint">{{ t('cms_media_empty_hint') }}</p>
      </div>
    </template>

    <!-- ═══ AUDIT ═══ -->
    <template v-if="currentTab==='audit' && !loading">
      <div class="tab-help">
        <div class="help-icon">📋</div>
        <div>
          <strong>{{ t('cms_audit_help_title') }}</strong>
          <p>{{ t('cms_audit_help_text') }}</p>
        </div>
      </div>

      <div class="audit-list">
        <div v-for="a in audit" :key="a.id" class="audit-row">
          <span class="audit-action">{{ a.action }}</span>
          <span class="audit-entity">{{ a.entity_type }} #{{ a.entity_id }}</span>
          <span class="audit-date">{{ fmtDate(a.created_at) }}</span>
        </div>
      </div>
      <p v-if="!audit.length" class="empty">{{ t('cms_empty_audit') }}</p>
    </template>

    <!-- ═══ MODALS ═══ -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="modal || showQuickSetup" class="modal-overlay" @click.self="modal=null; showQuickSetup=false">

          <!-- Quick Setup Modal -->
          <div v-if="showQuickSetup" class="modal modal-lg">
            <h2>⚡ {{ t('cms_quick_setup') }}</h2>
            <p class="modal-desc">{{ t('cms_quick_setup_desc') }}</p>
            <div class="quick-setup-fields">
              <div v-for="p in QUICK_SETUP_PRESETS" :key="p.key" class="field">
                <label>{{ p.label }} <code class="key-hint">{{ p.key }}</code></label>
                <input v-model="quickSetupValues[p.key]" :placeholder="p.placeholder" />
              </div>
            </div>
            <div class="btn-row">
              <button class="btn-save" @click="saveQuickSetup">{{ t('cms_save') }}</button>
              <button class="btn-cancel-modal" @click="showQuickSetup=false">{{ t('cms_cancel') }}</button>
            </div>
          </div>

          <!-- Page Modal -->
          <div v-if="modal==='page'" class="modal modal-lg">
            <h2>{{ editing ? t('cms_edit_page') : t('cms_new_page') }}</h2>
            <p class="modal-desc">{{ t('cms_page_modal_hint') }}</p>
            <div class="form-grid-2">
              <div class="field"><label>{{ t('cms_title') }} (TJ)</label><input v-model="pf.title" /></div>
              <div class="field"><label>{{ t('cms_slug') }} <span class="field-hint">{{ t('cms_slug_hint') }}</span></label><input v-model="pf.slug" placeholder="auto" /></div>
            </div>
            <div class="field"><label>{{ t('cms_description') }} (TJ)</label><textarea v-model="pf.description" rows="3"></textarea></div>
            <div class="form-grid-2">
              <div class="field">
                <label>{{ t('cms_status') }}</label>
                <select v-model="pf.status"><option value="draft">{{ t('cms_status_draft') }}</option><option value="published">{{ t('cms_status_published') }}</option><option value="archived">{{ t('cms_status_archived') }}</option></select>
              </div>
              <div class="field"><label>&nbsp;</label><label class="check"><input type="checkbox" v-model="pf.show_in_nav" /> {{ t('cms_show_in_nav') }}</label></div>
            </div>
            <details class="section-box"><summary>🌐 {{ t('cms_translations') }}</summary>
              <div class="tr-block"><span class="tr-lang">🇷🇺 {{ t('cms_translation_ru') }}</span>
                <div class="form-grid-2"><div class="field"><label>{{ t('cms_title') }}</label><input v-model="pf.tr_ru_title" /></div><div class="field"><label>{{ t('cms_description') }}</label><input v-model="pf.tr_ru_description" /></div></div>
              </div>
              <div class="tr-block"><span class="tr-lang">🇬🇧 {{ t('cms_translation_en') }}</span>
                <div class="form-grid-2"><div class="field"><label>{{ t('cms_title') }}</label><input v-model="pf.tr_en_title" /></div><div class="field"><label>{{ t('cms_description') }}</label><input v-model="pf.tr_en_description" /></div></div>
              </div>
            </details>
            <details class="section-box"><summary>🔍 {{ t('cms_seo_settings') }}</summary>
              <div class="form-grid-2"><div class="field"><label>{{ t('cms_meta_title') }}</label><input v-model="pf.meta_title" /></div><div class="field"><label>{{ t('cms_meta_description') }}</label><input v-model="pf.meta_description" /></div></div>
              <label class="check"><input type="checkbox" v-model="pf.robots_index" /> {{ t('cms_robots_index') }}</label>
            </details>
            <div class="btn-row"><button class="btn-save" @click="savePage">{{ t('cms_save') }}</button><button class="btn-cancel-modal" @click="modal=null">{{ t('cms_cancel') }}</button></div>
          </div>

          <!-- News Modal -->
          <div v-if="modal==='news'" class="modal modal-lg">
            <h2>{{ editing ? t('cms_edit_news') : t('cms_new_news') }}</h2>
            <div class="form-grid-2">
              <div class="field"><label>{{ t('cms_title') }} (TJ)</label><input v-model="nf.title" /></div>
              <div class="field"><label>{{ t('cms_slug') }}</label><input v-model="nf.slug" placeholder="auto" /></div>
            </div>
            <div class="field"><label>{{ t('cms_summary') }} (TJ)</label><input v-model="nf.summary" /></div>
            <div class="field"><label>{{ t('cms_content') }} (TJ, HTML)</label><textarea v-model="nf.content" rows="6"></textarea></div>
            <div class="form-grid-2">
              <div class="field"><label>{{ t('cms_image_url') }}</label><input v-model="nf.image_url" placeholder="https://..." /></div>
              <div class="field"><label>{{ t('cms_status') }}</label><select v-model="nf.status"><option value="draft">{{ t('cms_status_draft') }}</option><option value="published">{{ t('cms_status_published') }}</option></select></div>
            </div>
            <label class="check"><input type="checkbox" v-model="nf.pinned" /> {{ t('cms_pinned') }}</label>
            <details class="section-box"><summary>🌐 {{ t('cms_translations') }}</summary>
              <div class="tr-block"><span class="tr-lang">🇷🇺 {{ t('cms_translation_ru') }}</span>
                <div class="field"><label>{{ t('cms_title') }}</label><input v-model="nf.tr_ru_title" /></div>
                <div class="field"><label>{{ t('cms_summary') }}</label><input v-model="nf.tr_ru_summary" /></div>
                <div class="field"><label>{{ t('cms_content') }}</label><textarea v-model="nf.tr_ru_content" rows="3"></textarea></div>
              </div>
              <div class="tr-block"><span class="tr-lang">🇬🇧 {{ t('cms_translation_en') }}</span>
                <div class="field"><label>{{ t('cms_title') }}</label><input v-model="nf.tr_en_title" /></div>
                <div class="field"><label>{{ t('cms_summary') }}</label><input v-model="nf.tr_en_summary" /></div>
                <div class="field"><label>{{ t('cms_content') }}</label><textarea v-model="nf.tr_en_content" rows="3"></textarea></div>
              </div>
            </details>
            <div class="btn-row"><button class="btn-save" @click="saveNews">{{ t('cms_save') }}</button><button class="btn-cancel-modal" @click="modal=null">{{ t('cms_cancel') }}</button></div>
          </div>

          <!-- Menu Modal -->
          <div v-if="modal==='menu'" class="modal">
            <h2>{{ editing ? t('cms_edit_menu') : t('cms_new_menu') }}</h2>
            <p class="modal-desc">{{ t('cms_menu_modal_hint') }}</p>
            <div class="field"><label>{{ t('cms_menu_label') }} <span class="field-hint">{{ t('cms_menu_label_hint') }}</span></label><input v-model="mf.label" :placeholder="t('cms_menu_label_placeholder')" /></div>
            <div class="field"><label>{{ t('cms_menu_url') }} <span class="field-hint">{{ t('cms_menu_url_hint') }}</span></label><input v-model="mf.url" placeholder="/products" /></div>
            <div class="form-grid-2">
              <div class="field"><label>{{ t('cms_menu_location') }}</label>
                <select v-model="mf.location">
                  <option value="header">{{ t('cms_loc_header') }} — {{ t('cms_menu_header_hint') }}</option>
                  <option value="footer">{{ t('cms_loc_footer') }} — {{ t('cms_menu_footer_hint') }}</option>
                  <option value="sidebar">{{ t('cms_loc_sidebar') }} — {{ t('cms_menu_sidebar_hint') }}</option>
                </select>
              </div>
              <div class="field"><label>{{ t('cms_menu_sort') }} <span class="field-hint">{{ t('cms_menu_sort_hint') }}</span></label><input v-model.number="mf.sort_order" type="number" /></div>
            </div>
            <div class="check-row">
              <label class="check"><input type="checkbox" v-model="mf.is_active" /> {{ t('cms_menu_active') }}</label>
              <label class="check"><input type="checkbox" v-model="mf.open_new_tab" /> {{ t('cms_menu_new_tab') }}</label>
            </div>
            <div class="field"><label>{{ t('cms_menu_icon') }}</label><input v-model="mf.icon" placeholder="🏠" /></div>
            <div class="btn-row"><button class="btn-save" @click="saveMenu">{{ t('cms_save') }}</button><button class="btn-cancel-modal" @click="modal=null">{{ t('cms_cancel') }}</button></div>
          </div>

          <!-- Setting Modal -->
          <div v-if="modal==='setting'" class="modal">
            <h2>{{ editing ? t('cms_edit_setting') : t('cms_new_setting') }}</h2>
            <div class="form-grid-2">
              <div class="field"><label>{{ t('cms_setting_key') }} <span class="field-hint">{{ t('cms_setting_key_hint') }}</span></label><input v-model="sf.key" :disabled="!!editing" placeholder="site_name" /></div>
              <div class="field">
                <label>{{ t('cms_setting_group') }}</label>
                <select v-model="sf.group_name">
                  <option v-for="g in settingGroups" :key="g.key" :value="g.key">{{ g.icon }} {{ t(g.i18n) }}</option>
                </select>
              </div>
            </div>
            <div class="field"><label>{{ t('cms_setting_label') }} <span class="field-hint">{{ t('cms_setting_label_hint') }}</span></label><input v-model="sf.label" :placeholder="t('cms_setting_label')" /></div>
            <div class="field">
              <label>{{ t('cms_setting_type') }}</label>
              <select v-model="sf.value_type">
                <option value="text">{{ t('cms_value_type_text') }}</option>
                <option value="number">{{ t('cms_value_type_number') }}</option>
                <option value="boolean">{{ t('cms_value_type_boolean') }}</option>
                <option value="json">{{ t('cms_value_type_json') }}</option>
                <option value="url">{{ t('cms_value_type_url') }}</option>
                <option value="html">{{ t('cms_value_type_html') }}</option>
                <option value="color">{{ t('cms_value_type_color') }}</option>
              </select>
            </div>
            <div class="field">
              <label>{{ t('cms_setting_value') }}</label>
              <input v-if="sf.value_type==='color'" v-model="sf.value" type="color" class="color-input" />
              <select v-else-if="sf.value_type==='boolean'" v-model="sf.value">
                <option value="true">✓ True</option>
                <option value="false">✕ False</option>
              </select>
              <input v-else-if="sf.value_type==='number'" v-model="sf.value" type="number" />
              <textarea v-else-if="sf.value_type==='json' || sf.value_type==='html'" v-model="sf.value" rows="5" class="mono"></textarea>
              <input v-else v-model="sf.value" />
            </div>
            <div class="btn-row"><button class="btn-save" @click="saveSetting">{{ t('cms_save') }}</button><button class="btn-cancel-modal" @click="modal=null">{{ t('cms_cancel') }}</button></div>
          </div>

        </div>
      </Transition>
    </Teleport>

    <!-- Toast -->
    <Transition name="toast-anim">
      <div v-if="toast" class="toast" :class="toastType">{{ toast }}</div>
    </Transition>
  </div>
</template>

<style scoped>
.page{max-width:960px;margin:0 auto;padding:16px 16px 100px}
h1{font-size:20px;font-weight:800;margin-bottom:16px}
.tabs{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap}
.tab{padding:8px 14px;border:2px solid var(--border);border-radius:10px;background:var(--surface);cursor:pointer;font-weight:600;font-size:13px;color:var(--text);transition:all .15s;display:flex;align-items:center;gap:4px}
.tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.tab:hover:not(.active){background:var(--bg)}
.tab-icon{font-size:14px}
.loading{text-align:center;padding:40px;color:var(--muted)}
.empty{text-align:center;padding:40px;color:var(--muted);font-style:italic}

/* Tab help banner */
.tab-help{display:flex;gap:12px;align-items:flex-start;background:var(--accent-bg, rgba(37,99,235,.06));border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:16px}
.tab-help .help-icon{font-size:28px;flex-shrink:0;margin-top:2px}
.tab-help strong{display:block;font-size:14px;margin-bottom:4px;color:var(--text)}
.tab-help p{font-size:13px;color:var(--muted);line-height:1.5;margin:0}

/* Empty state */
.empty-state{text-align:center;padding:40px 20px;background:var(--surface);border:2px dashed var(--border);border-radius:16px;margin-top:12px}
.empty-icon{font-size:48px;margin-bottom:12px}
.empty-title{font-size:16px;font-weight:700;color:var(--text);margin-bottom:6px}
.empty-hint{font-size:13px;color:var(--muted);margin-bottom:16px;max-width:400px;margin-left:auto;margin-right:auto;line-height:1.5}

.btn-add{background:var(--accent);color:#fff;border:none;padding:8px 16px;border-radius:8px;font-weight:600;cursor:pointer;margin-bottom:12px;font-size:13px}
.btn-add:hover{opacity:.9}
.btn-quick{background:linear-gradient(135deg,#f59e0b,#ef4444);margin-right:8px}

.card-list{display:flex;flex-direction:column;gap:8px;margin-bottom:16px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;transition:border-color .15s}
.card:hover{border-color:var(--accent)}
.card-flat{border-radius:8px;padding:10px 14px}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.card-top strong{font-size:15px}
.slug{color:var(--muted);font-size:12px;margin-left:4px}
.card-meta{display:flex;flex-wrap:wrap;gap:8px;font-size:12px;color:var(--muted);margin-top:6px}
.card-actions{display:flex;gap:6px;margin-top:8px}
.badge{padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700}
.badge-pub{background:rgba(22,163,74,.1);color:#16a34a}
.badge-draft{background:rgba(234,179,8,.1);color:#ca8a04}
.badge-loc{background:var(--accent-bg,rgba(37,99,235,.08));color:var(--accent)}
.badge-type{background:rgba(139,92,246,.1);color:#7c3aed}
.tag{padding:2px 6px;background:var(--accent-bg,rgba(37,99,235,.08));color:var(--accent);border-radius:4px;font-size:11px;font-weight:600}
.tag-off{padding:2px 6px;background:var(--bg);color:var(--muted);border-radius:4px;font-size:11px}
.pin{margin-left:4px}
.summary{color:var(--text);font-style:italic}
.setting-val{font-family:monospace;font-size:12px;color:var(--text);word-break:break-all}
.menu-icon-preview{margin-right:4px}

.btn-sm{padding:4px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);cursor:pointer;font-size:12px;font-weight:600;color:var(--text);transition:all .15s}
.btn-sm:hover{background:var(--accent-bg,rgba(37,99,235,.08))}
.btn-danger{color:#ef4444;border-color:rgba(239,68,68,.3)}
.btn-danger:hover{background:rgba(239,68,68,.08)}
.btn-copy{color:var(--accent)}

/* Menu location hints */
.menu-locations-hint{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}
.loc-hint{display:flex;align-items:center;gap:6px;padding:8px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:12px;color:var(--muted);flex:1;min-width:200px}
.loc-badge{padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;flex-shrink:0}
.loc-header{background:rgba(37,99,235,.1);color:#2563eb}
.loc-footer{background:rgba(22,163,74,.1);color:#16a34a}
.loc-sidebar{background:rgba(139,92,246,.1);color:#7c3aed}
.loc-count{background:var(--bg);padding:1px 6px;border-radius:8px;font-size:10px;font-weight:700;margin-left:auto}

/* Settings groups */
.settings-top{display:flex;justify-content:flex-start;align-items:center;margin-bottom:8px;gap:8px}
.group-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.chip{padding:6px 12px;border:2px solid var(--border);border-radius:20px;background:var(--surface);cursor:pointer;font-size:12px;font-weight:600;color:var(--text);display:flex;align-items:center;gap:4px;transition:all .15s}
.chip.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.chip:hover:not(.active){background:var(--bg)}
.chip-icon{font-size:13px}
.chip-count{background:rgba(0,0,0,.1);padding:1px 6px;border-radius:10px;font-size:10px;font-weight:700}
.chip.active .chip-count{background:rgba(255,255,255,.25)}

.settings-group{margin-bottom:20px}
.group-header{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:2px solid var(--border);margin-bottom:8px}
.group-icon{font-size:18px}
.group-title{font-size:15px;font-weight:700;color:var(--text)}
.group-count{background:var(--accent-bg,rgba(37,99,235,.08));color:var(--accent);padding:1px 8px;border-radius:10px;font-size:11px;font-weight:700}

/* Quick setup */
.quick-setup-fields{display:flex;flex-direction:column;gap:4px}
.key-hint{font-size:10px;color:var(--muted);background:var(--bg);padding:1px 6px;border-radius:4px;margin-left:6px}

/* Media */
.upload-bar{margin-bottom:16px}
.upload-bar input{font-size:14px}
.media-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
.media-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.media-preview{height:120px;background:var(--bg);display:flex;align-items:center;justify-content:center;overflow:hidden}
.media-preview img{width:100%;height:100%;object-fit:cover}
.media-file-icon{font-size:40px}
.media-info{padding:8px 10px}
.media-name{font-size:12px;font-weight:600;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.media-size{font-size:11px;color:var(--muted)}
.media-card .card-actions{padding:0 10px 8px;justify-content:space-between}

/* Audit */
.audit-list{display:flex;flex-direction:column;gap:4px}
.audit-row{display:flex;gap:12px;padding:8px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:13px;align-items:center}
.audit-action{font-weight:700;color:var(--accent);min-width:100px}
.audit-entity{flex:1;color:var(--text)}
.audit-date{color:var(--muted);font-size:12px}

/* Modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:20000;display:flex;align-items:center;justify-content:center;padding:16px}
.modal{background:var(--surface);border-radius:16px;padding:24px;width:100%;max-width:500px;max-height:90vh;overflow-y:auto}
.modal-lg{max-width:640px}
.modal h2{margin:0 0 8px;font-size:18px}
.modal-desc{font-size:13px;color:var(--muted);margin:0 0 16px;line-height:1.5}
.modal-fade-enter-active,.modal-fade-leave-active{transition:opacity .2s ease}
.modal-fade-enter-from,.modal-fade-leave-to{opacity:0}

.field{margin-bottom:12px}
.field label{display:block;font-size:12px;font-weight:600;color:var(--muted);margin-bottom:4px}
.field-hint{font-weight:400;font-size:11px;color:var(--muted);opacity:.7}
.field input,.field select,.field textarea{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:14px;font-family:inherit;box-sizing:border-box}
.field textarea{resize:vertical}
.mono{font-family:monospace;font-size:13px}
.color-input{height:44px;padding:4px;cursor:pointer}
.form-grid-2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:500px){.form-grid-2{grid-template-columns:1fr}}
.check{display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer}
.check-row{display:flex;gap:16px;margin-bottom:12px}
.section-box{margin-bottom:12px;border:1px solid var(--border);border-radius:8px;padding:8px 12px}
.section-box summary{cursor:pointer;font-size:13px;font-weight:600;color:var(--accent)}
.section-box[open] summary{margin-bottom:8px}
.tr-block{margin-bottom:12px;padding:8px;background:var(--bg);border-radius:8px}
.tr-lang{font-size:12px;font-weight:700;display:block;margin-bottom:6px}
.btn-row{display:flex;gap:8px;margin-top:16px}
.btn-save{flex:1;padding:10px;background:var(--accent);color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:14px}
.btn-save:hover{opacity:.9}
.btn-cancel-modal{flex:1;padding:10px;background:var(--bg);border:1px solid var(--border);border-radius:8px;cursor:pointer;color:var(--text);font-size:14px}

/* Toast */
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);padding:10px 20px;border-radius:10px;font-size:13px;font-weight:600;z-index:25000;box-shadow:0 4px 16px rgba(0,0,0,.15)}
.toast.ok{background:#059669;color:#fff}
.toast.err{background:#ef4444;color:#fff}
.toast-anim-enter-active{animation:toast-in .3s ease}
.toast-anim-leave-active{animation:toast-in .2s ease reverse}
@keyframes toast-in{from{opacity:0;transform:translateX(-50%) translateY(10px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}

@media(max-width:500px){
  .tabs{gap:4px}
  .tab{padding:6px 10px;font-size:12px}
  .group-chips{gap:4px}
  .chip{padding:4px 8px;font-size:11px}
  .menu-locations-hint{flex-direction:column}
}
</style>
