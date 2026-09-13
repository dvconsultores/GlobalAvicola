/**
 * R-189 (F-01) · Serializador del asistente de operaciones.
 *
 * El formulario puede usar valores cómodos para la UI (p.ej. `[{}]` de arranque o `valueAsNumber`
 * vacío ⇒ `NaN`), pero lo que viaja en el POST debe ser el contrato canónico del API:
 *
 *   · listas sin registros ⇒ `[]` (nunca un objeto vacío accidental);
 *   · números vacíos (`NaN`) ⇒ omitidos (no se inventan valores; la cantidad 0 declarada se conserva);
 *   · filas de aves sin contenido real (solo `sex`/`week_number` por omisión) ⇒ descartadas;
 *   · la referencia SAP se identifica por su **código** (lo que el dominio valida), no por el id de UI.
 */

/** `true` cuando el valor es «no provisto»: vacío, nulo, cadena vacía o número no finito (`NaN`). */
const vacio = (v: unknown): boolean =>
  v === undefined || v === null || v === '' || (typeof v === 'number' && !Number.isFinite(v))

/** Campos que dan «contenido» a una fila de aves; `sex`/`week_number` por omisión no cuentan. */
const CAMPOS_CON_CONTENIDO = [
  'quantity', 'avg_weight', 'sample_size', 'breed_id', 'source_house_id', 'target_house_id',
] as const

/** Registros de almacenamiento con contenido real; sin ninguno ⇒ `[]` (contrato canónico). */
export function serializarAlmacenamientoDeHuevos(registros?: any[] | null): any[] {
  return (registros || []).filter(
    (r) => r && typeof r === 'object' && Object.values(r).some((v) => !vacio(v)),
  )
}

/** Limpia `NaN`/vacíos de cada fila y descarta las que no conservan contenido en `campos`. */
function filasConContenido(filas: any[] | null | undefined, campos: readonly string[]): any[] {
  return (filas || [])
    .map((fila) => {
      if (!fila || typeof fila !== 'object') return fila
      const limpia: Record<string, unknown> = {}
      for (const [clave, valor] of Object.entries(fila)) {
        if (!vacio(valor)) limpia[clave] = valor
      }
      return limpia
    })
    .filter((fila) => {
      if (!fila || typeof fila !== 'object') return false
      return campos.some((campo) => !vacio((fila as Record<string, unknown>)[campo]))
    })
}

/** Filas de aves: limpia `NaN`/vacíos y descarta filas sin contenido real. */
export function serializarMovimientosDeAves(filas?: any[] | null): any[] {
  return filasConContenido(filas, CAMPOS_CON_CONTENIDO)
}

/** Campos que dan «contenido» a una fila de alimento (`F-01d`). */
const CAMPOS_CON_CONTENIDO_ALIMENTO = [
  'feed_type_id', 'week_number', 'quantity_kg', 'sacks_count', 'sap_order_id',
] as const

/** Campos que dan «contenido» a los parámetros de incubadora (`F-01d`); `machine_type` es de UI y no cuenta. */
const CAMPOS_CON_CONTENIDO_INCUBADORA = [
  'hatchery_id', 'incubator_id', 'hatcher_id', 'temperature', 'humidity', 'co2',
  'turning', 'quantity_loaded', 'quantity_transferred',
] as const

/** Movimientos de alimento (`F-01d`): el `[{}]` de arranque del formulario nunca viaja; canónico ⇒ `[]`. */
export function serializarMovimientosDeAlimento(filas?: any[] | null): any[] {
  return filasConContenido(filas, CAMPOS_CON_CONTENIDO_ALIMENTO)
}

/** Parámetros de incubadora (`F-01d`): filas sin contenido real ⇒ descartadas. */
export function serializarParamsDeIncubadora(filas?: any[] | null): any[] {
  return filasConContenido(filas, CAMPOS_CON_CONTENIDO_INCUBADORA)
}

/** Identificador canónico de una referencia SAP: su código (`doc_number`/`ref_id`/`sap_code`), no el id de UI. */
export function identificadorDeOrdenSap(orden: any): string {
  if (!orden || typeof orden !== 'object') return ''
  const valor = orden.doc_number ?? orden.ref_id ?? orden.sap_code ?? orden.id ?? ''
  return valor === '' || valor === null || valor === undefined ? '' : String(valor)
}

// ============================================================
// `R-190` · ubicación del evento — una sola fuente de verdad
// ============================================================

/** Tipos de `location_events` que derivan la ubicación del evento (`R-190` C-01; incubadora queda fuera, `R-194`). */
const EVENTOS_CON_UBICACION_DERIVADA = new Set([
  'bird_reception', 'bird_distribution', 'bird_transfer', 'bird_exit',
  'farm_inspection', 'transport_inspection', 'egg_collection', 'egg_dispatch',
])

export interface FuentesDeUbicacion {
  eventType: string
  /** El lote seleccionado (o `null`): su galpón manda cuando existe (regla F-01e, C29). */
  lote?: { farm_id?: number | null; house_id?: number | null } | null
  /** Filas del formulario: destino de la fila 0 (distribución/inspección de granja) u origen/destino (traslado). */
  filas?: Array<{ source_house_id?: number | null; target_house_id?: number | null }>
  /** «Galpón del evento»: salida, recolección, despacho e inspección de transporte (C-05). */
  houseSeleccionado?: number | null
  /** Granja elegida a mano (inspección de granja, C-07). */
  granjaSeleccionada?: number | null
  /** Catálogo de galpones, para derivar la granja del galpón elegido cuando el lote no la declara (C-08). */
  galpones?: Array<{ id: number; farm_id?: number | null }>
}

/** `farm_id`/`house_id` del evento según la cadena de fuentes de `R-190` — sin inventar: sin fuente, ausencia. */
export function resolverUbicacionDelEvento({
  eventType, lote, filas, houseSeleccionado, granjaSeleccionada, galpones,
}: FuentesDeUbicacion): { farm_id?: number | null; house_id?: number | null } {
  if (!EVENTOS_CON_UBICACION_DERIVADA.has(eventType)) {
    // Fronteras (`R-194` incubadora, importación, etc.): conservan su mapeo actual.
    return { farm_id: lote?.farm_id ?? undefined, house_id: lote?.house_id ?? undefined }
  }
  let house: number | undefined = lote?.house_id ?? undefined
  let farm: number | undefined = lote?.farm_id ?? undefined
  if (farm === undefined && granjaSeleccionada != null) farm = granjaSeleccionada
  if (house === undefined) {
    if (eventType === 'bird_reception' || eventType === 'bird_distribution') {
      house = filas?.[0]?.target_house_id ?? undefined
    } else if (eventType === 'bird_transfer') {
      house = filas?.[0]?.source_house_id ?? filas?.[0]?.target_house_id ?? undefined
    } else if (eventType === 'farm_inspection') {
      house = filas?.[0]?.target_house_id ?? undefined
    } else {
      house = houseSeleccionado ?? undefined
    }
  }
  if (farm === undefined && house != null) {
    farm = galpones?.find((g) => g.id === house)?.farm_id ?? undefined
  }
  return { farm_id: farm ?? undefined, house_id: house ?? undefined }
}
