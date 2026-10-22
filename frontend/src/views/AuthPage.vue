<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-tabs">
        <button class="tab" :class="{ active: mode === 'login' }" @click="mode = 'login'; error = ''">
          {{ t('auth_login') }}
        </button>
        <button class="tab" :class="{ active: mode === 'register' }" @click="mode = 'register'; error = ''">
          {{ t('auth_register') }}
        </button>
      </div>

      <form @submit.prevent="submit" class="auth-form">
        <div v-if="mode === 'register'" class="field">
          <label>{{ t('auth_name') }}</label>
          <input v-model="fullName" type="text" required :placeholder="t('auth_namePlaceholder')" />
        </div>

        <div class="field">
          <label>Email</label>
          <input v-model="email" type="email" required placeholder="email@example.com" />
        </div>

        <div class="field">
          <label>{{ t('auth_password') }}</label>
          <input v-model="password" type="password" required :placeholder="t('auth_passwordPlaceholder')" minlength="8" />
        </div>

        <div v-if="mode === 'register'" class="field">
          <label>{{ t('auth_confirmPassword') || 'Такрори парол' }}</label>
          <input v-model="confirmPassword" type="password" required :placeholder="t('auth_confirmPasswordPlaceholder') || 'Паролро такрор кунед'" minlength="8" />
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>
        <p v-if="success" class="success-msg">{{ success }}</p>

        <button type="submit" class="btn-submit" :disabled="submitting">
          {{ submitting
            ? (t('common_loading') || '...')
            : mode === 'login' ? t('auth_loginBtn') : t('auth_registerBtn')
          }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const mode = ref('login')
const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const success = ref('')
const submitting = ref(false)

async function submit() {
  error.value = ''
  success.value = ''

  if (mode.value === 'register' && password.value !== confirmPassword.value) {
    error.value = t('auth_passwordMismatch') || 'Паролҳо мувофиқат намекунанд'
    return
  }

  submitting.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(email.value, password.value)
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    } else {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName.value,
          email: email.value,
          password: password.value,
          verification_code: '000000'
        })
      })
      if (!res.ok) {
        const e = await res.json()
        const detail = e.detail || 'Register failed'
        if (detail.includes('already registered')) {
          throw new Error(t('auth_emailExists') || 'Ин email аллакай сабт шудааст')
        }
        throw new Error(detail)
      }
      // Auto-login after registration
      const data = await res.json()
      if (data.tokens) {
        localStorage.setItem('access_token', data.tokens.access_token)
        localStorage.setItem('refresh_token', data.tokens.refresh_token)
        auth.token = data.tokens.access_token
        auth.refreshToken = data.tokens.refresh_token
        await auth.getMe()
        router.push('/')
      } else {
        success.value = t('auth_registerSuccess') || 'Бомуваффақият сабт шуд! Ворид шавед.'
        mode.value = 'login'
      }
    }
  } catch (e) {
    error.value = e.message || t('auth_error') || 'Хатогӣ'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.auth-page{min-height:80vh;display:flex;align-items:center;justify-content:center;padding:24px}
.auth-card{width:100%;max-width:400px;background:var(--surface);border:1px solid var(--border);border-radius:16px;overflow:hidden}
.auth-tabs{display:flex;border-bottom:1px solid var(--border)}
.tab{flex:1;padding:14px;text-align:center;background:transparent;border:none;font-size:15px;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;transition:color .15s;font-family:inherit}
.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.auth-form{padding:20px}
.field{margin-bottom:14px}
.field label{display:block;font-size:13px;font-weight:600;color:var(--text);margin-bottom:4px}
.field input{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:10px;font-size:14px;background:var(--bg);color:var(--text);box-sizing:border-box;font-family:inherit}
.field input:focus{outline:none;border-color:var(--accent)}
.error-msg{color:#dc2626;font-size:13px;margin-bottom:12px;padding:8px 12px;background:rgba(220,38,38,.06);border-radius:8px}
.success-msg{color:#16a34a;font-size:13px;margin-bottom:12px;padding:8px 12px;background:rgba(22,163,74,.06);border-radius:8px}
.btn-submit{width:100%;padding:12px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;transition:opacity .15s}
.btn-submit:hover{opacity:.9}
.btn-submit:disabled{opacity:.5;cursor:not-allowed}
</style>
