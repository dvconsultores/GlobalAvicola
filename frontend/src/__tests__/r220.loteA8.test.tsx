/**
 * R-220 · RED — Lote A, octava tanda: A15 (B-25).
 * `egg_classification` es una entrada **inalcanzable**: no pertenece a ningún flujo
 * de etapa (el flujo real es `egg_reception_classification`) y solo queda como
 * icono/color huérfano en el catálogo visual. Se retira del mapa (decisión del
 * SPEC: «retirar del switch/catálogo o cablear» — sin flujo que la produzca, retirar).
 */
import { describe, it, expect } from 'vitest'

import { EVENT_ICON_MAP, EVENT_COLOR_MAP, STAGE_OPERATIONS } from '../data/processCatalog'

describe('R-220 · Lote A octava tanda (RED)', () => {
  it('AC-R220-A·A15 · `egg_classification` deja de figurar como huérfana en los mapas', () => {
    expect('egg_classification' in EVENT_ICON_MAP, 'icono huérfano').toBe(false)
    expect('egg_classification' in EVENT_COLOR_MAP, 'color huérfano').toBe(false)
    // control: la entrada real (alcanzable por el flujo de recepción) permanece
    expect('egg_reception_classification' in EVENT_ICON_MAP).toBe(true)
    expect('egg_reception_classification' in EVENT_COLOR_MAP).toBe(true)
  })

  it('AC-R220-A·A15 · ningún flujo de etapa declara el tipo huérfano como paso', () => {
    const enFlujos = Object.values(STAGE_OPERATIONS).flat()
    expect(enFlujos.includes('egg_classification'), 'flujo lo produce').toBe(false)
  })
})
