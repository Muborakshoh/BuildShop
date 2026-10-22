<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ml } from '@/utils/helpers'
const route = useRoute()
const page = ref(null)
const loading = ref(true)
const error = ref(false)

async function loadPage(slug) {
  loading.value = true
  error.value = false
  try {
    const r = await fetch('/api/cms/pages/public/by-slug/' + encodeURIComponent(slug))
    if (r.ok) {
      page.value = await r.json()
    } else {
      page.value = null
      error.value = true
    }
  } catch {
    page.value = null
    error.value = true
  } finally {
    loading.value = false
  }
}

watch(() => route.params.slug, (s) => { if(s) loadPage(s) }, { immediate: true })
</script>
<template>
  <div class="page">
    <div v-if="loading" class="loading">Боргирӣ...</div>
    <template v-else-if="page">
      <h1>{{ ml(page,'title') }}</h1>
      <p v-if="page.description" class="description">{{ ml(page,'description') }}</p>
      <div v-if="page.blocks && page.blocks.length" class="blocks">
        <div v-for="block in page.blocks" :key="block.id" class="block" :class="'block-' + block.block_type">
          <h2 v-if="block.block_type === 'heading'">{{ block.content }}</h2>
          <div v-else-if="block.block_type === 'html'" v-html="block.content"></div>
          <p v-else-if="block.block_type === 'text'" class="block-text">{{ block.content }}</p>
          <img v-else-if="block.block_type === 'image'" :src="block.content" :alt="block.settings?.alt || ''" class="block-img" />
          <div v-else class="block-generic" v-html="block.content"></div>
        </div>
      </div>
      <div v-else-if="page.description" class="content">
        <div v-html="ml(page,'description')"></div>
      </div>
    </template>
    <div v-else class="empty">Саҳифа ёфт нашуд</div>
  </div>
</template>
<style scoped>
.page{max-width:800px;margin:0 auto;padding:16px 16px 100px}
h1{font-size:22px;font-weight:800;margin-bottom:12px}
.description{color:var(--muted);font-size:14px;margin-bottom:20px;line-height:1.6}
.blocks{display:flex;flex-direction:column;gap:16px}
.block-text{line-height:1.7;font-size:15px}
.block-img{max-width:100%;border-radius:12px;margin:8px 0}
.block-heading h2{font-size:18px;font-weight:700;margin:8px 0}
.block-html{line-height:1.7}
.block-html :deep(img){max-width:100%;border-radius:8px}
.content{line-height:1.7;font-size:15px}
.content :deep(img){max-width:100%;border-radius:8px}
.loading,.empty{text-align:center;padding:40px;color:var(--muted)}
</style>