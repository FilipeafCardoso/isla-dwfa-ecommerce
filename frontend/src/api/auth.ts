// Middleware do openapi-fetch: Bearer em cada pedido; num 401 renova uma vez e repete
import type { Middleware } from 'openapi-fetch'
import { useAuth } from '@/stores/auth'

// Endpoints que não levam Bearer nem são repetidos (evita loops de renovação)
const SKIP = ['/api/v1/auth/token/', '/api/v1/auth/token/refresh/']
// Cópia de cada pedido, por id: o corpo é consumido no envio
const clones = new Map<string, Request>()

export const authMiddleware: Middleware = {
  async onRequest({ request, schemaPath, id }) {
    if (SKIP.includes(schemaPath)) return request
    const auth = useAuth()
    if (auth.access) request.headers.set('Authorization', `Bearer ${auth.access}`)
    clones.set(id, request.clone())
    return request
  },
  async onResponse({ response, id }) {
    const retry = clones.get(id)
    clones.delete(id)
    if (response.status !== 401 || !retry) return response
    const access = await useAuth().refreshAccess() // renova UMA vez (single-flight)
    if (!access) return response // refreshAccess já fez logout()
    retry.headers.set('Authorization', `Bearer ${access}`)
    // Segunda e última tentativa, fora do middleware: um novo 401 é definitivo
    return globalThis.fetch(retry)
  },
  onError({ id }) {
    // Erro de rede: não há resposta, mas o clone tem de sair do Map
    clones.delete(id)
  },
}
