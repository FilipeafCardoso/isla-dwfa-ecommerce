// Cliente HTTP tipado sobre fetch
import type { Problem } from '@/types'

const API_URL = import.meta.env.VITE_API_URL

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
}

function messageOf(status: number, problem: Problem | null): string {
  const detail = problem?.errors?.detail
  if (typeof detail === 'string') return detail
  return problem?.title ?? `HTTP ${status}`
}

export type Query = Record<string, string | number | undefined>

export async function get<T>(path: string, query?: Query): Promise<T> {
  const url = new URL(path, API_URL)
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== '') url.searchParams.set(key, String(value))
  }

  const res = await fetch(url, { headers: { Accept: 'application/json' } })

  if (!res.ok) {
    let problem: Problem | null = null
    try {
      problem = (await res.json()) as Problem
    } catch {
    }
    throw new ApiError(res.status, problem)
  }
  return (await res.json()) as T
}