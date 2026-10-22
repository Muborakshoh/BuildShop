<script setup>
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import TopBar from './components/TopBar.vue'
import BottomNav from './components/BottomNav.vue'
import Toast from './components/Toast.vue'
import FooterBar from './components/FooterBar.vue'
import { useSettingsStore } from './stores/settings'
import { useAuthStore } from './stores/auth'
import i18n from './i18n'

const settings = useSettingsStore()
const auth = useAuthStore()
const route = useRoute()
const showFooter = computed(() => route.path !== '/guide')

onMounted(async () => {
  const savedLang = localStorage.getItem('lang') || 'tj'
  settings.setTheme(localStorage.getItem('theme') || 'light')
  settings.setLang(savedLang)
  i18n.global.locale.value = savedLang
  settings.loadSiteSettings()
  if (localStorage.getItem('access_token')) {
    auth.token = localStorage.getItem('access_token')
    try { await auth.getMe() } catch { auth.logout() }
  }
})
</script>
<template>
  <TopBar />
  <main class="app-main">
    <router-view />
  </main>
  <FooterBar v-if="showFooter" />
  <BottomNav />
  <Toast />
</template>
<style scoped>
.app-main {
  min-height: calc(100vh - 52px - 68px);
  padding-bottom: 80px;
}
</style>
