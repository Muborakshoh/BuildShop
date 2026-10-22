<template>
  <div class="docs-page">
    <div class="docs-sidebar" :class="{ open: sidebarOpen }">
      <div class="docs-sidebar-header">
        <h3>{{ t('docs_title') }}</h3>
        <button class="docs-close-btn" @click="sidebarOpen = false">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <nav class="docs-nav">
        <a
          v-for="item in tocItems"
          :key="item.file"
          :class="['docs-nav-item', { active: currentFile === item.file }]"
          @click="loadDoc(item.file); sidebarOpen = false"
        >
          <span class="docs-nav-num">{{ item.num }}</span>
          <span>{{ item.title }}</span>
        </a>
      </nav>
    </div>

    <div class="docs-overlay" v-if="sidebarOpen" @click="sidebarOpen = false"></div>

    <div class="docs-content">
      <button class="docs-menu-btn" @click="sidebarOpen = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        <span>{{ t('docs_menu') }}</span>
      </button>

      <div class="docs-lang-switcher">
        <button
          v-for="lang in langs"
          :key="lang.code"
          :class="['docs-lang-btn', { active: docLang === lang.code }]"
          @click="switchLang(lang.code)"
        >{{ lang.label }}</button>
      </div>

      <div v-if="loading" class="docs-loading">{{ t('loading') }}</div>
      <article v-else class="docs-article" v-html="renderedHtml"></article>

      <div class="docs-footer-nav">
        <a v-if="prevDoc" class="docs-prev" @click="loadDoc(prevDoc.file)">← {{ prevDoc.title }}</a>
        <span v-else></span>
        <a v-if="nextDoc" class="docs-next" @click="loadDoc(nextDoc.file)">{{ nextDoc.title }} →</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

const docLang = ref(locale.value || 'tj')
const currentFile = ref('01-registration')
const loading = ref(false)
const rawContent = ref('')
const sidebarOpen = ref(false)

const langs = [
  { code: 'tj', label: 'Тоҷикӣ' },
  { code: 'ru', label: 'Русский' },
  { code: 'en', label: 'English' },
]

const tocData = {
  tj: [
    { file: '01-registration', num: '01', title: 'Бақайдгирӣ ва Вуруд' },
    { file: '02-catalog', num: '02', title: 'Каталог ва Маҳсулот' },
    { file: '03-cart-orders', num: '03', title: 'Сабад ва Фармоишҳо' },
    { file: '04-calculator', num: '04', title: 'Калкулятор' },
    { file: '05-news', num: '05', title: 'Хабарҳо' },
    { file: '06-admin', num: '06', title: 'Панели Админ' },
    { file: '07-admin-products', num: '07', title: 'Идоракунии Маҳсулот' },
    { file: '08-admin-users', num: '08', title: 'Идоракунии Корбарон' },
    { file: '09-cashier', num: '09', title: 'Кассир' },
    { file: '10-telegram-bot', num: '10', title: 'Telegram-бот' },
  ],
  ru: [
    { file: '01-registration', num: '01', title: 'Регистрация и Вход' },
    { file: '02-catalog', num: '02', title: 'Каталог и Товары' },
    { file: '03-cart-orders', num: '03', title: 'Корзина и Заказы' },
    { file: '04-calculator', num: '04', title: 'Калькулятор' },
    { file: '05-news', num: '05', title: 'Новости' },
    { file: '06-admin', num: '06', title: 'Панель Администратора' },
    { file: '07-admin-products', num: '07', title: 'Управление Товарами' },
    { file: '08-admin-users', num: '08', title: 'Управление Пользователями' },
    { file: '09-cashier', num: '09', title: 'Кассир' },
    { file: '10-telegram-bot', num: '10', title: 'Telegram-бот' },
  ],
  en: [
    { file: '01-registration', num: '01', title: 'Registration & Login' },
    { file: '02-catalog', num: '02', title: 'Catalog & Products' },
    { file: '03-cart-orders', num: '03', title: 'Cart & Orders' },
    { file: '04-calculator', num: '04', title: 'Calculator' },
    { file: '05-news', num: '05', title: 'News' },
    { file: '06-admin', num: '06', title: 'Admin Panel' },
    { file: '07-admin-products', num: '07', title: 'Product Management' },
    { file: '08-admin-users', num: '08', title: 'User Management' },
    { file: '09-cashier', num: '09', title: 'Cashier' },
    { file: '10-telegram-bot', num: '10', title: 'Telegram Bot' },
  ],
}

const tocItems = computed(() => tocData[docLang.value] || tocData.tj)

const currentIndex = computed(() =>
  tocItems.value.findIndex(i => i.file === currentFile.value)
)

const prevDoc = computed(() =>
  currentIndex.value > 0 ? tocItems.value[currentIndex.value - 1] : null
)

const nextDoc = computed(() =>
  currentIndex.value < tocItems.value.length - 1 ? tocItems.value[currentIndex.value + 1] : null
)

function simpleMarkdown(md) {
  let html = md
    // Remove bottom navigation lines like [← ...](file.md) | [... →](file.md)
    .replace(/^\[.*?←.*?\]\(.*?\).*\[.*?→.*?\]\(.*?\)$/gm, '')
    .replace(/^\[←.*?\]\(.*?\)\s*\|.*$/gm, '')
    .replace(/^.*\|\s*\[.*?→\]\(.*?\)$/gm, '')
    .replace(/^\[← .*?\]\(.*?\)$/gm, '')
    .replace(/^\[.*? →\]\(.*?\)$/gm, '')

  // Escape HTML
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Blockquotes (screenshot placeholders) — process first before splitting by lines
  html = html.replace(/^&gt; \*\*\[(.*?)\]\*\*/gm, '<div class="docs-screenshot-placeholder"><span class="docs-screenshot-icon">📷</span> <span>$1</span></div>')
  html = html.replace(/^&gt; ⚠️(.*)/gm, '<div class="docs-warning">⚠️$1</div>')
  html = html.replace(/^&gt; (.*)/gm, '<blockquote>$1</blockquote>')

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // Horizontal rules
  html = html.replace(/^---$/gm, '')

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Markdown links [text](url) — render as plain text (navigation handled by component)
  html = html.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // Sub-list items (indented with spaces) — process before main list
  html = html.replace(/^   - (.+)$/gm, '<li class="sub-item">$1</li>')

  // Unordered list items
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')

  // Ordered list items
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="ol-item">$1</li>')

  // Wrap consecutive <li> into <ul> or <ol>
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>')
  html = html.replace(/((?:<li class="ol-item">.*<\/li>\n?)+)/g, '<ol>$1</ol>')
  html = html.replace(/<li class="ol-item">/g, '<li>')

  // Paragraphs — wrap lines that aren't already wrapped
  const lines = html.split('\n')
  const result = []
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) { result.push(''); continue }
    if (trimmed.startsWith('<')) { result.push(line); continue }
    result.push(`<p>${trimmed}</p>`)
  }

  return result.join('\n')
}

const renderedHtml = computed(() => simpleMarkdown(rawContent.value))

async function loadDoc(file) {
  currentFile.value = file
  loading.value = true
  try {
    const resp = await fetch(`/api/guide/${docLang.value}/${file}`)
    if (resp.ok) {
      rawContent.value = await resp.text()
    } else {
      rawContent.value = 'Document not found.'
    }
  } catch {
    rawContent.value = 'Error loading document.'
  }
  loading.value = false
  // Update URL without page reload
  router.replace({ query: { ...route.query, doc: file, lang: docLang.value } })
}

function switchLang(lang) {
  docLang.value = lang
  loadDoc(currentFile.value)
}

onMounted(() => {
  // Read from URL params
  if (route.query.doc) currentFile.value = route.query.doc
  if (route.query.lang && ['tj', 'ru', 'en'].includes(route.query.lang)) {
    docLang.value = route.query.lang
  }
  loadDoc(currentFile.value)
})
</script>

<style scoped>
.docs-page {
  display: flex;
  min-height: 100vh;
  padding-bottom: 80px;
}

/* Sidebar */
.docs-sidebar {
  width: 280px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 20px 0;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  overflow-y: auto;
  transition: transform 0.3s ease;
}

.docs-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 16px;
  border-bottom: 1px solid var(--border);
}

.docs-sidebar-header h3 {
  font-size: 16px;
  font-weight: 800;
  color: var(--accent);
  margin: 0;
}

.docs-close-btn {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: var(--muted);
}
.docs-close-btn svg { width: 20px; height: 20px; }

.docs-nav {
  padding: 12px 8px;
}

.docs-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 2px;
}

.docs-nav-item:hover {
  background: var(--accent-bg, rgba(37,99,235,.06));
}

.docs-nav-item.active {
  background: var(--accent);
  color: #fff;
  font-weight: 700;
}

.docs-nav-num {
  font-size: 11px;
  font-weight: 800;
  opacity: 0.5;
  min-width: 20px;
}

.docs-nav-item.active .docs-nav-num {
  opacity: 0.8;
}

/* Content */
.docs-content {
  flex: 1;
  margin-left: 280px;
  padding: 24px 32px;
  max-width: 800px;
}

.docs-menu-btn {
  display: none;
  align-items: center;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  margin-bottom: 16px;
}
.docs-menu-btn svg { width: 18px; height: 18px; }

.docs-lang-switcher {
  display: flex;
  gap: 6px;
  margin-bottom: 20px;
}

.docs-lang-btn {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.docs-lang-btn.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.docs-lang-btn:hover:not(.active) {
  background: var(--accent-bg, rgba(37,99,235,.06));
}

/* Article content */
.docs-article {
  line-height: 1.7;
  color: var(--text);
}

.docs-article :deep(h1) {
  font-size: 24px;
  font-weight: 800;
  margin-bottom: 20px;
  color: var(--text);
  border-bottom: 2px solid var(--accent);
  padding-bottom: 10px;
}

.docs-article :deep(h2) {
  font-size: 18px;
  font-weight: 700;
  margin-top: 28px;
  margin-bottom: 12px;
  color: var(--text);
}

.docs-article :deep(h3) {
  font-size: 15px;
  font-weight: 700;
  margin-top: 20px;
  margin-bottom: 8px;
}

.docs-article :deep(p) {
  margin-bottom: 10px;
  font-size: 14px;
}

.docs-article :deep(ol),
.docs-article :deep(ul) {
  padding-left: 24px;
  margin-bottom: 12px;
}

.docs-article :deep(li) {
  margin-bottom: 6px;
  font-size: 14px;
}

.docs-article :deep(strong) {
  font-weight: 700;
  color: var(--text);
}

.docs-article :deep(code) {
  background: var(--accent-bg, rgba(37,99,235,.08));
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: monospace;
}

.docs-article :deep(hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 24px 0;
}

.docs-article :deep(.docs-screenshot-placeholder) {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--accent-bg, rgba(37,99,235,.06));
  border: 2px dashed var(--accent);
  border-radius: 12px;
  padding: 16px 20px;
  margin: 14px 0;
  font-size: 13px;
  color: var(--accent);
  font-weight: 500;
}

.docs-article :deep(.docs-screenshot-icon) {
  font-size: 20px;
}

.docs-article :deep(.docs-warning) {
  background: rgba(245,158,11,.08);
  border: 1px solid rgba(245,158,11,.3);
  border-radius: 10px;
  padding: 12px 16px;
  margin: 12px 0;
  font-size: 13px;
  font-weight: 600;
  color: #b45309;
}

.docs-article :deep(blockquote) {
  border-left: 3px solid var(--accent);
  padding-left: 14px;
  margin: 12px 0;
  color: var(--muted);
  font-size: 13px;
}

/* Footer nav */
.docs-footer-nav {
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.docs-prev, .docs-next {
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 8px;
  transition: background 0.2s;
}

.docs-prev:hover, .docs-next:hover {
  background: var(--accent-bg, rgba(37,99,235,.06));
}

.docs-loading {
  text-align: center;
  padding: 40px;
  color: var(--muted);
  font-size: 14px;
}

.docs-overlay { display: none; }

/* Mobile responsive */
@media (max-width: 768px) {
  .docs-sidebar {
    transform: translateX(-100%);
    width: 280px;
    z-index: 10001;
  }
  .docs-sidebar.open {
    transform: translateX(0);
  }
  .docs-close-btn { display: flex; }
  .docs-menu-btn { display: flex; }
  .docs-content {
    margin-left: 0;
    padding: 16px;
  }
  .docs-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.4);
    z-index: 10000;
  }
}
</style>
