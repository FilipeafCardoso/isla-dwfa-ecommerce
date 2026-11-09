// Sessão: access só em memória; refresh em localStorage (sobrevive ao F5)
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api, unwrap } from '@/api/client'
import type { Me } from '@/types'

const REFRESH_KEY = 'refresh'

export const useAuth = defineStore('auth', () => {
  const access = ref<string | null>(null)
  const refresh = ref<string | null>(localStorage.getItem(REFRESH_KEY))
  const user = ref<Me | null>(null)
  const ready = ref(false)

  const isLoggedIn = computed(() => user.value !== null)
  const isGestor = computed(() => user.value?.groups.includes('gestores') ?? false)

  /** Único escritor do refresh: ref + localStorage. O access nunca vai para o storage. */
  function setRefresh(value: string | null) {
    refresh.value = value
    if (value) localStorage.setItem(REFRESH_KEY, value)
    else localStorage.removeItem(REFRESH_KEY)
  }

  async function login(username: string, password: string) {
    const pair = await unwrap(api.POST('/api/v1/auth/token/', { body: { username, password } }))
    access.value = pair.access
    setRefresh(pair.refresh)
    try {
      user.value = await unwrap(api.GET('/api/v1/me/'))
    } catch (e) {
      // Não deixar a store meio preenchida
      logout()
      throw e
    }
  }

  function logout() {
    access.value = null
    setRefresh(null)
    user.value = null
  }

  // Single-flight: com rotação + blacklist (Ficha 03) cada refresh só serve uma vez.
  // Se vários pedidos levarem 401 ao mesmo tempo, partilham a mesma renovação;
  // uma segunda renovação com o refresh já gasto falharia e expulsava o utilizador.
  let inFlight: Promise<string | null> | null = null

  /** O único sítio onde um refresh é gasto. Devolve o access novo, ou null (e faz logout). */
  function refreshAccess(): Promise<string | null> {
    inFlight ??= (async () => {
      const current = refresh.value
      if (!current) return null
      const { data } = await api.POST('/api/v1/auth/token/refresh/', {
        body: { refresh: current },
      })
      if (!data) {
        logout()
        return null
      }
      access.value = data.access
      if (data.refresh) setRefresh(data.refresh) // rotação
      return data.access
    })().finally(() => {
      inFlight = null
    })
    return inFlight
  }

  /** Arranque: recupera a sessão a partir do refresh guardado. */
  async function bootstrap() {
    try {
      if (refresh.value && (await refreshAccess())) {
        user.value = await unwrap(api.GET('/api/v1/me/'))
      }
    } catch {
      // API em baixo ou /me/ falhou: começa sem sessão
      logout()
    } finally {
      ready.value = true
    }
  }

  return {
    access,
    refresh,
    user,
    ready,
    isLoggedIn,
    isGestor,
    login,
    logout,
    refreshAccess,
    bootstrap,
  }
})
