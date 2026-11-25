import { describe, expect, it } from 'vitest'

import { faseVigente, semanaProductiva } from '../semanaProductiva'

/**
 * `SPEC 020 §6` · `OD04` — paridad con la función canónica del servidor
 * (`backend/app/operations/semana.py`): la semana es la edad productiva del lote, no la semana ISO.
 * Fechas fijas, sin reloj: las pruebas no dependen del día en que corran.
 */
describe('semanaProductiva (OD04)', () => {
  it.each([
    ['2026-10-01', '2026-10-01', 1],
    ['2026-10-01', '2026-10-07', 1],
    ['2026-10-01', '2026-10-08', 2],
    ['2026-10-01', '2026-10-14', 2],
    ['2026-10-01', '2026-10-15', 3],
  ])('lote %s · evento %s ⇒ semana %i', (inicio, evento, esperada) => {
    expect(semanaProductiva(inicio, evento)).toBe(esperada)
  })

  it.each([
    ['2025-12-29', '2026-01-04', 1],   // cambio de año, día 6
    ['2025-12-29', '2026-01-05', 2],   // cambio de año, día 7
    ['2025-12-28', '2026-01-11', 3],
    ['2026-11-25', '2026-12-01', 1],   // cambia la semana ISO (48→49) y no la productiva
    ['2026-12-31', '2027-01-07', 2],
    ['2026-02-28', '2026-03-01', 1],
  ])('fronteras: lote %s · evento %s ⇒ semana %i', (inicio, evento, esperada) => {
    expect(semanaProductiva(inicio, evento)).toBe(esperada)
  })

  it('acepta el inicio del lote como instante ISO con hora', () => {
    expect(semanaProductiva('2026-10-01T00:00:00+00:00', '2026-10-08')).toBe(2)
  })

  it('sin fecha base o con evento anterior al inicio no inventa una semana', () => {
    expect(semanaProductiva(null, '2026-10-08')).toBeNull()
    expect(semanaProductiva(undefined, '2026-10-08')).toBeNull()
    expect(semanaProductiva('2026-10-08', '')).toBeNull()
    expect(semanaProductiva('2026-10-08', '2026-10-07')).toBeNull()
  })
})

describe('faseVigente (OD07)', () => {
  const fases = [
    { id: 1, phase_id: 10, start_date: '2026-10-01', end_date: '2026-10-20', phase: { name: 'Cría' } },
    { id: 2, phase_id: 20, start_date: '2026-10-20', end_date: null, phase: { name: 'Producción' } },
  ]

  it('antes de la transición rige la fase A; después, la B', () => {
    expect(faseVigente(fases, '2026-10-15')?.phase_id).toBe(10)
    expect(faseVigente(fases, '2026-10-25')?.phase_id).toBe(20)
  })

  it('el día de la transición gana la fase más reciente', () => {
    expect(faseVigente(fases, '2026-10-20')?.phase_id).toBe(20)
  })

  it('sin fase vigente (antes de la primera o sin fases) devuelve null', () => {
    expect(faseVigente(fases, '2026-09-30')).toBeNull()
    expect(faseVigente([], '2026-10-15')).toBeNull()
    expect(faseVigente(null, '2026-10-15')).toBeNull()
  })
})
