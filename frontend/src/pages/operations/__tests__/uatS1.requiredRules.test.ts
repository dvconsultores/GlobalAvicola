/**
 * `F6` · spec 015 §4 (matriz por operación + `RR-20`..`RR-23`) — RED unitario de la regla pura
 * `validarObligatoriosDeOperacion`: el cliente exige lo mismo que el servidor ANTES de enviar,
 * sin autorrellenar ceros (vacío = ausente, `0` = cero conocido) y sin sustituir al backend.
 */
import { describe, it, expect } from 'vitest'
import { validarObligatoriosDeOperacion } from '../operationPayload'

describe('F6 · obligatorios por operación (paridad cliente-servidor)', () => {
  it('mortalidad sin cantidad ⇒ operations.quantityRequired', () => {
    expect(validarObligatoriosDeOperacion({
      event_type: 'mortality_recording',
      bird_movements: [{ sex: 'male' }, { sex: 'female' }],
    })).toBe('operations.quantityRequired')
  })

  it('mortalidad con cantidad 0 declarada ⇒ sigue faltando (el 0 no es «hay cantidad»)', () => {
    expect(validarObligatoriosDeOperacion({
      event_type: 'mortality_recording',
      bird_movements: [{ quantity: 0 }, { quantity: 0 }],
    })).toBe('operations.quantityRequired')
  })

  it('descarte y salida también exigen cantidad total > 0 (BR-01)', () => {
    for (const eventType of ['cull_recording', 'bird_exit']) {
      expect(validarObligatoriosDeOperacion({ event_type: eventType, bird_movements: [{}, {}] }), eventType)
        .toBe('operations.quantityRequired')
    }
  })

  it('agua sin litros ⇒ operations.waterLitersRequired', () => {
    expect(validarObligatoriosDeOperacion({ event_type: 'water_consumption' }))
      .toBe('operations.waterLitersRequired')
    expect(validarObligatoriosDeOperacion({ event_type: 'water_consumption', water_liters: 0 }))
      .toBe('operations.waterLitersRequired')
  })

  it('pesaje sin peso ⇒ operations.weightRequired (RR-20)', () => {
    expect(validarObligatoriosDeOperacion({
      event_type: 'weight_recording',
      bird_movements: [{ quantity: 50 }, { sex: 'female' }],
    })).toBe('operations.weightRequired')
  })

  it('vacunación sin vacuna ⇒ operations.vaccineRequired (RR-21)', () => {
    expect(validarObligatoriosDeOperacion({
      event_type: 'vaccination',
      bird_movements: [{ quantity: 10 }],
    })).toBe('operations.vaccineRequired')
  })

  it('medicación sin medicamento ⇒ operations.medicationRequired (RR-22)', () => {
    expect(validarObligatoriosDeOperacion({
      event_type: 'medication',
      bird_movements: [{ quantity: 10 }],
    })).toBe('operations.medicationRequired')
  })

  it('alimento sin kg ⇒ operations.feedRequired (RR-23)', () => {
    expect(validarObligatoriosDeOperacion({
      event_type: 'feed_registration',
      feed_movements: [{}],
    })).toBe('operations.feedRequired')
    expect(validarObligatoriosDeOperacion({
      event_type: 'feed_registration',
      feed_movements: [{ feed_type_id: 3, quantity_kg: 0 }],
    })).toBe('operations.feedRequired')
  })

  it('inspección de granja con granja y sin galpón ⇒ operations.eventHouseRequired (BR-08)', () => {
    expect(validarObligatoriosDeOperacion(
      { event_type: 'farm_inspection', house_inspections: [{}] },
      { derivedFarmId: 1, derivedHouseId: undefined },
    )).toBe('operations.eventHouseRequired')
  })

  it('positivo: con los datos exigidos no hay error (null)', () => {
    const validos = [
      [{ event_type: 'mortality_recording', bird_movements: [{}, { quantity: 3 }] }, {}],
      [{ event_type: 'water_consumption', water_liters: 120 }, {}],
      [{ event_type: 'weight_recording', bird_movements: [{ avg_weight: 2150 }] }, {}],
      [{ event_type: 'vaccination', vaccine_id: 4 }, {}],
      [{ event_type: 'medication', medication_id: 9 }, {}],
      [{ event_type: 'feed_registration', feed_movements: [{ quantity_kg: 100 }] }, {}],
      [{ event_type: 'farm_inspection' }, { derivedFarmId: 1, derivedHouseId: 11 }],
    ] as const
    for (const [datos, contexto] of validos) {
      expect(validarObligatoriosDeOperacion(datos as any, contexto as any), (datos as any).event_type)
        .toBeNull()
    }
  })

  it('vacío/`NaN` cuenta como ausente y los tipos sin regla propia pasan (null)', () => {
    expect(validarObligatoriosDeOperacion({
      event_type: 'vaccination', vaccine_id: Number.NaN,
      bird_movements: [{ quantity: 2 }],
    })).toBe('operations.vaccineRequired')
    expect(validarObligatoriosDeOperacion({ event_type: 'egg_collection', egg_movements: [] })).toBeNull()
    expect(validarObligatoriosDeOperacion({})).toBeNull()
    expect(validarObligatoriosDeOperacion(null)).toBeNull()
  })
})
