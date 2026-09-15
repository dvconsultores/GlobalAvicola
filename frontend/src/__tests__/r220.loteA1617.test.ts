/**
 * R-220 · A16/A17 (B-35/B-38/B-39).
 *
 * A17: la «Semana» y el «Peso prom.» del evento (capturados una vez, fila 0 de la UI) se
 * anclan a la PRIMERA fila superviviente al descarte de filas sin cantidad — el dato
 * declarado ya no se pierde si la fila 0 (machos / fértiles) va en 0. (RED original en
 * `f11786c`: la semana/peso declarados se perdían.)
 *
 * A16: validador cliente de BR-21 en `birth_registration` — `mixed` excluyente con las
 * filas sexadas; sanos/débiles obligatorios. El servidor sigue siendo la autoridad.
 */
import { describe, it, expect } from 'vitest'
import { anclarCampoEnPrimeraFila, serializarMovimientosDeAves, validarReglasDeNacimiento } from '../pages/operations/operationPayload'

describe('R-220 · A17 (B-38) · «Semana» del evento con la fila 0 en 0', () => {
  it('la semana declarada (fila machos) sobrevive al descarte de filas sin cantidad', () => {
    const crudas = [
      { sex: 'male', quantity: 0, week_number: 5 },
      { sex: 'female', quantity: 10 },
    ]
    const vivas = serializarMovimientosDeAves(crudas).filter((m: any) => (m.quantity ?? 0) > 0)
    const ancladas = anclarCampoEnPrimeraFila(vivas, 'week_number', (crudas[0] as any).week_number)
    expect(ancladas).toEqual([{ sex: 'female', quantity: 10, week_number: 5 }])
  })

  it('sin valor declarado o sin filas vivas ⇒ filas intactas (no se inventa)', () => {
    const vivas = [{ sex: 'female', quantity: 10 }]
    expect(anclarCampoEnPrimeraFila(vivas, 'week_number', undefined)).toEqual(vivas)
    expect(anclarCampoEnPrimeraFila([], 'week_number', 5)).toEqual([])
  })

  it('si la primera fila viva ya trae el campo, no se pisa', () => {
    const vivas = [{ sex: 'female', quantity: 10, week_number: 3 }, { sex: 'male', quantity: 2 }]
    expect(anclarCampoEnPrimeraFila(vivas, 'week_number', 5)).toEqual(vivas)
  })
})

describe('R-220 · A17 (B-39) · «Peso prom.» del huevo con fértiles en 0', () => {
  it('el peso promedio declarado (fila fértil) viaja anclado a la primera fila viva', () => {
    const crudas = [
      { egg_type: 'fertile', quantity: 0, avg_weight: 62.5 },
      { egg_type: 'dirty', quantity: 30 },
    ]
    const vivas = crudas.filter((m: any) => (m.quantity ?? 0) > 0)
    const ancladas = anclarCampoEnPrimeraFila(vivas, 'avg_weight', (crudas[0] as any).avg_weight)
    expect(ancladas).toEqual([{ egg_type: 'dirty', quantity: 30, avg_weight: 62.5 }])
  })
})

describe('R-220 · A16 (B-35) · validación cliente de nacimiento (BR-21)', () => {
  it('`mixed` con sexadas ⇒ mensaje de exclusividad (400 legítimo del servidor ya no es la 1ª defensa)', () => {
    expect(validarReglasDeNacimiento({
      bird_movements: [{ quantity: 50 }, { quantity: 20 }, { quantity: 10 }],
      chicks_healthy: 40,
      chicks_weak: 5,
    })).toBe('operations.mixedExclusive')
  })

  it('sanos/débiles en blanco ⇒ mensaje de obligatoriedad', () => {
    expect(validarReglasDeNacimiento({
      bird_movements: [{ quantity: 50 }, { quantity: 20 }, { quantity: 0 }],
      chicks_healthy: 40,
      chicks_weak: undefined,
    })).toBe('operations.chicksRequired')
  })

  it('nacimiento válido ⇒ sin mensaje (el servidor conserva la última palabra)', () => {
    expect(validarReglasDeNacimiento({
      bird_movements: [{ quantity: 50 }, { quantity: 20 }, { quantity: 0 }],
      chicks_healthy: 40,
      chicks_weak: 5,
    })).toBeNull()
  })
})
