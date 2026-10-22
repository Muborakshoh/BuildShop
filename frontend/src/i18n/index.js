import { createI18n } from 'vue-i18n'
import tj from './tj.json'
import ru from './ru.json'
import en from './en.json'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('lang') || 'tj',
  fallbackLocale: 'tj',
  messages: { tj, ru, en }
})

export default i18n
