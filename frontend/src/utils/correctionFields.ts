/**
 * `015` · UAT-S1 (AC-S1-C03/C05) — nombre legible de un campo corregible.
 *
 * El backend (`GET /corrections/events/{id}/correctable-fields`) identifica el campo con su
 * nombre técnico: columnas del evento (`observations`, `water_liters`, `cause_id`…) o campos
 * de submovimiento con la forma `bird_movements[12].avg_weight` /
 * `feed_movements[3].quantity_kg`. Ese texto crudo no debe llegar al operador: esta función
 * lo traduce con `label_key`-equivalente (`corrections.fields.*`) y, en los submovimientos,
 * añade la fila (`corrections.row`) para distinguir p. ej. el peso de los machos del de las
 * hembras. Siempre devuelve una cadena (nunca `undefined`), aunque la clave no exista.
 */
const SUBMOVIMIENTO = /^(bird_movements|feed_movements)\[(\d+)\]\.(\w+)$/

export function describirCampoCorregido(t: (k: string, o?: any) => any, fieldName: string): string {
 const nombre = String(fieldName ?? '')
 const m = SUBMOVIMIENTO.exec(nombre)
 if (m) {
 const [, tabla, id, campo] = m
 const etiqueta = t(`corrections.fields.${tabla}.${campo}`, campo)
 const fila = t('corrections.row', { id })
 return `${String(etiqueta)} · ${String(fila)}`
 }
 return String(t(`corrections.fields.${nombre}`, nombre))
}
