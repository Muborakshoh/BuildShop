<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { money, ml } from '@/utils/helpers'
import ProductCard from '@/components/ProductCard.vue'

const { t } = useI18n()
const activeTab = ref('walls')
const results = ref(null)
const suggested = ref([])

const wallForm = ref({ length:12, height:3, thickness:25, openings:6 })
const floorForm = ref({ length:5, width:4, tileSize:50, waste:10 })
const paintForm = ref({ area:40, layers:2, consumption:0.15 })
const roofForm = ref({ length:10, width:6, angle:30, overlap:15 })

const KEYWORDS = {
  walls: ['кирпич','хишт','brick','блок','цемент','cement'],
  floor: ['плитка','кошин','tile','кафель','ламинат'],
  paint: ['краска','ранг','paint','грунтовка','лак'],
  roof: ['кровля','шифер','профнастил','черепица','roofing','бом']
}

async function findProducts(type) {
  try {
    const res = await fetch('/api/products?limit=500')
    if (!res.ok) return []
    const products = await res.json()
    const kw = KEYWORDS[type] || []
    return products.filter(p => {
      const txt = ((p.name||'')+(p.description||'')+JSON.stringify(p.translations||{})).toLowerCase()
      return kw.some(k => txt.includes(k)) && p.stock_quantity > 0
    }).slice(0, 6)
  } catch { return [] }
}

async function calcWalls() {
  const f = wallForm.value
  const area = f.length * f.height - f.openings
  if (area <= 0) return
  const bricksPerM2 = f.thickness <= 12 ? 52 : f.thickness <= 25 ? 104 : f.thickness <= 38 ? 156 : 208
  const bricks = Math.ceil(area * bricksPerM2 * 1.07)
  const cement = Math.ceil(area * f.thickness / 25 * 0.25)
  results.value = [
    { value: area.toFixed(1)+' м²', label: t('calc_wall_area') },
    { value: bricks.toLocaleString(), label: t('calc_bricks_count') },
    { value: cement, label: t('calc_cement_bags') }
  ]
  suggested.value = await findProducts('walls')
}

async function calcFloor() {
  const f = floorForm.value
  const area = f.length * f.width
  const tileM = f.tileSize / 100
  const tiles = Math.ceil(area / (tileM * tileM) * (1 + f.waste / 100))
  const glue = Math.ceil(area * 5 / 25)
  results.value = [
    { value: area.toFixed(1)+' м²', label: t('calc_floor_area') },
    { value: tiles.toLocaleString(), label: t('calc_tiles_count') },
    { value: glue, label: t('calc_glue_bags') }
  ]
  suggested.value = await findProducts('floor')
}

async function calcPaint() {
  const f = paintForm.value
  const total = f.area * f.layers * f.consumption
  results.value = [
    { value: f.area.toFixed(1)+' м²', label: t('calc_paint_total_area') },
    { value: total.toFixed(1)+' кг', label: t('calc_paint_total_kg') },
    { value: Math.ceil(total/10)+' × 10кг', label: t('calc_paint_buckets') }
  ]
  suggested.value = await findProducts('paint')
}

async function calcRoof() {
  const f = roofForm.value
  const slope = (f.width/2) / Math.cos(f.angle * Math.PI / 180)
  const area = f.length * slope * 2
  const total = area * (1 + f.overlap / 100)
  results.value = [
    { value: area.toFixed(1)+' м²', label: t('calc_roof_area') },
    { value: total.toFixed(1)+' м²', label: t('calc_roof_with_overlap') },
    { value: Math.ceil(total / 2.36), label: t('calc_roof_sheets') }
  ]
  suggested.value = await findProducts('roof')
}

function calculate() {
  if (activeTab.value==='walls') calcWalls()
  else if (activeTab.value==='floor') calcFloor()
  else if (activeTab.value==='paint') calcPaint()
  else calcRoof()
}
</script>

<template>
  <div class="page">
    <h1>{{ t('calc_title') }}</h1>
    <p class="desc">{{ t('calc_desc') }}</p>
    <div class="tabs">
      <button v-for="tab in ['walls','floor','paint','roof']" :key="tab" :class="['tab',{active:activeTab===tab}]" @click="activeTab=tab;results=null">
        {{ t('calc_'+tab) }}
      </button>
    </div>
    <div class="form-card">
      <!-- Walls -->
      <div v-if="activeTab==='walls'" class="form-grid">
        <label>{{ t('calc_wall_length') }}<input v-model.number="wallForm.length" type="number" step="0.1"/></label>
        <label>{{ t('calc_wall_height') }}<input v-model.number="wallForm.height" type="number" step="0.1"/></label>
        <label>{{ t('calc_wall_thickness') }}
          <select v-model.number="wallForm.thickness"><option :value="12">12см</option><option :value="25">25см</option><option :value="38">38см</option><option :value="51">51см</option></select>
        </label>
        <label>{{ t('calc_openings') }}<input v-model.number="wallForm.openings" type="number" step="0.1"/></label>
      </div>
      <!-- Floor -->
      <div v-if="activeTab==='floor'" class="form-grid">
        <label>{{ t('calc_floor_length') }}<input v-model.number="floorForm.length" type="number" step="0.1"/></label>
        <label>{{ t('calc_floor_width') }}<input v-model.number="floorForm.width" type="number" step="0.1"/></label>
        <label>{{ t('calc_tile_size') }}
          <select v-model.number="floorForm.tileSize"><option :value="30">30×30</option><option :value="40">40×40</option><option :value="50">50×50</option><option :value="60">60×60</option></select>
        </label>
        <label>{{ t('calc_waste') }}<input v-model.number="floorForm.waste" type="number" min="0" max="30"/></label>
      </div>
      <!-- Paint -->
      <div v-if="activeTab==='paint'" class="form-grid">
        <label>{{ t('calc_paint_area') }}<input v-model.number="paintForm.area" type="number" step="0.1"/></label>
        <label>{{ t('calc_paint_layers') }}
          <select v-model.number="paintForm.layers"><option :value="1">1</option><option :value="2">2</option><option :value="3">3</option></select>
        </label>
        <label>{{ t('calc_paint_consumption') }}<input v-model.number="paintForm.consumption" type="number" step="0.01"/></label>
      </div>
      <!-- Roof -->
      <div v-if="activeTab==='roof'" class="form-grid">
        <label>{{ t('calc_roof_length') }}<input v-model.number="roofForm.length" type="number" step="0.1"/></label>
        <label>{{ t('calc_roof_width') }}<input v-model.number="roofForm.width" type="number" step="0.1"/></label>
        <label>{{ t('calc_roof_angle') }}<input v-model.number="roofForm.angle" type="number" min="0" max="60"/></label>
        <label>{{ t('calc_roof_overlap') }}<input v-model.number="roofForm.overlap" type="number" min="0" max="30"/></label>
      </div>
      <button class="btn-calc" @click="calculate">{{ t('calc_calculate') }}</button>
    </div>
    <div v-if="results" class="results">
      <h3>{{ t('calc_result_title') }}</h3>
      <div class="result-grid">
        <div v-for="r in results" :key="r.label" class="result-card">
          <div class="rval">{{ r.value }}</div>
          <div class="rlbl">{{ r.label }}</div>
        </div>
      </div>
      <div v-if="suggested.length" class="suggested">
        <h4>{{ t('calc_suggested') }}</h4>
        <div class="sgrid"><ProductCard v-for="p in suggested" :key="p.id" :product="p" /></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page{max-width:900px;margin:0 auto;padding:16px}
h1{font-size:22px;margin-bottom:4px}
.desc{color:var(--muted);font-size:14px;margin-bottom:16px}
.tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.tab{padding:8px 16px;border:2px solid var(--border);border-radius:10px;background:var(--surface);cursor:pointer;font-weight:600;font-size:14px}
.tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.form-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.form-grid label{font-size:13px;color:var(--muted);font-weight:600;display:flex;flex-direction:column;gap:4px}
.form-grid input,.form-grid select{padding:10px;border:1px solid var(--border);border-radius:8px;font-size:15px;background:var(--bg);color:var(--text)}
.btn-calc{width:100%;margin-top:12px;padding:12px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:700;cursor:pointer}
.results{margin-top:20px;background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:20px}
.result-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:16px}
.result-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center}
.rval{font-size:22px;font-weight:800;color:var(--accent)}
.rlbl{font-size:12px;color:var(--muted);margin-top:2px}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
@media(max-width:600px){.form-grid{grid-template-columns:1fr}}
</style>
