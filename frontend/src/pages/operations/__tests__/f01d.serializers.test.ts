/**
 * R-189 (F-01d) · serializadores de alimento e incubadora — unit.
 *
 * El formulario arranca con `[{}]` en `feed_movements`/`hatchery_params`; el contrato canónico
 * exige que una fila sin contenido nunca viaje (`[]`), sin inventar valores y conservando las
 * filas con contenido real.
 */
import { describe, it, expect } from 'vitest'
import {
  serializarMovimientosDeAlimento,
  serializarParamsDeIncubadora,
  serializarMovimientosDeAves,
} from '../operationPayload'

describe('R-189 · F-01d · serializadores de alimento/incubadora', () => {
  it('alimento: [{}] y NaN ⇒ [] (nunca un objeto vacío)', () => {
    expect(serializarMovimientosDeAlimento([{}])).toEqual([])
    expect(serializarMovimientosDeAlimento([{ quantity_kg: NaN }])).toEqual([])
    expect(serializarMovimientosDeAlimento(undefined)).toEqual([])
    expect(serializarMovimientosDeAlimento(null)).toEqual([])
  })

  it('alimento: la fila con contenido se conserva y los NaN se omiten', () => {
    expect(
      serializarMovimientosDeAlimento([{ feed_type_id: 1, quantity_kg: 12.5, week_number: NaN }]),
    ).toEqual([{ feed_type_id: 1, quantity_kg: 12.5 }])
  })

  it('incubadora: [{}] y fila con solo machine_type (campo de UI) ⇒ []', () => {
    expect(serializarParamsDeIncubadora([{}])).toEqual([])
    expect(serializarParamsDeIncubadora([{ machine_type: 'incubadora' }])).toEqual([])
  })

  it('incubadora: la fila con contenido se conserva', () => {
    expect(serializarParamsDeIncubadora([{ temperature: 37.5 }])).toEqual([{ temperature: 37.5 }])
  })

  it('aves: el comportamiento del C2 queda intacto (cantidad 0 declarada se conserva)', () => {
    expect(serializarMovimientosDeAves([{ quantity: 0, sex: 'male' }])).toEqual([{ quantity: 0, sex: 'male' }])
    expect(serializarMovimientosDeAves([{ sex: 'female' }])).toEqual([])
  })
})
