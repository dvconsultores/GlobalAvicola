/**
 * SPEC 013 · UAT Admin/RBAC · Lote F2 — Perfil (`AC-PF-01`).
 *
 * Sin cambio funcional: estas pruebas FIJAN la conducta del cambio de contraseña para que
 * ninguna regresión silenciosa la altere —
 *  · nueva ≠ confirmación ⇒ no viaja a la API y se explica el desajuste;
 *  · nueva < 8 ⇒ política única de longitud (la misma del alta);
 *  · sin contraseña actual ⇒ campos obligatorios;
 *  · éxito ⇒ `POST /users/{id}/password` con `{current_password, new_password}`, mensaje de
 *    confirmación y campos vaciados;
 *  · error del servidor (400) ⇒ se muestra SU texto y NUNCA «actualizada».
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

const get = vi.fn()
const post = vi.fn()

vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

// `t` devuelve la clave: los mensajes se afirman por clave, no por idioma.
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

import ProfilePage from '../ProfilePage'
import { useAuthStore } from '../../../stores/auth.store'
import { useCompanyStore } from '../../../stores/company.store'

interface UsuarioSesion {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  company_id: number | null
  effective_company_id: number | null
  permissions: string[]
  [k: string]: unknown
}

const YO: UsuarioSesion = {
  id: 61, username: 'ana', first_name: 'Ana', last_name: 'Díaz', email: 'ana@x.com',
  company_id: 1, effective_company_id: 1, permissions: ['users:read'],
}

function setSession() {
  useAuthStore.setState({ isAuthenticated: true, isLoading: false, token: null, user: YO as any })
  useCompanyStore.setState({ activeCompanyId: 1, activeCompanyName: null, companies: [], isSwitching: false })
}

const campo = (clave: string) => screen.getByPlaceholderText(clave) as HTMLInputElement
const enviar = () => fireEvent.click(screen.getByRole('button', { name: 'profile.updatePassword' }))

function escribir(actual: string, nueva: string, confirmacion: string) {
  fireEvent.change(campo('profile.currentPassword'), { target: { value: actual } })
  fireEvent.change(campo('profile.newPassword'), { target: { value: nueva } })
  fireEvent.change(campo('profile.confirmPassword'), { target: { value: confirmacion } })
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  post.mockResolvedValue({ data: {} })
  setSession()
})

describe('SPEC 013 · Lote F2 · ProfilePage (AC-PF-01)', () => {
  it('nueva ≠ confirmación: no llama a la API y lo explica', async () => {
    render(<ProfilePage />)
    escribir('Actual1234', 'Nueva12345', 'Distinta123')

    enviar()

    expect(await screen.findByText('profile.passwordMismatch')).toBeTruthy()
    expect(post).not.toHaveBeenCalled()
  })

  it('nueva < 8: rechaza antes de llamar a la API', async () => {
    render(<ProfilePage />)
    escribir('Actual1234', 'Corta1', 'Corta1')

    enviar()

    expect(await screen.findByText('profile.passwordMinLength')).toBeTruthy()
    expect(post).not.toHaveBeenCalled()
  })

  it('sin contraseña actual: campos obligatorios (no llama a la API)', async () => {
    render(<ProfilePage />)
    escribir('', 'Nueva12345', 'Nueva12345')

    enviar()

    expect(await screen.findByText('profile.currentPasswordRequired')).toBeTruthy()
    expect(post).not.toHaveBeenCalled()
  })

  it('éxito: POST del contrato exacto, mensaje de confirmación y campos vaciados', async () => {
    render(<ProfilePage />)
    escribir('Actual1234', 'Nueva12345', 'Nueva12345')

    enviar()

    await waitFor(() => expect(post).toHaveBeenCalled())
    expect(post).toHaveBeenCalledWith('/users/61/password', {
      current_password: 'Actual1234', new_password: 'Nueva12345',
    })
    expect(await screen.findByText('profile.passwordUpdated')).toBeTruthy()
    expect(campo('profile.currentPassword').value).toBe('')
    expect(campo('profile.newPassword').value).toBe('')
    expect(campo('profile.confirmPassword').value).toBe('')
  })

  it('error 400 del servidor: muestra SU texto y nunca «actualizada»', async () => {
    post.mockRejectedValueOnce({
      response: { status: 400, data: { detail: 'La contraseña actual no es correcta' } },
    })
    render(<ProfilePage />)
    escribir('Equivocada1', 'Nueva12345', 'Nueva12345')

    enviar()

    expect(await screen.findByText('La contraseña actual no es correcta')).toBeTruthy()
    expect(screen.queryByText('profile.passwordUpdated')).toBeNull()
  })
})
