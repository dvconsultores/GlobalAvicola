/**
 * Cliente de las curvas estándar de peso — `OD-06` · `GA-REM-037` enmienda A.
 *
 * Los tipos siguen el contrato **real** del backend, leído del `openapi()` en ejecución y
 * anotado en `audit/remediation/R96_WEIGHT_CURVE_FRONTEND_CONTRACT_MATRIX.md`. No hay `any`
 * en las respuestas: escribirlo sería renunciar a modelar el contrato.
 */
import api from './api'

export interface WeightCurvePoint {
  id?: number
  age_days: number
  min_weight: number
  max_weight: number
  target_weight?: number | null
}

export interface WeightCurve {
  id: number
  genetic_line_id: number
  /**
   * `version_label`, nunca `version`. Este proyecto reserva `version` para lo que fija el
   * servidor, y `R-32` barre los esquemas de escritura buscando ese nombre. Aquí lo escribe
   * el administrador: es la etiqueta que publica el proveedor de la genética.
   */
  version_label: string
  is_active: boolean
  source?: string | null
  created_at: string
  points: WeightCurvePoint[]
}

export interface GeneticLine {
  id: number
  name: string
  code?: string | null
}

/** Una fila rechazada por el backend: fila, campo y motivo. */
export interface CurveRowError {
  fila: number
  campo: string
  motivo: string
}

export async function listWeightCurves(geneticLineId: number): Promise<WeightCurve[]> {
  const r = await api.get<WeightCurve[]>(
    `/masters/genetic-lines/${geneticLineId}/weight-curves`)
  return r.data
}

export async function getGeneticLine(id: number): Promise<GeneticLine> {
  const r = await api.get<GeneticLine>(`/masters/genetic-lines/${id}`)
  return r.data
}

export async function uploadWeightCurve(input: {
  genetic_line_id: number
  version_label: string
  source?: string
  is_active?: boolean
  points: WeightCurvePoint[]
}): Promise<WeightCurve> {
  // JSON, no `FormData`: el backend no recibe multipart. Ver §4 de la matriz de contrato.
  const r = await api.post<WeightCurve>('/masters/weight-curves', input)
  return r.data
}

export async function activateWeightCurve(curveId: number): Promise<WeightCurve> {
  const r = await api.put<WeightCurve>(`/masters/weight-curves/${curveId}/activate`)
  return r.data
}

/**
 * Convierte la tabla del proveedor en las filas que el backend espera.
 *
 * Es **aritmética de formato y nada más**: separa filas y columnas y convierte a número. No
 * comprueba edades repetidas, ni que el mínimo no supere al máximo, ni que el objetivo caiga
 * dentro del rango. Todo eso lo juzga el backend (`AC03`, `AC04`), y repetirlo aquí crearía
 * un segundo juez que acabaría discrepando.
 *
 * Se hace en el cliente porque el contrato exige los puntos ya estructurados: no existe
 * endpoint que reciba un archivo.
 */
export function parsearTabla(texto: string): WeightCurvePoint[] {
  const lineas = texto.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
  if (!lineas.length) return []

  const separador = lineas[0].includes(';') ? ';' : ','
  const columnas = lineas[0].split(separador).map(c => c.trim().toLowerCase())
  const conCabecera = columnas.includes('age_days') || columnas.some(c => c.startsWith('edad'))

  const indice = (...nombres: string[]) =>
    columnas.findIndex(c => nombres.some(n => c === n || c.startsWith(n)))

  const iEdad = conCabecera ? indice('age_days', 'edad') : 0
  const iObjetivo = conCabecera ? indice('target_weight', 'objetivo') : 1
  const iMin = conCabecera ? indice('min_weight', 'minimo', 'mínimo') : 2
  const iMax = conCabecera ? indice('max_weight', 'maximo', 'máximo') : 3

  const numero = (v: string | undefined): number | null => {
    if (v === undefined || v.trim() === '') return null
    const n = Number(v.replace(',', '.'))
    return Number.isFinite(n) ? n : null
  }

  return lineas.slice(conCabecera ? 1 : 0).map(linea => {
    const celdas = linea.split(separador)
    return {
      age_days: numero(celdas[iEdad]) ?? NaN,
      target_weight: iObjetivo >= 0 ? numero(celdas[iObjetivo]) : null,
      min_weight: numero(celdas[iMin]) ?? NaN,
      max_weight: numero(celdas[iMax]) ?? NaN,
    }
  })
}
