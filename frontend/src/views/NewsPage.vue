<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ml } from '@/utils/helpers'

const { t } = useI18n()
const news = ref([])
const expanded = ref(null)
const loadingDetail = ref(false)
const newsDetails = ref({})

onMounted(async () => {
  try {
    const r = await fetch('/api/cms/news/public')
    if (r.ok) news.value = await r.json()
  } catch {}
})

async function toggleExpand(item) {
  if (expanded.value === item.id) {
    expanded.value = null
    return
  }
  expanded.value = item.id
  if (!newsDetails.value[item.id]) {
    loadingDetail.value = true
    try {
      const r = await fetch('/api/cms/news/public/by-slug/' + encodeURIComponent(item.slug))
      if (r.ok) {
        newsDetails.value[item.id] = await r.json()
      }
    } catch {}
    loadingDetail.value = false
  }
}

function getContent(item) {
  const detail = newsDetails.value[item.id]
  return detail ? ml(detail, 'content') : (item.summary || '')
}
</script>
<template>
  <div class="page">
    <h1>{{ t('news') || 'Хабарҳо' }}</h1>
    <div v-for="item in news" :key="item.id" class="news-card" @click="toggleExpand(item)">
      <div class="news-header">
        <div>
          <h3>{{ ml(item,'title') }}</h3>
          <div class="date">{{ new Date(item.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }) }}</div>
        </div>
        <span v-if="item.pinned" class="pin">📌</span>
        <svg :class="['chevron', {open: expanded===item.id}]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
      <p v-if="item.summary && expanded !== item.id" class="summary">{{ ml(item,'summary') }}</p>
      <img v-if="item.image_url && expanded === item.id" :src="item.image_url" :alt="ml(item,'title')" class="news-img" />
      <Transition name="slide">
        <div v-if="expanded===item.id" class="content-wrap">
          <div v-if="loadingDetail" class="loading-detail">Боргирӣ...</div>
          <div v-else class="content" v-html="getContent(item)"></div>
        </div>
      </Transition>
    </div>
    <p v-if="!news.length" class="empty">{{ t('news_empty') || 'Хабарҳо нест' }}</p>
  </div>
</template>
<style scoped>
.page{max-width:800px;margin:0 auto;padding:16px 16px 100px}
h1{font-size:20px;font-weight:800;margin-bottom:16px}
.news-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:10px;cursor:pointer;transition:border-color .2s}
.news-card:hover{border-color:var(--accent)}
.news-header{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}
.news-card h3{margin:0 0 4px;font-size:16px;font-weight:700}
.date{font-size:12px;color:var(--muted)}
.pin{font-size:14px}
.chevron{width:18px;height:18px;color:var(--muted);transition:transform .2s;flex-shrink:0;margin-top:4px}
.chevron.open{transform:rotate(180deg)}
.summary{font-size:13px;color:var(--muted);margin-top:8px;line-height:1.5}
.news-img{width:100%;max-height:300px;object-fit:cover;border-radius:10px;margin-top:12px}
.content-wrap{margin-top:12px;border-top:1px solid var(--border);padding-top:12px}
.content{font-size:14px;line-height:1.7;color:var(--text)}
.content :deep(img){max-width:100%;border-radius:8px;margin:8px 0}
.content :deep(h2){font-size:17px;margin:12px 0 6px}
.content :deep(p){margin:6px 0}
.loading-detail{text-align:center;padding:12px;color:var(--muted);font-size:13px}
.empty{color:var(--muted);text-align:center;padding:40px}
.slide-enter-active,.slide-leave-active{transition:all .25s ease;overflow:hidden}
.slide-enter-from,.slide-leave-to{max-height:0;opacity:0;padding-top:0}
.slide-enter-to,.slide-leave-from{max-height:2000px;opacity:1}
</style>