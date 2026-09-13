/**
 * `R-205` · RED unit puro — `resolverStageDelAsistente`.
 *
 * El asistente (`OperationFormPage`) arrancaba con `stage=null` cuando llegaba por enlace
 * profundo (`?type=`), y el bloque de cuadre `breeder_rearing` (BR-20, `B01`) no se
 * renderizaba: la recepción de reproductoras por el hub canónico nacía sin cuadre y el
 * backend respondía 400. El `stage` debe derivarse del contexto con prioridad:
 * `?stage=` → lote (`bird_type` + fase) → sin contexto `null` (paso 1 actual).
 *
 * En HEAD el helper **no existe** (`operationPayload.ts` no lo exporta): RED válida.
 */
import { describe, it, expect } from 'vitest'

import { resolverStageDelAsistente } from '../operationPayload'

describe('R-205 · resolverStageDelAsistente (prioridad de fuentes)', () => {
  it.each([
    ['?stage= manda sobre todo',
      { search: '?stage=breeder_rearing', lote: { bird_type: 'broiler' }, eventType: 'bird_reception' },
      'breeder_rearing'],
    ['?stage= de producción',
      { search: '?stage=grandparent_production', lote: null, eventType: 'egg_collection' },
      'grandparent_production'],
    ['?stage= inválido ⇒ fallback al lote',
      { search: '?stage=no_existe', lote: { bird_type: 'breeder', fase: 'cría' }, eventType: 'bird_reception' },
      'breeder_rearing'],
    ['lote breeder en cría ⇒ breeder_rearing',
      { search: '', lote: { bird_type: 'breeder', fase: 'cría' }, eventType: 'bird_reception' },
      'breeder_rearing'],
    ['lote breeder en producción ⇒ breeder_production',
      { search: '', lote: { bird_type: 'breeder', fase: 'producción' }, eventType: 'feed_registration' },
      'breeder_production'],
    ['lote broiler ⇒ broiler',
      { search: '', lote: { bird_type: 'broiler' }, eventType: 'feed_registration' },
      'broiler'],
    ['lote grandparent en cría ⇒ grandparent_rearing',
      { search: '', lote: { bird_type: 'grandparent', fase: 'cría' }, eventType: 'bird_distribution' },
      'grandparent_rearing'],
    ['sin lote ni stage ⇒ null (paso 1)',
      { search: '', lote: null, eventType: 'bird_reception' },
      null],
    ['con stage pero sin lote ⇒ stage',
      { search: '?stage=broiler', lote: null, eventType: 'bird_exit' },
      'broiler'],
  ] as const)('%s', (_nombre, args, esperado) => {
    expect(resolverStageDelAsistente(args as any)).toBe(esperado)
  })
})
