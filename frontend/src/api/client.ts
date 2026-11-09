// Cliente HTTP tipado, gerado a partir do OpenAPI (npm run gen:api)
import createClient from 'openapi-fetch'
import type { paths } from './schema'
import type { Problem } from '@/types'

export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_URL,
  headers: { Accept: 'application/json' },
  // O openapi-fetch guarda o fetch global ao criar o cliente; assim é lido a cada pedido
  // e o vi.stubGlobal('fetch', …) dos testes funciona.
  fetch: (request) => globalThis.fetch(request),
})

/** Erro de um pedido à API, com o corpo Problem Details */
export class ApiError extends Error {
  readonly status: number
  readonly problem: Problem | null

  constructor(status: number, problem: Problem | null) {
    super(messageOf(status, problem))
    this.name = 'ApiError'
    this.status = status
    this.problem = problem
  }

  /** Mensagem de um campo (ex.: 'quantity'), ou null. */
  field(name: string): string | null {
    const value = this.problem?.errors?.[name]
    if (value === undefined) return null
    return Array.isArray(value) ? value.join(' ') : value
  }

  /** Mensagem geral: errors.detail, senão o title, senão a message. */
  get detail(): string {
    return this.field('detail') ?? this.problem?.title ?? this.message
  }
}

function messageOf(status: number, problem: Problem | null): string {
  const detail = problem?.errors?.detail
  if (typeof detail === 'string') return detail
  return problem?.title ?? `HTTP ${status}`
}

type Result<T> = { data?: T; error?: unknown; response: Response }

/** O openapi-fetch nunca lança; o useFetch e as views querem uma promise que lança. */
export async function unwrap<T>(call: Promise<Result<T>>): Promise<T> {
  const { data, error, response } = await call
  if (!response.ok || data === undefined) {
    throw new ApiError(response.status, (error ?? null) as Problem | null)
  }
  return data
}
