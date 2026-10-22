export function money(amount) {
  const n = parseFloat(amount) || 0
  return n.toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' TJS'
}

export function escapeHtml(str) {
  const d = document.createElement('div')
  d.textContent = str || ''
  return d.innerHTML
}

export function ml(item, field) {
  if (!item) return ''
  const lang = localStorage.getItem('lang') || 'tj'
  if (lang === 'tj') return item[field] || ''
  let tr = item.translations
  if (!tr) return item[field] || ''
  if (typeof tr === 'string') {
    try { tr = JSON.parse(tr) } catch { return item[field] || '' }
  }
  // Support flat format: {ru_name: "..."} and nested: {ru: {name: "..."}}
  return tr[`${lang}_${field}`] || tr[lang]?.[field] || item[field] || ''
}

export function debounce(fn, ms = 300) {
  let timer
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), ms)
  }
}
