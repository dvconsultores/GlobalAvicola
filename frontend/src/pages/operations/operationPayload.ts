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

// ============================================================
// `R-220` · A17 (B-38/B-39) — campos de EVENTO anclados a la primera fila viva
// ============================================================

/**
 * La «Semana» o el «Peso prom.» del evento se capturan UNA vez (fila 0 de la UI), pero el
 * submit descarta las filas sin cantidad: si la fila 0 cae, el dato declarado se perdía.
 * Esta canonización re-ancla el valor declarado a la PRIMERA fila superviviente.
 *
 * Sin filas, sin valor declarado, o si la primera fila ya trae el campo ⇒ filas intactas
 * (nunca se inventa contenido).
 */
export function anclarCampoEnPrimeraFila<T extends Record<string, any>>(
  filas: T[],
  campo: string,
  valor: unknown,
): T[] {
  if (filas.length === 0 || vacio(valor)) return filas
  const primera = filas[0] as Record<string, unknown>
  if (!vacio(primera[campo])) return filas
  return [{ ...primera, [campo]: valor } as T, ...filas.slice(1)]
}

// ============================================================
// `R-220` · A16 (B-35 · BR-21) — reglas de nacimiento advertidas en cliente
// ============================================================

/**
 * Valida en cliente las reglas de `birth_registration` que el servidor aplica (BR-21):
 * `mixed` es excluyente con las filas sexadas, y sanos/débiles son obligatorios en la
 * cadena de incubadora. Devuelve la clave i18n del problema, o `null` si es válido.
 * El backend sigue siendo la autoridad final.
 */
export function validarReglasDeNacimiento(datos: {
  bird_movements?: Array<{ quantity?: unknown }> | null
  chicks_healthy?: unknown
  chicks_weak?: unknown
} | null | undefined): string | null {
  const filas = datos?.bird_movements || []
  const cantidad = (i: number) => Number((filas[i] as any)?.quantity || 0)
  const hayMixto = cantidad(2) > 0
  const haySexadas = cantidad(0) > 0 || cantidad(1) > 0
  if (hayMixto && haySexadas) return 'operations.mixedExclusive'
  const completos = [datos?.chicks_healthy, datos?.chicks_weak].every(
    (v) => v !== undefined && v !== null && Number.isFinite(Number(v)),
  )
  if (!completos) return 'operations.chicksRequired'
  return null
}

// ============================================================
// `R-206` · vacíos del asistente — «cadena vacía de un opcional» ⇒ ausencia
// ============================================================

/**
 * `''` ⇒ ausencia, recursivo (objetos y arrays). Conserva lo declarado — texto,
 * números (incluido el cero) y `null`—; las claves que quedan ausentes se **omiten**
 * (el contrato canónico no lleva `''` ni `undefined`).
 */
export function limpiarVacios(valor: unknown): unknown {
  if (valor === '') return undefined
  if (Array.isArray(valor)) return valor.map(limpiarVacios)
  if (valor && typeof valor === 'object' && Object.getPrototypeOf(valor) === Object.prototype) {
    const limpio: Record<string, unknown> = {}
    for (const [clave, v] of Object.entries(valor as Record<string, unknown>)) {
      const limpioV = limpiarVacios(v)
      if (limpioV !== undefined) limpio[clave] = limpioV
    }
    return limpio
  }
  return valor
}

/** Identificador canónico de una referencia SAP: su código (`doc_number`/`ref_id`/`sap_code`), no el id de UI. */
export function identificadorDeOrdenSap(orden: any): string {
  if (!orden || typeof orden !== 'object') return ''
  // `R-209` · C-02: sin código canónico se devuelve **ausencia** — el id de UI no viaja.
  const valor = orden.doc_number ?? orden.ref_id ?? orden.sap_code ?? ''
  return valor === '' || valor === null || valor === undefined ? '' : String(valor)
}

// ============================================================
// `R-190` · ubicación del evento — una sola fuente de verdad
// ============================================================

/** Tipos de `location_events` que derivan la ubicación del evento (`R-190` C-01; incubadora queda fuera, `R-194`). */
const EVENTOS_CON_UBICACION_DERIVADA = new Set([
  'bird_reception', 'bird_distribution', 'bird_transfer', 'bird_exit',
  'farm_inspection', 'transport_inspection', 'egg_collection', 'egg_dispatch',
  // `R-194`: la cadena de incubadora también es de `location_events` — su ubicación son
  // las declaradas por el lote incubadora (planta/galpón), nunca inventadas.
  'egg_reception_hatchery', 'chick_dispatch',
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

// ============================================================
// `R-205` · etapa del asistente — derivada, no sólo por navegación
// ============================================================

const STAGES_VALIDOS = new Set([
  'grandparent_rearing', 'grandparent_production', 'breeder_rearing',
  'breeder_production', 'hatchery', 'broiler',
])

/** Etapa del asistente: `?stage=` manda; si no, el lote (`bird_type` + fase); sin contexto ⇒ `null` (paso 1). */
export function resolverStageDelAsistente({ search, lote, eventType }: {
  search?: string
  lote?: { bird_type?: string | null; fase?: string | null } | null
  eventType?: string | null
}): string | null {
  void eventType
  const pedida = new URLSearchParams(search || '').get('stage')
  if (pedida && STAGES_VALIDOS.has(pedida)) return pedida
  const tipo = lote?.bird_type
  if (!tipo) return null
  const fase = String(lote?.fase || '').toLowerCase()
  const enProduccion = fase.includes('prod') || fase.includes('producc')
  if (tipo === 'breeder') return enProduccion ? 'breeder_production' : 'breeder_rearing'
  if (tipo === 'grandparent') return enProduccion ? 'grandparent_production' : 'grandparent_rearing'
  if (tipo === 'broiler') return 'broiler'
  if (tipo === 'hatchery') return 'hatchery'
  return null
}
