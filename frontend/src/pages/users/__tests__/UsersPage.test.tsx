/**
 * Los cinco estados de la administración de usuarios — `GA-REM-002` enmienda B · `AC16`.
 *
 * El defecto que estas pruebas cierran no era cosmético. La pantalla envolvía cuatro llamadas
 * en un `Promise.all` con un `catch` que solo escribía en consola, de modo que **«no tienes
 * permiso» y «no hay usuarios» se veían exactamente igual**: una tabla con cabeceras y sin
 * filas. Esa confusión es lo que mantuvo invisibles durante meses los cuatro `P0` de
 * aislamiento de inquilino — una fuga que no se puede ver no se reporta.
 *
 * El mismo principio ya estaba escrito para la campana de avisos (`GA-REM-038 AC19`) y nunca
 * se había generalizado.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import UsersPage from '../UsersPage'

const get = vi.fn()

vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: vi.fn(), put: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (clave: string) => clave }),
}))

/** Un fallo con la forma que produce `axios`, que es de donde sale el código real. */
function fallo(status: number) {
  return Object.assign(new Error(`HTTP ${status}`), { response: { status } })
}

const CATALOGOS_OK = { data: [] }

function usuario(extra: Partial<any> = {}) {
  return {
    id: 1, username: 'jperez', first_name: 'Juan', last_name: 'Pérez',
    email: 'jperez@globalavicola.com', role_id: 3, view_type: 'web',
    is_active: true, ...extra,
  }
}

beforeEach(() => {
  get.mockReset()
})

describe('UsersPage · estados de carga', () => {
  it('un 403 se muestra como permiso insuficiente, nunca como tabla vacía', async () => {
    get.mockImplementation((url: string) =>
      url === '/users' ? Promise.reject(fallo(403)) : Promise.resolve(CATALOGOS_OK))

    render(<UsersPage />)

    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy())
    expect(screen.getByText('users.forbidden')).toBeTruthy()
    // Y **no** el vacío: es la mitad que hace que la prueba signifique algo.
    expect(screen.queryByText('users.noUsers')).toBeNull()
  })

  it('un 500 ofrece reintentar, y tampoco es una lista vacía', async () => {
    get.mockImplementation((url: string) =>
      url === '/users' ? Promise.reject(fallo(500)) : Promise.resolve(CATALOGOS_OK))

    render(<UsersPage />)

    await waitFor(() => expect(screen.getByText('users.loadError')).toBeTruthy())
    expect(screen.getByText('common.retry')).toBeTruthy()
    expect(screen.queryByText('users.noUsers')).toBeNull()
  })

  it('doscientos con lista vacía es el único caso que dice «no hay usuarios»', async () => {
    get.mockResolvedValue({ data: [] })

    render(<UsersPage />)

    await waitFor(() => expect(screen.getByText('users.noUsers')).toBeTruthy())
    expect(screen.queryByText('users.forbidden')).toBeNull()
    expect(screen.queryByText('users.loadError')).toBeNull()
  })

  it('con datos se pintan las filas y ningún estado de excepción', async () => {
    get.mockImplementation((url: string) =>
      url === '/users'
        ? Promise.resolve({ data: [usuario(), usuario({ id: 2, username: 'mlopez' })] })
        : Promise.resolve(CATALOGOS_OK))

    render(<UsersPage />)

    await waitFor(() => expect(screen.getAllByText('jperez').length).toBeGreaterThan(0))
    expect(screen.getAllByText('mlopez').length).toBeGreaterThan(0)
    expect(screen.queryByText('users.noUsers')).toBeNull()
    expect(screen.queryByText('users.forbidden')).toBeNull()
  })

  it('un catálogo auxiliar caído degrada el desplegable, no la pantalla', async () => {
    // `/users` **es** la página; roles, empresas y áreas solo rellenan el formulario. Antes
    // cualquiera de las tres vaciaba la tabla entera por venir en el mismo `Promise.all`.
    get.mockImplementation((url: string) =>
      url === '/users' ? Promise.resolve({ data: [usuario()] })
        : url.startsWith('/masters/areas') ? Promise.reject(fallo(403))
        : Promise.resolve(CATALOGOS_OK))

    render(<UsersPage />)

    await waitFor(() => expect(screen.getAllByText('jperez').length).toBeGreaterThan(0))
    expect(screen.getByText('users.partialCatalogs')).toBeTruthy()
    expect(screen.queryByText('users.forbidden')).toBeNull()
  })
})
