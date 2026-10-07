// @vitest-environment jsdom
/**
 * SPEC 005 · SapManagerPage en fase READ ONLY — `AC-HANA-05`, `§39`.
 *
 *   el inbound manda            estado HANA, objetos, registros, errores, Sincronizar
 *   el outbound no se ofrece    «Exportar a SAP» no existe mientras esté deshabilitado
 *   la pantalla no inventa      «configurado» no es «conectado»; el simulador se anuncia
 *   sin secretos                solo se muestran los NOMBRES de las variables que faltan
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
const toast = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }
vi.mock('../../../services/api', () => ({ default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a) } }))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, f?: any) => {
      if (typeof f === 'string') return f
      if (f && typeof f === 'object' && typeof f.defaultValue === 'string') {
        return f.defaultValue.replace(/\{\{(\w+)\}\}/g, (_: string, n: string) => String(f[n]))
      }
      return k
    },
    i18n: { language: 'es', resolvedLanguage: 'es' },
  }),
}))
vi.mock('../../../components/Toast', () => ({
  useToast: () => toast,
  getErrorMessage: (_e: any, f: string) => f,
}))

import SapManagerPage from '../SapManagerPage'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', email: 'p@x', first_name: 'P', last_name: 'X', role_id: 3,
      view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const SIN_CREDENCIALES = {
  inbound_hana: {
    phase: 'READ_ONLY_INBOUND', status: 'PENDING_CREDENTIALS', configured: false, connected: false,
    simulated: false, missing: ['SAP_HANA_HOST', 'SAP_HANA_USER', 'SAP_HANA_PASSWORD'],
    write_operations_allowed: false,
  },
  outbound: { enabled: false, delivers_to_sap: false, mode: 'disabled_read_only_phase', adapter: 'ManualSapAdapter' },
  connected: false, adapter: 'ManualSapAdapter', delivers_to_sap: false, mode: 'manual',
}
const SIMULADO = {
  ...SIN_CREDENCIALES,
  inbound_hana: {
    phase: 'READ_ONLY_INBOUND', status: 'SIMULATED_CONNECTED', configured: true, connected: true,
    simulated: true, missing: [], write_operations_allowed: false,
  },
}
const JOB = {
  id: 7, object_type: 'purchase_order', status: 'completed', rows_read: 2, rows_raw: 2,
  rows_promoted: 2, rows_pending_mapping: 0, completed_at: '2026-10-06T12:00:00Z',
}
const JOB_FALLIDO = {
  id: 8, object_type: 'vendor', status: 'failed', rows_read: 0, rows_raw: 0, rows_promoted: 0,
  rows_pending_mapping: 0, error_code: 'SAP_AUTH_ERROR', error_message: 'Autenticación rechazada',
}

function backend(conn: any, extra: Record<string, any> = {}) {
  get.mockImplementation((url: string) => {
    if (url === '/sap/connection-check') return Promise.resolve({ data: conn })
    if (url === '/sap/inbound/objects') {
      return Promise.resolve({ data: { objects: [{ object_type: 'purchase_order' }, { object_type: 'vendor' }] } })
    }
    for (const [prefijo, data] of Object.entries(extra)) {
      if (url.startsWith(prefijo)) return Promise.resolve({ data })
    }
    return Promise.resolve({ data: {} })
  })
}

const pinta = () => render(<MemoryRouter><SapManagerPage /></MemoryRouter>)

beforeEach(() => {
  get.mockReset(); post.mockReset()
  Object.values(toast).forEach(f => f.mockReset())
})

describe('SPEC 005 · SapManagerPage — inbound SAP HANA (solo lectura)', () => {
  it('sin credenciales ⇒ pendiente, con los nombres que faltan y sin fingir conexión', async () => {
    backend(SIN_CREDENCIALES)
    setSession(['sap:read', 'sap:send_sap'])
    pinta()
    const estado = await screen.findByTestId('sap-inbound-status')
    expect(estado.getAttribute('data-status')).toBe('PENDING_CREDENTIALS')
    expect(estado.textContent).toMatch(/Pendiente de credenciales/)
    expect(screen.getByText(/SAP_HANA_HOST, SAP_HANA_USER, SAP_HANA_PASSWORD/)).toBeTruthy()
    expect(screen.queryByText(/Conectado/)).toBeNull()
    // No se presenta el modo manual como si fuera una conexión.
    expect(screen.queryByText(/ManualSapAdapter/)).toBeNull()
    // Sin configuración no se puede sincronizar.
    expect((screen.getByTestId('sap-inbound-sync') as HTMLButtonElement).disabled).toBe(true)
  })

  it('outbound deshabilitado ⇒ no existe «Exportar a SAP» ni reintento de envío', async () => {
    backend(SIMULADO)
    setSession(['sap:read', 'sap:send_sap'])
    pinta()
    await screen.findByTestId('sap-inbound-status')
    expect(screen.queryByRole('button', { name: /Exportar/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Reintentar env/ })).toBeNull()
    expect(screen.getByTestId('sap-outbound-disabled')).toBeTruthy()
    expect(screen.getByText(/Solo lectura · sin escritura a SAP/)).toBeTruthy()
  })

  it('outbound habilitado ⇒ «Exportar a SAP» vuelve, bajo su permiso', async () => {
    backend({ ...SIMULADO, outbound: { ...SIMULADO.outbound, enabled: true } })
    setSession(['sap:read', 'sap:send_sap'])
    pinta()
    await waitFor(() => expect(screen.getAllByRole('button', { name: /Exportar/ }).length).toBeGreaterThan(0))
    expect(screen.queryByTestId('sap-outbound-disabled')).toBeNull()
  })

  it('solo sap:read ⇒ ve el estado pero no puede sincronizar', async () => {
    backend(SIMULADO)
    setSession(['sap:read'])
    pinta()
    await screen.findByTestId('sap-inbound-status')
    expect(screen.queryByTestId('sap-inbound-sync')).toBeNull()
  })

  it('el simulador se anuncia como simulador, no como SAP', async () => {
    backend(SIMULADO)
    setSession(['sap:read'])
    pinta()
    const estado = await screen.findByTestId('sap-inbound-status')
    expect(estado.getAttribute('data-status')).toBe('SIMULATED_CONNECTED')
    expect(estado.textContent).toMatch(/Simulador local \(no es SAP\)/)
    expect(screen.getByText(/No hay conexión con SAP real/)).toBeTruthy()
  })

  it('Sincronizar ⇒ POST /sap/inbound/sync, resumen honesto y recarga', async () => {
    backend(SIMULADO, { '/sap/inbound/jobs': { jobs: [JOB] } })
    post.mockResolvedValue({ data: { sync_request_id: 'r1', jobs: [JOB, JOB_FALLIDO] } })
    setSession(['sap:read', 'sap:send_sap'])
    pinta()
    const boton = await screen.findByTestId('sap-inbound-sync')
    const antes = get.mock.calls.length
    fireEvent.click(boton)
    await waitFor(() => expect(post).toHaveBeenCalledWith('/sap/inbound/sync', {}))
    // Un objeto falló: se avisa, no se celebra.
    await waitFor(() => expect(toast.warning).toHaveBeenCalled())
    expect(toast.warning.mock.calls[0][0]).toMatch(/1 objetos completados, 1 con error/)
    expect(toast.success).not.toHaveBeenCalled()
    await waitFor(() => expect(get.mock.calls.length).toBeGreaterThan(antes))
    // Nunca se envía SQL ni nombre de tabla desde el navegador.
    expect(JSON.stringify(post.mock.calls)).not.toMatch(/select|from |sql/i)
  })

  it('objetos, registros y errores se leen del inbound', async () => {
    backend(SIMULADO, {
      '/sap/inbound/jobs': { jobs: [JOB, JOB_FALLIDO] },
      '/sap/inbound/records': { records: [{ id: 1, object_type: 'purchase_order', source_key: '100|4500000001', version: 1, promotion_status: 'PROMOTED' }] },
      '/sap/inbound/errors': {
        jobs: [JOB_FALLIDO],
        records: [{ id: 2, object_type: 'plant', source_key: '100|1200', error_code: 'SAP_MAPPING_PENDING', error_message: 'centro 1200 sin mapping a esta empresa' }],
      },
    })
    setSession(['sap:read'])
    pinta()
    const fila = await screen.findByTestId('sap-inbound-object-purchase_order')
    expect(fila.textContent).toMatch(/2 leídos · 2 promovidos/)
    expect(screen.getByTestId('sap-inbound-object-vendor').textContent).toMatch(/SAP_AUTH_ERROR/)

    fireEvent.click(screen.getByRole('button', { name: /Registros/ }))
    expect(await screen.findByText('100|4500000001')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: /Errores de sincronización/ }))
    expect(await screen.findByText(/centro 1200 sin mapping/)).toBeTruthy()
    expect(screen.getByText(/Autenticación rechazada/)).toBeTruthy()
  })

  it('las claves del inbound existen en ES y EN', async () => {
    const es = (await import('../../../../public/locales/es/translation.json')).default as any
    const en = (await import('../../../../public/locales/en/translation.json')).default as any
    const hojas = (o: any, p = ''): string[] => Object.entries(o).flatMap(([k, v]) =>
      v && typeof v === 'object' ? hojas(v, `${p}${k}.`) : [`${p}${k}`])
    expect(hojas(es.sap.inbound).sort()).toEqual(hojas(en.sap.inbound).sort())
    expect(hojas(es.sap.inbound).length).toBeGreaterThan(40)
    for (const clave of ['PENDING_CREDENTIALS', 'CONNECTED', 'SIMULATED_CONNECTED', 'CONNECTION_FAILED']) {
      expect(es.sap.inbound.status[clave]).toBeTruthy()
      expect(en.sap.inbound.status[clave]).toBeTruthy()
    }
  })
})
