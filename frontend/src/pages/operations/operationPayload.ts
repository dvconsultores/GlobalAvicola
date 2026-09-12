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

/** Filas de aves: limpia `NaN`/vacíos y descarta filas sin contenido real. */
export function serializarMovimientosDeAves(filas?: any[] | null): any[] {
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
      return CAMPOS_CON_CONTENIDO.some((campo) => !vacio((fila as Record<string, unknown>)[campo]))
    })
}

/** Identificador canónico de una referencia SAP: su código (`doc_number`/`ref_id`/`sap_code`), no el id de UI. */
export function identificadorDeOrdenSap(orden: any): string {
  if (!orden || typeof orden !== 'object') return ''
  const valor = orden.doc_number ?? orden.ref_id ?? orden.sap_code ?? orden.id ?? ''
  return valor === '' || valor === null || valor === undefined ? '' : String(valor)
}
