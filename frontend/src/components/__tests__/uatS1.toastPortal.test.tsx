/**
 * `UAT S1` · `AC-S1-U01` (`F8`) — el toast vive en un PORTAL sobre `document.body`.
 *
 * Con el contenedor dentro del árbol de la app, un `z-[70]` no bastaba: quedaba atrapado
 * en un contexto de apilamiento inferior al del overlay del `ConfirmDialog` (portal en
 * `body`, z-[60]) y el aviso desaparecía bajo él. La prueba fija la condición real que lo
 * evita: el contenedor NO está en el contenedor de render y es hijo directo de `body`.
 */
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import { ToastProvider, useToast } from '../Toast'

function Disparador() {
  const toast = useToast()
  return <button onClick={() => toast.success('Registro guardado')}>disparar</button>
}

describe('UAT S1 · el contenedor de toasts vive en un portal sobre document.body', () => {
  it('el toast aparece en body, fuera del contenedor de render y con z-[70]', () => {
    const { container } = render(
      <ToastProvider>
        <Disparador />
      </ToastProvider>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))

    const cont = document.body.querySelector('[data-testid="toast-container"]') as HTMLElement | null
    expect(cont).not.toBeNull()
    // Fuera del árbol de la app ⇒ ningún contexto de apilamiento propio puede taparlo.
    expect(container.contains(cont)).toBe(false)
    expect(cont!.parentElement).toBe(document.body)
    // Por encima del overlay del `ConfirmDialog` (z-[60]).
    expect(cont!.className).toContain('z-[70]')
    expect(cont!.className).toContain('fixed')
    expect(cont!.textContent).toContain('Registro guardado')
    // Anuncio accesible del aviso.
    expect(cont!.getAttribute('role')).toBe('status')
    expect(cont!.getAttribute('aria-live')).toBe('polite')
  })
})
