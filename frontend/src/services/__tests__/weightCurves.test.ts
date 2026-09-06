/**
 * Conversión de la tabla del proveedor — `AC-FE04`, `AC-FE14`.
 *
 * Lo que se comprueba aquí es que la conversión es **aritmética de formato**: separa filas y
 * columnas y convierte a número. Lo que se comprueba que **no** hace es juzgar: ninguna regla
 * de curva se evalúa en el cliente, porque el motor vive en el backend y dos jueces acaban
 * discrepando.
 */
import { describe, it, expect } from 'vitest'
import { parsearTabla } from '../weightCurves'

describe('parsearTabla', () => {
  it('lee una tabla con cabecera en el orden del backend', () => {
    const filas = parsearTabla(
      'age_days,target_weight,min_weight,max_weight\n10,100,90,110\n20,200,180,220')
    expect(filas).toEqual([
      { age_days: 10, target_weight: 100, min_weight: 90, max_weight: 110 },
      { age_days: 20, target_weight: 200, min_weight: 180, max_weight: 220 },
    ])
  })

  it('acepta cabeceras en español y punto y coma como separador', () => {
    const filas = parsearTabla('edad;objetivo;minimo;maximo\n10;100;90;110')
    expect(filas).toEqual([{ age_days: 10, target_weight: 100, min_weight: 90, max_weight: 110 }])
  })

  it('acepta la coma decimal cuando el separador es punto y coma', () => {
    // Es el CSV que exporta media Europa: `;` separa y `,` decimaliza. Con `,` separadora la
    // coma decimal es imposible por construcción, y no se intenta adivinarla.
    const filas = parsearTabla('edad;objetivo;minimo;maximo\n10;100,5;90,5;110,5')
    expect(filas[0].min_weight).toBe(90.5)
    expect(filas[0].max_weight).toBe(110.5)
    expect(filas[0].target_weight).toBe(100.5)
  })

  it('no descarta ni corrige filas incoherentes: eso lo juzga el backend', () => {
    // Mínimo mayor que máximo y edad repetida. Si el cliente las filtrara, el usuario vería
    // una carga «correcta» a la que le faltan filas, en vez del rechazo entero que `AC06`
    // exige.
    const filas = parsearTabla(
      'age_days,target_weight,min_weight,max_weight\n10,100,300,200\n10,100,90,110')
    expect(filas).toHaveLength(2)
    expect(filas[0].min_weight).toBe(300)
    expect(filas[0].max_weight).toBe(200)
  })

  it('deja el objetivo nulo cuando la tabla no lo trae', () => {
    const filas = parsearTabla('age_days,target_weight,min_weight,max_weight\n10,,90,110')
    expect(filas[0].target_weight).toBeNull()
  })

  it('devuelve nada ante un texto vacío', () => {
    expect(parsearTabla('   \n  ')).toEqual([])
  })
})
