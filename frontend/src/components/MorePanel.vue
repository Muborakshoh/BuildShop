<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { ml } from '@/utils/helpers'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue'])
const auth = useAuthStore()
const { t } = useI18n()

const cmsPages = ref([])
const hasNews = ref(false)

onMounted(async () => {
  try {
    const [pages, news] = await Promise.all([
      fetch('/api/cms/pages/public').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/api/cms/news/public?limit=1').then(r => r.ok ? r.json() : []).catch(() => [])
    ])
    cmsPages.value = pages.filter(p => p.show_in_nav)
    hasNews.value = news.length > 0
  } catch {}
})

function close() { emit('update:modelValue', false) }

const staticItems = [
  { to: '/calculator', icon: 'M4 2h16a2 2 0 012 2v16a2 2 0 01-2 2H4a2 2 0 01-2-2V4a2 2 0 012-2zM8 6h8M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01M8 18h4', label: 'nav_calculator' },
  { to: '/categories', icon: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z', label: 'nav_categories' },
  { to: '/guide', icon: 'M4 19.5A2.5 2.5 0 016.5 17H20M4 19.5A2.5 2.5 0 016.5 17H20M4 19.5V4.5A2.5 2.5 0 016.5 2H20v20H6.5A2.5 2.5 0 014 19.5z', label: 'nav_docs' },
]

// Staff items (seller, manager, admin can see)
const staffItems = [
  { to: '/admin/products', icon: 'M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z', label: 'admin_products' },
  { to: '/cashier', icon: 'M2 4h20a2 2 0 012 2v12a2 2 0 01-2 2H2a2 2 0 01-2-2V6a2 2 0 012-2zM2 10h20M6 14h4', label: 'nav_cashier' },
]

// Admin-only items
const adminItems = [
  { to: '/admin/analytics', icon: 'M18 20V10M12 20V4M6 20v-6', label: 'nav_analytics' },
  { to: '/admin/users', icon: 'M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 7a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75', label: 'admin_users' },
  { to: '/admin/cms', icon: 'M3 3h18a2 2 0 012 2v14a2 2 0 01-2 2H3a2 2 0 01-2-2V5a2 2 0 012-2zM3 9h18M9 21V9', label: 'admin_cms' },
]
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="mp-overlay" @click="close"></div>
    </Transition>
    <Transition name="slide">
      <div v-if="modelValue" class="mp-panel">
        <div class="mp-header">
          <span>{{ t('nav_more') || 'Бештар' }}</span>
          <button class="mp-close" @click="close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="mp-grid">
          <router-link v-for="item in staticItems" :key="item.to" :to="item.to" class="mp-item" @click="close">
            <div class="mp-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path :d="item.icon"/></svg></div>
            <span>{{ t(item.label) }}</span>
          </router-link>

          <router-link v-if="hasNews" to="/news" class="mp-item" @click="close">
            <div class="mp-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2"/></svg></div>
            <span>{{ t('cms_news') || 'Навигарон' }}</span>
          </router-link>

          <router-link v-for="page in cmsPages" :key="page.slug" :to="'/page/'+page.slug" class="mp-item" @click="close">
            <div class="mp-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2z"/><line x1="2" y1="10" x2="22" y2="10"/></svg></div>
            <span>{{ ml(page,'title') }}</span>
          </router-link>

          <!-- Profile/Dashboard link -->
          <router-link :to="auth.isLoggedIn ? '/admin' : '/auth'" class="mp-item" @click="close">
            <div class="mp-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>
            <span>{{ auth.isLoggedIn ? (auth.user?.full_name || t('profile')) : t('login') }}</span>
          </router-link>
        </div>

        <!-- Staff section (seller + manager + admin) -->
        <template v-if="auth.isStaff">
          <div class="mp-divider">{{ t('staff_panel') || 'Панели кор' }}</div>
          <div class="mp-grid">
            <router-link v-for="item in staffItems" :key="item.to" :to="item.to" class="mp-item mp-item--staff" @click="close">
              <div class="mp-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path :d="item.icon"/></svg></div>
              <span>{{ t(item.label) }}</span>
            </router-link>
          </div>
        </template>

        <!-- Admin-only section -->
        <template v-if="auth.isAdmin">
          <div class="mp-divider">{{ t('admin_panel') }}</div>
          <div class="mp-grid">
            <router-link v-for="item in adminItems" :key="item.to" :to="item.to" class="mp-item mp-item--admin" @click="close">
              <div class="mp-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path :d="item.icon"/></svg></div>
              <span>{{ t(item.label) }}</span>
            </router-link>
          </div>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.mp-overlay{position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:10000}
.mp-panel{position:fixed;bottom:0;left:0;right:0;background:var(--surface);border-radius:20px 20px 0 0;box-shadow:0 -8px 40px rgba(0,0,0,.18);z-index:10001;padding:0 16px 80px;max-height:70vh;overflow-y:auto}
.mp-header{display:flex;align-items:center;justify-content:space-between;padding:16px 4px 12px;font-size:16px;font-weight:700;color:var(--text)}
.mp-close{background:none;border:none;cursor:pointer;padding:8px;color:var(--muted);border-radius:50%;display:flex}
.mp-close:hover{background:var(--accent-bg)}
.mp-close svg{width:22px;height:22px}
.mp-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.mp-item{display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 8px;border-radius:14px;text-decoration:none;color:var(--text);font-size:12px;font-weight:600;text-align:center;transition:background .2s}
.mp-item:hover{background:var(--accent-bg)}
.mp-icon{width:48px;height:48px;border-radius:14px;background:var(--bg);display:flex;align-items:center;justify-content:center}
.mp-icon svg{width:24px;height:24px}
.mp-item--staff .mp-icon{background:rgba(5,150,105,.08)}
.mp-item--staff{color:#059669}
.mp-item--admin .mp-icon{background:rgba(37,99,235,.08)}
.mp-item--admin{color:var(--accent)}
.mp-divider{grid-column:1/-1;padding:14px 4px 6px;font-size:11px;font-weight:800;color:var(--accent);text-transform:uppercase;letter-spacing:.5px;border-top:1px solid var(--border);margin-top:8px}

.fade-enter-active,.fade-leave-active{transition:opacity .3s}
.fade-enter-from,.fade-leave-to{opacity:0}
.slide-enter-active,.slide-leave-active{transition:transform .3s cubic-bezier(.4,0,.2,1)}
.slide-enter-from,.slide-leave-to{transform:translateY(100%)}

@media(max-width:400px){.mp-grid{grid-template-columns:repeat(3,1fr)}}
</style>
