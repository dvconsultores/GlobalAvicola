/**
 * `015` · UAT-S1 — el nombre del campo corregido se muestra legible (nunca el crudo).
 */
import { describe, it, expect } from 'vitest'
import { describirCampoCorregido } from '../correctionFields'

const DICC: Record<string, string> = {
 'corrections.fields.observations': 'Observaciones',
 'corrections.fields.bird_movements.avg_weight': 'Peso promedio',
 'corrections.fields.bird_movements.week_number': 'Semana',
 'corrections.fields.feed_movements.quantity_kg': 'Cantidad de alimento (kg)',
 'corrections.fields.water_liters': 'Litros de agua',
}
// `t` de i18next simulado: interpola `{{id}}` y cae al valor por defecto/ clave.
const t = (k: string, o?: any) => {
 const plantilla = DICC[k] ?? (typeof o === 'string' ? o : k)
 return String(plantilla).replace(/\{\{(\w+)\}\}/g, (_m, p) => String(o?.[p] ?? ''))
}
// El mock de i18next real devuelve `fila {{id}}` sin interpolar cuando no hay valor.
const tConFila = (k: string, o?: any) => (k === 'corrections.row' ? `fila ${o?.id}` : t(k, o))

describe('describirCampoCorregido', () => {
 it('traduce un campo del evento', () => {
  expect(describirCampoCorregido(t, 'observations')).toBe('Observaciones')
  expect(describirCampoCorregido(t, 'water_liters')).toBe('Litros de agua')
 })

 it('campo de submovimiento: etiqueta traducida + fila', () => {
  expect(describirCampoCorregido(tConFila, 'bird_movements[5].avg_weight')).toBe('Peso promedio · fila 5')
  expect(describirCampoCorregido(tConFila, 'bird_movements[12].week_number')).toBe('Semana · fila 12')
  expect(describirCampoCorregido(tConFila, 'feed_movements[3].quantity_kg')).toBe('Cantidad de alimento (kg) · fila 3')
 })

 it('nunca devuelve el nombre crudo del submovimiento ni un valor no-string', () => {
  const crudo = describirCampoCorregido(tConFila, 'bird_movements[5].avg_weight')
  expect(crudo).not.toContain('bird_movements[')
  expect(typeof describirCampoCorregido((k: string) => k, 'desconocido')).toBe('string')
  expect(describirCampoCorregido((k: string) => k, 'desconocido')).toBe('corrections.fields.desconocido')
 })

 it('sin traducción cae al nombre del campo (campo del evento)', () => {
  expect(describirCampoCorregido(t, 'campo_raro')).toBe('campo_raro')
 })
})
