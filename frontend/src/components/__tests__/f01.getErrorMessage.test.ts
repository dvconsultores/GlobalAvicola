/**
 * R-189 (F-01) · RED — `getErrorMessage` debe entregar SIEMPRE un string renderizable,
 * también para el `detail` estructurado de FastAPI (lista de objetos de validación),
 * que hoy se filtra crudo y rompe el render (React #31).
 */
import { describe, it, expect } from 'vitest'
import { getErrorMessage } from '../Toast'

describe('R-189 · normalizador de errores (F-01)', () => {
  it('detail estructurado (lista FastAPI) ⇒ string legible con ubicación y mensaje', () => {
    const error = {
      response: {
        data: {
          detail: [{ type: 'missing', loc: ['body', 'egg_storage_records', 0, 'arrival_date'], msg: 'Field required', input: {} }],
        },
      },
    }
    const salida = getErrorMessage(error, 'Error al guardar')
    expect(typeof salida).toBe('string')
    expect(salida).toContain('Field required')
    expect(salida).toContain('arrival_date')
    expect(salida).not.toContain('[object Object]')
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
