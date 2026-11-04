import { createRouter, createWebHistory } from 'vue-router'
import ProductsView from '@/views/ProductsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: { name: 'products' } },
    { path: '/products', name: 'products', component: ProductsView },
  ],
})

export default router