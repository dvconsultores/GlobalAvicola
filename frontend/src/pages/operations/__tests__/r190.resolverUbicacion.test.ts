/**
 * `R-190` · RED unit puro — `resolverUbicacionDelEvento`.
 *
 * La ubicación del evento (`farm_id`/`house_id` que valida `BR-08`) se deriva de fuentes
 * ordenadas: el galpón del lote manda; si no lo tiene, la fila declarada (distribución —
 * destino), el origen (traslado), el selector «Galpón del evento» (salida/recolección/
 * despacho/inspección de transporte) o la fila inspeccionada (inspección de granja).
 * La granja se deriva del lote, de la selección o del catálogo del galpón elegido.
 *
 * En HEAD el helper **no existe** (`operationPayload.ts` no lo exporta): este fichero falla
 * al importar — RED válida por diseño.
 */
import { describe, it, expect } from 'vitest'

import { resolverUbicacionDelEvento } from '../operationPayload'

const LOTE_CON_GALPON = { farm_id: 1, house_id: 55 }
const LOTE_SIN_GALPON = { farm_id: 1, house_id: null }
const LOTE_SIN_GRANJA = { farm_id: null, house_id: null }

const FILA_DESTINO_11 = { target_house_id: 11 }
const FILA_ORIGEN_11_DESTINO_12 = { source_house_id: 11, target_house_id: 12 }
const FILA_SOLO_DESTINO_12 = { target_house_id: 12 }
const GALPONES = [
  { id: 11, farm_id: 1 },
  { id: 12, farm_id: 1 },
  { id: 55, farm_id: 1 },
]

describe('R-190 · resolverUbicacionDelEvento (tabla tipo × fuente)', () => {
  it.each([
    // El galpón del lote manda en todos los tipos (regla F-01e, C29)
    ['bird_distribution · lote con galpón manda sobre la fila',
      { eventType: 'bird_distribution', lote: LOTE_CON_GALPON, filas: [FILA_SOLO_DESTINO_12] },
      { farm_id: 1, house_id: 55 }],
    ['bird_transfer · lote con galpón manda sobre origen',
      { eventType: 'bird_transfer', lote: LOTE_CON_GALPON, filas: [FILA_ORIGEN_11_DESTINO_12] },
      { farm_id: 1, house_id: 55 }],
    // Distribución sin galpón de lote ⇒ destino de la fila 0
    ['bird_distribution · sin galpón de lote ⇒ target de la fila 0',
      { eventType: 'bird_distribution', lote: LOTE_SIN_GALPON, filas: [FILA_DESTINO_11] },
      { farm_id: 1, house_id: 11 }],
    ['bird_distribution · sin filas ⇒ ausencia (no se inventa)',
      { eventType: 'bird_distribution', lote: LOTE_SIN_GALPON, filas: [] },
      { farm_id: 1, house_id: undefined }],
    // Traslado ⇒ origen de la fila 0; en su defecto destino
    ['bird_transfer · sin galpón de lote ⇒ origen de la fila 0',
      { eventType: 'bird_transfer', lote: LOTE_SIN_GALPON, filas: [FILA_ORIGEN_11_DESTINO_12] },
      { farm_id: 1, house_id: 11 }],
    ['bird_transfer · sin origen ⇒ destino de la fila 0',
      { eventType: 'bird_transfer', lote: LOTE_SIN_GALPON, filas: [FILA_SOLO_DESTINO_12] },
      { farm_id: 1, house_id: 12 }],
    // Selector «Galpón del evento» × salida/recolección/despacho/inspección de transporte
    ['bird_exit · selector',
      { eventType: 'bird_exit', lote: LOTE_SIN_GALPON, houseSeleccionado: 11 },
      { farm_id: 1, house_id: 11 }],
    ['bird_exit · sin selector ⇒ ausencia',
      { eventType: 'bird_exit', lote: LOTE_SIN_GALPON },
      { farm_id: 1, house_id: undefined }],
    ['egg_collection · selector',
      { eventType: 'egg_collection', lote: LOTE_SIN_GALPON, houseSeleccionado: 11 },
      { farm_id: 1, house_id: 11 }],
    ['egg_dispatch · selector',
      { eventType: 'egg_dispatch', lote: LOTE_SIN_GALPON, houseSeleccionado: 11 },
      { farm_id: 1, house_id: 11 }],
    ['transport_inspection · selector',
      { eventType: 'transport_inspection', lote: LOTE_SIN_GALPON, houseSeleccionado: 11 },
      { farm_id: 1, house_id: 11 }],
    // Inspección de granja ⇒ granja elegida ?? granja de la fila inspeccionada
    ['farm_inspection · granja elegida + fila',
      { eventType: 'farm_inspection', lote: null, filas: [FILA_DESTINO_11], granjaSeleccionada: 1 },
      { farm_id: 1, house_id: 11 }],
    ['farm_inspection · sin granja ⇒ granja del catálogo del galpón de la fila',
      { eventType: 'farm_inspection', lote: null, filas: [FILA_DESTINO_11], galpones: GALPONES },
      { farm_id: 1, house_id: 11 }],
    ['farm_inspection · sin granja ni filas ⇒ ausencia total',
      { eventType: 'farm_inspection', lote: null },
      { farm_id: undefined, house_id: undefined }],
    // Lote sin granja + galpón elegido ⇒ granja derivada del catálogo
    ['lote sin granja + selector ⇒ farm del catálogo',
      { eventType: 'bird_exit', lote: LOTE_SIN_GRANJA, houseSeleccionado: 11, galpones: GALPONES },
      { farm_id: 1, house_id: 11 }],
    // Frontera incubadora: sin cambio (R-194)
    ['egg_reception_hatchery · sin cambio',
      { eventType: 'egg_reception_hatchery', lote: LOTE_CON_GALPON, houseSeleccionado: 11 },
      { farm_id: 1, house_id: 55 }],
    ['chick_dispatch · sin cambio',
      { eventType: 'chick_dispatch', lote: LOTE_CON_GALPON, houseSeleccionado: 11 },
      { farm_id: 1, house_id: 55 }],
  ] as const)('%s', (_nombre, args, esperado) => {
    expect(resolverUbicacionDelEvento(args as any)).toEqual(esperado)
  })
})
