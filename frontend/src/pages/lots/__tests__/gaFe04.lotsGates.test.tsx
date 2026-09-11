/**
 * GA-FE-04 · RED — LotListPage: CTA «Nuevo lote» por `lots:create` (§38 CTA de vacío/alta).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a) },
}))
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }) }))

import LotListPage from '../LotListPage'
import { useAuthStore } from '../../../stores/auth.store'

const LOTS = [{ id: 1, lot_code: 'L-BO-2026-05', bird_type: 'broiler', status: 'active', current_quantity: 10 }]

function setSession(permissions: string[], effective: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: effective, effective_business_units: effective,
    } as any,
  })
}

beforeEach(() => {
  get.mockReset()
  get.mockImplementation((url: string) => {
    if (String(url).startsWith('/lots')) return Promise.resolve({ data: LOTS })
    return Promise.resolve({ data: [] })
  })
})

describe('GA-FE-04 · LotListPage — CTA de alta', () => {
  it('lots:read sin lots:create ⇒ sin CTA «Nuevo lote»', async () => {
    setSession(['lots:read'], ['broiler'])
    render(<MemoryRouter><LotListPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText('L-BO-2026-05').length).toBeGreaterThan(0))
    expect(screen.queryAllByText('lots.newLot').length).toBe(0)
  })

  it('control: con lots:create ⇒ CTA visible', async () => {
    setSession(['lots:read', 'lots:create'], ['broiler'])
    render(<MemoryRouter><LotListPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText('L-BO-2026-05').length).toBeGreaterThan(0))
    expect(screen.getAllByText('lots.newLot').length).toBeGreaterThan(0)
  })
})
