/**
 * `F8` — el diálogo de rechazo de aprobaciones debe permitir escribir el motivo.
 *
 * Hallazgo del E2E `P18D` (P5c): el `ConfirmDialog` de «Rechazar» no tenía campo de
 * motivo, así que `handleRejectSingle` caía SIEMPRE en el aviso «al menos 10 caracteres»
 * y el rechazo era imposible de completar. Aquí se fija el contrato:
 * - abrir el diálogo de rechazo muestra `reject-reason`;
 * - con < 10 caracteres no se llama a la API y se muestra el error en el diálogo;
 * - con ≥ 10 caracteres se rechaza de verdad, con el motivo como `observations`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a) },
}))
// `t` estable (una sola identidad por módulo): con identidades nuevas por render
// `fetchEvents` se recrea y el refetch borra el estado que la prueba observa.
vi.mock('react-i18next', () => {
  const t = (k: string, f?: string) => f ?? k
  return { useTranslation: () => ({ t, i18n: {} }) }
})

import ApprovalPanel from '../ApprovalPanel'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTS = [{ id: 11, lot_id: 11, event_type: 'x', status: 'corrected', event_date: '2026-09-11', operator: { username: 'op' } }]
const MOTIVO = 'Rechazo UAT: datos inconsistentes'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: ['broiler'], effective_business_units: ['broiler'],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  post.mockResolvedValue({ data: {} })
  get.mockImplementation((url: string) => {
    if (String(url).startsWith('/approvals/pending')) return Promise.resolve({ data: { events: EVENTS, total: 1 } })
    return Promise.resolve({ data: { events: [], total: 0 } })
  })
  setSession(['approvals:approve', 'approvals:reject', 'review:review'])
})

const montar = () =>
  render(<MemoryRouter><ToastProvider><ApprovalPanel /></ToastProvider></MemoryRouter>)

/** Abre el diálogo de rechazo del evento #11 y devuelve el diálogo. */
async function abrirDialogoRechazo() {
  await waitFor(() => expect(screen.getAllByText(/#11/).length).toBeGreaterThan(0))
  fireEvent.click(screen.getAllByRole('button', { name: /^Rechazar$/ })[0])
  const dialogo = await screen.findByRole('dialog')
  return dialogo as HTMLElement
}

describe('F8 · motivo de rechazo dentro del diálogo', () => {
  it('abrir «Rechazar» ofrece el campo de motivo', async () => {
    montar()
    const dialogo = await abrirDialogoRechazo()
    expect(within(dialogo).getByTestId('reject-reason')).toBeTruthy()
  })

  it('motivo de 3 caracteres: no llama a /approvals/reject y muestra el error', async () => {
    montar()
    const dialogo = await abrirDialogoRechazo()
    const campo = within(dialogo).getByTestId('reject-reason') as HTMLTextAreaElement
    fireEvent.change(campo, { target: { value: 'abc' } })
    expect(within(dialogo).getByTestId('reject-reason-error')).toBeTruthy()

    fireEvent.click(within(dialogo).getByRole('button', { name: /^Rechazar$/ }))

    await waitFor(() => expect(within(dialogo).getByTestId('reject-reason-error')).toBeTruthy())
    expect(post).not.toHaveBeenCalledWith('/approvals/reject', expect.anything())
    expect(post.mock.calls.some(c => c[0] === '/approvals/reject')).toBe(false)
    // El diálogo sigue abierto: el usuario corrige, no pierde lo escrito.
    expect(screen.getByRole('dialog')).toBeTruthy()
  })

  it('motivo válido (≥ 10): rechaza con event_id y observations', async () => {
    montar()
    const dialogo = await abrirDialogoRechazo()
    const campo = within(dialogo).getByTestId('reject-reason')
    fireEvent.change(campo, { target: { value: MOTIVO } })
    expect(within(dialogo).queryByTestId('reject-reason-error')).toBeNull()

    fireEvent.click(within(dialogo).getByRole('button', { name: /^Rechazar$/ }))

    await waitFor(() => expect(post).toHaveBeenCalledWith(
      '/approvals/reject',
      expect.objectContaining({ event_id: 11, observations: MOTIVO }),
    ))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
  })
})
