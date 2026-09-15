/**
 * R-220 · A16/A17 (B-35/B-38/B-39) — RED.
 *
 * A17 (B-38/B-39): la «Semana» (y el «Peso prom.» del huevo) se capturan UNA sola vez
 * —ligadas a la fila 0 de la UI—, pero el submit descarta las filas sin cantidad. Si la
 * fila 0 cae (machos=0, fértiles=0), el dato declarado se PIERDE antes de viajar.
 * Canonización esperada: anclar el campo declarado a la PRIMERA fila superviviente.
 *
 * A16 (B-35): `birth_registration` no advierte en cliente las reglas que el servidor sí
 * aplica (BR-21): `mixed` excluyente con sexadas, y sanos/débiles obligatorios.
 */
import { describe, it, expect } from 'vitest'
import * as payload from '../pages/operations/operationPayload'
import { serializarMovimientosDeAves } from '../pages/operations/operationPayload'

describe('R-220 · A17 (B-38) · «Semana» del evento con la fila 0 en 0', () => {
  it('la semana declarada (fila machos) debe sobrevivir al descarte de filas sin cantidad', () => {
    const crudas = [
      { sex: 'male', quantity: 0, week_number: 5 },
      { sex: 'female', quantity: 10 },
    ]
    // Pipeline actual del submit: serializar → descartar filas sin cantidad.
    const vivas = serializarMovimientosDeAves(crudas).filter((m: any) => (m.quantity ?? 0) > 0)
    expect(vivas, 'queda la fila de hembras').toHaveLength(1)
    expect((vivas[0] as any).week_number, 'la semana declarada NO puede perderse (B-38)').toBe(5)
  })
})

describe('R-220 · A17 (B-39) · «Peso prom.» del huevo con fértiles en 0', () => {
  it('el peso promedio declarado (fila fértil) debe sobrevivir al descarte', () => {
    const crudas = [
      { egg_type: 'fertile', quantity: 0, avg_weight: 62.5 },
      { egg_type: 'dirty', quantity: 30 },
    ]
    const vivas = crudas.filter((m: any) => (m.quantity ?? 0) > 0)
    expect((vivas[0] as any).avg_weight, 'el peso declarado NO puede perderse (B-39)').toBe(62.5)
  })
})

describe('R-220 · A16 (B-35) · validación cliente de nacimiento (BR-21)', () => {
  it('existe el validador canónico de reglas de nacimiento', () => {
    expect(typeof (payload as any).validarReglasDeNacimiento, 'validador ausente').toBe('function')
  })
})
