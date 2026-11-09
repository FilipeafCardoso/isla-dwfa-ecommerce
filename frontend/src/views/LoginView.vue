<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { useAuth } from '@/stores/auth'

const auth = useAuth()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const submitting = ref(false)
const error = ref<string | null>(null)

function messageFor(e: unknown): string {
  if (e instanceof ApiError && e.status === 401) return 'Utilizador ou password inválidos.'
  if (e instanceof ApiError && e.status === 429)
    return 'Demasiadas tentativas — aguarde um minuto e tente de novo.'
  return 'Não foi possível contactar a API.'
}

async function submit() {
  submitting.value = true
  error.value = null
  try {
    await auth.login(username.value, password.value)
  } catch (e) {
    error.value = messageFor(e)
    return
  } finally {
    submitting.value = false
  }
  // Só caminhos internos: "//site.com" ou "https://…" levariam para fora da app
  const next = route.query.next
  const target =
    typeof next === 'string' && next.startsWith('/') && !next.startsWith('//') ? next : '/orders'
  await router.push(target)
}
</script>

<template>
  <section class="login">
    <h1>Entrar</h1>
    <form @submit.prevent="submit">
      <label for="username">Utilizador</label>
      <input id="username" v-model.trim="username" autocomplete="username" required />

      <label for="password">Password</label>
      <input
        id="password"
        v-model="password"
        type="password"
        autocomplete="current-password"
        required
      />

      <p v-if="error" role="alert" class="error">{{ error }}</p>

      <button type="submit" :disabled="submitting">
        {{ submitting ? 'A entrar…' : 'Entrar' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.login {
  max-width: 320px;
}
form {
  display: grid;
  gap: 0.5rem;
}
input {
  padding: 0.5rem;
}
button {
  margin-top: 0.5rem;
  padding: 0.5rem;
}
.error {
  color: #c0392b;
}
</style>
