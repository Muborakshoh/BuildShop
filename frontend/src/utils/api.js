import { useAuthStore } from '@/stores/auth'

const BASE = '/api'

class ApiClient {
  async request(path, opts = {}) {
    const auth = useAuthStore()
    const headers = { 'Content-Type': 'application/json', ...opts.headers }
    if (auth.token) headers['Authorization'] = `Bearer ${auth.token}`

    const res = await fetch(`${BASE}${path}`, { ...opts, headers })

    if (res.status === 401 && auth.refreshToken) {
      const ok = await auth.refresh()
      if (ok) {
        headers['Authorization'] = `Bearer ${auth.token}`
        const retry = await fetch(`${BASE}${path}`, { ...opts, headers })
        if (!retry.ok) throw new Error(await retry.text())
        return retry.status === 204 ? null : retry.json()
      }
      auth.logout()
      throw new Error('Unauthorized')
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || res.statusText)
    }
    return res.status === 204 ? null : res.json()
  }

  get(path) { return this.request(path) }
  post(path, data) { return this.request(path, { method: 'POST', body: JSON.stringify(data) }) }
  put(path, data) { return this.request(path, { method: 'PUT', body: JSON.stringify(data) }) }
  patch(path, data) { return this.request(path, { method: 'PATCH', body: JSON.stringify(data) }) }
  delete(path) { return this.request(path, { method: 'DELETE' }) }
}

export const api = new ApiClient()
