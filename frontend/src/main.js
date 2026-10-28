import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import i18n from './i18n'
import { useAuthStore } from './stores/auth'
import App from './App.vue'
import './assets/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)

const auth = useAuthStore()
window.authStore = auth  // ✅ для доступа из консоли
auth.init().finally(() => {
  app.mount('#app')
})
