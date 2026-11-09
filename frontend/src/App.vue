<script setup lang="ts">
import { watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'

const auth = useAuth()
const route = useRoute()
const router = useRouter()

// Renovação falhou a meio da utilização: o logout() limpou a store, mas o guard só corre
// na próxima navegação. Se o ecrã atual for privado, ir já para o login.
watch(
  () => auth.isLoggedIn,
  (loggedIn) => {
    if (!loggedIn && route.meta.requiresAuth) {
      router.replace({ name: 'login', query: { next: route.fullPath } })
    }
  },
)

function logout() {
  auth.logout()
  router.push({ name: 'products' })
}
</script>

<template>
  <header>
    <h1>ISLA Shop</h1>
    <nav>
      <RouterLink :to="{ name: 'products' }">Produtos</RouterLink>
      <template v-if="auth.isLoggedIn">
        <RouterLink :to="{ name: 'orders' }">As minhas encomendas</RouterLink>
        <RouterLink :to="{ name: 'order-new' }">Nova encomenda</RouterLink>
      </template>
      <span class="session">
        <template v-if="auth.isLoggedIn">
          {{ auth.user?.username }}
          <button type="button" @click="logout">Logout</button>
        </template>
        <RouterLink v-else :to="{ name: 'login' }">Entrar</RouterLink>
      </span>
    </nav>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
header {
  margin-bottom: 1.5rem;
}
nav {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
}
nav a.router-link-exact-active {
  font-weight: bold;
}
.session {
  margin-left: auto;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
</style>
