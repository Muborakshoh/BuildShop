<script setup>
import { useToast } from '@/utils/toast'
const { toasts } = useToast()
</script>

<template>
  <Teleport to="body">
    <div class="toast-wrap">
      <TransitionGroup name="toast">
        <div v-for="t in toasts" :key="t.id" :class="['toast', 'toast--'+t.type]">{{ t.message }}</div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-wrap{position:fixed;top:60px;right:16px;z-index:20000;display:flex;flex-direction:column;gap:8px}
.toast{padding:12px 20px;border-radius:10px;color:#fff;font-size:14px;font-weight:600;box-shadow:0 4px 16px rgba(0,0,0,.15);max-width:320px}
.toast--success{background:#16a34a}
.toast--error{background:#ef4444}
.toast--info{background:#2563eb}
.toast-enter-active,.toast-leave-active{transition:all .3s}
.toast-enter-from{transform:translateX(100%);opacity:0}
.toast-leave-to{opacity:0;transform:translateY(-10px)}
</style>
