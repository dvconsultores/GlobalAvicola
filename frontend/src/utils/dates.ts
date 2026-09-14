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
