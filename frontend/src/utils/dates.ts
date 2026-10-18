/**
 * `R-220` · A1 (C#17) — fechas civiles de la API.
 *
 * Las fechas `YYYY-MM-DD` que devuelve el backend son **fechas civiles**, no
 * instantes: `new Date('2026-09-10')` las interpreta como medianoche **UTC** y en
 * husos negativos (UTC−4) `toLocaleDateString()` muestra el día anterior. Este
 * formateador único construye la fecha por partes (año, mes, día) y la pinta con
 * el idioma indicado (o el del entorno).
 */
export function parseFechaCivil(value: string): Date {
  return new Date(
    Number(value.slice(0, 4)),
    Number(value.slice(5, 7)) - 1,
    Number(value.slice(8, 10)),
  )
}

const SOLO_FECHA = /^\d{4}-\d{2}-\d{2}$/

export function formatFecha(value?: string | null, locale?: string): string {
  if (!value) return '—'
  const d = SOLO_FECHA.test(value) ? parseFechaCivil(value) : new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString(locale, { day: '2-digit', month: '2-digit', year: 'numeric' })
}

/**
 * `QA-016` (R-30) — «hoy» como fecha civil `YYYY-MM-DD` en la zona horaria **local** del
 * operador, para usarla como tope (`max`) de los `<input type="date">` que registran hechos
 * ya ocurridos. `toISOString()` mide en UTC: en husos al este de Greenwich devuelve el día
 * anterior durante la madrugada y, al oeste, el día siguiente por la noche, de modo que el
 * calendario dejaría (o negaría) un día que el operador sí (o no) está viviendo. Se compone
 * por partes con `padStart`, sin pasar por UTC.
 */
export function hoyISO(base: Date = new Date()): string {
  const y = String(base.getFullYear())
  const m = String(base.getMonth() + 1).padStart(2, '0')
  const d = String(base.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/**
 * `R-220` · C6 (F G-13): fecha-HORA (marca de tiempo) con el locale de la app — nunca el
 * del navegador. Complementa `formatFecha` (fechas civiles) para `created_at`/`updated_at`.
 */
export function formatFechaHora(value?: string | Date | null, locale?: string): string {
  if (!value) return '—'
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString(locale, {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
