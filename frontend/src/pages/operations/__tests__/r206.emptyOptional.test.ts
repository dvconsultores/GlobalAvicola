/**
 * `R-206` · RED unit — `limpiarVacios` (cadena vacía de un opcional ⇒ ausencia).
 *
 * El asistente normaliza `NaN` pero no la clase «`''` para un campo opcional»: la fecha de
 * cuarentena en blanco viaja como `''` y el servidor tipado la rechaza (400 BR-22). El
 * normalizador debe ser **recursivo** y conservar lo declarado (texto, números — incluido
 * el cero).
 *
 * En HEAD `limpiarVacios` no existe en `operationPayload.ts`: RED válida.
 */
import { describe, it, expect } from 'vitest'

import { limpiarVacios } from '../operationPayload'

describe('R-206 · limpiarVacios (canónico: vacío ⇒ ausencia)', () => {
  it.each([
    ['cadena vacía ⇒ ausencia', '', undefined],
    ['texto ⇒ texto', 'abc', 'abc'],
    ['número ⇒ número', 5, 5],
    ['cero declarado se conserva', 0, 0],
    ['espacios ⇒ tal cual (no es vacío)', '  ', '  '],
    ['null/undefined se conservan como ausencia', null, null],
  ] as const)('%s', (_n, entrada, salida) => {
    expect(limpiarVacios(entrada as any)).toEqual(salida as any)
  })

  it('recursivo: objetos y arrays anidados', () => {
    const entrada = {
      plan: { quarantine_end_date: '', quarantine_days: '', origin_country: 'Francia' },
      filas: [{ note: '', qty: 0 }, { note: 'ok' }],
      vacio: '',
    }
    expect(limpiarVacios(entrada)).toEqual({
      plan: { quarantine_end_date: undefined, quarantine_days: undefined, origin_country: 'Francia' },
      filas: [{ note: undefined, qty: 0 }, { note: 'ok' }],
      vacio: undefined,
    })
  })
})
