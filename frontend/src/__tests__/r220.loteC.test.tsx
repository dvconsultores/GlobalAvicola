/**
 * R-220 · Lote C (i18n) — primera tanda: C1 (enumerados crudos → `t()` en pantallas
 * críticas), C2 (namespaces `roles.actions/modules` vacíos) y C7 (claves engañosas:
 * `common.edit` sobre un enlace a detalle, `common.back` como «Anterior» de paginación,
 * `process.hub.title` como cabecera/optgroup).
 *
 * El mock de `t` devuelve SIEMPRE la clave ⇒ lo traducido es distinguible del enumerado
 * crudo (p.ej. «status.approved» vs «approved»).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const get = vi.fn()
vi.mock('../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string) => k, i18n: { language: 'es', resolvedLanguage: 'es' } }),
}))
vi.mock('../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))
vi.mock('../components/TraceabilityTree', () => ({ TraceabilityTree: () => null }))

import OperationListPage from '../pages/operations/OperationListPage'
import OperationDetailPage from '../pages/operations/OperationDetailPage'
import ReviewDetail from '../pages/review/ReviewDetail'
import LotDetailPage from '../pages/lots/LotDetailPage'
import ApprovalPanel from '../pages/approvals/ApprovalPanel'
import { useAuthStore } from '../stores/auth.store'

const here = dirname(fileURLToPath(import.meta.url))
const src = (rel: string) => readFileSync(resolve(here, '..', rel), 'utf8')

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220c', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset()
  get.mockResolvedValue({ data: [], headers: {} })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-220 · Lote C · C1 enumerados + C7 claves (pantallas)', () => {
  it('C1/C7 · lista de operaciones: estado traducido, enlace «Ver detalle», optgroup propio', async () => {
    setSession(['operations:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations') {
        return Promise.resolve({ data: [{ id: 1, event_type: 'feed_registration', status: 'approved', event_date: '2026-09-10' }], headers: { 'x-total-count': '1' } })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/operations']}>
        <Routes><Route path="/operations" element={<OperationListPage />} /></Routes>
      </MemoryRouter>,
    )
    await screen.findByText('eventsShort.feed_registration')
    expect(screen.getByText('status.approved'), 'el estado no puede pintarse crudo').toBeTruthy()
    expect(screen.queryByText('approved')).toBeNull()
    expect(screen.getByText('common.viewDetail'), 'enlace a detalle rotulado como edición').toBeTruthy()
    const optgroup = document.querySelector('optgroup')
    expect(optgroup?.getAttribute('label')).toBe('operations.stagesGroup')
  })

  it('C1 · detalle de operación: tipo de evento, sexo y tipo de huevo traducidos', async () => {
    setSession(['operations:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations/1') {
        return Promise.resolve({ data: {
          id: 1, event_type: 'feed_registration', status: 'approved', event_date: '2026-09-10',
          bird_movements: [{ sex: 'male', quantity: 5, avg_weight: 2400 }],
          egg_movements: [{ egg_type: 'fertile', quantity: 10 }],
          feed_movements: [],
        } })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/operations/1']}>
        <Routes><Route path="/operations/:id" element={<OperationDetailPage />} /></Routes>
      </MemoryRouter>,
    )
    await screen.findByText('eventsShort.feed_registration')
    expect(screen.getByText(/sex\.male/), 'sexo crudo en movimientos').toBeTruthy()
    expect(screen.getByText(/operations\.fertile/), 'tipo de huevo crudo').toBeTruthy()
  })

  it('C1 · detalle de revisión: sexo y acción del historial traducidos', async () => {
    setSession(['review:read', 'review:review', 'operations:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations/55') {
        return Promise.resolve({ data: {
          id: 55, event_type: 'mortality_recording', status: 'in_review', event_date: '2026-09-10',
          bird_movements: [{ sex: 'male', quantity: 5 }], egg_movements: [], feed_movements: [],
        } })
      }
      if (u.startsWith('/review/events/55/actions')) {
        return Promise.resolve({ data: [{ id: 1, action_type: 'approved', created_at: '2026-09-11T10:00:00', observations: null }] })
      }
      if (u.startsWith('/corrections')) return Promise.resolve({ data: [] })
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/review/55']}>
        <Routes><Route path="/review/:id" element={<ReviewDetail />} /></Routes>
      </MemoryRouter>,
    )
    await screen.findByText(/sex\.male/)
    await waitFor(() => expect(screen.getByText('audit.actions.approved')).toBeTruthy())
  })

  it('C1 · detalle de lote: los registros recientes muestran el evento traducido', async () => {
    setSession(['lots:read', 'reports:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/lots/9') return Promise.resolve({ data: { id: 9, lot_code: 'L-9', status: 'active' } })
      if (u.startsWith('/operations?lot_id=9')) {
        return Promise.resolve({ data: [{ id: 3, event_type: 'feed_registration', status: 'approved', event_date: '2026-09-10' }], headers: { 'x-total-count': '1' } })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/lots/9']}>
        <Routes><Route path="/lots/:id" element={<LotDetailPage />} /></Routes>
      </MemoryRouter>,
    )
    await screen.findByText('eventsShort.feed_registration')
  })

  it('C7 · paginación del panel de aprobaciones: «Anterior» no es `common.back`', async () => {
    setSession(['review:read', 'approvals:approve', 'approvals:reject'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.includes('/approvals/pending')) {
        return Promise.resolve({ data: { events: [{ id: 31, status: 'corrected', event_type: 'mortality_recording', event_date: '2026-09-10' }], total: 30 } })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/approvals']}>
        <Routes><Route path="/approvals" element={<ApprovalPanel />} /></Routes>
      </MemoryRouter>,
    )
    await screen.findByText(/common\.prev/)
  })
})

describe('R-220 · Lote C · C2 namespaces `roles.*` y claves nuevas (ES/EN)', () => {
  const ACCIONES = ['read', 'create', 'update', 'delete', 'review', 'correct', 'approve', 'reject', 'send_sap']
  const MODULOS = ['approvals', 'audit', 'business_units', 'corrections', 'dashboard', 'lots', 'masters', 'operations', 'reports', 'reversals', 'review', 'sap', 'users']

  it('`roles.actions` (9) y `roles.modules` (13) existen en ambos idiomas', () => {
    for (const lang of ['es', 'en']) {
      const d = JSON.parse(readFileSync(resolve(here, '..', '..', 'public', 'locales', lang, 'translation.json'), 'utf8'))
      for (const a of ACCIONES) expect(d.roles?.actions?.[a], `roles.actions.${a} (${lang})`).toBeTruthy()
      for (const m of MODULOS) expect(d.roles?.modules?.[m], `roles.modules.${m} (${lang})`).toBeTruthy()
    }
  })

  it('claves C7/C1 nuevas: common.prev, common.viewDetail, sex.*, dashboard.processes, operations.stagesGroup', () => {
    for (const lang of ['es', 'en']) {
      const d = JSON.parse(readFileSync(resolve(here, '..', '..', 'public', 'locales', lang, 'translation.json'), 'utf8'))
      expect(d.common?.prev, `common.prev (${lang})`).toBeTruthy()
      expect(d.common?.viewDetail, `common.viewDetail (${lang})`).toBeTruthy()
      for (const s of ['male', 'female', 'mixed']) expect(d.sex?.[s], `sex.${s} (${lang})`).toBeTruthy()
      expect(d.dashboard?.processes, `dashboard.processes (${lang})`).toBeTruthy()
      expect(d.operations?.stagesGroup, `operations.stagesGroup (${lang})`).toBeTruthy()
    }
  })

  it('C7 · la cabecera de procesos del dashboard usa su propia clave (no `process.hub.title`)', () => {
    const s = src('pages/dashboard/DashboardPage.tsx')
    expect(s).toContain("t('dashboard.processes'")
  })
})
