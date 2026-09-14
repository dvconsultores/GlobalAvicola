/**
 * R-196 · RED jsdom — formularios de maestros por entidad, creación completa y
 * navegación de maestros.
 *
 * Diseño: `specs/R-196/R-196_RED_E2E_UAT_DESIGN.md §1.1`.
 *
 * Rojos en HEAD (causas previstas):
 *   AC-02  · houses: sin selector de granja ⇒ POST sin `farm_id` ⇒ 422.
 *   AC-03a · incubators: sin selector de planta ⇒ POST sin `hatchery_id`.
 *   AC-03b · hatchers: ídem.
 *   AC-04  · capacity vacía viaja `''` ⇒ 422 (debe viajar `null`/ausente).
 *   AC-05  · sin control de reactivación (PUT `is_active:true`).
 *   AC-07  · `/masters` no ofrece selector de entidades (hub inexistente).
 *
 * Verdes que se conservan como regresión (R-215 ya cerró el render del error):
 *   AC-01 (contrato: el Create de farms NO lleva `company_id` del cliente),
 *   AC-06 (422 ⇒ texto), AC-08 (409 legible).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
const put = vi.fn()
const del = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: (...a: any[]) => put(...a), delete: (...a: any[]) => del(...a),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))

if (!window.matchMedia) {
  // jsdom no implementa matchMedia; SearchSelect lo consulta al montar.
  // @ts-expect-error polyfill de prueba
  window.matchMedia = (q: string) => ({
    matches: false, media: q, onchange: null,
    addEventListener: () => {}, removeEventListener: () => {},
    addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false,
  })
}
if (!Element.prototype.scrollIntoView) Element.prototype.scrollIntoView = () => {}

import MasterListPage from '../MasterListPage'
import { useAuthStore } from '../../../stores/auth.store'

const E422 = {
  response: {
    data: {
      detail: [
        { type: 'missing', loc: ['body', 'farm_id'], msg: 'Field required', input: {} },
      ],
    },
  },
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 77, username: 'r196', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

const COLS_FARMS = [
  { key: 'name', labelKey: 'masters.farms' },
  { key: 'code', labelKey: 'simple.code' },
  { key: 'location', labelKey: 'simple.location' },
]
const COLS_NAME_CAP = [
  { key: 'name', labelKey: 'simple.name' },
  { key: 'capacity', labelKey: 'simple.capacity' },
]
const COLS_NAME_CODE = [
  { key: 'name', labelKey: 'simple.name' },
  { key: 'code', labelKey: 'simple.code' },
]

const cambio = (el: Element, valor: string) => fireEvent.change(el, { target: { value: valor } })

/** El modal (`role=dialog`) contiene los campos; la página tiene su propio buscador. */
const enModal = () => within(screen.getByRole('dialog'))

/** Selección en `SearchSelect` (variante desktop: botón → opción). */
const elegirEnSelector = async (boton: RegExp, opcion: RegExp) => {
  fireEvent.click(await screen.findByRole('button', { name: boton }))
  fireEvent.click(await screen.findByText(opcion))
}

const abrirNuevo = async () => {
  fireEvent.click(await screen.findByRole('button', { name: 'Nuevo' }))
}

const guardar = async () => {
  fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))
}

const cuerpoDe = (llamada: any[]) => llamada[1]

beforeEach(() => {
  get.mockReset(); post.mockReset(); put.mockReset(); del.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-196 · creación de maestros por entidad (RED)', () => {
  it('AC-01 · farm: POST sin `company_id` (contrato R-50) y éxito', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    get.mockImplementation((url: string) =>
      String(url).startsWith('/masters/farms')
        ? Promise.resolve({ data: [], headers: {} })
        : Promise.resolve({ data: [], headers: {} }))
    post.mockResolvedValueOnce({ data: { id: 77, name: 'Granja R196', is_active: true } })
    render(
      <MemoryRouter>
        <MasterListPage entity="farms" titleKey="masters.farms" columns={COLS_FARMS} />
      </MemoryRouter>,
    )
    await abrirNuevo()
    const campos = await enModal().findAllByRole('textbox')
    cambio(campos[0], 'Granja R196')
    await guardar()

    await waitFor(() => expect(post).toHaveBeenCalled())
    const [url, cuerpo] = post.mock.calls[0]
    expect(url).toBe('/masters/farms')
    expect(cuerpo.name).toBe('Granja R196')
    expect(cuerpo).not.toHaveProperty('company_id')
  })

  it('AC-02 · house: selector de granja ⇒ POST con `farm_id`', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/masters/houses')) return Promise.resolve({ data: [], headers: {} })
      if (u.startsWith('/masters/farms')) {
        return Promise.resolve({ data: [{ id: 1, name: 'Granja A', is_active: true }], headers: {} })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    post.mockImplementation((url: string, cuerpo: any) => {
      if (url === '/masters/houses' && Number(cuerpo?.farm_id) === 1 && cuerpo?.name) {
        return Promise.resolve({ data: { id: 42, name: cuerpo.name, farm_id: 1, is_active: true } })
      }
      return Promise.reject(E422)
    })
    render(
      <MemoryRouter>
        <MasterListPage entity="houses" titleKey="masters.houses" columns={COLS_NAME_CAP} />
      </MemoryRouter>,
    )
    await abrirNuevo()
    cambio((await enModal().findAllByRole('textbox'))[0], 'Galpón A1')
    await elegirEnSelector(/Seleccionar granja/, /Granja A/)
    await guardar()

    await waitFor(() => expect(post).toHaveBeenCalled())
    expect(cuerpoDe(post.mock.calls[0]).farm_id).toBe(1)
  })

  it('AC-03a · incubator: selector de planta ⇒ POST con `hatchery_id`', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/masters/hatcheries')) {
        return Promise.resolve({ data: [{ id: 2, name: 'Planta B', is_active: true }], headers: {} })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    post.mockImplementation((url: string, cuerpo: any) => {
      if (url === '/masters/incubators' && Number(cuerpo?.hatchery_id) === 2 && cuerpo?.name) {
        return Promise.resolve({ data: { id: 43, name: cuerpo.name, hatchery_id: 2 } })
      }
      return Promise.reject(E422)
    })
    render(
      <MemoryRouter>
        <MasterListPage entity="incubators" titleKey="masters.incubators" columns={COLS_NAME_CAP} />
      </MemoryRouter>,
    )
    await abrirNuevo()
    cambio((await enModal().findAllByRole('textbox'))[0], 'Incubadora B1')
    await elegirEnSelector(/Seleccionar planta/, /Planta B/)
    await guardar()

    await waitFor(() => expect(post).toHaveBeenCalled())
    expect(cuerpoDe(post.mock.calls[0]).hatchery_id).toBe(2)
  })

  it('AC-03b · hatcher: selector de planta ⇒ POST con `hatchery_id`', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/masters/hatcheries')) {
        return Promise.resolve({ data: [{ id: 2, name: 'Planta B', is_active: true }], headers: {} })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    post.mockImplementation((url: string, cuerpo: any) => {
      if (url === '/masters/hatchers' && Number(cuerpo?.hatchery_id) === 2 && cuerpo?.name) {
        return Promise.resolve({ data: { id: 44, name: cuerpo.name, hatchery_id: 2 } })
      }
      return Promise.reject(E422)
    })
    render(
      <MemoryRouter>
        <MasterListPage entity="hatchers" titleKey="masters.hatchers" columns={COLS_NAME_CAP} />
      </MemoryRouter>,
    )
    await abrirNuevo()
    cambio((await enModal().findAllByRole('textbox'))[0], 'Nacedora B1')
    await elegirEnSelector(/Seleccionar planta/, /Planta B/)
    await guardar()

    await waitFor(() => expect(post).toHaveBeenCalled())
    expect(cuerpoDe(post.mock.calls[0]).hatchery_id).toBe(2)
  })

  it('AC-04 · capacity vacía ⇒ `null` (nunca cadena vacía)', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/masters/farms')) {
        return Promise.resolve({ data: [{ id: 1, name: 'Granja A', is_active: true }], headers: {} })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    // El servidor nuevo rechaza `capacity:''` (int inválido) y acepta null/ausente.
    post.mockImplementation((url: string, cuerpo: any) => {
      const cap = cuerpo?.capacity
      const capValida = cap === null || cap === undefined || typeof cap === 'number'
      if (url === '/masters/houses' && Number(cuerpo?.farm_id) === 1 && cuerpo?.name && capValida) {
        return Promise.resolve({ data: { id: 45, name: cuerpo.name, capacity: null } })
      }
      return Promise.reject(E422)
    })
    render(
      <MemoryRouter>
        <MasterListPage entity="houses" titleKey="masters.houses" columns={COLS_NAME_CAP} />
      </MemoryRouter>,
    )
    await abrirNuevo()
    cambio((await enModal().findAllByRole('textbox'))[0], 'Galpón sin capacidad')
    // Limpiar un opcional (queda `''`) es el caso real del defecto: debe viajar
    // `null`, nunca cadena vacía (el int del servidor la rechaza con 422).
    const capacidad = await enModal().findByRole('spinbutton')
    cambio(capacidad, '250')
    cambio(capacidad, '')
    await elegirEnSelector(/Seleccionar granja/, /Granja A/)
    await guardar()

    await waitFor(() => expect(post).toHaveBeenCalled())
    expect(cuerpoDe(post.mock.calls[0]).capacity ?? null).toBeNull()
  })

  it('AC-05 · reactivar un maestro inactivo ⇒ PUT `is_active:true`', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    get.mockImplementation((url: string) =>
      String(url).startsWith('/masters/areas')
        ? Promise.resolve({ data: [{ id: 9, name: 'Área X', code: 'AX', is_active: false }], headers: {} })
        : Promise.resolve({ data: [], headers: {} }))
    put.mockResolvedValueOnce({ data: { id: 9, name: 'Área X', is_active: true } })
    render(
      <MemoryRouter>
        <MasterListPage entity="areas" titleKey="masters.areas" columns={COLS_NAME_CODE} />
      </MemoryRouter>,
    )
    await screen.findAllByText('Área X')
    fireEvent.click((await screen.findAllByRole('button', { name: 'common.edit' }))[0])

    fireEvent.click(await enModal().findByRole('button', { name: /^Activar/ }))
    const confirmaciones = screen.queryAllByRole('button', { name: /^(Activar|Confirmar|Sí)/ })
    if (confirmaciones.length > 0) fireEvent.click(confirmaciones[0])

    await waitFor(() =>
      expect(put).toHaveBeenCalledWith('/masters/areas/9', expect.objectContaining({ is_active: true })))
  })

  it('AC-06 · 422 lista ⇒ texto legible (regresión R-215)', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    get.mockResolvedValue({ data: [], headers: {} })
    post.mockRejectedValueOnce({
      response: {
        data: {
          detail: [{ type: 'missing', loc: ['body', 'name'], msg: 'String should have at least 1 character', input: {} }],
        },
      },
    })
    render(
      <MemoryRouter>
        <MasterListPage entity="farms" titleKey="masters.farms" columns={COLS_FARMS} />
      </MemoryRouter>,
    )
    await abrirNuevo()
    cambio((await enModal().findAllByRole('textbox'))[0], 'Granja X')
    await guardar()

    await waitFor(() =>
      expect(screen.getByText(/name: String should have at least 1 character/)).toBeTruthy())
  })

  it('AC-07 · /masters ofrece selector con todas las entidades', async () => {
    setSession(['masters:read'])
    const modulos: any = import.meta.glob('../MastersHubPage.tsx')
    const claves = Object.keys(modulos)
    expect(claves.length, 'MastersHubPage no existe todavía (AC-07)').toBeGreaterThan(0)
    const mod: any = await modulos[claves[0]]()
    const entidades = ['farms', 'houses', 'hatcheries', 'incubators', 'hatchers', 'areas', 'suppliers', 'breeds']
      .map((entity) => ({ entity, title: `masters.${entity}` }))
    render(
      <MemoryRouter initialEntries={['/masters']}>
        <mod.default entities={entidades} />
      </MemoryRouter>,
    )
    const accesos = await screen.findAllByRole('link')
    expect(accesos.length).toBeGreaterThanOrEqual(8)
  })

  it('AC-08 · 409 duplicado ⇒ texto legible (regresión)', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    get.mockResolvedValue({ data: [], headers: {} })
    post.mockRejectedValueOnce({
      response: { data: { detail: 'Ya existe una granja con ese nombre' } },
    })
    render(
      <MemoryRouter>
        <MasterListPage entity="farms" titleKey="masters.farms" columns={COLS_FARMS} />
      </MemoryRouter>,
    )
    await abrirNuevo()
    cambio((await enModal().findAllByRole('textbox'))[0], 'Granja Duplicada')
    await guardar()

    await waitFor(() =>
      expect(screen.getByText(/Ya existe una granja con ese nombre/)).toBeTruthy())
  })
})
