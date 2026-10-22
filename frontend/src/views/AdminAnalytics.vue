<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'
import { money } from '@/utils/helpers'

const { t } = useI18n()
const loading = ref(true)
const stats = ref(null)
const orders = ref([])
const products = ref([])

const statusLabels = {
  created: { tj:'Сохташуда', ru:'Создан', en:'Created' },
  confirmed: { tj:'Тасдиқшуда', ru:'Подтверждён', en:'Confirmed' },
  assembling: { tj:'Ҷамъоварӣ', ru:'Сборка', en:'Assembling' },
  delivering: { tj:'Расонидан', ru:'Доставка', en:'Delivering' },
  delivered: { tj:'Расонида шуд', ru:'Доставлен', en:'Delivered' },
  completed: { tj:'Иҷрошуда', ru:'Завершён', en:'Completed' },
  cancelled: { tj:'Бекоршуда', ru:'Отменён', en:'Cancelled' },
}
const lang = localStorage.getItem('lang') || 'tj'
function sl(s) { return statusLabels[(s||'').toLowerCase()]?.[lang] || s }

const statusColors = {
  created:'#3b82f6', confirmed:'#22c55e', assembling:'#eab308',
  delivering:'#a855f7', delivered:'#6366f1', completed:'#059669', cancelled:'#ef4444'
}
function sc(s) { return statusColors[(s||'').toLowerCase()] || '#6b7280' }

// Computed analytics
const revenue = computed(() => orders.value.reduce((s,o) => s + parseFloat(o.total_amount || 0), 0))
const avgCheck = computed(() => orders.value.length ? revenue.value / orders.value.length : 0)

const todayOrders = computed(() => {
  const today = new Date().toDateString()
  return orders.value.filter(o => new Date(o.created_at).toDateString() === today)
})
const todayRevenue = computed(() => todayOrders.value.reduce((s,o) => s + parseFloat(o.total_amount || 0), 0))

const statusCounts = computed(() => {
  const counts = {}
  orders.value.forEach(o => {
    const s = (o.status || '').toLowerCase()
    counts[s] = (counts[s] || 0) + 1
  })
  return Object.entries(counts).sort((a,b) => b[1] - a[1])
})

const lowStock = computed(() =>
  products.value.filter(p => p.stock_quantity <= 5 && p.stock_quantity >= 0)
    .sort((a,b) => a.stock_quantity - b.stock_quantity).slice(0,8)
)

const outOfStock = computed(() => products.value.filter(p => p.stock_quantity <= 0).length)

const topCategories = computed(() => {
  const cats = {}
  products.value.forEach(p => {
    const name = p.category?.name || '—'
    if (!cats[name]) cats[name] = { count: 0, value: 0 }
    cats[name].count++
    cats[name].value += parseFloat(p.price || 0)
  })
  return Object.entries(cats).sort((a,b) => b[1].count - a[1].count).slice(0,6)
})

const recentOrders = computed(() => orders.value.slice(0, 8))

// Weekly revenue (last 7 days)
const weeklyData = computed(() => {
  const days = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const key = d.toDateString()
    const label = d.toLocaleDateString('ru-RU', { day:'2-digit', month:'2-digit' })
    const dayOrders = orders.value.filter(o => new Date(o.created_at).toDateString() === key)
    const rev = dayOrders.reduce((s,o) => s + parseFloat(o.total_amount || 0), 0)
    days.push({ label, revenue: rev, count: dayOrders.length })
  }
  return days
})

const maxWeeklyRev = computed(() => Math.max(...weeklyData.value.map(d => d.revenue), 1))

onMounted(async () => {
  try {
    const [dashboard, ord, prod] = await Promise.all([
      api.get('/cms/reports/dashboard').catch(() => ({})),
      api.get('/orders?limit=500').catch(() => []),
      api.get('/products?limit=500').catch(() => [])
    ])
    orders.value = Array.isArray(ord) ? ord : []
    products.value = Array.isArray(prod) ? prod : []
    stats.value = dashboard
  } catch (e) { console.error(e) }
  loading.value = false
})

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })
}
</script>

<template>
  <div class="analytics">
    <h1>{{ t('nav_analytics') }}</h1>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <template v-else>
      <!-- Top stats -->
      <div class="stats-row">
        <div class="stat-card accent">
          <div class="sc-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
          </div>
          <div class="sc-data">
            <div class="sc-value">{{ money(revenue) }}</div>
            <div class="sc-label">{{ t('revenue') }}</div>
          </div>
        </div>
        <div class="stat-card green">
          <div class="sc-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
          </div>
          <div class="sc-data">
            <div class="sc-value">{{ orders.length }}</div>
            <div class="sc-label">{{ t('orders') }}</div>
          </div>
        </div>
        <div class="stat-card purple">
          <div class="sc-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>
          </div>
          <div class="sc-data">
            <div class="sc-value">{{ products.length }}</div>
            <div class="sc-label">{{ t('products') }}</div>
          </div>
        </div>
        <div class="stat-card amber">
          <div class="sc-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>
          </div>
          <div class="sc-data">
            <div class="sc-value">{{ money(avgCheck) }}</div>
            <div class="sc-label">{{ t('avg_check') || 'Миёна чек' }}</div>
          </div>
        </div>
      </div>

      <!-- Today highlight -->
      <div class="today-bar">
        <div class="tb-left">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span>{{ t('today') || 'Имрӯз' }}</span>
        </div>
        <div class="tb-stats">
          <span><strong>{{ todayOrders.length }}</strong> {{ t('orders') }}</span>
          <span><strong>{{ money(todayRevenue) }}</strong></span>
        </div>
      </div>

      <!-- Weekly chart -->
      <div class="card">
        <h3>{{ t('weekly_revenue') || 'Даромади ҳафтагӣ' }}</h3>
        <div class="bar-chart">
          <div v-for="day in weeklyData" :key="day.label" class="bar-col">
            <div class="bar-value">{{ day.count > 0 ? money(day.revenue) : '' }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{height: (day.revenue / maxWeeklyRev * 100) + '%'}"></div>
            </div>
            <div class="bar-label">{{ day.label }}</div>
          </div>
        </div>
      </div>

      <!-- Two columns -->
      <div class="two-cols">
        <!-- Order status breakdown -->
        <div class="card">
          <h3>{{ t('order_statuses') || 'Статусҳои фармоиш' }}</h3>
          <div class="status-bars">
            <div v-for="[status, count] in statusCounts" :key="status" class="sb-row">
              <div class="sb-label">
                <span class="sb-dot" :style="{background: sc(status)}"></span>
                <span>{{ sl(status) }}</span>
              </div>
              <div class="sb-bar-wrap">
                <div class="sb-bar" :style="{width: (count / orders.length * 100) + '%', background: sc(status)}"></div>
              </div>
              <span class="sb-count">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- Top categories -->
        <div class="card">
          <h3>{{ t('categories') }}</h3>
          <div class="cat-list">
            <div v-for="[name, data] in topCategories" :key="name" class="cat-row">
              <span class="cat-name">{{ name }}</span>
              <span class="cat-count">{{ data.count }} {{ t('pcs') }}</span>
            </div>
            <div v-if="!topCategories.length" class="empty-msg">—</div>
          </div>
        </div>
      </div>

      <!-- Two columns: Recent orders + Low stock -->
      <div class="two-cols">
        <div class="card">
          <div class="card-header">
            <h3>{{ t('recent_orders') }}</h3>
            <router-link to="/orders" class="see-all">{{ t('see_all') }} →</router-link>
          </div>
          <div class="orders-list">
            <div v-for="o in recentOrders" :key="o.id" class="ol-row">
              <span class="ol-id">#{{ o.id }}</span>
              <span class="ol-status" :style="{color: sc(o.status)}">{{ sl(o.status) }}</span>
              <span class="ol-amount">{{ money(o.total_amount) }}</span>
              <span class="ol-date">{{ formatDate(o.created_at) }}</span>
            </div>
            <div v-if="!recentOrders.length" class="empty-msg">{{ t('no_results') }}</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3>{{ t('low_stock') }}</h3>
            <span class="stock-warn" v-if="outOfStock">{{ outOfStock }} {{ t('out_of_stock') || 'нест' }}</span>
          </div>
          <div class="stock-list">
            <div v-for="p in lowStock" :key="p.id" class="stk-row">
              <span class="stk-name">{{ p.name }}</span>
              <span class="stk-qty" :class="{'critical': p.stock_quantity <= 0}">
                {{ p.stock_quantity }} {{ t('pcs') }}
              </span>
            </div>
            <div v-if="!lowStock.length" class="empty-msg">{{ t('all_good') || 'Ҳама хуб аст' }}</div>
          </div>
        </div>
      </div>

      <!-- Top products -->
      <div class="card" v-if="stats?.popular_products?.length">
        <h3>{{ t('top_products') }}</h3>
        <div class="top-products">
          <div v-for="(p, idx) in stats.popular_products" :key="p.name" class="tp-row">
            <div class="tp-rank" :class="'r'+Math.min(idx+1,4)">{{ idx+1 }}</div>
            <span class="tp-name">{{ p.name }}</span>
            <span class="tp-sold">{{ p.sold }} {{ t('pcs') }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.analytics{max-width:900px;margin:0 auto;padding:16px 16px 100px}
h1{font-size:20px;font-weight:800;margin-bottom:16px}

.loading{display:flex;justify-content:center;padding:60px}
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* Stats row */
.stats-row{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:16px}
.stat-card{display:flex;align-items:center;gap:12px;padding:14px;background:var(--surface);border:1px solid var(--border);border-radius:14px;transition:transform .2s}
.stat-card:hover{transform:translateY(-2px)}
.sc-icon{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sc-icon svg{width:22px;height:22px}
.accent .sc-icon{background:rgba(37,99,235,.1)}
.accent .sc-icon svg{stroke:#2563eb}
.green .sc-icon{background:rgba(5,150,105,.1)}
.green .sc-icon svg{stroke:#059669}
.purple .sc-icon{background:rgba(139,92,246,.1)}
.purple .sc-icon svg{stroke:#8b5cf6}
.amber .sc-icon{background:rgba(217,119,6,.1)}
.amber .sc-icon svg{stroke:#d97706}
.sc-value{font-size:18px;font-weight:800;color:var(--text);line-height:1.2}
.sc-label{font-size:11px;color:var(--muted);font-weight:500}

/* Today bar */
.today-bar{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:linear-gradient(135deg,#2563eb,#0ea5e9);border-radius:12px;color:#fff;margin-bottom:16px}
.tb-left{display:flex;align-items:center;gap:8px;font-weight:700;font-size:14px}
.tb-left svg{width:20px;height:20px}
.tb-stats{display:flex;gap:16px;font-size:13px}
.tb-stats strong{font-weight:800}

/* Card */
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:12px}
.card h3{margin:0 0 12px;font-size:15px;font-weight:700}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.card-header h3{margin:0}
.see-all{font-size:12px;font-weight:600;color:var(--accent);text-decoration:none}

/* Bar chart */
.bar-chart{display:flex;align-items:flex-end;gap:8px;height:140px;padding-top:20px}
.bar-col{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;height:100%}
.bar-value{font-size:9px;color:var(--muted);font-weight:600;white-space:nowrap;min-height:14px}
.bar-track{flex:1;width:100%;background:var(--bg);border-radius:6px;position:relative;overflow:hidden;display:flex;align-items:flex-end}
.bar-fill{width:100%;background:linear-gradient(to top,#2563eb,#60a5fa);border-radius:6px;transition:height .5s ease;min-height:2px}
.bar-label{font-size:10px;color:var(--muted);font-weight:600}

/* Two cols */
.two-cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:600px){.two-cols{grid-template-columns:1fr}}

/* Status bars */
.sb-row{display:flex;align-items:center;gap:8px;padding:5px 0}
.sb-label{display:flex;align-items:center;gap:6px;min-width:100px;font-size:12px;font-weight:600}
.sb-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.sb-bar-wrap{flex:1;height:8px;background:var(--bg);border-radius:4px;overflow:hidden}
.sb-bar{height:100%;border-radius:4px;transition:width .5s}
.sb-count{font-size:12px;font-weight:800;color:var(--text);min-width:24px;text-align:right}

/* Category list */
.cat-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.cat-row:last-child{border:none}
.cat-name{font-weight:600}
.cat-count{color:var(--muted);font-weight:600}

/* Orders list */
.ol-row{display:grid;grid-template-columns:auto 1fr auto auto;gap:6px;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-size:12px}
.ol-row:last-child{border:none}
.ol-id{font-weight:700;color:var(--muted)}
.ol-status{font-weight:600;text-transform:capitalize}
.ol-amount{font-weight:700}
.ol-date{color:var(--muted);font-size:11px}

/* Stock */
.stock-warn{font-size:11px;font-weight:700;color:#ef4444;background:rgba(239,68,68,.08);padding:2px 8px;border-radius:6px}
.stk-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.stk-row:last-child{border:none}
.stk-name{font-weight:500;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-right:8px}
.stk-qty{font-weight:700;color:#d97706;white-space:nowrap}
.stk-qty.critical{color:#ef4444}

/* Top products */
.tp-row{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.tp-row:last-child{border:none}
.tp-rank{width:26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;flex-shrink:0}
.r1{background:rgba(37,99,235,.12);color:#2563eb}
.r2{background:rgba(139,92,246,.1);color:#8b5cf6}
.r3{background:rgba(217,119,6,.1);color:#d97706}
.r4{background:var(--bg);color:var(--muted)}
.tp-name{flex:1;font-weight:500}
.tp-sold{font-weight:700;color:var(--accent)}

.empty-msg{text-align:center;padding:20px;color:var(--muted);font-size:13px}
</style>
