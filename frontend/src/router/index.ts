import { createRouter, createWebHistory } from 'vue-router'
import ProductsView from '@/views/ProductsView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import { useAuth } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: { name: 'products' } },
    { path: '/products', name: 'products', component: ProductsView },
    {
      // (\\d+): só ids numéricos; /products/abc cai no catch-all
      path: '/products/:id(\\d+)',
      name: 'product',
      props: true,
      // lazy: o código do detalhe só é descarregado quando se abre o primeiro produto
      component: () => import('@/views/ProductView.vue'),
    },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    {
      path: '/orders',
      name: 'orders',
      component: () => import('@/views/OrdersView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/orders/new',
      name: 'order-new',
      component: () => import('@/views/NewOrderView.vue'),
      meta: { requiresAuth: true },
    },
    // Tem de ser a última rota
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
  ],
})

// O guard protege o ecrã; os dados são protegidos pela API (401/403/404 da Ficha 03)
router.beforeEach((to) => {
  const auth = useAuth()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  // Já tem sessão: o login não faz sentido
  if (to.name === 'login' && auth.isLoggedIn) return { name: 'orders' }
})

export default router
