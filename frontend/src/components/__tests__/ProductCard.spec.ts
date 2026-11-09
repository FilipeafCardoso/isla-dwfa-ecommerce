import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ProductCard from '../ProductCard.vue'
import type { Product } from '@/types'

const product: Product = {
  id: 7,
  sku: 'SKU-00007',
  name: '<b>Lamp</b>',
  category: 1,
  category_name: 'Lamps',
  price: '9.90',
  stock: 3,
  attributes: {},
  is_active: true,
  created_at: '2026-11-01T00:00:00Z',
}

describe('ProductCard', () => {
  it('mostra o nome como texto, sem interpretar HTML', () => {
    const wrapper = mount(ProductCard, { props: { product } })
    expect(wrapper.find('h2').text()).toBe('<b>Lamp</b>')
    expect(wrapper.find('b').exists()).toBe(false)
  })

  it('um clique emite select com o id do produto', async () => {
    const wrapper = mount(ProductCard, { props: { product } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('select')).toEqual([[7]])
  })
})
