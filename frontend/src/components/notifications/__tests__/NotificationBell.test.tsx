/**
 * La campana — `AC16`…`AC19` de `GA-REM-038`.
 *
 * Lo que se fija aquí es que el contador venga del **servidor** y que los tres estados de la
 * bandeja —vacía, cargando y con error— sean distinguibles. Confundir un fallo de API con
 * «no tienes nada» es el defecto que `AC19` persigue: el usuario dejaría de mirar.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import NotificationBell from '../NotificationBell'

const get = vi.fn()
const patch = vi.fn()
const navigate = vi.fn()

vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), patch: (...a: any[]) => patch(...a) },
}))
vi.mock('react-router-dom', () => ({ useNavigate: () => navigate }))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (clave: string, opciones?: any) =>
      opciones?.count !== undefined ? `${clave}:${opciones.count}` : clave,
  }),
}))

function aviso(extra: Partial<any> = {}) {
  return {
    id: 1, company_id: 1, recipient_user_id: 2,
    notification_type: 'record_rejected',
    payload: { observations: 'Pesaje incoherente' },
    related_entity_type: 'operational_event', related_entity_id: 77,
    created_at: new Date().toISOString(), read_at: null, ...extra,
  }
}

/** Encamina cada ruta a su respuesta, para no depender del orden de las llamadas. */
function responder(contador: number, lista: any[] | Error) {
  get.mockImplementation((ruta: string) => {
    if (ruta.includes('unread-count')) return Promise.resolve({ data: { unread: contador } })
    if (lista instanceof Error) return Promise.reject(lista)
    return Promise.resolve({ data: lista })
  })
}

beforeEach(() => {
  get.mockReset(); patch.mockReset(); navigate.mockReset()
})

describe('NotificationBell', () => {
  it('`AC16` · el número de sin leer viaja en el nombre accesible, no solo en un color',
    async () => {
      responder(3, [aviso()])
      render(<NotificationBell />)
      // Quien navega con lector de pantalla también debe saber cuántas tiene.
      expect(await screen.findByLabelText('notifications.bellWithUnread:3')).toBeInTheDocument()
    })

  it('`AC16` · el contador sale del servidor, no de contar la primera página', async () => {
    // Cinco sin leer y una sola en la página: si se contara lo cargado, diría uno.
    responder(5, [aviso()])
    render(<NotificationBell />)
    expect(await screen.findByLabelText('notifications.bellWithUnread:5')).toBeInTheDocument()
    expect(get).toHaveBeenCalledWith('/notifications/unread-count')
  })

  it('sin nada sin leer, la campana no anuncia número', async () => {
    responder(0, [])
    render(<NotificationBell />)
    expect(await screen.findByLabelText('notifications.bell')).toBeInTheDocument()
  })

  it('`AC17` · distingue leída de no leída por texto', async () => {
    responder(1, [aviso({ id: 1 }), aviso({ id: 2, read_at: new Date().toISOString() })])
    render(<NotificationBell />)
    await userEvent.click(await screen.findByLabelText(/notifications.bell/))

    expect(await screen.findByText('notifications.unread')).toBeInTheDocument()
    expect(screen.getByText('notifications.read')).toBeInTheDocument()
  })

  it('`AC18` · abrir una la marca leída, baja el contador y navega', async () => {
    responder(1, [aviso()])
    patch.mockResolvedValue({ data: aviso({ read_at: new Date().toISOString() }) })
    render(<NotificationBell />)

    await userEvent.click(await screen.findByLabelText('notifications.bellWithUnread:1'))
    await userEvent.click(await screen.findByText('notifications.types.record_rejected'))

    await waitFor(() => expect(patch).toHaveBeenCalledWith('/notifications/1/read'))
    expect(navigate).toHaveBeenCalledWith('/operations/77')
    await waitFor(() =>
      expect(screen.getByLabelText('notifications.bell')).toBeInTheDocument())
  })

  it('no navega cuando el aviso no tiene pantalla destino', async () => {
    // Un enlace roto es peor que ninguno: `sap_payload` no tiene vista propia.
    responder(1, [aviso({ notification_type: 'sap_send_failed',
                          related_entity_type: 'sap_payload', related_entity_id: 9,
                          payload: { error_message: 'SAP no disponible' } })])
    patch.mockResolvedValue({ data: aviso({ read_at: new Date().toISOString() }) })
    render(<NotificationBell />)

    await userEvent.click(await screen.findByLabelText(/notifications.bell/))
    await userEvent.click(await screen.findByText('notifications.types.sap_send_failed'))

    await waitFor(() => expect(patch).toHaveBeenCalled())
    expect(navigate).not.toHaveBeenCalled()
  })

  it('`AC19` · la bandeja vacía se declara', async () => {
    responder(0, [])
    render(<NotificationBell />)
    await userEvent.click(await screen.findByLabelText('notifications.bell'))
    expect(await screen.findByText('notifications.empty')).toBeInTheDocument()
  })

  it('`AC19` · un fallo de API no se presenta como bandeja vacía', async () => {
    responder(0, new Error('red caída'))
    render(<NotificationBell />)
    await userEvent.click(await screen.findByLabelText('notifications.bell'))

    expect(await screen.findByRole('alert')).toHaveTextContent('notifications.loadFailed')
    expect(screen.queryByText('notifications.empty')).not.toBeInTheDocument()
  })
})
