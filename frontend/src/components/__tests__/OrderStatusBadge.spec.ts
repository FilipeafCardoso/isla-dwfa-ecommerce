import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import OrderStatusBadge from '../OrderStatusBadge.vue'
import type { OrderStatus } from '@/types'

describe('OrderStatusBadge', () => {
  it.each<[OrderStatus, string]>([
    ['pending', 'Pendente'],
    ['paid', 'Paga'],
    ['cancelled', 'Cancelada'],
  ])('%s → %s', (status, label) => {
    const wrapper = mount(OrderStatusBadge, { props: { status } })
    expect(wrapper.text()).toBe(label)
    expect(wrapper.classes()).toContain(status)
  })
})
