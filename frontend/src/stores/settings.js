import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

// Color palette definitions with gradients
const COLOR_PALETTES = {
  blue:     { accent: '#2563eb', hover: '#1d4ed8', bg8: 'rgba(37,99,235,.08)',  gradient: 'linear-gradient(135deg,#1e40af 0%,#3b82f6 50%,#0ea5e9 100%)' },
  indigo:   { accent: '#4f46e5', hover: '#4338ca', bg8: 'rgba(79,70,229,.08)',  gradient: 'linear-gradient(135deg,#3730a3 0%,#6366f1 50%,#818cf8 100%)' },
  purple:   { accent: '#7c3aed', hover: '#6d28d9', bg8: 'rgba(124,58,237,.08)', gradient: 'linear-gradient(135deg,#5b21b6 0%,#8b5cf6 50%,#a78bfa 100%)' },
  pink:     { accent: '#db2777', hover: '#be185d', bg8: 'rgba(219,39,119,.08)', gradient: 'linear-gradient(135deg,#9d174d 0%,#ec4899 50%,#f472b6 100%)' },
  rose:     { accent: '#e11d48', hover: '#be123c', bg8: 'rgba(225,29,72,.08)',  gradient: 'linear-gradient(135deg,#9f1239 0%,#f43f5e 50%,#fb7185 100%)' },
  orange:   { accent: '#ea580c', hover: '#c2410c', bg8: 'rgba(234,88,12,.08)',  gradient: 'linear-gradient(135deg,#9a3412 0%,#f97316 50%,#fb923c 100%)' },
  amber:    { accent: '#d97706', hover: '#b45309', bg8: 'rgba(217,119,6,.08)',  gradient: 'linear-gradient(135deg,#92400e 0%,#f59e0b 50%,#fbbf24 100%)' },
  emerald:  { accent: '#059669', hover: '#047857', bg8: 'rgba(5,150,105,.08)',  gradient: 'linear-gradient(135deg,#065f46 0%,#10b981 50%,#34d399 100%)' },
  teal:     { accent: '#0d9488', hover: '#0f766e', bg8: 'rgba(13,148,136,.08)', gradient: 'linear-gradient(135deg,#115e59 0%,#14b8a6 50%,#2dd4bf 100%)' },
  cyan:     { accent: '#0891b2', hover: '#0e7490', bg8: 'rgba(8,145,178,.08)',  gradient: 'linear-gradient(135deg,#155e75 0%,#06b6d4 50%,#22d3ee 100%)' },
  slate:    { accent: '#475569', hover: '#334155', bg8: 'rgba(71,85,105,.08)',  gradient: 'linear-gradient(135deg,#1e293b 0%,#64748b 50%,#94a3b8 100%)' },
}

export { COLOR_PALETTES }

export const useSettingsStore = defineStore('settings', () => {
  const theme = ref(localStorage.getItem('theme') || 'light')
  const lang = ref(localStorage.getItem('lang') || 'tj')
  const colorKey = ref(localStorage.getItem('colorKey') || 'blue')
  const siteSettings = ref({})

  function setTheme(t) {
    theme.value = t
    localStorage.setItem('theme', t)
    document.documentElement.setAttribute('data-theme', t)
  }

  function setLang(l) {
    lang.value = l
    localStorage.setItem('lang', l)
  }

  function setColor(key) {
    const palette = COLOR_PALETTES[key]
    if (!palette) return
    colorKey.value = key
    localStorage.setItem('colorKey', key)
    applyColor(palette)
  }

  function applyColor(palette) {
    const root = document.documentElement
    root.style.setProperty('--accent', palette.accent)
    root.style.setProperty('--accent-hover', palette.hover)
    root.style.setProperty('--accent-bg', palette.bg8)
    root.style.setProperty('--accent-gradient', palette.gradient)
  }

  async function loadSiteSettings() {
    try {
      const res = await fetch('/api/cms/settings/public')
      if (res.ok) siteSettings.value = await res.json()
    } catch {}
  }

  // Apply theme + color on init
  document.documentElement.setAttribute('data-theme', theme.value)
  const savedPalette = COLOR_PALETTES[colorKey.value]
  if (savedPalette) applyColor(savedPalette)

  return { theme, lang, colorKey, siteSettings, setTheme, setLang, setColor, loadSiteSettings }
})
