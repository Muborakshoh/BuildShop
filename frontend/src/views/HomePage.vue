<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-content">
        <h1>{{ t('hero_title') }}</h1>
        <p>{{ t('hero_subtitle') }}</p>
        <div class="hero-btns">
          <router-link to="/products" class="btn-primary">{{ t('hero_cta') }}</router-link>
          <router-link to="/calculator" class="btn-outline">{{ t('nav_calculator') }}</router-link>
        </div>
      </div>
    </section>

    <!-- Stats bar -->
    <section class="stats-bar">
      <div class="stat" v-for="stat in stats" :key="stat.label">
        <span class="stat-value">{{ stat.value }}</span>
        <span class="stat-label">{{ stat.label }}</span>
      </div>
    </section>

    <!-- Categories -->
    <section class="section">
      <h2 class="section-title">{{ t('home_categories') }}</h2>
      <div class="categories-grid">
        <router-link v-for="cat in categories" :key="cat.id" :to="`/products?category=${cat.id}`" class="category-card">
          <div class="category-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>
          </div>
          <span>{{ ml(cat, 'name') }}</span>
          <span class="cat-count" v-if="catCounts[cat.id]">{{ catCounts[cat.id] }} {{ t('pcs') }}</span>
        </router-link>
      </div>
    </section>

    <!-- Popular products -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">{{ t('home_popular') }}</h2>
        <router-link to="/products" class="see-all">{{ t('see_all') }} →</router-link>
      </div>
      <div class="products-grid">
        <router-link v-for="p in products" :key="p.id" :to="`/products/${p.id}`" class="product-card">
          <div class="product-img">
            <img v-if="p.image_url" :src="p.image_url" :alt="ml(p, 'name')" loading="lazy" />
            <div v-else class="img-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
            </div>
            <span class="product-badge" v-if="p.stock_quantity <= 0">{{ t('out_of_stock') || 'Нест' }}</span>
          </div>
          <div class="product-info">
            <h3>{{ ml(p, 'name') }}</h3>
            <div class="price-row">
              <span class="price">{{ money(p.price) }}</span>
              <span class="unit" v-if="p.unit">/ {{ p.unit }}</span>
            </div>
          </div>
        </router-link>
      </div>
    </section>

    <!-- News preview -->
    <section class="section" v-if="news.length">
      <div class="section-header">
        <h2 class="section-title">{{ t('cms_news') || 'Навигарон' }}</h2>
        <router-link to="/news" class="see-all">{{ t('see_all') }} →</router-link>
      </div>
      <div class="news-grid">
        <router-link v-for="n in news" :key="n.id" :to="`/news`" class="news-card">
          <img v-if="n.image_url" :src="n.image_url" class="news-img" loading="lazy" />
          <div class="news-body">
            <h3>{{ ml(n, 'title') || n.title }}</h3>
            <p>{{ n.summary || '' }}</p>
            <span class="news-date">{{ formatDate(n.created_at) }}</span>
          </div>
        </router-link>
      </div>
    </section>

    <!-- Features / Why us -->
    <section class="section features-section">
      <h2 class="section-title">{{ t('why_us') || 'Чаро мо?' }}</h2>
      <div class="features-grid">
        <div class="feature-card" v-for="f in features" :key="f.icon">
          <div class="feature-icon" v-html="f.icon"></div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Contact section -->
    <section class="section contact-section">
      <div class="contact-inner">
        <div class="contact-info">
          <h2>{{ t('contact_us') || 'Тамос бо мо' }}</h2>
          <p>{{ t('contact_desc') || 'Саволе доред? Бо мо тамос гиред!' }}</p>
          <div class="contact-details" v-if="siteSettings.phone || siteSettings.address">
            <p v-if="siteSettings.phone">📞 {{ siteSettings.phone }}</p>
            <p v-if="siteSettings.email">✉️ {{ siteSettings.email }}</p>
            <p v-if="siteSettings.address">📍 {{ siteSettings.address }}</p>
            <p v-if="siteSettings.work_hours">🕐 {{ siteSettings.work_hours }}</p>
          </div>
        </div>
        <form class="contact-form" @submit.prevent="submitContact">
          <input v-model="contactForm.name" :placeholder="t('your_name') || 'Номи шумо'" required />
          <input v-model="contactForm.phone" :placeholder="t('your_phone') || 'Телефон'" required />
          <textarea v-model="contactForm.message" :placeholder="t('your_message') || 'Паём'" rows="3"></textarea>
          <button type="submit" :disabled="contactSending">{{ contactSent ? '✓' : (t('send') || 'Фиристодан') }}</button>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'
import { money, ml } from '@/utils/helpers'

const { t, locale } = useI18n()

const categories = ref([])
const products = ref([])
const news = ref([])
const siteSettings = ref({})
const catCounts = ref({})

const contactForm = ref({ name:'', phone:'', message:'' })
const contactSending = ref(false)
const contactSent = ref(false)

const stats = computed(() => [
  { value: categories.value.length + '+', label: t('home_statCategories') },
  { value: products.value.length + '+', label: t('home_statProducts') },
  { value: '24/7', label: t('home_statSupport') },
  { value: '🚚', label: t('home_statDelivery') }
])

const features = computed(() => {
  const lang = locale.value || 'tj'
  const data = {
    tj: [
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>', title:'Сифати баланд', desc:'Танҳо масолеҳи сертификатсияшуда' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>', title:'Расонидани тез', desc:'Дар ҳамон рӯз ё рӯзи дигар' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>', title:'Нархи арзон', desc:'Нархи рақобатӣ ва тахфифҳо' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>', title:'Маслиҳати касбӣ', desc:'Мутахассисони мо ёрӣ мерасонанд' },
    ],
    ru: [
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>', title:'Высокое качество', desc:'Только сертифицированные материалы' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>', title:'Быстрая доставка', desc:'В тот же день или на следующий' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>', title:'Лучшие цены', desc:'Конкурентные цены и скидки' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>', title:'Консультации', desc:'Наши специалисты помогут вам' },
    ],
    en: [
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>', title:'High Quality', desc:'Only certified materials' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>', title:'Fast Delivery', desc:'Same day or next day delivery' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>', title:'Best Prices', desc:'Competitive prices and discounts' },
      { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>', title:'Expert Advice', desc:'Our specialists will help you' },
    ],
  }
  return data[lang] || data.tj
})

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU', { day:'2-digit', month:'short' })
}

async function submitContact() {
  contactSending.value = true
  try {
    await fetch('/api/cms/contact', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(contactForm.value)
    })
    contactSent.value = true
    contactForm.value = { name:'', phone:'', message:'' }
    setTimeout(() => { contactSent.value = false }, 3000)
  } catch {}
  contactSending.value = false
}

onMounted(async () => {
  try {
    const [cats, prods, n, sGeneral, sContacts] = await Promise.all([
      api.get('/categories'),
      api.get('/products?limit=8'),
      fetch('/api/cms/news/public?limit=3').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/api/cms/settings/public?group=general').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/api/cms/settings/public?group=contacts').then(r => r.ok ? r.json() : []).catch(() => [])
    ])
    categories.value = Array.isArray(cats) ? cats : []
    products.value = Array.isArray(prods) ? prods : []
    news.value = Array.isArray(n) ? n : []

    const map = {}
    if (Array.isArray(sGeneral)) sGeneral.forEach(s => map[s.key] = s.value)
    if (Array.isArray(sContacts)) sContacts.forEach(s => map[s.key] = s.value)
    siteSettings.value = map

    // Count products per category
    const all = await api.get('/products?limit=500').catch(() => [])
    const counts = {}
    if (Array.isArray(all)) all.forEach(p => {
      const cid = p.category?.id || p.category_id
      if (cid) counts[cid] = (counts[cid] || 0) + 1
    })
    catCounts.value = counts
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.home{min-height:100vh}

/* Hero */
.hero{background:var(--accent-gradient);color:#fff;padding:48px 24px 56px;text-align:center;position:relative;overflow:hidden}
.hero::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:40px;background:var(--bg);border-radius:50% 50% 0 0}
.hero-content{position:relative;z-index:1}
.hero-content h1{font-size:28px;font-weight:900;margin-bottom:10px;line-height:1.2}
.hero-content p{font-size:15px;opacity:.9;margin-bottom:20px;max-width:500px;margin-left:auto;margin-right:auto}
.hero-btns{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.btn-primary{display:inline-block;background:#fff;color:#1e40af;padding:12px 28px;border-radius:12px;font-weight:700;text-decoration:none;font-size:15px;transition:transform .2s}
.btn-primary:hover{transform:translateY(-2px)}
.btn-outline{display:inline-block;background:transparent;color:#fff;padding:12px 28px;border-radius:12px;font-weight:700;text-decoration:none;font-size:15px;border:2px solid rgba(255,255,255,.4);transition:all .2s}
.btn-outline:hover{background:rgba(255,255,255,.15)}

/* Stats bar */
.stats-bar{display:flex;justify-content:center;gap:32px;padding:20px;background:var(--surface);border-bottom:1px solid var(--border);flex-wrap:wrap}
.stat{text-align:center}
.stat-value{display:block;font-size:22px;font-weight:800;color:var(--accent)}
.stat-label{font-size:12px;color:var(--muted);font-weight:500}

/* Section */
.section{max-width:1100px;margin:0 auto;padding:28px 16px}
.section-title{font-size:20px;font-weight:800;margin-bottom:16px}
.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.section-header .section-title{margin:0}
.see-all{color:var(--accent);font-size:13px;font-weight:600;text-decoration:none}

/* Categories */
.categories-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px}
.category-card{display:flex;flex-direction:column;align-items:center;gap:6px;padding:16px 10px;background:var(--surface);border:1px solid var(--border);border-radius:14px;text-decoration:none;color:var(--text);font-size:13px;font-weight:600;text-align:center;transition:all .2s}
.category-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.08);transform:translateY(-2px)}
.category-icon{width:44px;height:44px;border-radius:12px;background:var(--accent-bg,rgba(37,99,235,.08));display:flex;align-items:center;justify-content:center}
.category-icon svg{width:24px;height:24px;stroke:var(--accent)}
.cat-count{font-size:11px;color:var(--muted);font-weight:500}

/* Products grid */
.products-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
.product-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;text-decoration:none;color:var(--text);transition:all .2s}
.product-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.08);transform:translateY(-2px)}
.product-img{height:160px;background:#f8f9fa;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative}
.product-img img{max-width:90%;max-height:90%;width:auto;height:auto;object-fit:contain}
.img-placeholder{opacity:.15}
.img-placeholder svg{width:48px;height:48px}
.product-badge{position:absolute;top:8px;right:8px;background:#ef4444;color:#fff;font-size:10px;font-weight:700;padding:3px 8px;border-radius:6px}
.product-info{padding:10px 12px}
.product-info h3{font-size:13px;margin-bottom:4px;line-height:1.3;font-weight:600}
.price-row{display:flex;align-items:baseline;gap:4px}
.price{font-weight:800;color:var(--accent);font-size:15px}
.unit{font-size:11px;color:var(--muted)}

/* News */
.news-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.news-card{display:flex;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;text-decoration:none;color:var(--text);transition:all .2s;padding:12px}
.news-card:hover{box-shadow:0 4px 12px rgba(0,0,0,.06)}
.news-img{width:80px;height:80px;border-radius:10px;object-fit:cover;flex-shrink:0}
.news-body h3{font-size:14px;font-weight:700;margin-bottom:4px;line-height:1.3}
.news-body p{font-size:12px;color:var(--muted);line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.news-date{font-size:11px;color:var(--muted)}

/* Features */
.features-section{background:var(--surface);border-radius:20px;border:1px solid var(--border);padding:28px 20px !important;margin-top:16px}
.features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}
.feature-card{text-align:center;padding:16px}
.feature-icon{width:48px;height:48px;border-radius:14px;background:var(--accent-bg,rgba(37,99,235,.08));display:flex;align-items:center;justify-content:center;margin:0 auto 10px}
.feature-icon svg{width:24px;height:24px;stroke:var(--accent)}
.feature-card h3{font-size:14px;font-weight:700;margin-bottom:4px}
.feature-card p{font-size:12px;color:var(--muted);line-height:1.4}

/* Contact */
.contact-section{margin-top:16px}
.contact-inner{display:grid;grid-template-columns:1fr 1fr;gap:24px;background:var(--accent-gradient);border-radius:20px;padding:28px;color:#fff}
.contact-info h2{font-size:20px;font-weight:800;margin-bottom:8px}
.contact-info p{font-size:14px;opacity:.9;margin-bottom:12px}
.contact-details p{font-size:13px;margin:4px 0;opacity:.85}
.contact-form{display:flex;flex-direction:column;gap:10px}
.contact-form input,.contact-form textarea{padding:10px 14px;border:none;border-radius:10px;background:rgba(255,255,255,.15);color:#fff;font-size:14px;font-family:inherit;backdrop-filter:blur(4px)}
.contact-form input::placeholder,.contact-form textarea::placeholder{color:rgba(255,255,255,.6)}
.contact-form button{padding:10px;background:#fff;color:#1e40af;border:none;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer;transition:opacity .2s}
.contact-form button:hover{opacity:.9}
.contact-form button:disabled{opacity:.5}

@media(max-width:640px){
  .hero-content h1{font-size:22px}
  .stats-bar{gap:16px}
  .products-grid{grid-template-columns:repeat(2,1fr);gap:8px}
  .contact-inner{grid-template-columns:1fr;padding:20px}
  .features-grid{grid-template-columns:repeat(2,1fr)}
}
</style>
