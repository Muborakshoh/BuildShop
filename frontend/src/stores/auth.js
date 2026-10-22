import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const user = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => ['admin','ADMIN','manager','MANAGER'].includes(user.value?.role))
  const isStaff = computed(() => ['admin','ADMIN','manager','MANAGER','seller','SELLER'].includes(user.value?.role))

  async function getMe() {
    if (!token.value) return null
    try {
      const res = await fetch('/api/users/me', {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      if (res.ok) { user.value = await res.json(); return user.value }
      user.value = null
    } catch { user.value = null }
    return null
  }

  async function login(email, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Login failed') }
    const data = await res.json()
    token.value = data.access_token
    refreshToken.value = data.refresh_token
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    await getMe()
    return user.value
  }

  async function register(full_name, email, password, verification_code) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name, email, password, verification_code })
    })
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Register failed') }
    return res.json()
  }

  async function refresh() {
    try {
      const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken.value })
      })
      if (res.ok) {
        const d = await res.json()
        token.value = d.access_token
        refreshToken.value = d.refresh_token
        localStorage.setItem('access_token', d.access_token)
        localStorage.setItem('refresh_token', d.refresh_token)
        return true
      }
    } catch {}
    return false
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { token, refreshToken, user, isLoggedIn, isAdmin, isStaff, getMe, login, register, refresh, logout }
})
