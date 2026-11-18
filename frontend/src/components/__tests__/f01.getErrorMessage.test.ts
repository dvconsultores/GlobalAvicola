/**
 * R-189 (F-01) · RED — `getErrorMessage` debe entregar SIEMPRE un string renderizable,
 * también para el `detail` estructurado de FastAPI (lista de objetos de validación),
 * que hoy se filtra crudo y rompe el render (React #31).
 */
import { describe, it, expect } from 'vitest'
import { getErrorMessage } from '../Toast'

describe('R-189 · normalizador de errores (F-01)', () => {
  it('detail estructurado (lista FastAPI) ⇒ string legible con la ubicación en español', () => {
    const error = {
      response: {
        data: {
          detail: [{ type: 'missing', loc: ['body', 'egg_storage_records', 0, 'arrival_date'], msg: 'Field required', input: {} }],
        },
      },
    }
    const salida = getErrorMessage(error, 'Error al guardar')
    expect(typeof salida).toBe('string')
    // `F4` (AC-S1-F01): el mensaje de pydantic (inglés) se sustituye por uno en español.
    // `F6` §4: `type: 'missing'` no es un «valor no válido» — es un dato obligatorio que falta.
    expect(salida).toBe('Falta el dato obligatorio «arrival_date»')
    expect(salida).not.toContain('Field required')
    expect(salida).not.toContain('[object Object]')
  })

  it('item no `missing` ⇒ sigue siendo «Valor no válido en «campo»»', () => {
    const error = {
      response: {
        data: {
          detail: [{ type: 'int_parsing', loc: ['body', 'house_id'], msg: 'Input should be a valid integer' }],
        },
      },
    }
    expect(getErrorMessage(error, 'x')).toBe('Valor no válido en «galpón»')
  })

  it('detail string ⇒ se conserva', () => {
    const error = { response: { data: { detail: 'La importación de abuelas declara la orden de compra SAP' } } }
    expect(getErrorMessage(error, 'fallback')).toBe('La importación de abuelas declara la orden de compra SAP')
  })

  it('Error de red con message ⇒ string', () => {
    expect(getErrorMessage(new Error('Network Error'), 'fallback')).toBe('Network Error')
  })

  it('objeto desconocido ⇒ fallback humano (nunca un objeto)', () => {
    const salida = getErrorMessage({ raro: true }, 'Error al guardar')
    expect(typeof salida).toBe('string')
    expect(salida).toBe('Error al guardar')
  })

  it('detail objeto con msg ⇒ string', () => {
    const error = { response: { data: { detail: { msg: 'Campo inválido' } } } }
    expect(getErrorMessage(error, 'fallback')).toBe('Campo inválido')
  })
})
