import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import LoginView from '../LoginView.vue'

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

// Rotas mínimas: só o necessário para o LoginView navegar
function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: LoginView },
      { path: '/orders', name: 'orders', component: { template: '<p>Encomendas</p>' } },
    ],
  })
}

describe('LoginView', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('um 401 mostra a mensagem e não sai do login', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValue(
        json(
          {
            type: 'about:blank',
            title: 'Unauthorized',
            status: 401,
            errors: { detail: 'No active account found with the given credentials' },
          },
          401,
        ),
      ),
    )
    const router = makeRouter()
    await router.push('/login?next=/orders')
    const push = vi.spyOn(router, 'push')
    const wrapper = mount(LoginView, { global: { plugins: [router] } })

    await wrapper.find('#username').setValue('ana')
    await wrapper.find('#password').setValue('errada')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').text()).toBe('Utilizador ou password inválidos.')
    expect(push).not.toHaveBeenCalled()
    expect(router.currentRoute.value.name).toBe('login')
  })
})
