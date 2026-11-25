/**
 * `SPEC 020 §6` · `RR-30` / `RR-34` — espejo **de presentación** de la derivación del servidor.
 *
 * La «Semana N» es la edad productiva del lote: `(fecha_evento − inicio_del_lote).días // 7 + 1`
 * (semana 1 = días 0–6), no la semana ISO del calendario. El servidor es la autoridad y recalcula
 * al guardar; esta función solo permite mostrar la semana y la fase de solo lectura mientras se
 * captura. Nunca inventa: sin fecha base, o con un evento anterior al inicio, devuelve `null`.
 */

/** Día de calendario (UTC, sin hora) de `AAAA-MM-DD` o de un ISO con hora; `null` si no hay. */
export function diaDeCalendario(valor: string | Date | null | undefined): number | null {
  if (!valor) return null
  const texto = typeof valor === 'string' ? valor.slice(0, 10) : valor.toISOString().slice(0, 10)
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto)
  if (!m) return null
  return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
}

const MS_POR_DIA = 86_400_000

/** Semana productiva (1 = días 0–6 de vida del lote) o `null` si no se puede derivar. */
export function semanaProductiva(
  inicioDelLote: string | Date | null | undefined,
  fechaDelEvento: string | Date | null | undefined,
): number | null {
  const inicio = diaDeCalendario(inicioDelLote)
  const fecha = diaDeCalendario(fechaDelEvento)
  if (inicio === null || fecha === null) return null
  const dias = Math.round((fecha - inicio) / MS_POR_DIA)
  if (dias < 0) return null
  return Math.floor(dias / 7) + 1
}

export interface FaseDelLote {
  id?: number
  phase_id: number
  start_date: string
  end_date?: string | null
  phase?: { name?: string | null; code?: string | null } | null
}

/** Fase vigente en `fecha`: `start_date <= fecha` y `end_date` nulo o `>= fecha`; gana la más reciente. */
export function faseVigente(
  fases: FaseDelLote[] | null | undefined,
  fecha: string | Date | null | undefined,
): FaseDelLote | null {
  const dia = diaDeCalendario(fecha)
  if (dia === null) return null
  const vigentes = (fases || []).filter((f) => {
    const inicio = diaDeCalendario(f.start_date)
    const fin = diaDeCalendario(f.end_date ?? null)
    return inicio !== null && inicio <= dia && (fin === null || fin >= dia)
  })
  vigentes.sort((a, b) =>
    (diaDeCalendario(b.start_date) as number) - (diaDeCalendario(a.start_date) as number)
    || (b.id ?? 0) - (a.id ?? 0))
  return vigentes[0] ?? null
}
