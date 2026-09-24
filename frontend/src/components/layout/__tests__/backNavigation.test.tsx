import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k?: string, f?: string) => f ?? k }),
}))

import BackNavigation from '../BackNavigation'

function renderCase(entries: string[], initialIndex: number, back: React.ReactNode) {
  return render(
    <MemoryRouter initialEntries={entries} initialIndex={initialIndex}>
      <Routes>
        <Route path="/list" element={<div>LIST-STUB</div>} />
        <Route path="/home" element={<div>HOME-STUB</div>} />
        <Route path="/form" element={<div>FORM-STUB{back}</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('004 · BackNavigation (NAV-01)', () => {
  it('AC02 · renderiza icono+texto con aria-label y testid; navega al `to` explícito', () => {
    renderCase(['/list', '/form'], 1, <BackNavigation to="/list" />)
    const btn = screen.getByTestId('back-navigation')
    expect(btn.getAttribute('aria-label')).toBe('Volver')
    expect(btn.textContent).toContain('Volver')
    fireEvent.click(btn)
    expect(screen.getByText('LIST-STUB')).toBeTruthy()
  })

  it('AC19 · deep-link sin historial interno: usa `fallbackTo` canónico', () => {
    renderCase(['/form'], 0, <BackNavigation fallbackTo="/home" />)
    fireEvent.click(screen.getByTestId('back-navigation'))
    expect(screen.getByText('HOME-STUB')).toBeTruthy()
  })

  it('AC05 · con historial interno: vuelve atrás (navigate -1)', () => {
    renderCase(['/list', '/form'], 1, <BackNavigation fallbackTo="/home" />)
    fireEvent.click(screen.getByTestId('back-navigation'))
    expect(screen.getByText('LIST-STUB')).toBeTruthy()
  })

  it('AC14 · con cambios sin guardar pide confirmación; cancelar permanece; confirmar sale', () => {
    renderCase(['/list', '/form'], 1, <BackNavigation to="/list" dirty />)
    fireEvent.click(screen.getByTestId('back-navigation'))
    expect(screen.getByText('Cambios sin guardar')).toBeTruthy()

    fireEvent.click(screen.getByText('Quedarme'))
    expect(screen.getByText('FORM-STUB', { exact: false })).toBeTruthy()
    expect(screen.queryByText('Cambios sin guardar')).toBeNull()

    fireEvent.click(screen.getByTestId('back-navigation'))
    fireEvent.click(screen.getByText('Salir sin guardar'))
    expect(screen.getByText('LIST-STUB')).toBeTruthy()
  })
})
