import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuth } from '../auth'

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

describe('auth store', () => {
  beforeEach(() => {
    // Limpar antes de criar a store: o refresh inicial é lido do localStorage
    localStorage.clear()
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('login guarda o access só em memória e o refresh no localStorage', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn<typeof fetch>()
        .mockResolvedValueOnce(json({ access: 'A1', refresh: 'R1' }))
        .mockResolvedValueOnce(json({ id: 1, username: 'ana', groups: [] })),
    )
    const auth = useAuth()

    await auth.login('ana', 'pass1234')

    expect(auth.access).toBe('A1')
    expect(auth.user?.username).toBe('ana')
    expect(auth.isLoggedIn).toBe(true)
    expect(localStorage.getItem('refresh')).toBe('R1')
    // A decisão: o access nunca vai para o storage
    expect(localStorage.getItem('access')).toBeNull()
  })

  it('um 401 no token deixa a store vazia', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValueOnce(
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
    const auth = useAuth()

    await expect(auth.login('ana', 'errada')).rejects.toMatchObject({ status: 401 })

    expect(auth.user).toBeNull()
    expect(auth.access).toBeNull()
    expect(localStorage.getItem('refresh')).toBeNull()
  })

  it('refreshAccess com rotação substitui o refresh guardado', async () => {
    localStorage.setItem('refresh', 'R1')
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(json({ access: 'A2', refresh: 'R2' }))
    vi.stubGlobal('fetch', fetchMock)
    // Nova store: lê o R1 do localStorage
    setActivePinia(createPinia())
    const auth = useAuth()

    // Duas chamadas em simultâneo: single-flight → um só pedido de renovação
    const [a, b] = await Promise.all([auth.refreshAccess(), auth.refreshAccess()])

    expect(a).toBe('A2')
    expect(b).toBe('A2')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(auth.access).toBe('A2')
    expect(localStorage.getItem('refresh')).toBe('R2')
  })
})
