import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomePage.vue') },
  { path: '/products', name: 'Products', component: () => import('@/views/ProductsPage.vue') },
  { path: '/products/:id', name: 'Product', component: () => import('@/views/ProductPage.vue') },
  { path: '/categories', name: 'Categories', component: () => import('@/views/CategoriesPage.vue') },
  { path: '/cart', name: 'Cart', component: () => import('@/views/CartPage.vue') },
  { path: '/orders', name: 'Orders', component: () => import('@/views/OrdersPage.vue'), meta: { requiresAuth: true } },
  { path: '/calculator', name: 'Calculator', component: () => import('@/views/CalculatorPage.vue') },
  { path: '/auth', name: 'Auth', component: () => import('@/views/AuthPage.vue') },
  { path: '/news', name: 'News', component: () => import('@/views/NewsPage.vue') },
  { path: '/guide', name: 'Docs', component: () => import('@/views/DocsPage.vue') },
  { path: '/page/:slug', name: 'CmsPage', component: () => import('@/views/CmsPage.vue') },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  },
  {
    path: '/admin/products',
    name: 'AdminProducts',
    component: () => import('@/views/AdminProducts.vue'),
    meta: { requiresStaff: true }
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/AdminUsers.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/cms',
    name: 'AdminCms',
    component: () => import('@/views/AdminCms.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/analytics',
    name: 'AdminAnalytics',
    component: () => import('@/views/AdminAnalytics.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/cashier',
    name: 'Cashier',
    component: () => import('@/views/CashierPage.vue'),
    meta: { requiresStaff: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (!auth.user && auth.token) {
    await auth.getMe()
  }

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'Auth', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'Home' }
  }

  if (to.meta.requiresStaff && !auth.isStaff) {
    return { name: 'Home' }
  }
})

export default router
