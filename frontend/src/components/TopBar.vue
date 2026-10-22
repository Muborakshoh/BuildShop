<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import i18n from '@/i18n'
import ColorPicker from './ColorPicker.vue'

const settings = useSettingsStore()
const auth = useAuthStore()
const { t } = useI18n()
const router = useRouter()

const showMenu = ref(false)
const showInfo = ref(false)
const showGuestSettings = ref(false)
const fontSize = ref(localStorage.getItem('fontSize') || '16')
const menuRef = ref(null)
const guestRef = ref(null)

function toggleMenu() { showMenu.value = !showMenu.value; showInfo.value = false }
function toggleGuestSettings() { showGuestSettings.value = !showGuestSettings.value }

function changeLang(val) {
  settings.setLang(val)
  i18n.global.locale.value = val
}
function changeFontSize(val) {
  fontSize.value = val
  localStorage.setItem('fontSize', val)
  document.documentElement.style.fontSize = val + 'px'
}
function doLogout() {
  auth.logout()
  showMenu.value = false
  router.push('/')
}

function onClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    showMenu.value = false
    showInfo.value = false
  }
  if (guestRef.value && !guestRef.value.contains(e.target)) {
    showGuestSettings.value = false
  }
}
onMounted(() => {
  document.addEventListener('click', onClickOutside, true)
  if (localStorage.getItem('fontSize')) {
    document.documentElement.style.fontSize = localStorage.getItem('fontSize') + 'px'
  }
})
onUnmounted(() => document.removeEventListener('click', onClickOutside, true))
</script>

<template>
  <header class="topbar">
    <router-link to="/" class="brand">
      <div class="brand-icon">С</div>
      <span>{{ settings.siteSettings.site_name || 'СохтМатериал' }}</span>
    </router-link>
    <div class="topbar-right">
      <!-- Guest: settings gear + login button -->
      <template v-if="!auth.isLoggedIn">
        <div class="guest-settings-wrap" ref="guestRef">
          <button class="btn-gear" @click.stop="toggleGuestSettings" :title="t('settings') || 'Танзимот'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          </button>

          <Transition name="dropdown">
            <div v-if="showGuestSettings" class="guest-dropdown">
              <div class="dd-section-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
                <span>{{ t('settings') || 'Танзимот' }}</span>
              </div>

              <div class="dd-row">
                <span class="dd-label">{{ t('language') || 'Забон' }}</span>
                <div class="dd-lang-btns">
                  <button v-for="l in [{v:'tj',l:'🇹🇯 TJ'},{v:'ru',l:'🇷🇺 RU'},{v:'en',l:'🇬🇧 EN'}]" :key="l.v"
                    :class="['lang-btn',{active:settings.lang===l.v}]"
                    @click="changeLang(l.v)">{{ l.l }}</button>
                </div>
              </div>

              <div class="dd-row">
                <span class="dd-label">{{ t('theme') || 'Тема' }}</span>
                <div class="dd-theme-btns">
                  <button :class="['theme-btn',{active:settings.theme==='light'}]" @click="settings.setTheme('light')">☀️ {{ t('light') || '' }}</button>
                  <button :class="['theme-btn',{active:settings.theme==='dark'}]" @click="settings.setTheme('dark')">🌙 {{ t('dark') || '' }}</button>
                </div>
              </div>

              <div class="dd-row">
                <span class="dd-label">{{ t('font_size') || 'Ҳарф' }}</span>
                <div class="dd-font-btns">
                  <button v-for="s in [{v:'14',l:'A'},{v:'16',l:'A'},{v:'18',l:'A'}]" :key="s.v"
                    :class="['font-btn',{active:fontSize===s.v}]"
                    :style="{fontSize:s.v+'px'}"
                    @click="changeFontSize(s.v)">{{ s.l }}</button>
                </div>
              </div>

              <ColorPicker />
            </div>
          </Transition>
        </div>

        <router-link to="/auth" class="btn-login">{{ t('login') }}</router-link>
      </template>

      <!-- Logged in: avatar dropdown -->
      <div v-else class="user-wrap" ref="menuRef">
        <button class="btn-user" @click.stop="toggleMenu">
          {{ (auth.user?.full_name || '?')[0] }}
        </button>

        <Transition name="dropdown">
          <div v-if="showMenu" class="user-dropdown">
            <div class="dd-header">
              <div class="dd-avatar">{{ (auth.user?.full_name || '?')[0] }}</div>
              <div class="dd-user-info">
                <span class="dd-name">{{ auth.user?.full_name || '—' }}</span>
                <span class="dd-email">{{ auth.user?.email || '' }}</span>
              </div>
            </div>

            <div class="dd-divider"></div>

            <div class="dd-section-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
              <span>{{ t('settings') || 'Танзимот' }}</span>
            </div>

            <div class="dd-row">
              <span class="dd-label">{{ t('theme') || 'Тема' }}</span>
              <div class="dd-theme-btns">
                <button :class="['theme-btn',{active:settings.theme==='light'}]" @click="settings.setTheme('light')">☀️</button>
                <button :class="['theme-btn',{active:settings.theme==='dark'}]" @click="settings.setTheme('dark')">🌙</button>
              </div>
            </div>

            <div class="dd-row">
              <span class="dd-label">{{ t('font_size') || 'Ҳарф' }}</span>
              <div class="dd-font-btns">
                <button v-for="s in [{v:'14',l:'A'},{v:'16',l:'A'},{v:'18',l:'A'}]" :key="s.v"
                  :class="['font-btn',{active:fontSize===s.v}]"
                  :style="{fontSize:s.v+'px'}"
                  @click="changeFontSize(s.v)">{{ s.l }}</button>
              </div>
            </div>

            <div class="dd-row">
              <span class="dd-label">{{ t('language') || 'Забон' }}</span>
              <div class="dd-lang-btns">
                <button v-for="l in [{v:'tj',l:'TJ'},{v:'ru',l:'RU'},{v:'en',l:'EN'}]" :key="l.v"
                  :class="['lang-btn',{active:settings.lang===l.v}]"
                  @click="changeLang(l.v)">{{ l.l }}</button>
              </div>
            </div>

            <ColorPicker />

            <div class="dd-divider"></div>

            <button class="dd-item" @click="showInfo=!showInfo">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span>{{ t('site_info') || 'Маълумот' }}</span>
              <svg :class="['chevron',{open:showInfo}]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </button>

            <Transition name="slide-info">
              <div v-if="showInfo" class="dd-info-panel">
                <div class="info-row"><span>{{ t('project_name') || 'Лоиҳа' }}</span><strong>СохтМатериал</strong></div>
                <div class="info-row"><span>{{ t('version') || 'Версия' }}</span><strong>2.0.0</strong></div>
                <div class="info-row"><span>Backend</span><strong>FastAPI + PostgreSQL</strong></div>
                <div class="info-row"><span>Frontend</span><strong>Vue 3 + Vite</strong></div>
              </div>
            </Transition>

            <div class="dd-divider"></div>

            <button class="dd-item dd-logout" @click="doLogout">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
              <span>{{ t('logout') || 'Баромадан' }}</span>
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topbar{position:sticky;top:0;z-index:100;height:50px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;background:var(--surface);border-bottom:1px solid var(--border);backdrop-filter:blur(12px)}
.brand{display:flex;align-items:center;gap:8px;font-weight:800;font-size:16px;text-decoration:none;color:var(--text)}
.brand-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;background:var(--accent-gradient);color:#fff;font-size:14px;font-weight:900}
.topbar-right{display:flex;align-items:center;gap:8px}
.btn-login{padding:6px 14px;background:var(--accent);color:#fff;border-radius:8px;font-size:12px;font-weight:600;text-decoration:none}
.btn-user{width:34px;height:34px;border-radius:50%;background:var(--accent);color:#fff;border:none;font-weight:700;cursor:pointer;font-size:14px;transition:box-shadow .2s}
.btn-user:hover{box-shadow:0 0 0 3px var(--accent-bg)}

/* Guest settings gear */
.guest-settings-wrap{position:relative}
.btn-gear{width:34px;height:34px;border-radius:10px;background:var(--bg);border:1px solid var(--border);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}
.btn-gear:hover{background:var(--accent-bg);border-color:var(--accent)}
.btn-gear svg{width:18px;height:18px;color:var(--muted)}
.btn-gear:hover svg{color:var(--accent)}

.guest-dropdown{position:absolute;top:calc(100% + 8px);right:0;width:260px;background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.15);z-index:200;padding:6px 0}

/* User dropdown */
.user-wrap{position:relative}
.user-dropdown{position:absolute;top:calc(100% + 8px);right:0;width:280px;background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.15);z-index:200;overflow:hidden}

.dd-header{display:flex;align-items:center;gap:10px;padding:14px 16px}
.dd-avatar{width:38px;height:38px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px;flex-shrink:0}
.dd-user-info{display:flex;flex-direction:column;min-width:0}
.dd-name{font-weight:700;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dd-email{font-size:12px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

.dd-divider{height:1px;background:var(--border);margin:0 12px}

.dd-section-label{display:flex;align-items:center;gap:6px;padding:10px 16px 4px;font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.dd-section-label svg{width:14px;height:14px}

.dd-row{display:flex;align-items:center;justify-content:space-between;padding:8px 16px}
.dd-label{font-size:13px;color:var(--text)}

.dd-theme-btns,.dd-font-btns,.dd-lang-btns{display:flex;gap:4px}
.theme-btn,.font-btn,.lang-btn{min-width:32px;height:30px;border:1px solid var(--border);border-radius:8px;background:var(--bg);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--text);transition:all .15s;padding:0 6px}
.theme-btn.active,.font-btn.active,.lang-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.lang-btn{width:auto;padding:0 10px;font-weight:600;font-size:12px}

.dd-item{display:flex;align-items:center;gap:8px;width:100%;padding:10px 16px;border:none;background:none;cursor:pointer;font-size:13px;font-weight:500;color:var(--text);text-align:left;font-family:inherit;transition:background .15s}
.dd-item:hover{background:var(--accent-bg)}
.dd-item svg{width:18px;height:18px;flex-shrink:0}
.dd-item span{flex:1}
.chevron{width:16px!important;height:16px!important;transition:transform .2s;color:var(--muted)}
.chevron.open{transform:rotate(180deg)}

.dd-info-panel{padding:4px 16px 10px;display:flex;flex-direction:column;gap:4px}
.info-row{display:flex;justify-content:space-between;font-size:12px;padding:2px 0}
.info-row span{color:var(--muted)}
.info-row strong{color:var(--text);font-weight:600}

.dd-logout{color:#ef4444}
.dd-logout:hover{background:rgba(239,68,68,.06)}
.dd-logout svg{stroke:#ef4444}

.dropdown-enter-active{animation:dd-in .2s ease}
.dropdown-leave-active{animation:dd-in .15s ease reverse}
@keyframes dd-in{from{opacity:0;transform:translateY(-8px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}

.slide-info-enter-active,.slide-info-leave-active{transition:all .2s ease;overflow:hidden}
.slide-info-enter-from,.slide-info-leave-to{max-height:0;opacity:0}
.slide-info-enter-to,.slide-info-leave-from{max-height:200px;opacity:1}
</style>
