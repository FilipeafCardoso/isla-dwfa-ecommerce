// Três estados (a carregar / erro / dados) + reload
import { ref, watchEffect, type Ref } from 'vue'
import { ApiError } from '@/api/client'

export type FetchStatus = 'loading' | 'error' | 'success'

export function useFetch<T>(fetcher: () => Promise<T>) {
  const data = ref(null) as Ref<T | null>
  const error = ref<string | null>(null)
  const status = ref<FetchStatus>('loading')

  // Só a resposta do pedido mais recente conta
  let current = 0

  function load() {
    const id = ++current
    status.value = 'loading'
    error.value = null
    // fetcher() lê props/route de forma síncrona
    fetcher().then(
      (result) => {
        if (id !== current) return
        data.value = result
        status.value = 'success'
      },
      (e: unknown) => {
        if (id !== current) return
        error.value = e instanceof ApiError ? e.message : 'Não foi possível contactar a API.'
        status.value = 'error'
      },
    )
  }

  // Re-executa sempre que algo lido dentro do fetcher muda
  watchEffect(load)

  return { data, error, status, reload: load }
}
