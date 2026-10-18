/**
 * QA-Yolinel · RED jsdom — tres hallazgos de la sesión de QA de campo.
 *
 *   QA-017 · El Centro de Revisión se relee a sí mismo: `fetchEvents` depende de `can`
 *            (nuevo en cada render, `auth/actionAuthority.useCan` devuelve una flecha
 *            fresca) y de `t`/`toast`, así que el `useEffect` vuelve a dispararse en cada
 *            render ⇒ bucle de `GET /review/pending` sin interacción del usuario.
 *   QA-013 · Las columnas secundarias de los maestros están rotuladas con claves de
 *            ACCIÓN: la cabecera de la tabla muestra «Editar»/«Guardar»
 *            (`common.edit`/`common.save` en `masterEntities`, App.tsx) en vez del
 *            nombre del campo (`code`, `location`, `capacity`, `laboratory`...).
 *   QA-016 · El campo `event_date` del alta de operaciones es `type="date"` sin `max`:
 *            el calendario deja registrar una fecha futura.
 *
 * Rojos esperados en HEAD, todos por la ASERCIÓN funcional (no por montaje).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// ── API mockeada (patrón de src/pages/review/__tests__/r197.reviewQueue.test.tsx) ──
const get = vi.fn()
const post = vi.fn()
vi.mock('../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k?: string, f?: any) => (typeof f === 'string' ? f : k),
    i18n: { resolvedLanguage: 'es', language: 'es', changeLanguage: vi.fn() },
  }),
}))
vi.mock('../i18n', () => ({ normalizeLanguage: () => 'es', nextLanguage: () => 'en' }))
vi.mock('../hooks/useTelegram', () => ({
  useTelegram: () => ({ enableClosingConfirmation: vi.fn(), isAvailable: false }),
  useTelegramBackHandler: () => undefined,
}))
vi.mock('../components/notifications/NotificationBell', () => ({ default: () => null }))

const toastCtx = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }
vi.mock('../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useToast: () => toastCtx }
})

import ReviewCenter from '../pages/review/ReviewCenter'
import OperationFormPage from '../pages/operations/OperationFormPage'
import App from '../App'
import { ToastProvider } from '../components/Toast'
import { useAuthStore } from '../stores/auth.store'
import { hoyISO } from '../utils/dates'

// jsdom: polyfills que ya necesitan estas pantallas (ver r210.weightUnit.test.tsx).
if (!window.matchMedia) {
  // @ts-expect-error polyfill de prueba
  window.matchMedia = (q: string) => ({
    matches: false, media: q, onchange: null,
    addEventListener: () => {}, removeEventListener: () => {},
    addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false,
  })
}
if (!Element.prototype.scrollIntoView) Element.prototype.scrollIntoView = () => {}

function setSession(permissions: string[], userId = 5) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: userId, username: 'qa', first_name: 'Q', last_name: 'A', email: 'qa@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

const llamadas = (prefijo: string) =>
  get.mock.calls.map((c) => String(c[0])).filter((u) => u.startsWith(prefijo))

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/review/pending')) return Promise.resolve({ data: { events: [], total: 0 } })
    if (u.startsWith('/masters/farms')) {
      return Promise.resolve({ data: [{ id: 1, name: 'Granja Norte', code: 'GN', location: 'Cali' }], headers: {} })
    }
    if (u.startsWith('/masters/houses')) {
      return Promise.resolve({ data: [{ id: 2, name: 'Galpón 1', capacity: 5000, farm_id: 1 }], headers: {} })
    }
    return Promise.resolve({ data: [], headers: {} })
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// R1 · QA-017 · el Centro de Revisión no debe re-consultar sin interacción
// ─────────────────────────────────────────────────────────────────────────────
describe('QA-017 · Centro de Revisión sin bucle de peticiones', () => {
  const montarReview = () => render(
    <MemoryRouter initialEntries={['/review?status=in_review']}>
      <ToastProvider><ReviewCenter /></ToastProvider>
    </MemoryRouter>,
  )

  it('la carga inicial se estabiliza en 1 GET /review/pending (sin interacción)', async () => {
    setSession(['review:read', 'review:review', 'approvals:approve', 'users:read'])
    montarReview()

    // la primera carga ocurre
    await waitFor(() => expect(llamadas('/review/pending').length).toBeGreaterThan(0))
    // …y se deja correr el reloj: nada más debería pasar sin interacción.
    await new Promise((r) => setTimeout(r, 300))

    const total = llamadas('/review/pending').length
    const urlsDistintas = new Set(llamadas('/review/pending')).size
    // N_INICIAL = 1: un único listado, una única URL.
    expect(urlsDistintas, `URLs distintas: ${urlsDistintas}`).toBeLessThanOrEqual(1)
    expect(total, `GET /review/pending ejecutados: ${total}`).toBeLessThanOrEqual(1)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// R2 · QA-013 · las cabeceras de maestros no son acciones
// ─────────────────────────────────────────────────────────────────────────────
describe('QA-013 · etiquetas de columnas de maestros', () => {
  const PROHIBIDO = /^(Editar|Guardar|common\.edit|common\.save)$/i

  const montarMaestro = (entity: string) => render(
    <MemoryRouter initialEntries={[`/masters/${entity}`]}><App /></MemoryRouter>,
  )

  const cabeceras = () =>
    Array.from(document.querySelectorAll('table thead th')).map((th) => (th.textContent ?? '').trim())

  it.each(['farms', 'houses'])('/masters/%s: ningún th dice «Editar» ni «Guardar»', async (entity) => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete', 'dashboard:read'])
    montarMaestro(entity)

    // la tabla con datos se pinta (si no, el rojo sería de montaje/datos, no de rótulos)
    await waitFor(() => expect(cabeceras().length).toBeGreaterThan(0))
    await screen.findByRole('table')

    const rotulos = cabeceras()
    expect(rotulos.length).toBeGreaterThan(0)
    const deAccion = rotulos.filter((h) => PROHIBIDO.test(h))
    expect(deAccion, `th con rótulo de acción: ${JSON.stringify(deAccion)}`).toEqual([])
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// R3 · QA-016 · el calendario de operaciones no admite fechas futuras
// ─────────────────────────────────────────────────────────────────────────────
describe('QA-016 · `event_date` acota el calendario a hoy', () => {
  const montarFormulario = () => render(
    <MemoryRouter initialEntries={['/operations/new?type=feed_registration']}>
      <ToastProvider><OperationFormPage /></ToastProvider>
    </MemoryRouter>,
  )

  it('el input de event_date lleva `max` = hoy (YYYY-MM-DD)', async () => {
    setSession(['operations:read', 'operations:create'])
    montarFormulario()

    const campo = await waitFor(() => {
      const el = document.querySelector('input[name="event_date"]') as HTMLInputElement | null
      expect(el, 'campo event_date ausente').toBeTruthy()
      return el!
    })
    // mismo criterio de «hoy» que usa el propio formulario en su `max`: `hoyISO()`, fecha
    // civil en la zona LOCAL del operador (`utils/dates`). `toISOString()` mide en UTC y en
    // husos negativos ya devolvía el día siguiente por la noche.
    const hoy = hoyISO()

    expect(campo.getAttribute('type')).toBe('date')
    expect(campo.getAttribute('max'), `max=${campo.getAttribute('max')}`).toBe(hoy)
  })
})
