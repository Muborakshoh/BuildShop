<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useCartStore } from '@/stores/cart'
import { useI18n } from 'vue-i18n'
import MorePanel from './MorePanel.vue'

const route = useRoute()
const cart = useCartStore()
const { t } = useI18n()
const showMore = ref(false)

const tabs = [
  { to: '/', icon: 'home', label: 'nav_home' },
  { to: '/products', icon: 'search', label: 'nav_products' },
  { to: '/cart', icon: 'cart', label: 'nav_cart' },
  { to: '/orders', icon: 'orders', label: 'nav_my_orders' },
]

const iconPaths = {
  home: '<path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  search: '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
  cart: '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/>',
  orders: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
}

function isActive(tab) {
  if (tab.to === '/') return route.path === '/'
  return route.path.startsWith(tab.to)
}
</script>

<template>
  <nav class="bnav">
    <router-link v-for="tab in tabs" :key="tab.to" :to="tab.to" :class="['bnav-tab', { 'bnav-tab--active': isActive(tab) }]">
      <!-- Active state: notch + fab -->
      <template v-if="isActive(tab)">
        <div class="bnav-notch"></div>
        <div class="bnav-fab">
          <span v-if="tab.icon==='cart' && cart.count" class="bnav-badge">{{ cart.count }}</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" v-html="iconPaths[tab.icon]"></svg>
        </div>
        <span class="bnav-lbl">{{ t(tab.label) }}</span>
      </template>
      <!-- Inactive state -->
      <template v-else>
        <span v-if="tab.icon==='cart' && cart.count" class="bnav-badge">{{ cart.count }}</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" v-html="iconPaths[tab.icon]"></svg>
      </template>
    </router-link>

    <!-- More button -->
    <button class="bnav-tab bnav-more-btn" @click="showMore=true">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="2" fill="currentColor" stroke="none"/><circle cx="12" cy="19" r="2" fill="currentColor" stroke="none"/></svg>
    </button>

    <MorePanel v-model="showMore" />
  </nav>
</template>

<style scoped>
.bnav{position:fixed;bottom:0;left:0;right:0;z-index:9999;height:60px;display:flex;align-items:stretch;background:var(--surface);box-shadow:0 -2px 20px rgba(0,0,0,.1)}
.bnav-tab{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-decoration:none;color:var(--muted);position:relative;cursor:pointer;border:none;background:none;padding:0;font-family:inherit;transition:color .2s}
.bnav-tab:hover{color:var(--text)}
.bnav-tab svg{width:26px;height:26px}
.bnav-tab--active{color:var(--accent)}

.bnav-notch{position:absolute;top:-24px;left:50%;transform:translateX(-50%);width:72px;height:28px;background:var(--surface);border-radius:36px 36px 0 0;z-index:1}
.bnav-notch::before,.bnav-notch::after{content:'';position:absolute;top:0;width:20px;height:20px;background:transparent}
.bnav-notch::before{left:-20px;border-bottom-right-radius:20px;box-shadow:8px 8px 0 0 var(--surface)}
.bnav-notch::after{right:-20px;border-bottom-left-radius:20px;box-shadow:-8px 8px 0 0 var(--surface)}

.bnav-fab{position:absolute;top:-26px;left:50%;transform:translateX(-50%);width:54px;height:54px;background:var(--accent-gradient);border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(0,0,0,.22);z-index:2}
.bnav-fab svg{width:26px;height:26px;stroke:#fff;stroke-width:2}
.bnav-lbl{position:absolute;bottom:5px;font-size:10px;font-weight:700;color:var(--accent);white-space:nowrap;z-index:3}

.bnav-badge{position:absolute;top:4px;right:calc(50% - 18px);background:#ef4444;color:#fff;font-size:9px;font-weight:800;min-width:16px;height:16px;border-radius:8px;display:flex;align-items:center;justify-content:center;padding:0 4px;z-index:5}
.bnav-fab .bnav-badge{top:-4px;right:-4px}

.bnav-more-btn svg{width:26px;height:26px}
@media(max-width:400px){
  .bnav-fab{width:48px;height:48px;top:-22px}
  .bnav-fab svg{width:22px;height:22px}
  .bnav-notch{width:64px;height:24px;top:-20px}
}
</style>
