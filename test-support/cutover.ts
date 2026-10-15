/**
 * SPEC 006 · soporte E2E del cutover v2 (Cargas Iniciales).
 *
 * Cada BU certifica su propio flujo por la interfaz; aquí viven las precondiciones por API
 * (permisos del módulo `cutover`, maestros por BU, fases) y el relleno de la plantilla
 * **descargada** con openpyxl (el fixture nunca fabrica la cabecera: usa la del servidor).
 */
import { expect, type APIRequestContext } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { API, empresaActiva, sufijo } from './e2e-api'

export type Bu = 'grandparent' | 'breeder' | 'hatchery' | 'broiler'

export const PERMISOS_CUTOVER = ['read', 'validate', 'submit', 'approve', 'apply', 'create']

/** Fecha civil `n` días atrás (UTC), sin literales que caduquen (R-28). */
export function haceDias(n: number): string {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - n)
  return d.toISOString().slice(0, 10)
}

/** Corte a medianoche UTC `n` días atrás, en el formato que acepta el backend. */
export function corteHaceDias(n: number): string {
  return `${haceDias(n)}T00:00:00+00:00`
}

/** Valor `datetime-local` (hora local) equivalente al corte, para el input de la pantalla. */
export function corteParaInput(n: number): string {
  return `${haceDias(n)}T00:00`
}

/** Asegura que todos los roles pueden operar el cutover (los seeds no lo traen). */
export async function habilitarCutoverEnRoles(request: APIRequestContext, cab: any): Promise<void> {
  const roles = await (await request.get(`${API}/roles`, { headers: cab })).json()
  for (const rol of roles) {
    const actuales = (rol.permissions ?? []).map((p: any) => ({ module: p.module, action: p.action }))
    const fusion = [...actuales]
    for (const action of PERMISOS_CUTOVER) {
      if (!fusion.some(p => p.module === 'cutover' && p.action === action)) fusion.push({ module: 'cutover', action })
    }
    for (const action of ['read', 'create']) {
      if (!fusion.some(p => p.module === 'lots' && p.action === action)) fusion.push({ module: 'lots', action })
    }
    if (fusion.length !== actuales.length) {
      const r = await request.put(`${API}/roles/${rol.id}`, { headers: cab, data: { permissions: fusion } })
      expect(r.status(), await r.text()).toBe(200)
    }
  }
}

/** Deja la unidad habilitada para la empresa efectiva (idempotente). */
export async function habilitarUnidad(request: APIRequestContext, cab: any, bu: Bu): Promise<void> {
  const unidades = await (await request.get(`${API}/business-units`, { headers: cab })).json()
  const objetivo = unidades.find((u: any) => u.code === bu || u.business_unit?.code === bu)
  if (objetivo && objetivo.is_enabled === false) {
    const r = await request.patch(`${API}/business-units/${objetivo.code ?? bu}/enable`, { headers: cab })
    expect(r.status(), await r.text()).toBe(200)
  }
}

/** Fases globales por código (`CRIA/PROD/INCUB/ENGORDE`): el contrato v2 declara la fase por código. */
export async function asegurarFases(request: APIRequestContext, cab: any): Promise<Record<string, number>> {
  const r = await request.get(`${API}/masters/productive-phases`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  const fases: any[] = await r.json()
  const ids: Record<string, number> = {}
  const esperadas: [string, string, number, boolean, boolean][] = [
    ['CRIA', 'Cría', 1, true, false], ['PROD', 'Producción', 2, false, false],
    ['INCUB', 'Incubación', 3, false, false], ['ENGORDE', 'Engorde', 4, false, true],
  ]
  for (const [code, name, order, inicial, final] of esperadas) {
    const existente = fases.find(f => f.code === code)
    if (existente) { ids[code] = existente.id; continue }
    const creada = await request.post(`${API}/masters/productive-phases`, {
      headers: cab, data: { name, code, order, duration_days: 140, is_initial: inicial, is_final: final },
    })
    expect(creada.status(), await creada.text()).toBe(201)
    ids[code] = (await creada.json()).id
  }
  return ids
}

export interface MaestrosCutover {
  companyId: number
  farmId: number
  houseId: number
  farmCode: string
  houseName: string
  hatcheryCode: string
  incubatorName: string
  hatcherName: string
  lineCode: string
  breedName: string
  prefijo: string
}

/** Granja+galpón, planta+incubadora+nacedora, línea+raza propios del escenario (códigos únicos). */
export async function crearMaestrosCutover(request: APIRequestContext, cab: any, bu: Bu): Promise<MaestrosCutover> {
  const companyId = empresaActiva(cab)
  const s = sufijo().toUpperCase()
  const crear = async (ruta: string, data: any) => {
    const r = await request.post(`${API}${ruta}`, { headers: cab, data })
    expect(r.status(), `${ruta}: ${await r.text()}`).toBe(201)
    return await r.json()
  }
  const granja = await crear('/masters/farms', {
    company_id: companyId, name: `P16-${bu}-granja-${s}`, code: `P16-G-${s}`, farm_type: 'breeding', location: 'E2E',
  })
  const galpon = await crear('/masters/houses', { farm_id: granja.id, name: `P16-GALPON-${s}`, capacity: 60_000 })
  const planta = await crear('/masters/hatcheries', { company_id: companyId, name: `P16-planta-${s}`, code: `P16-INC-${s}` })
  await crear('/masters/incubators', { hatchery_id: planta.id, name: `P16-INCUBADORA-${s}`, capacity: 120_000 })
  await crear('/masters/hatchers', { hatchery_id: planta.id, name: `P16-NACEDORA-${s}`, capacity: 120_000 })
  const linea = await crear('/masters/genetic-lines', { company_id: companyId, name: `P16-linea-${s}`, code: `P16-L-${s}` })
  await crear('/masters/breeds', { genetic_line_id: linea.id, name: `P16-RAZA-${s}`, bird_type: bu === 'hatchery' ? 'breeder' : bu })
  return {
    companyId, farmId: granja.id, houseId: galpon.id, farmCode: `P16-G-${s}`, houseName: `P16-GALPON-${s}`, hatcheryCode: `P16-INC-${s}`,
    incubatorName: `P16-INCUBADORA-${s}`, hatcherName: `P16-NACEDORA-${s}`, lineCode: `P16-L-${s}`,
    breedName: `P16-RAZA-${s}`, prefijo: s,
  }
}

/**
 * Rellena la plantilla descargada: cada fila es un objeto `{columna: valor}`; las columnas se
 * toman de la cabecera real de `Datos` (lo que no se indica queda vacío = UNKNOWN).
 */
export function rellenarPlantilla(plantilla: Buffer, filas: Record<string, unknown>[]): Buffer {
  const dir = mkdtempSync(join(tmpdir(), 'ga-cut2-'))
  const entrada = join(dir, 'plantilla.xlsx')
  const salida = join(dir, 'carga.xlsx')
  writeFileSync(entrada, plantilla)
  const script = `
import json, sys
from openpyxl import load_workbook
entrada, salida, filas = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
wb = load_workbook(entrada)
hoja = wb["Datos"]
cabecera = [c.value for c in hoja[1] if c.value is not None]
for fila in filas:
    desconocidas = set(fila) - set(cabecera)
    assert not desconocidas, f"columnas fuera de la plantilla: {sorted(desconocidas)}"
    hoja.append([fila.get(c, None) for c in cabecera])
wb.save(salida)
print(";".join(cabecera))
`
  execFileSync(resolve('backend/.venv/bin/python'), ['-c', script, entrada, salida, JSON.stringify(filas)])
  return readFileSync(salida)
}

/** CSV v2 (`;`, UTF-8 con BOM) a partir de la cabecera descargada del servidor. */
export function construirCsv(cabeceraCsv: string, filas: Record<string, unknown>[]): Buffer {
  const texto = cabeceraCsv.replace(/^﻿/, '').trim()
  const delimitador = texto.includes(';') ? ';' : ','
  const columnas = texto.split(delimitador)
  const lineas = [columnas.join(delimitador)]
  for (const fila of filas) {
    lineas.push(columnas.map(c => {
      const v = fila[c]
      return v === undefined || v === null ? '' : String(v)
    }).join(delimitador))
  }
  return Buffer.from('﻿' + lineas.join('\n') + '\n', 'utf8')
}

/** Filas canónicas por BU para el escenario (valores KNOWN/UNKNOWN/N/A deliberados). */
export function filasPorBu(bu: Bu, m: MaestrosCutover, ref: string): Record<string, unknown>[] {
  if (bu === 'hatchery') {
    return [{
      legacy_lot_code: ref, hatchery_code: m.hatcheryCode, incubator_name: m.incubatorName, hatcher_name: m.hatcherName,
      generation: 'breeder', reception_date: haceDias(50), set_date: haceDias(48), expected_hatch_date: haceDias(27),
      eggs_received: 10000, eggs_set: 9000, eggs_transferred: 0, eggs_discarded: 100, chicks_hatched: 0, chicks_available: 0,
      source_system: 'LEGACY', source_reference: `E2E-${ref}`,
    }]
  }
  if (bu === 'broiler') {
    return [{
      legacy_lot_code: ref, farm_code: m.farmCode, house_name: m.houseName, productive_phase_code: 'ENGORDE',
      real_start_date: haceDias(60), live_birds: 10000, age_days: 20, accumulated_birds_received: 10500,
      historical_mortality: 300, historical_culls: 200, partial_outbound_birds: 0, accumulated_feed_kg: 15000,
      current_avg_weight_g: 900, source_system: 'LEGACY',
    }]
  }
  return [{
    legacy_lot_code: ref, farm_code: m.farmCode, house_name: m.houseName, productive_phase_code: 'PROD',
    real_start_date: haceDias(200), phase_start_date: haceDias(60), genetic_line_code: m.lineCode, breed_name: m.breedName,
    live_males: 1000, live_females: 9000, historical_mortality_males: 50, historical_mortality_females: 450,
    historical_culls_males: 0, historical_culls_females: 0, accumulated_feed_kg: 120000.5, current_avg_weight_g: 3200,
    accumulated_egg_production: 180000, accumulated_eggs_to_hatchery: 150000, source_system: 'LEGACY',
  }]
}

/** Primer evento operativo post-corte por BU (mandato §30), por API. */
export async function primerEventoPostCorte(request: APIRequestContext, cab: any, bu: Bu, lotId: number, m?: MaestrosCutover) {
  const fecha = haceDias(7)
  if (bu === 'hatchery') {
    return request.post(`${API}/operations`, { headers: cab, data: {
      lot_id: lotId, event_type: 'incubation_load', event_date: fecha, hatchery_params: [{ quantity_loaded: 1000 }],
    } })
  }
  if (bu === 'broiler') {
    return request.post(`${API}/operations`, { headers: cab, data: {
      lot_id: lotId, event_type: 'mortality_recording', event_date: fecha,
      bird_movements: [{ sex: 'mixed', quantity: 35, avg_weight: 900 }],
    } })
  }
  if (bu === 'breeder') {
    return request.post(`${API}/operations`, { headers: cab, data: {
      lot_id: lotId, event_type: 'egg_collection', event_date: fecha, farm_id: m?.farmId, house_id: m?.houseId,
      egg_movements: [{ egg_type: 'fertile', quantity: 7000 }],
    } })
  }
  return request.post(`${API}/operations`, { headers: cab, data: {
    lot_id: lotId, event_type: 'mortality_recording', event_date: fecha,
    bird_movements: [{ sex: 'female', quantity: 20, avg_weight: 3200 }, { sex: 'male', quantity: 15, avg_weight: 3600 }],
  } })
}
