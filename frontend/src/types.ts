// Contrato com a API

export interface Category {
  id: number
  name: string
}

export interface Product {
  id: number
  sku: string
  name: string
  category: number
  category_name: string
  price: string
  stock: number
  /* chaves e valores livres, definidos por produto. */
  attributes: Record<string, unknown>
  is_active: boolean
  created_at: string
}

/* Envelope do PageNumberPagination do DRF. */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/* Corpo de erro da API */
export interface Problem {
  type: string
  title: string
  status: number
  errors?: Record<string, string | string[]>
}