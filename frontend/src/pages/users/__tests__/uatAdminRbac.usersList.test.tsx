/**
 * SPEC 013 · UAT Admin/RBAC · Lote F5 — AR-22: la administración de Usuarios truncaba en
 * silencio a 20.
 *
 * `GET /users` pagina (`skip`/`limit`, `limit` por defecto 20 y máximo 100) y el `search` del
 * servidor filtra por usuario/nombre/correo **antes** de paginar. La pantalla pedía `/users` a
 * secas, así que en una empresa con más de 20 usuarios los recién creados simplemente no
 * aparecían: no había error ni aviso, solo una tabla incompleta que parecía completa.
 *
 * Lo que se fija aquí:
 *  (a) la primera carga pide `limit=100` y NO manda `search`;
 *  (b) buscar se aplica al pulsar Enter (o el botón), no en cada tecla, y viaja codificado;
 *  (c) con exactamente 100 filas se avisa de que la lista está truncada, con 99 no;
 *  (d) una búsqueda sin coincidencias dice «ningún usuario coincide», no «no hay usuarios».
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

const get = vi.fn()

vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: vi.fn(), put: vi.fn(), delete: vi.fn(),
  },
}))

// `t` devuelve la clave: así se afirma por CLAVE y la prueba no depende del literal de respaldo.
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string) => k }),
}))

import { ToastProvider } from '../../../components/Toast'
import UsersPage from '../UsersPage'
import { useAuthStore } from '../../../stores/auth.store'

function usuario(id: number) {
  return {
    id, username: `u${id}`, first_name: 'Nombre', last_name: `Apellido${id}`,
    email: `u${id}@x.com`, role_id: 2, view_type: 'web', is_active: true,
  }
}

const conN = (n: number) => Array.from({ length: n }, (_, i) => usuario(i + 1))

/** URLs pedidas a `/users...` (los catálogos auxiliares no interesan aquí). */
const urlsUsuarios = () => get.mock.calls.map((c) => String(c[0])).filter((u) => u.startsWith('/users'))

beforeEach(() => {
  get.mockReset()
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 1, username: 'ana', first_name: 'Ana', last_name: 'Díaz', email: 'ana@x.com',
      role_id: 2, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions: ['users:read', 'users:create', 'users:update', 'users:delete'],
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
})

const responder = (usuarios: any[]) => {
  get.mockImplementation((url: string) =>
    String(url).startsWith('/users') ? Promise.resolve({ data: usuarios }) : Promise.resolve({ data: [] }))
}

const cajaBusqueda = () => screen.getByLabelText('users.search') as HTMLInputElement

describe('SPEC 013 · Lote F5 · AR-22 — la lista no se trunca en 20', () => {
  it('(a) la primera carga pide limit=100 y NO manda search', async () => {
    responder([usuario(1)])
    render(<ToastProvider><UsersPage /></ToastProvider>)
    await screen.findAllByText('u1')

    const url = urlsUsuarios()[0]
    expect(url).toContain('limit=100')
    expect(url).not.toContain('search=')
    // El defecto original: `/users` a secas ⇒ el servidor devolvía solo los primeros 20.
    expect(url).not.toBe('/users')
  })

  it('(b) escribir no dispara petición; Enter sí, y con el texto codificado', async () => {
    responder([usuario(1)])
    render(<ToastProvider><UsersPage /></ToastProvider>)
    await screen.findAllByText('u1')
    const inicial = urlsUsuarios().length

    // Ni una petición por tecla: la búsqueda se aplica, no se teclea.
    fireEvent.change(cajaBusqueda(), { target: { value: 'ana díaz' } })
    expect(urlsUsuarios()).toHaveLength(inicial)

    responder([usuario(7)])
    fireEvent.keyDown(cajaBusqueda(), { key: 'Enter' })

    await waitFor(() => expect(urlsUsuarios().length).toBeGreaterThan(inicial))
    const url = urlsUsuarios()[urlsUsuarios().length - 1]
    expect(url).toContain(`search=${encodeURIComponent('ana díaz')}`)
    expect(url).toContain('limit=100')
    // Y la tabla refleja el resultado del servidor, no un filtro local.
    await screen.findAllByText('u7')
  })

  it('(b bis) el botón «Buscar» aplica la búsqueda igual que Enter', async () => {
    responder([usuario(1)])
    render(<ToastProvider><UsersPage /></ToastProvider>)
    await screen.findAllByText('u1')

    responder([])
    fireEvent.change(cajaBusqueda(), { target: { value: 'zzz' } })
    fireEvent.click(screen.getByRole('button', { name: 'users.searchAction' }))

    await waitFor(() => expect(urlsUsuarios().some((u) => u.includes('search=zzz'))).toBe(true))
  })

  it('(c) con 100 filas avisa del truncado; con 99 no', async () => {
    responder(conN(100))
    render(<ToastProvider><UsersPage /></ToastProvider>)
    await waitFor(() => expect(urlsUsuarios().length).toBeGreaterThan(0))
    expect(await screen.findByText('users.truncated')).toBeTruthy()
    const aviso = screen.getByText('users.truncated')
    expect(aviso.closest('[role="status"]')).toBeTruthy()
  })

  it('(c bis) con 99 filas no hay aviso de truncado', async () => {
    responder(conN(99))
    render(<ToastProvider><UsersPage /></ToastProvider>)
    await screen.findAllByText('u1')
    expect(screen.queryByText('users.truncated')).toBeNull()
  })

  it('(d) una búsqueda sin coincidencias dice noResults, no «no hay usuarios»', async () => {
    responder([usuario(1)])
    render(<ToastProvider><UsersPage /></ToastProvider>)
    await screen.findAllByText('u1')

    responder([])
    fireEvent.change(cajaBusqueda(), { target: { value: 'inexistente' } })
    fireEvent.keyDown(cajaBusqueda(), { key: 'Enter' })

    expect(await screen.findByText('users.noResults')).toBeTruthy()
    expect(screen.queryByText('users.noUsers')).toBeNull()
  })
})
