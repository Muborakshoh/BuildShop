<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ml } from '@/utils/helpers'

const { t } = useI18n()
const settings = ref({})
const footerMenu = ref([])

onMounted(async () => {
  try {
    const [sGeneral, sContacts, menu] = await Promise.all([
      fetch('/api/cms/settings/public?group=general').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/api/cms/settings/public?group=contacts').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/api/cms/menus/public/footer').then(r => r.ok ? r.json() : []).catch(() => [])
    ])
    const map = {}
    if (Array.isArray(sGeneral)) sGeneral.forEach(i => map[i.key] = i.value)
    if (Array.isArray(sContacts)) sContacts.forEach(i => map[i.key] = i.value)
    settings.value = map
    footerMenu.value = menu
  } catch {}
})

const year = new Date().getFullYear()
</script>

<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-col">
        <div class="footer-brand">
          <span class="footer-logo">🏗️</span>
          <span class="footer-name">{{ settings.site_name || 'СохтМатериал' }}</span>
        </div>
        <p class="footer-desc">{{ settings.site_description || t('footer_desc') || 'Мағозаи масолеҳи сохтмонӣ' }}</p>
      </div>

      <div class="footer-col">
        <h4>{{ t('footer_links') || 'Саҳифаҳо' }}</h4>
        <nav class="footer-nav">
          <router-link to="/products">{{ t('products_title') }}</router-link>
          <router-link to="/categories">{{ t('nav_categories') }}</router-link>
          <router-link to="/calculator">{{ t('nav_calculator') }}</router-link>
          <router-link to="/news">{{ t('cms_news') || 'Навигарон' }}</router-link>
          <router-link to="/guide">{{ t('nav_docs') }}</router-link>
        </nav>
      </div>

      <div class="footer-col">
        <h4>{{ t('footer_contact') || 'Тамос' }}</h4>
        <div class="contact-info">
          <p v-if="settings.phone">📞 {{ settings.phone }}</p>
          <p v-if="settings.email">✉️ {{ settings.email }}</p>
          <p v-if="settings.address">📍 {{ settings.address }}</p>
        </div>
      </div>

      <div class="footer-col" v-if="footerMenu.length">
        <h4>{{ t('footer_info') || 'Маълумот' }}</h4>
        <nav class="footer-nav">
          <a v-for="item in footerMenu" :key="item.id" :href="item.url" :target="item.open_new_tab ? '_blank' : '_self'">{{ item.label }}</a>
        </nav>
      </div>
    </div>

    <div class="footer-bottom">
      <p>© {{ year }} {{ settings.site_name || 'СохтМатериал' }}. {{ t('footer_rights') || 'Ҳамаи ҳуқуқҳо маҳфузанд.' }}</p>
    </div>
  </footer>
</template>

<style scoped>
.site-footer{background:var(--surface);border-top:1px solid var(--border);padding:32px 16px 90px;margin-top:40px}
.footer-inner{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px}
.footer-col h4{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--accent);margin-bottom:12px}
.footer-brand{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.footer-logo{font-size:24px}
.footer-name{font-size:16px;font-weight:800}
.footer-desc{font-size:13px;color:var(--muted);line-height:1.5}
.footer-nav{display:flex;flex-direction:column;gap:6px}
.footer-nav a{color:var(--text);text-decoration:none;font-size:13px;transition:color .2s}
.footer-nav a:hover{color:var(--accent)}
.contact-info p{font-size:13px;color:var(--muted);margin:4px 0}
.footer-bottom{max-width:1100px;margin:24px auto 0;padding-top:16px;border-top:1px solid var(--border);text-align:center}
.footer-bottom p{font-size:12px;color:var(--muted)}
@media(max-width:600px){.footer-inner{grid-template-columns:1fr 1fr;gap:16px}}
</style>
