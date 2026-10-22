<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ml } from '@/utils/helpers'
const { t } = useI18n()
const categories = ref([])
onMounted(async () => {
  try { const r = await fetch('/api/categories'); if(r.ok) categories.value = await r.json() } catch{}
})
</script>
<template>
  <div class="page">
    <h1>{{ t('nav_categories') }}</h1>
    <div class="grid">
      <router-link v-for="c in categories" :key="c.id" :to="'/products?category='+c.id" class="cat-card">
        <div class="cat-icon">{{ (ml(c,'name')||'?')[0] }}</div>
        <span class="cat-name">{{ ml(c,'name') }}</span>
      </router-link>
    </div>
  </div>
</template>
<style scoped>
.page{max-width:900px;margin:0 auto;padding:16px}
h1{margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
.cat-card{display:flex;flex-direction:column;align-items:center;gap:10px;padding:24px 16px;background:var(--surface);border:1px solid var(--border);border-radius:14px;text-decoration:none;color:var(--text);transition:box-shadow .2s}
.cat-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.08)}
.cat-icon{width:56px;height:56px;border-radius:16px;background:var(--accent-bg);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;color:var(--accent)}
.cat-name{font-weight:600;font-size:14px;text-align:center}
</style>
