import { describe, expect, it } from 'vitest'

import { inspeccionConContenido, validarObligatoriosDeOperacion } from '../operationPayload'

/**
 * `SPEC 020 §6` — espejo en cliente de `RR-28`, `RR-29`, `RR-31`, `RR-32` y `RR-33`: el servidor
 * sigue siendo la autoridad; el cliente lo advierte antes de enviar, sin autorrellenar valores.
 */
const CASA = { derivedHouseId: 1 }

describe('causa obligatoria (RR-32)', () => {
  it('mortalidad sin causa ⇒ clave de causa de mortalidad', () => {
    const datos = { event_type: 'mortality_recording', bird_movements: [{ quantity: 3 }] }
    expect(validarObligatoriosDeOperacion(datos, CASA)).toBe('operations.mortalityCauseRequired')
  })
  it('mortalidad con causa ⇒ sin faltante', () => {
    const datos = { event_type: 'mortality_recording', cause_id: 7, bird_movements: [{ quantity: 3 }] }
    expect(validarObligatoriosDeOperacion(datos, CASA)).toBeNull()
  })
  it('descarte sin causa ⇒ clave de causa de descarte; con causa ⇒ sin faltante', () => {
    const base = { event_type: 'cull_recording', bird_movements: [{ quantity: 2 }] }
    expect(validarObligatoriosDeOperacion(base, CASA)).toBe('operations.cullCauseRequired')
    expect(validarObligatoriosDeOperacion({ ...base, cull_cause_id: 4 }, CASA)).toBeNull()
  })
})

describe('lote de vacuna obligatorio (RR-31)', () => {
  const base = { event_type: 'vaccination', vaccine_id: 3 }
  it.each([[undefined], [''], ['   ']])('lote %j ⇒ clave de lote de vacuna', (lote) => {
    expect(validarObligatoriosDeOperacion({ ...base, vaccine_lot_number: lote }, CASA)).toBe('operations.vaccineLotRequired')
  })
  it('lote con texto ⇒ sin faltante', () => {
    expect(validarObligatoriosDeOperacion({ ...base, vaccine_lot_number: 'LOT-2026-01' }, CASA)).toBeNull()
  })
})

describe('tipo de alimento obligatorio (RR-33)', () => {
  it('kilos sin tipo ⇒ clave de tipo de alimento', () => {
    const datos = { event_type: 'feed_registration', feed_movements: [{ quantity_kg: 5 }] }
    expect(validarObligatoriosDeOperacion(datos, CASA)).toBe('operations.feedTypeRequired')
  })
  it('kilos con tipo ⇒ sin faltante', () => {
    const datos = { event_type: 'feed_registration', feed_movements: [{ quantity_kg: 5, feed_type_id: 2 }] }
    expect(validarObligatoriosDeOperacion(datos, CASA)).toBeNull()
  })
  it('sin kilos sigue siendo el faltante de la cantidad', () => {
    const datos = { event_type: 'feed_registration', feed_movements: [{ feed_type_id: 2 }] }
    expect(validarObligatoriosDeOperacion(datos, CASA)).toBe('operations.feedRequired')
  })
})

describe('distribución con aves (RR-29)', () => {
  it('sin filas o con suma cero ⇒ clave de distribución', () => {
    expect(validarObligatoriosDeOperacion({ event_type: 'bird_distribution', bird_movements: [] }, CASA))
      .toBe('operations.distributionRequired')
    expect(validarObligatoriosDeOperacion(
      { event_type: 'bird_distribution', bird_movements: [{ quantity: 0 }, { quantity: 0 }] }, CASA))
      .toBe('operations.distributionRequired')
  })
  it('suma positiva ⇒ sin faltante', () => {
    expect(validarObligatoriosDeOperacion(
      { event_type: 'bird_distribution', bird_movements: [{ quantity: 40 }, { quantity: 0 }] }, CASA)).toBeNull()
  })
})

describe('inspección de granja con contenido (RR-28)', () => {
  const vacia = { event_type: 'farm_inspection', house_inspections: [{ house_id: 1, litter_condition: '' }] }
  it('completamente vacía ⇒ clave de contenido', () => {
    expect(inspeccionConContenido(vacia)).toBe(false)
    expect(validarObligatoriosDeOperacion(vacia, CASA)).toBe('operations.inspectionContentRequired')
  })
  it.each([
    ['temperatura', { house_inspections: [{ house_id: 1, temperature: 27.5 }] }],
    ['humedad cero (valor declarado)', { house_inspections: [{ house_id: 1, humidity: 0 }] }],
    ['condición de cama', { house_inspections: [{ house_id: 1, litter_condition: 'good' }] }],
    ['notas de cama', { house_inspections: [{ house_id: 1, litter_notes: 'húmeda' }] }],
    ['equipo observado', { house_inspections: [{ house_id: 1, equipment_items: [{ equipment_type: 'bebedero', observation: 'gotea' }] }] }],
    ['observación general', { house_inspections: [{ house_id: 1 }], observations: 'Todo en orden' }],
  ])('%s cuenta como contenido', (_nombre, extra) => {
    const datos = { event_type: 'farm_inspection', ...extra }
    expect(inspeccionConContenido(datos)).toBe(true)
    expect(validarObligatoriosDeOperacion(datos, CASA)).toBeNull()
  })
  it('una observación de espacios y un equipo sin observación no son contenido', () => {
    const datos = {
      event_type: 'farm_inspection', observations: '   ',
      house_inspections: [{ house_id: 1, equipment_items: [{ equipment_type: 'bebedero', observation: '' }] }],
    }
    expect(inspeccionConContenido(datos)).toBe(false)
  })
})
