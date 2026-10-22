<script setup>
import { useCartStore } from '@/stores/cart'
import { useI18n } from 'vue-i18n'
import { money, ml } from '@/utils/helpers'
import { ref } from 'vue'

const props = defineProps({ product: Object })
const cart = useCartStore()
const { t } = useI18n()
const added = ref(false)

function addToCart() {
  cart.add(props.product)
  added.value = true
  setTimeout(() => added.value = false, 1500)
}
</script>

<template>
  <div class="pcard">
    <router-link :to="'/products/'+product.id" class="pcard-img">
      <div class="pcard-placeholder">{{ ml(product,'name')?.[0] || '?' }}</div>
    </router-link>
    <div class="pcard-body">
      <router-link :to="'/products/'+product.id" class="pcard-name">{{ ml(product,'name') }}</router-link>
      <div class="pcard-price">{{ money(product.price) }}</div>
      <div class="pcard-stock" :class="product.stock_quantity>0?'in':'out'">
        {{ product.stock_quantity > 0 ? t('in_stock')+': '+product.stock_quantity+' '+(product.unit||'') : t('out_of_stock') || 'Нест' }}
      </div>
      <button class="pcard-btn" @click="addToCart" :disabled="product.stock_quantity<=0">
        {{ added ? '✓' : t('add_to_cart') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.pcard{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden;transition:box-shadow .2s}
.pcard:hover{box-shadow:0 4px 20px rgba(0,0,0,.08)}
.pcard-img{display:block;height:160px;background:linear-gradient(135deg,var(--accent-bg),var(--bg))}
.pcard-placeholder{height:100%;display:flex;align-items:center;justify-content:center;font-size:48px;font-weight:900;color:var(--accent);opacity:.3}
.pcard-body{padding:12px}
.pcard-name{display:block;font-weight:600;font-size:14px;color:var(--text);text-decoration:none;margin-bottom:4px;line-height:1.3}
.pcard-name:hover{color:var(--accent)}
.pcard-price{font-size:18px;font-weight:800;color:var(--accent);margin-bottom:4px}
.pcard-stock{font-size:12px;margin-bottom:8px}
.pcard-stock.in{color:#16a34a}
.pcard-stock.out{color:#ef4444}
.pcard-btn{width:100%;padding:8px;border:none;border-radius:8px;background:var(--accent);color:#fff;font-weight:600;font-size:13px;cursor:pointer;transition:opacity .2s}
.pcard-btn:hover{opacity:.9}
.pcard-btn:disabled{background:var(--muted);cursor:not-allowed}
</style>
