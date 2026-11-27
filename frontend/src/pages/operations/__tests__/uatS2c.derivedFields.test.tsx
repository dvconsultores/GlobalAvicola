/**
 * SPEC 020 §6 (`RR-30`, `RR-34`) · RED jsdom — semana y fase derivadas, sólo lectura.
 *
 * La semana la deriva el servidor de la edad del lote y la fase es la fase productiva vigente
 * del lote en la fecha del evento: aquí sólo se muestran. Sin fase vigente se avisa; nunca se
 * ofrece un campo editable para corregirlas a mano.
 *
 * `t` va mockeado (como en `uatS2.listLotLabel.test.tsx`) y devuelve la clave: los textos
 * viven en `public/locales/es/translation.json` bajo `operations.derived*`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

const { t } = vi.hoisted(() => ({
  t: vi.fn((k: string, opts?: any) => (typeof opts === 'string' ? opts : k)),
}))

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t }) }))

import { SemanaDerivada, FaseDerivada } from '../DerivedFields'

const SIN_CAMPOS = 'input,select,textarea'

beforeEach(() => {
  t.mockClear()
})

describe('SPEC 020 §6 · semana derivada (sólo lectura)', () => {
  it('semana=3 ⇒ «Semana 3» (operations.derivedWeek con n=3)', () => {
    render(<SemanaDerivada semana={3} />)
    const caja = screen.getByTestId('derived-week')
    expect(caja.textContent).toBe('operations.derivedWeek')
    expect(t).toHaveBeenCalledWith('operations.derivedWeek', { n: 3 })
    expect(t).not.toHaveBeenCalledWith('operations.derivedWeekPending', expect.anything())
  })

  it('semana=null ⇒ pendiente (operations.derivedWeekPending), no «Semana {{n}}»', () => {
    render(<SemanaDerivada semana={null} />)
    const caja = screen.getByTestId('derived-week')
    expect(caja.textContent).toBe('operations.derivedWeekPending')
    expect(t).not.toHaveBeenCalledWith('operations.derivedWeek', expect.anything())
  })
})

describe('SPEC 020 §6 · fase derivada (sólo lectura)', () => {
  it('sin fase y con lote elegido ⇒ aviso de fase vigente inexistente', () => {
    render(<FaseDerivada fase={null} lotElegido />)
    const caja = screen.getByTestId('derived-phase')
    expect(caja.textContent).toBe('operations.derivedPhaseNone')
    expect(t).not.toHaveBeenCalledWith('operations.derivedWeekPending', expect.anything())
  })

  it('con fase vigente ⇒ «Fase: Cría» (operations.derivedPhase con name)', () => {
    render(
      <FaseDerivada
        fase={{ phase_id: 1, start_date: '2026-10-01', phase: { name: 'Cría' } }}
        lotElegido
      />,
    )
    const caja = screen.getByTestId('derived-phase')
    expect(caja.textContent).toBe('operations.derivedPhase')
    expect(t).toHaveBeenCalledWith('operations.derivedPhase', { name: 'Cría' })
    expect(t).not.toHaveBeenCalledWith('operations.derivedPhaseNone', expect.anything())
  })

  it('sin fase y sin lote elegido ⇒ pendiente, no el aviso', () => {
    render(<FaseDerivada fase={null} lotElegido={false} />)
    const caja = screen.getByTestId('derived-phase')
    expect(caja.textContent).toBe('operations.derivedWeekPending')
    expect(t).not.toHaveBeenCalledWith('operations.derivedPhaseNone', expect.anything())
  })
})

describe('SPEC 020 §6 · derivados sin campos editables', () => {
  it('ni `derived-week` ni `derived-phase` contienen input/select/textarea', () => {
    render(
      <>
        <SemanaDerivada semana={3} />
        <SemanaDerivada semana={null} />
        <FaseDerivada
          fase={{ phase_id: 1, start_date: '2026-10-01', phase: { name: 'Cría' } }}
          lotElegido
        />
        <FaseDerivada fase={null} lotElegido />
        <FaseDerivada fase={null} lotElegido={false} />
      </>,
    )
    const cajas = [...screen.getAllByTestId('derived-week'), ...screen.getAllByTestId('derived-phase')]
    expect(cajas).toHaveLength(5)
    for (const caja of cajas) {
      expect(caja.querySelector(SIN_CAMPOS)).toBeNull()
    }
  })
})
