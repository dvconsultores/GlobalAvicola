/**
 * P-16 — CUTOVER OPERACIONAL / CARGAS INICIALES   (`GA-REQ-061`)
 *
 * Corrida E2E específica por BU (regla del plan: no certificar BU por
 * transitividad) + escenario transversal con sondas negativas. El caso numérico
 * de oro es ENGORDE (§53 del mandato): 10.000 vivos − 35 mortalidad post ⇒
 * **9.965** (jamás 9.465), lifetime **535**, histórico ausente ⇒ UNKNOWN visible
 * (nunca 0).
 *
 * Artefactos: journal JSON por BU en `test-results/ga-req-061/` (pasos, cuerpos
 * y reconciliación) para la evidencia de la tranche.
 */
import { test, expect } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  API, cabeceraAdmin, cabeceraAprobador, cabeceraOtraEmpresa,
  registrar, sufijo,
} from '../test-support/e2e-api'

const CORTE = '2026-08-01T00:00:00+00:00'
const BU_IDS = ['grandparent', 'breeder', 'hatchery', 'broiler'] as const
type Bu = (typeof BU_IDS)[number]

const JOURNAL_DIR = resolve(process.cwd(), 'test-results', 'ga-req-061')

function journal(bu: string, paso: string, payload: unknown) {
  mkdirSync(JOURNAL_DIR, { recursive: true })
  const archivo = resolve(JOURNAL_DIR, `e2e-${bu}.json`)
  writeFileSync(archivo, JSON.stringify(payload, null, 2))
}

function haceDias(n: number): string {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - n)
  return d.toISOString().slice(0, 10)
}

/** Rellena la plantilla descargada con filas de datos (openpyxl del venv backend). */
function plantillaConFilasConEntrada(entrada: string, filas: unknown[][]): Buffer {
  const salida = `/tmp/ga061-rellena-${sufijo()}.xlsx`
  const script = `
import json, sys
from openpyxl import load_workbook
entrada, salida, filas = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
wb = load_workbook(entrada)
hoja = wb["Datos"]
for fila in filas:
    hoja.append(fila)
wb.save(salida)
`
  execFileSync(resolve('backend/.venv/bin/python'), ['-c', script, entrada, salida, JSON.stringify(filas)])
  return readFileSync(salida)
}

/** Deja la unidad habilitada para la empresa efectiva (idempotente). */
async function habilitarUnidad(request: any, cab: any, bu: Bu) {
  const unidades = await (await request.get(`${API}/business-units`, { headers: cab })).json()
  const objetivo = unidades.find((u: any) => u.code === bu || u.business_unit?.code === bu)
  if (objetivo && objetivo.is_enabled === false) {
    const r = await request.patch(`${API}/business-units/${objetivo.code ?? bu}/enable`, { headers: cab })
    expect(r.status(), await r.text()).toBe(200)
  }
}

/** El apply ancla el opening a la primera fase productiva activa (patrón P-11). */
async function asegurarFaseInicial(request: any, cab: any) {
  const r = await request.get(`${API}/masters/productive-phases`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  const fases = await r.json()
  if (fases.some((f: any) => f.is_active !== false)) return
  const creada = await request.post(`${API}/masters/productive-phases`, {
    headers: cab,
    data: { name: `P16-Cría-${sufijo()}`, code: `P16-${sufijo()}`, order: 1, duration_days: 140, is_initial: true },
  })
  expect(creada.status(), await creada.text()).toBe(201)
}

/** Descarga la plantilla real del endpoint a un fichero temporal. */
async function descargarPlantilla(request: any, cab: any, bu: string, destino: string) {
  const r = await request.get(`${API}/cutover-templates/${bu}`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  writeFileSync(destino, await r.body())
}

async function subir(request: any, cab: any, batchId: number, contenido: Buffer) {
  return request.post(`${API}/cutover-batches/${batchId}/upload`, {
    headers: cab,
    multipart: {
      file: {
        name: 'corte.xlsx',
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        buffer: contenido,
      },
    },
  })
}

/** Asegura que el rol del actor puede operar cutover (los seeds no lo traen). */
async function habilitarCutoverEnRoles(request: any, cab: any) {
  const roles = await (await request.get(`${API}/roles`, { headers: cab })).json()
  for (const rol of roles) {
    const actuales = (rol.permissions ?? []).map((p: any) => ({ module: p.module, action: p.action }))
    const faltan = [
      { module: 'cutover', action: 'read' },
      { module: 'cutover', action: 'validate' },
      { module: 'cutover', action: 'submit' },
      { module: 'cutover', action: 'approve' },
      { module: 'cutover', action: 'apply' },
      { module: 'cutover', action: 'create' },
      { module: 'corrections', action: 'read' },
      { module: 'corrections', action: 'correct' },
    ]
    const fusion = [...actuales]
    for (const f of faltan) {
      if (!fusion.some(p => p.module === f.module && p.action === f.action)) fusion.push(f)
    }
    if (fusion.length !== actuales.length) {
      const r = await request.put(`${API}/roles/${rol.id}`, { headers: cab, data: { permissions: fusion } })
      expect(r.status(), await r.text()).toBe(200)
    }
  }
}

async function cicloHastaApply(request: any, cab: any, cabAprobador: any, bu: Bu, filas: unknown[][]) {
  const s = sufijo()
  await habilitarUnidad(request, cab, bu)
  await asegurarFaseInicial(request, cab)
  const entrada = `/tmp/ga061-plantilla-${bu}-${s}.xlsx`
  await descargarPlantilla(request, cab, bu, entrada)
  const contenido = plantillaConFilasConEntrada(entrada, filas)

  const creado = await request.post(`${API}/cutover-batches`, {
    headers: cab, data: { business_unit: bu, cutover_datetime: CORTE },
  })
  expect(creado.status(), await creado.text()).toBe(201)
  const batchId = (await creado.json()).id

  const subida = await subir(request, cab, batchId, contenido)
  expect(subida.status(), await subida.text()).toBe(200)
  expect((await subida.json()).status).toBe('validated')

  const enviado = await request.post(`${API}/cutover-batches/${batchId}/submit`, { headers: cab })
  expect(enviado.status(), await enviado.text()).toBe(200)

  const aprobado = await request.post(`${API}/cutover-batches/${batchId}/approve`, { headers: cabAprobador })
  expect(aprobado.status(), await aprobado.text()).toBe(200)

  const aplicado = await request.post(`${API}/cutover-batches/${batchId}/apply`, { headers: cab })
  expect(aplicado.status(), await aplicado.text()).toBe(200)

  const items = await (await request.get(`${API}/cutover-batches/${batchId}/items`, { headers: cab })).json()
  const rec = await (await request.get(`${API}/cutover-batches/${batchId}/reconciliation`, { headers: cab })).json()
  return { batchId, items: items.items, reconciliacion: rec, s }
}

test.describe('P-16 · Cutover operacional — Cargas Iniciales (GA-REQ-061)', () => {
  for (const bu of BU_IDS) {
    test(`${bu}: ciclo batch→plantilla→apply→reconciliación`, async ({ request }) => {
      const cab = await cabeceraAdmin(request)
      const cabAprobador = await cabeceraAprobador(request)
      await habilitarCutoverEnRoles(request, cab)

      const s = sufijo()
      // ENGORDE: caso numérico de oro (10.000/500/35). Resto de BUs: caso vivo simple.
      const filas = bu === 'broiler'
        ? [
            [`E2E-${bu}-${s}-A`, '2026-07-01', 5000, 5000, 300, 200, null, 'golden'],
            [`E2E-${bu}-${s}-B`, '2026-07-01', 2000, 2000, null, null, null, 'histórico desconocido'],
          ]
        : [[`E2E-${bu}-${s}-1`, '2026-07-01', 1200, 800, 40, 30, null, '']]

      const corrida = await cicloHastaApply(request, cab, cabAprobador, bu, filas)

      // Reconciliación reproducible (mismas entradas ⇒ mismo reporte).
      const rec2 = await (await request.get(
        `${API}/cutover-batches/${corrida.batchId}/reconciliation`, { headers: cab })).json()
      expect(rec2).toEqual(corrida.reconciliacion)

      if (bu === 'broiler') {
        const loteA = corrida.items.find((i: any) => i.legacy_lot_reference.endsWith('-A')).lot_id
        const loteB = corrida.items.find((i: any) => i.legacy_lot_reference.endsWith('-B')).lot_id

        // Mortalidad post-cutover por el motor normal (35).
        const evento = await registrar(request, cab, {
          lot_id: loteA, event_type: 'mortality_recording', event_date: haceDias(7),
          bird_movements: [{ sex: 'female', quantity: 20, avg_weight: 1600 }, { sex: 'male', quantity: 15, avg_weight: 1700 }],
        })
        expect(evento.status(), await evento.text()).toBe(201)

        const rec = await (await request.get(
          `${API}/cutover-batches/${corrida.batchId}/reconciliation`, { headers: cab })).json()
        const filaA = rec.lots.find((l: any) => l.lot_id === loteA)
        const filaB = rec.lots.find((l: any) => l.lot_id === loteB)

        // GOLDEN §53: nunca 9.465.
        expect(filaA.opening.live).toBe(10000)
        expect(filaA.post.mortality).toBe(35)
        expect(filaA.current_live).toBe(9965)
        expect(filaA.current_live).not.toBe(9465)
        expect(filaA.lifetime.mortality).toBe(535)
        // Histórico desconocido ⇒ UNKNOWN visible en TODAS sus piezas (jamás 0).
        expect(filaB.opening.mortality_status).toBe('UNKNOWN')
        expect(filaB.lifetime.mortality).toBeNull()
        expect(filaA.post.feed_kg).toBeNull()  // feed UNKNOWN: 0 sería fabricación
        journal(bu, 'broiler', { ...corrida, rec })

        // Sondas negativas transversales (mismo batch de oro):
        // cross-company ⇒ 404 en lectura e intento de modificación.
        const ajeno = await cabeceraOtraEmpresa(request)
        const cruzado = await request.get(`${API}/cutover-batches/${corrida.batchId}/items`, { headers: ajeno })
        expect(cruzado.status()).toBe(404)
        const cruzadoApply = await request.post(`${API}/cutover-batches/${corrida.batchId}/apply`, { headers: ajeno })
        expect([403, 404]).toContain(cruzadoApply.status())
        // Re-apply ⇒ 409 determinista.
        const reapply = await request.post(`${API}/cutover-batches/${corrida.batchId}/apply`, { headers: cab })
        expect(reapply.status()).toBe(409)
        // Apply con errores pendientes: fila inválida ⇒ submit bloqueado (409).
        const mala = await request.post(`${API}/cutover-batches`, {
          headers: cab, data: { business_unit: 'broiler', cutover_datetime: CORTE },
        })
        expect(mala.status(), await mala.text()).toBe(201)
        const badId = (await mala.json()).id
        const s2 = sufijo()
        const entrada2 = `/tmp/ga061-plantilla-broiler-${s2}.xlsx`
        await descargarPlantilla(request, cab, 'broiler', entrada2)
        const conError = plantillaConFilasConEntrada(entrada2, [
          [`E2E-ERR-${s2}`, '2026-07-01', 10, 10, null, null, 'F-99999', 'granja inexistente'],
        ])
        const subidaMala = await subir(request, cab, badId, conError)
        expect((await subidaMala.json()).invalid_rows).toBe(1)
        const submitMalo = await request.post(`${API}/cutover-batches/${badId}/submit`, { headers: cab })
        expect(submitMalo.status()).toBe(409)
      } else {
        const rec = corrida.reconciliacion
        expect(rec.items).toBe(1)
        expect(rec.lots[0].current_live).toBe(2000)
        expect(rec.lots[0].opening.live).toBe(2000)
        journal(bu, bu, corrida)
      }
      journal(`${bu}-ok`, bu, { batchId: corrida.batchId, at: new Date().toISOString() })
    })
  }
})
