// Contrato com a API: aliases dos tipos gerados (src/api/schema.d.ts)
import type { components } from '@/api/schema'

type Schemas = components['schemas']

export type Category = Schemas['Category']
// Sem estreitamentos: o hook shop.schema.require_response_fields já marca todos os campos
// da resposta como obrigatórios (ex.: stock, que tem default no modelo).
export type Product = Schemas['Product']
export type Order = Schemas['Order']
export type OrderItem = Schemas['OrderItem']
export type OrderStatus = Schemas['StatusEnum']
export type Me = Schemas['Me']

/* Envelope do PageNumberPagination do DRF. */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/* Corpo de erro da API (Problem Details; não está no schema) */
export interface Problem {
  type: string
  title: string
  status: number
  errors?: Record<string, string | string[]>
}
