<script setup>
import { useSettingsStore } from '@/stores/settings'
import { COLOR_PALETTES } from '@/stores/settings'
import { useI18n } from 'vue-i18n'

const settings = useSettingsStore()
const { t } = useI18n()

const colors = Object.entries(COLOR_PALETTES).map(([key, val]) => ({
  key,
  accent: val.accent,
  gradient: val.gradient,
}))
</script>

<template>
  <div class="cp-row">
    <span class="cp-label">{{ t('color_theme') }}</span>
    <div class="cp-grid">
      <button
        v-for="c in colors"
        :key="c.key"
        :class="['cp-swatch', { active: settings.colorKey === c.key }]"
        :style="{ background: c.gradient }"
        :title="c.key"
        @click="settings.setColor(c.key)"
      >
        <svg v-if="settings.colorKey === c.key" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.cp-row {
  padding: 8px 16px;
}
.cp-label {
  display: block;
  font-size: 13px;
  color: var(--text);
  margin-bottom: 8px;
}
.cp-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
}
.cp-swatch {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 10px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
}
.cp-swatch:hover {
  transform: scale(1.15);
  box-shadow: 0 2px 12px rgba(0,0,0,.2);
}
.cp-swatch.active {
  border-color: var(--text);
  box-shadow: 0 0 0 2px var(--surface), 0 0 0 4px var(--accent);
  transform: scale(1.1);
}
.cp-swatch svg {
  width: 16px;
  height: 16px;
}
</style>
