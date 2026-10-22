<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { api } from '@/utils/api'
import { money } from '@/utils/helpers'
import i18n from '@/i18n'

const auth = useAuthStore()
const settings = useSettingsStore()
const { t } = useI18n()
const router = useRouter()

const loading = ref(true)
const stats = ref(null)
const recentOrders = ref([])
const lowStock = ref([])
const showSettings = ref(false)
const showInfo = ref(false)
const fontSize = ref(localStorage.getItem('fontSize') || '16')

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return t('greeting_night')
  if (h < 12) return t('greeting_morning')
  if (h < 18) return t('greeting_afternoon')
  return t('greeting_evening')
})

const adminSections = [
  { to: '/admin/products', icon: 'box', label: 'admin_products', desc: 'admin_products_desc', color: '#2563eb' },
  { to: '/admin/analytics', icon: 'chart', label: 'nav_analytics', desc: 'admin_analytics_desc', color: '#8b5cf6' },
  { to: '/admin/users', icon: 'users', label: 'admin_users', desc: 'admin_users_desc', color: '#059669' },
  { to: '/admin/cms', icon: 'layout', label: 'admin_cms', desc: 'admin_cms_desc', color: '#d97706' },
  { to: '/cashier', icon: 'cashier', label: 'nav_cashier', desc: 'admin_cashier_desc', color: '#dc2626' },
]

const iconSvgs = {
  box: 'M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z',
  chart: 'M18 20V10M12 20V4M6 20v-6',
  users: 'M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 7a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75',
  layout: 'M3 3h18a2 2 0 012 2v14a2 2 0 01-2 2H3a2 2 0 01-2-2V5a2 2 0 012-2zM3 9h18M9 21V9',
  cashier: 'M2 4h20v16H2zM2 10h20M6 14h4',
}

const statusColors = {
  CREATED: '#6b7280', created: '#6b7280',
  CONFIRMED: '#2563eb', confirmed: '#2563eb',
  ASSEMBLING: '#d97706', assembling: '#d97706',
  DELIVERING: '#8b5cf6', delivering: '#8b5cf6',
  DELIVERED: '#059669', delivered: '#059669',
  CANCELLED: '#dc2626', cancelled: '#dc2626',
}

onMounted(async () => {
  try {
    const [dashboard, orders, products] = await Promise.all([
      api.get('/cms/reports/dashboard').catch(() => ({ products: 0, users: 0, orders: 0 })),
      api.get('/orders?limit=10').catch(() => []),
      api.get('/products?limit=500').catch(() => [])
    ])
    const revenue = orders.reduce((s, o) => s + parseFloat(o.total_amount || 0), 0)
    const todayOrders = orders.filter(o => {
      const d = new Date(o.created_at)
      const now = new Date()
      return d.toDateString() === now.toDateString()
    })
    lowStock.value = products.filter(p => p.stock_quantity <= 5 && p.stock_quantity >= 0).sort((a, b) => a.stock_quantity - b.stock_quantity).slice(0, 5)
    recentOrders.value = orders.slice(0, 5)
    stats.value = {
      products: dashboard.products || products.length,
      orders: dashboard.orders || orders.length,
      revenue,
      todayOrders: todayOrders.length,
      users: dashboard.users || 0,
      avgCheck: orders.length ? revenue / orders.length : 0,
      popularProducts: dashboard.popular_products || []
    }
  } catch (e) { console.error(e) }
  loading.value = false
})

function changeLang(val) {
  settings.setLang(val)
  i18n.global.locale.value = val
}
function changeFontSize(val) {
  fontSize.value = val
  localStorage.setItem('fontSize', val)
  document.documentElement.style.fontSize = val + 'px'
}
function doLogout() {
  auth.logout()
  router.push('/')
}
function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="admin-dash">
    <!-- Header area with gradient -->
    <div class="dash-header">
      <div class="dash-header-top">
        <div>
          <div class="greeting">{{ greeting }},</div>
          <div class="user-name">{{ auth.user?.full_name || 'User' }}</div>
          <div class="user-role">{{ auth.user?.role || '' }}</div>
        </div>
        <div class="header-actions">
          <button class="action-btn" @click="router.push('/')" title="Back to site">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          </button>
          <button class="action-btn" @click="showSettings = !showSettings" :class="{active: showSettings}">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          </button>
          <button class="action-btn logout-btn" @click="doLogout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      </div>

      <!-- Settings panel (collapsible) -->
      <Transition name="slide-settings">
        <div v-if="showSettings" class="settings-panel">
          <div class="settings-row">
            <span class="settings-label">{{ t('theme') }}</span>
            <div class="settings-btns">
              <button :class="['s-btn',{active:settings.theme==='light'}]" @click="settings.setTheme('light')">☀️</button>
              <button :class="['s-btn',{active:settings.theme==='dark'}]" @click="settings.setTheme('dark')">🌙</button>
            </div>
          </div>
          <div class="settings-row">
            <span class="settings-label">{{ t('font_size') }}</span>
            <div class="settings-btns">
              <button v-for="s in [{v:'14',l:'A'},{v:'16',l:'A'},{v:'18',l:'A'}]" :key="s.v"
                :class="['s-btn',{active:fontSize===s.v}]"
                :style="{fontSize:s.v+'px'}" @click="changeFontSize(s.v)">{{ s.l }}</button>
            </div>
          </div>
          <div class="settings-row">
            <span class="settings-label">{{ t('language') }}</span>
            <div class="settings-btns">
              <button v-for="l in [{v:'tj',l:'TJ'},{v:'ru',l:'RU'},{v:'en',l:'EN'}]" :key="l.v"
                :class="['s-btn lang',{active:settings.lang===l.v}]" @click="changeLang(l.v)">{{ l.l }}</button>
            </div>
          </div>
          <!-- Info -->
          <button class="info-toggle" @click="showInfo=!showInfo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>{{ t('site_info') }}</span>
            <svg :class="['chev',{open:showInfo}]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          <Transition name="slide-info">
            <div v-if="showInfo" class="info-block">
              <div class="info-r"><span>{{ t('project_name') }}</span><strong>СохтМатериал</strong></div>
              <div class="info-r"><span>{{ t('version') }}</span><strong>2.0.0 (Vue)</strong></div>
              <div class="info-r"><span>{{ t('company') }}</span><strong>BuildShop LLC</strong></div>
              <div class="info-r"><span>Backend</span><strong>FastAPI + PostgreSQL</strong></div>
              <div class="info-r"><span>Frontend</span><strong>Vue 3 + Vite</strong></div>
            </div>
          </Transition>
        </div>
      </Transition>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ t('loading') }}</span>
    </div>

    <template v-else>
      <!-- Stats cards -->
      <div class="stats-grid" v-if="stats">
        <div class="stat-card blue">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>
          </div>
          <div class="stat-value">{{ stats.products }}</div>
          <div class="stat-label">{{ t('products') }}</div>
        </div>
        <div class="stat-card purple">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/><path d="M20 8v6M23 11h-6"/></svg>
          </div>
          <div class="stat-value">{{ stats.users }}</div>
          <div class="stat-label">{{ t('users') }}</div>
        </div>
        <div class="stat-card green">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
          </div>
          <div class="stat-value">{{ stats.orders }}</div>
          <div class="stat-label">{{ t('orders') }}</div>
        </div>
        <div class="stat-card amber">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
          </div>
          <div class="stat-value">{{ money(stats.revenue) }}</div>
          <div class="stat-label">{{ t('revenue') }}</div>
        </div>
      </div>

      <!-- Quick actions (admin only) -->
      <template v-if="auth.isAdmin">
        <h2 class="section-title">{{ t('quick_actions') }}</h2>
        <div class="actions-grid">
          <router-link v-for="sec in adminSections" :key="sec.to" :to="sec.to" class="action-card">
            <div class="action-icon" :style="{background: sec.color + '14', color: sec.color}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path :d="iconSvgs[sec.icon]"/></svg>
            </div>
            <div class="action-text">
              <span class="action-title">{{ t(sec.label) }}</span>
              <span class="action-desc">{{ t(sec.desc) }}</span>
            </div>
            <svg class="action-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </router-link>
        </div>
      </template>

      <!-- User quick links (for non-admin users) -->
      <template v-if="!auth.isAdmin">
        <h2 class="section-title">{{ t('quick_actions') }}</h2>
        <div class="actions-grid">
          <router-link to="/orders" class="action-card">
            <div class="action-icon" style="background:rgba(37,99,235,.1);color:#2563eb">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
            </div>
            <div class="action-text">
              <span class="action-title">{{ t('orders') }}</span>
            </div>
            <svg class="action-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </router-link>
          <router-link to="/cart" class="action-card">
            <div class="action-icon" style="background:rgba(5,150,105,.1);color:#059669">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>
            </div>
            <div class="action-text">
              <span class="action-title">{{ t('nav_cart') }}</span>
            </div>
            <svg class="action-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </router-link>
          <router-link to="/calculator" class="action-card">
            <div class="action-icon" style="background:rgba(217,119,6,.1);color:#d97706">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="10" y2="10"/><line x1="14" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="10" y2="14"/><line x1="14" y1="14" x2="16" y2="14"/><line x1="8" y1="18" x2="16" y2="18"/></svg>
            </div>
            <div class="action-text">
              <span class="action-title">{{ t('nav_calculator') }}</span>
            </div>
            <svg class="action-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </router-link>
        </div>
      </template>

      <!-- Two columns: Recent Orders & Low Stock -->
      <div class="two-cols">
        <div class="col-card" v-if="recentOrders.length">
          <div class="col-header">
            <h3>{{ t('recent_orders') }}</h3>
            <router-link to="/orders" class="see-all">{{ t('see_all') }} →</router-link>
          </div>
          <div class="order-list">
            <div v-for="order in recentOrders" :key="order.id" class="order-row">
              <div class="order-id">#{{ order.id }}</div>
              <div class="order-status" :style="{color: statusColors[order.status] || '#6b7280'}">
                {{ order.status }}
              </div>
              <div class="order-amount">{{ money(order.total_amount) }}</div>
              <div class="order-date">{{ formatDate(order.created_at) }}</div>
            </div>
          </div>
        </div>

        <div class="col-card" v-if="lowStock.length">
          <div class="col-header">
            <h3>{{ t('low_stock') }}</h3>
            <router-link to="/admin/products" class="see-all">{{ t('see_all') }} →</router-link>
          </div>
          <div class="stock-list">
            <div v-for="p in lowStock" :key="p.id" class="stock-row">
              <span class="stock-name">{{ p.name }}</span>
              <span class="stock-qty" :class="{'critical': p.stock_quantity <= 2}">{{ p.stock_quantity }} {{ t('pcs') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Top products -->
      <div class="col-card" v-if="stats?.popularProducts?.length">
        <div class="col-header">
          <h3>{{ t('top_products') }}</h3>
        </div>
        <div class="top-list">
          <div v-for="(p, idx) in stats.popularProducts" :key="p.name" class="top-row">
            <div class="top-rank" :class="'rank-'+Math.min(idx+1,4)">{{ idx + 1 }}</div>
            <span class="top-name">{{ p.name }}</span>
            <span class="top-sold">{{ p.sold }} {{ t('pcs') }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.admin-dash{max-width:900px;margin:0 auto;padding:0 16px 100px}

/* Header */
.dash-header{background:linear-gradient(135deg,#2563eb 0%,#0ea5e9 100%);margin:-0px -16px 20px;padding:24px 20px 20px;color:#fff;border-radius:0 0 20px 20px}
.dash-header-top{display:flex;justify-content:space-between;align-items:flex-start}
.greeting{font-size:14px;opacity:.85;font-weight:500}
.user-name{font-size:22px;font-weight:800;margin-top:2px}
.user-role{font-size:12px;opacity:.7;font-weight:500;margin-top:2px;text-transform:capitalize}
.header-actions{display:flex;gap:8px}
.action-btn{width:38px;height:38px;border-radius:12px;border:none;background:rgba(255,255,255,.18);color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .2s;backdrop-filter:blur(4px)}
.action-btn:hover,.action-btn.active{background:rgba(255,255,255,.3)}
.action-btn svg{width:20px;height:20px}
.logout-btn:hover{background:rgba(239,68,68,.6)}

/* Settings panel */
.settings-panel{margin-top:16px;background:rgba(255,255,255,.12);border-radius:14px;padding:12px 14px;backdrop-filter:blur(8px)}
.settings-row{display:flex;align-items:center;justify-content:space-between;padding:6px 0}
.settings-label{font-size:13px;font-weight:600}
.settings-btns{display:flex;gap:4px}
.s-btn{width:34px;height:30px;border:1px solid rgba(255,255,255,.25);border-radius:8px;background:rgba(255,255,255,.1);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:13px;color:#fff;transition:all .15s}
.s-btn.active{background:#fff;color:#2563eb;border-color:#fff;font-weight:700}
.s-btn.lang{width:auto;padding:0 10px;font-weight:600;font-size:12px}
.info-toggle{display:flex;align-items:center;gap:6px;width:100%;padding:8px 0 4px;border:none;background:none;color:#fff;cursor:pointer;font-size:13px;font-weight:600;font-family:inherit}
.info-toggle svg{width:16px;height:16px;flex-shrink:0}
.info-toggle span{flex:1;text-align:left}
.chev{width:14px!important;transition:transform .2s}
.chev.open{transform:rotate(180deg)}
.info-block{padding:8px 0 4px;display:flex;flex-direction:column;gap:3px}
.info-r{display:flex;justify-content:space-between;font-size:12px;padding:2px 0}
.info-r span{opacity:.75}
.info-r strong{font-weight:600}

.slide-settings-enter-active,.slide-settings-leave-active{transition:all .25s ease;overflow:hidden}
.slide-settings-enter-from,.slide-settings-leave-to{max-height:0;opacity:0;margin-top:0;padding:0 14px}
.slide-settings-enter-to,.slide-settings-leave-from{max-height:300px;opacity:1}
.slide-info-enter-active,.slide-info-leave-active{transition:all .2s;overflow:hidden}
.slide-info-enter-from,.slide-info-leave-to{max-height:0;opacity:0}
.slide-info-enter-to,.slide-info-leave-from{max-height:200px;opacity:1}

/* Loading */
.loading-state{display:flex;flex-direction:column;align-items:center;gap:12px;padding:60px 0;color:var(--muted)}
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* Stats */
.stats-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:24px}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:16px;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s}
.stat-card:hover{transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.08)}
.stat-card::before{content:'';position:absolute;top:0;right:0;width:60px;height:60px;border-radius:0 0 0 60px;opacity:.08}
.stat-card.blue::before{background:#2563eb}
.stat-card.purple::before{background:#8b5cf6}
.stat-card.green::before{background:#059669}
.stat-card.amber::before{background:#d97706}
.stat-icon{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:10px}
.stat-icon svg{width:22px;height:22px}
.blue .stat-icon{background:rgba(37,99,235,.1);color:#2563eb}
.blue .stat-icon svg{stroke:#2563eb}
.purple .stat-icon{background:rgba(139,92,246,.1);color:#8b5cf6}
.purple .stat-icon svg{stroke:#8b5cf6}
.green .stat-icon{background:rgba(5,150,105,.1);color:#059669}
.green .stat-icon svg{stroke:#059669}
.amber .stat-icon{background:rgba(217,119,6,.1);color:#d97706}
.amber .stat-icon svg{stroke:#d97706}
.stat-value{font-size:22px;font-weight:800;color:var(--text);line-height:1.2}
.stat-label{font-size:12px;color:var(--muted);margin-top:2px;font-weight:500}

/* Section title */
.section-title{font-size:16px;font-weight:700;margin-bottom:12px;color:var(--text)}

/* Action cards */
.actions-grid{display:flex;flex-direction:column;gap:8px;margin-bottom:24px}
.action-card{display:flex;align-items:center;gap:14px;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-radius:14px;text-decoration:none;color:var(--text);transition:all .2s}
.action-card:hover{border-color:var(--accent);box-shadow:0 2px 12px rgba(37,99,235,.08);transform:translateY(-1px)}
.action-icon{width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.action-icon svg{width:24px;height:24px}
.action-text{flex:1;min-width:0}
.action-title{display:block;font-weight:700;font-size:14px}
.action-desc{display:block;font-size:12px;color:var(--muted);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.action-arrow{width:20px;height:20px;flex-shrink:0;color:var(--muted)}
.action-card:hover .action-arrow{color:var(--accent)}

/* Two columns */
.two-cols{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
@media(max-width:600px){.two-cols{grid-template-columns:1fr}}

.col-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:16px;margin-bottom:12px}
.col-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.col-header h3{margin:0;font-size:15px;font-weight:700}
.see-all{font-size:12px;font-weight:600;color:var(--accent);text-decoration:none}

/* Orders */
.order-list{display:flex;flex-direction:column;gap:0}
.order-row{display:grid;grid-template-columns:auto 1fr auto auto;gap:8px;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.order-row:last-child{border:none}
.order-id{font-weight:700;font-size:12px;color:var(--muted)}
.order-status{font-weight:600;font-size:12px;text-transform:capitalize}
.order-amount{font-weight:700;font-size:13px}
.order-date{font-size:11px;color:var(--muted)}

/* Stock */
.stock-list{display:flex;flex-direction:column}
.stock-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.stock-row:last-child{border:none}
.stock-name{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1;margin-right:8px}
.stock-qty{font-weight:700;color:#d97706;white-space:nowrap}
.stock-qty.critical{color:#dc2626}

/* Top products */
.top-list{display:flex;flex-direction:column}
.top-row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.top-row:last-child{border:none}
.top-rank{width:26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;flex-shrink:0}
.rank-1{background:rgba(37,99,235,.12);color:#2563eb}
.rank-2{background:rgba(139,92,246,.1);color:#8b5cf6}
.rank-3{background:rgba(217,119,6,.1);color:#d97706}
.rank-4{background:var(--bg);color:var(--muted)}
.top-name{flex:1;font-weight:500}
.top-sold{font-weight:700;color:var(--accent)}
</style>
