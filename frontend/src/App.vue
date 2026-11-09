<script setup lang="ts">
import { watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
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
</script>

<template>
  <header>
    <h1>ISLA Shop</h1>
  </header>
  <main>
    <RouterView />
  </main>
</template>
