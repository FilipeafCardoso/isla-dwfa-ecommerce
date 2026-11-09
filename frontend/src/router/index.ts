import { createRouter, createWebHistory } from 'vue-router'
import ProductsView from '@/views/ProductsView.vue'
import NotFoundView from '@/views/NotFoundView.vue'

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
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
  ],
})

export default router
