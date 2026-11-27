/**
 * SPEC 018 · E2E de la incubadora V4 — desglose de no incubables + huevos fértiles a fosa.
 *
 * Certifica el flujo completo del §44 del mandato sobre el contrato **V4** (23 columnas, sin
 * `eggs_discarded`): plantilla XLSX/CSV descargada del batch, relleno, validación, preview,
 * aprobación con **otro actor**, apply, reconciliación (`opening.hatchery` + `current`),
 * refresco/re-login, rechazos controlados de cabeceras ajenas e históricas y la BR-03
 * post-corte con el saldo ya descontado de los no incubables (sin doble conteo).
 *
 * Reglas del contrato que se verifican aquí (SPEC 018 §2):
 * - D-3: `eggs_non_incubable_total = oversized + dirty + broken` solo si los tres son KNOWN.
 * - D-4: el saldo es `received − set − Σ(no incubables KNOWN)` (una sola resta ⇒ nunca −1 000).
 * - D-21/D-23 (SPEC 018 §9 · OD-HATCH-V4-02 RATIFIED): la fosa es PRE-CARGA (`set + no incubables +
 *   fosa ≤ received`) y `eggs_in_process = set − transferred` (no es un no incubable ni un descarte).
 * - D-2: `eggs_discarded` fuera del contrato V4 ⇒ NULL + NOT_APPLICABLE en persistencia.
 *
 * La evidencia (capturas + JSON saneado, sin tokens ni DSN) queda en
 * `audit/ga-cutover-hatchery-v4/evidence/e2e_spec018/`.
 */
import { expect, test, type APIRequestContext } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { API, cabeceraAdmin, cabeceraAprobador, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'
import {
  asegurarFases, construirCsv, corteHaceDias, corteParaInput, crearMaestrosCutover, filasPorBu,
  habilitarCutoverEnRoles, habilitarUnidad, haceDias, leerPlantilla, rellenarPlantilla,
  type MaestrosCutover,
} from '../test-support/cutover'

test.describe.configure({ mode: 'serial' })

const EV = 'audit/ga-cutover-hatchery-v4/evidence/e2e_spec018'
const PNG = `${EV}/screenshots`
const MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const MIME_CSV = 'text/csv'

/** Los 4 campos nuevos del contrato V4 (SPEC 018 §1.4/D-5). */
const NUEVOS = [
  'eggs_non_incubable_oversized', 'eggs_non_incubable_dirty', 'eggs_non_incubable_broken', 'fertile_eggs_to_pit',
]

/** Cabecera exacta de `Datos` en V4 (D-7): 23 columnas, en este orden y sin `eggs_discarded`. */
const COLUMNAS_V4 = [
  'legacy_lot_code', 'existing_lot_code', 'hatchery_code', 'incubator_name', 'hatcher_name', 'source_lot_code',
  'generation', 'egg_origin', 'reception_date', 'set_date', 'expected_hatch_date', 'eggs_received', 'eggs_set',
  'eggs_non_incubable_oversized', 'eggs_non_incubable_dirty', 'eggs_non_incubable_broken', 'eggs_transferred',
  'fertile_eggs_to_pit', 'chicks_hatched', 'chicks_available', 'source_system', 'source_reference', 'notes',
]
const ev: Record<string, any> = {}
let cab: { Authorization: string }
let cabAprobador: { Authorization: string }
let maestros: MaestrosCutover
let s: string

/** Manipulación de la plantilla descargada con openpyxl (la librería que usa `test-support`). */
const PY = resolve('backend/.venv/bin/python')
const AGREGAR_AJENA = `
import sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1])
hoja = wb["Datos"]
columna = hoja.max_column + 1
hoja.cell(row=1, column=columna, value=sys.argv[3])
for r in range(2, hoja.max_row + 1):
    hoja.cell(row=r, column=columna, value=sys.argv[4])
wb.save(sys.argv[2])
`
const DEGRADAR_A_V3 = `
import json, sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1])
for fila in wb["Meta"].iter_rows(min_row=2):
    if str(fila[0].value) == "template_version": fila[1].value = "v3"
    elif str(fila[0].value) == "schema_id": fila[1].value = "CUTOVER_HATCHERY_V3"
hoja = wb["Datos"]
cabecera = [c.value for c in hoja[1]]
for i in sorted([cabecera.index(n) + 1 for n in json.loads(sys.argv[3]) if n in cabecera], reverse=True):
    hoja.delete_cols(i)
hoja.cell(row=1, column=hoja.max_column + 1, value="eggs_discarded")
wb.save(sys.argv[2])
`

function conColumnaAjena(plantilla: Buffer, columna: string, valor: unknown): Buffer {
  const dir = mkdtempSync(join(tmpdir(), 'ga-v4-'))
  writeFileSync(join(dir, 'v4.xlsx'), plantilla)
  execFileSync(PY, ['-c', AGREGAR_AJENA, join(dir, 'v4.xlsx'), join(dir, 'ajena.xlsx'), columna, String(valor)])
  return readFileSync(join(dir, 'ajena.xlsx'))
}

function degradarAHistoricosV3(plantilla: Buffer): Buffer {
  const dir = mkdtempSync(join(tmpdir(), 'ga-v4-'))
  writeFileSync(join(dir, 'v4.xlsx'), plantilla)
  execFileSync(PY, ['-c', DEGRADAR_A_V3, join(dir, 'v4.xlsx'), join(dir, 'v3.xlsx'), JSON.stringify(NUEVOS)])
  return readFileSync(join(dir, 'v3.xlsx'))
}
/** Fila V4 canónica de la BU: recibidos 10 000 y cargados 9 000; cada escenario añade su desglose. */
const filaV4 = (ref: string, extra: Record<string, unknown> = {}): Record<string, unknown> => ({
  ...filasPorBu('hatchery', maestros, ref)[0], ...extra,
})

/** Batch nuevo por API. Cada test usa un corte propio: la misma carga y corte es DUPLICATE_UPLOAD. */
async function crearBatch(request: APIRequestContext, corteDias: number): Promise<any> {
  const r = await request.post(`${API}/cutover-batches`, { headers: cab, data: {
    business_unit: 'hatchery', cutover_datetime: corteHaceDias(corteDias),
  } })
  const texto = await r.text()
  expect(r.status(), texto).toBe(201)
  return JSON.parse(texto)
}

async function plantillaDe(request: APIRequestContext, batchId: number, formato: 'xlsx' | 'csv') {
  const r = await request.get(`${API}/cutover-templates/hatchery?format=${formato}&batch_id=${batchId}`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  return r
}

async function subir(
  request: APIRequestContext, batchId: number, archivo: { name: string; mimeType: string; buffer: Buffer },
) {
  return request.post(`${API}/cutover-batches/${batchId}/upload`, { headers: cab, multipart: { file: archivo } })
}

const reconciliacion = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/reconciliation`, { headers: cab })).json()

const loteRec = (rec: any, ref: string) => rec.lots.find((l: any) => l.legacy_lot_code === ref)
/** Submit (admin) → approve (aprobador: otro actor) → apply (admin), como los demás specs de proceso. */
async function cicloDeAprobacion(request: APIRequestContext, batchId: number) {
  const envio = await request.post(`${API}/cutover-batches/${batchId}/submit`, { headers: cab })
  expect(envio.status(), await envio.text()).toBe(200)
  const enviado = await envio.json()
  expect(enviado.status).toBe('pending_approval')
  const aprobacion = await request.post(`${API}/cutover-batches/${batchId}/approve`, { headers: cabAprobador })
  expect(aprobacion.status(), await aprobacion.text()).toBe(200)
  const aprobado = await aprobacion.json()
  expect(aprobado.status).toBe('approved')
  expect(aprobado.approved_by_id, 'segregación: el aprobador no es quien envió').not.toBe(enviado.submitted_by_id)
  const aplicacion = await request.post(`${API}/cutover-batches/${batchId}/apply`, { headers: cab })
  expect(aplicacion.status(), await aplicacion.text()).toBe(200)
  const aplicado = await aplicacion.json()
  expect(aplicado.status).toBe('applied')
  expect(aplicado.template_version).toBe('v4')
  return aplicado
}

/** `lot_id` de la fila migrada, por la API de items del batch. */
async function loteDe(request: APIRequestContext, batchId: number, ref: string): Promise<number> {
  const items = await (await request.get(`${API}/cutover-batches/${batchId}/items`, { headers: cab })).json()
  const fila = items.items.find((i: any) => i.legacy_lot_reference === ref)
  expect(fila, `la fila ${ref} debe haberse migrado`).toBeTruthy()
  expect(fila.validation_status, JSON.stringify(fila)).toBe('applied')
  return fila.lot_id as number
}

test.beforeAll(async ({ request }) => {
  mkdirSync(PNG, { recursive: true })
  cab = await cabeceraAdmin(request)
  await habilitarCutoverEnRoles(request, cab)
  await habilitarUnidad(request, cab, 'hatchery')
  await asegurarFases(request, cab)
  maestros = await crearMaestrosCutover(request, cab, 'hatchery')
  cabAprobador = await cabeceraAprobador(request)
  s = sufijo().toUpperCase()
  ev.inicio = new Date().toISOString()
  ev.maestros = maestros
})

test.afterAll(() => {
  ev.fin = new Date().toISOString()
  mkdirSync(PNG, { recursive: true })
  writeFileSync(`${EV}/e2e_spec018_hatchery_v4.json`, JSON.stringify(ev, null, 2))
})
test('E2E-V4-01 plantilla v4 del batch: Meta, Instrucciones de los 4 campos nuevos y Datos de 23 columnas sin eggs_discarded', async ({ request }) => {
  const batch = await crearBatch(request, 27)

  // ── XLSX: nombre de descarga, Meta y cabecera exacta ──
  const xlsx = await plantillaDe(request, batch.id, 'xlsx')
  const nombre = String(xlsx.headers()['content-disposition'] ?? '')
  expect(nombre, 'el archivo descargado declara la versión vigente').toContain('cutover_template_hatchery_v4.xlsx')
  const libro = leerPlantilla(await xlsx.body())
  expect(libro.meta.template_version).toBe('v4')
  expect(libro.meta.schema_id).toBe('CUTOVER_HATCHERY_V4')
  expect(libro.meta.business_unit).toBe('hatchery')
  expect(libro.cabecera, 'cabecera D-7 completa y en orden').toEqual(COLUMNAS_V4)
  expect(libro.cabecera.length).toBe(23)
  expect(libro.cabecera).not.toContain('eggs_discarded')

  // ── Instrucciones: una fila por campo nuevo (significado, tipo, unidad, UNKNOWN/N-A, destino) ──
  for (const campo of NUEVOS) {
    const fila = libro.instrucciones[campo]
    expect(fila, `Instrucciones debe documentar ${campo}`).toBeTruthy()
    expect(String(fila!.significado ?? '').length, `significado de ${campo}`).toBeGreaterThan(40)
    expect(fila!.obligatorio).toBe('no')
    expect(fila!.tipo).toBe('int')
    expect(fila!.unidad).toBe('huevos')
    expect(fila!.formato).toBe('entero ≥ 0')
    expect(fila!['admite_UNKNOWN_(vacío)'], `UNKNOWN de ${campo}`).toMatch(/^s/i)
    expect(fila!['admite_N/A'], `N/A de ${campo}`).toMatch(/^no$/i)
    expect(fila!.destino_tras_apply).toBe(`hatchery_openings.${campo}`)
  }

  // ── CSV: la misma cabecera de 23 columnas (D-9) ──
  const csv = await plantillaDe(request, batch.id, 'csv')
  expect(String(csv.headers()['content-disposition'] ?? '')).toContain('cutover_template_hatchery_v4.csv')
  const primeraLinea = (await csv.body()).toString('utf8').replace(/^\uFEFF/, '').split('\n')[0].trim()
  expect(primeraLinea.split(';')).toEqual(COLUMNAS_V4)

  ev['01'] = {
    batch: batch.id, archivo: nombre, meta: libro.meta, columnas: libro.cabecera.length,
    instruidos: NUEVOS.map(c => libro.instrucciones[c]?.campo ?? null), cabecera_csv: primeraLinea,
  }
})
test('E2E-V4-02 XLSX v4 de punta a punta por la interfaz: 500/300/200 + fosa 25, total derivado 1 000 y saldo 0 sin doble conteo', async ({ page, browser, request }) => {
  test.setTimeout(360_000)

  // ── 1 · batch de incubadora con corte, por la interfaz ──
  await entrar(page, 'admin')
  await page.goto('/cutover')
  await expect(page.getByLabel(/Unidad de negocio|Business unit/)).toBeVisible()
  await page.getByLabel(/Unidad de negocio|Business unit/).selectOption('hatchery')
  await page.getByLabel(/Fecha y hora de corte|Cutover date/).fill(corteParaInput(24))
  const creacion = page.waitForResponse(r => r.url().includes('/cutover-batches') && r.request().method() === 'POST')
  await page.getByRole('button', { name: /Crear carga|Create load/ }).click()
  const batch = await (await creacion).json()
  expect(batch.business_unit).toBe('hatchery')
  const cabeceraUI = page.getByTestId('cutover-batch-header')
  await expect(cabeceraUI).toContainText(`#${batch.id}`)

  // ── 2 · la plantilla de ESA carga es la v4 (nombre de descarga del servidor + Meta) ──
  const [descarga] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: /Descargar plantilla Excel|Download Excel template/ }).click(),
  ])
  expect(descarga.suggestedFilename(), 'el nombre de descarga declara v4').toContain('cutover_template_hatchery_v4')
  const plantilla = readFileSync((await descarga.path()) as string)
  const libro = leerPlantilla(plantilla)
  expect(libro.meta.template_version).toBe('v4')
  expect(libro.cabecera).toEqual(COLUMNAS_V4)

  // ── 3 · rellenar (10 000 recibidos / 8 975 cargados, 500+300+200 no incubables, fosa 25 = 10 000) y subir ──
  const ref = `E2E-V4-${s}-XLSX`
  const filas = [filaV4(ref, {
    eggs_set: 8975,
    eggs_non_incubable_oversized: 500, eggs_non_incubable_dirty: 300, eggs_non_incubable_broken: 200,
    fertile_eggs_to_pit: 25,
  })]
  const subida = page.waitForResponse(r => r.url().includes('/upload'))
  await page.getByTestId('cutover-file-input').setInputFiles({
    name: 'cutover_template_hatchery_v4.xlsx', mimeType: MIME_XLSX, buffer: rellenarPlantilla(plantilla, filas),
  })
  const respSubida = await subida
  const cuerpoSubida = await respSubida.json()
  expect(respSubida.status(), JSON.stringify(cuerpoSubida)).toBe(200)
  expect(cuerpoSubida.status).toBe('validated')
  expect(cuerpoSubida.invalid_rows).toBe(0)
  expect(cuerpoSubida.source_type).toBe('XLSX')
  expect(cuerpoSubida.template_version).toBe('v4')
  await expect(page.getByTestId('cutover-errors')).toHaveCount(0)
  // ── 4 · preview: desglose + total derivado 1 000 y NINGUNA columna de descartados V3 ──
  const previewUI = page.getByTestId('cutover-preview')
  await expect(previewUI).toBeVisible()
  await expect(previewUI).toContainText(ref)
  await expect(page.getByTestId(/^cutover-preview-total-/)).toContainText(/1[.,]000/)
  await expect(previewUI).not.toContainText(/descartad/i)
  const prev = await (await request.get(`${API}/cutover-batches/${batch.id}/preview`, { headers: cab })).json()
  expect(prev.template_version).toBe('v4')
  expect(prev.schema_id).toBe('CUTOVER_HATCHERY_V4')
  expect(prev.columns).toEqual(COLUMNAS_V4)
  const filaPrev = prev.rows.find((f: any) => f.legacy_lot_code === ref)
  expect(filaPrev.derived.eggs_non_incubable_total, 'D-3: total derivado de los tres KNOWN').toBe(1000)
  // SPEC 018 §9 · D-23: 8 975 − 0 = 8 975 (la fosa es pre-carga: ya salió de lo recibido, no de lo cargado).
  expect(filaPrev.derived.eggs_in_process, 'D-23: set − transferred').toBe(8975)
  expect(filaPrev.derived.eggs_available_to_set, 'D-24: 10 000 − 8 975 − 1 000 − 25').toBe(0)
  expect(filaPrev.values.eggs_non_incubable_oversized).toEqual({ value: 500, status: 'KNOWN' })
  expect(filaPrev.values.eggs_non_incubable_dirty).toEqual({ value: 300, status: 'KNOWN' })
  expect(filaPrev.values.eggs_non_incubable_broken).toEqual({ value: 200, status: 'KNOWN' })
  expect(filaPrev.values.fertile_eggs_to_pit).toEqual({ value: 25, status: 'KNOWN' })
  await page.screenshot({ path: `${PNG}/p02_preview.png`, fullPage: true })

  // ── 5 · enviar, aprobar con OTRO actor y aplicar, por la interfaz ──
  const envio = page.waitForResponse(r => r.url().includes('/submit'))
  await page.getByRole('button', { name: /Enviar a aprobación|Submit for approval/ }).click()
  expect((await envio).status()).toBe(200)
  await expect(cabeceraUI).toContainText(/Pendiente de aprobación|Pending approval/)
  const ctxAprobador = await browser.newContext()
  const paginaAprobador = await ctxAprobador.newPage()
  await entrar(paginaAprobador, 'approver')
  await paginaAprobador.goto(`/cutover?batch=${batch.id}`)
  const aprobacion = paginaAprobador.waitForResponse(r => r.url().includes('/approve'))
  await paginaAprobador.getByRole('button', { name: /^Aprobar$|^Approve$/ }).click()
  expect((await aprobacion).status()).toBe(200)
  await expect(paginaAprobador.getByTestId('cutover-batch-header')).toContainText(/Aprobado|Approved/)
  await ctxAprobador.close()
  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(cabeceraUI).toContainText(/Aprobado|Approved/)
  const aplicacion = page.waitForResponse(r => r.url().includes('/apply'))
  await page.getByRole('button', { name: /^Aplicar$|^Apply$/ }).click()
  const respApply = await aplicacion
  expect(respApply.status(), await respApply.text()).toBe(200)
  await expect(cabeceraUI).toContainText(/Aplicado|Applied/)
  // ── 6 · reconciliación por la interfaz: desglose, total derivado, fosa y sin descartados ──
  const lotId = await loteDe(request, batch.id, ref)
  await expect(page.getByTestId('cutover-reconciliation')).toBeVisible()
  await expect(page.getByTestId('cutover-applied')).toBeVisible()
  const filaUI = page.getByTestId('cutover-reconciliation').locator('tbody tr').filter({ hasText: ref })
  await expect(filaUI).toHaveCount(1)
  await expect(page.getByTestId('cutover-th-non-incubable-total')).toBeVisible()
  await expect(page.getByTestId('cutover-th-eggs-discarded'), 'V4 no pinta la columna de descartados V3').toHaveCount(0)
  await expect(page.getByTestId(`cutover-eggs-discarded-${lotId}`)).toHaveCount(0)
  const totalUI = page.getByTestId(`cutover-non-incubable-total-${lotId}`)
  await expect(totalUI.locator('span').first()).toHaveText(/1[.,]000/)
  // La marca «derivado» vive en la CABECERA de la columna (nunca editable), no en la celda.
  await expect(page.getByTestId('cutover-th-non-incubable-total')).toContainText(/derivado/i)
  await expect(totalUI.getByTestId('cutover-non-incubable-eggs_non_incubable_oversized')).toContainText('500')
  await expect(totalUI.getByTestId('cutover-non-incubable-eggs_non_incubable_dirty')).toContainText('300')
  await expect(totalUI.getByTestId('cutover-non-incubable-eggs_non_incubable_broken')).toContainText('200')
  await expect(page.getByTestId(`cutover-fertile-pit-${lotId}`)).toHaveText('25')
  // «En proceso» y «disponible»: 8 975 (8 975 − 0) y 0 (una sola resta: nunca −1 000 ni −25).
  await expect(page.getByTestId(`cutover-eggs-in-process-${lotId}`), 'D-23: set − transferred ⇒ 8 975').toContainText(/8[.,]975/)
  await expect(page.getByTestId(`cutover-eggs-available-${lotId}`), 'D-24: una sola resta ⇒ 0').toHaveText('0')
  await page.screenshot({ path: `${PNG}/p02_reconciliacion.png`, fullPage: true })
  // ── 7 · la misma verdad por API (opening.hatchery + current) ──
  const rec = await reconciliacion(request, batch.id)
  expect(rec.source.template_version).toBe('v4')
  const lote = loteRec(rec, ref)
  const h = lote.opening.hatchery
  expect(h.eggs_received).toBe(10000)
  expect(h.eggs_set).toBe(8975)
  expect(h.eggs_non_incubable_oversized).toBe(500)
  expect(h.eggs_non_incubable_dirty).toBe(300)
  expect(h.eggs_non_incubable_broken).toBe(200)
  expect(h.eggs_non_incubable_oversized_status).toBe('KNOWN')
  expect(h.eggs_non_incubable_total).toBe(1000)
  expect(h.eggs_non_incubable_total_status).toBe('KNOWN')
  expect(h.fertile_eggs_to_pit).toBe(25)
  expect(h.fertile_eggs_to_pit_status).toBe('KNOWN')
  // D-2: fuera del contrato V4 ⇒ NULL + NOT_APPLICABLE persistidos (el histórico V3 no se toca).
  expect(h.eggs_discarded).toBeNull()
  expect(h.eggs_discarded_status).toBe('NOT_APPLICABLE')
  // SPEC 018 §9 · D-23: `set − transferred` = 8 975 − 0 = 8 975 (la fosa no vuelve a restar).
  expect(h.eggs_in_process).toBe(8975)
  expect(lote.current.eggs_in_process, 'sin eventos post-corte el en proceso es el de la apertura').toBe(8975)
  // D-4 / AC-V4-10: 10 000 − 9 000 − 1 000 = 0 y jamás −1 000 (una sola resta).
  expect(lote.current.eggs_available_hatchery).toBe(0)
  expect(lote.current.eggs_available_hatchery).not.toBe(-1000)
  // ── 8 · refresco y re-login: la reconciliación es persistente, no memoria de pantalla ──
  await page.reload()
  await expect(page.getByTestId('cutover-reconciliation')).toContainText(ref)
  await expect(page.getByTestId(`cutover-non-incubable-total-${lotId}`)).toContainText(/1[.,]000/)
  const ctxNuevo = await browser.newContext()
  const paginaNueva = await ctxNuevo.newPage()
  await entrar(paginaNueva, 'admin')
  await paginaNueva.goto(`/cutover?batch=${batch.id}`)
  await expect(paginaNueva.getByTestId('cutover-batch-header')).toContainText(/Aplicado|Applied/)
  await expect(paginaNueva.getByTestId('cutover-reconciliation')).toContainText(ref)
  await expect(paginaNueva.getByTestId(`cutover-non-incubable-total-${lotId}`)).toContainText(/1[.,]000/)
  await expect(paginaNueva.getByTestId('cutover-th-eggs-discarded')).toHaveCount(0)
  await paginaNueva.screenshot({ path: `${PNG}/p02_relogin.png`, fullPage: true })
  await ctxNuevo.close()
  const cabNueva = await cabeceraAdmin(request)
  const recNueva = await (await request.get(`${API}/cutover-batches/${batch.id}/reconciliation`, { headers: cabNueva })).json()
  const loteNuevo = loteRec(recNueva, ref)
  expect(loteNuevo.opening.hatchery.eggs_non_incubable_total).toBe(1000)
  expect(loteNuevo.current.eggs_available_hatchery).toBe(0)
  expect(loteNuevo.current.eggs_in_process).toBe(8975)

  ev['02'] = {
    batch: batch.id, lote: lotId, ref, archivo: 'cutover_template_hatchery_v4.xlsx',
    preview: { total: filaPrev.derived.eggs_non_incubable_total, en_proceso: filaPrev.derived.eggs_in_process },
    opening_hatchery: h, current: lote.current,
    persistencia: { recarga: true, relogin_disponible: loteNuevo.current.eggs_available_hatchery },
  }
})
test('E2E-V4-03 CSV v4 con un componente UNKNOWN: total UNKNOWN (null en API) y los ceros conocidos como 0', async ({ page, request }) => {
  test.setTimeout(300_000)
  const batch = await crearBatch(request, 31)
  const csv = await plantillaDe(request, batch.id, 'csv')
  expect(String(csv.headers()['content-disposition'] ?? '')).toContain('cutover_template_hatchery_v4.csv')
  const cabeceraCsv = (await csv.body()).toString('utf8').replace(/^\uFEFF/, '').split('\n')[0].trim()
  expect(cabeceraCsv.split(';')).toEqual(COLUMNAS_V4)

  // Una fila con el roto sin declarar (UNKNOWN) y otra con ceros conocidos: la suma parcial no se inventa.
  const refUnk = `E2E-V4-${s}-CSV-UNK`
  const refCero = `E2E-V4-${s}-CSV-CERO`
  const filas = [
    filaV4(refUnk, {
      eggs_non_incubable_oversized: 100, eggs_non_incubable_dirty: 80, eggs_non_incubable_broken: '', fertile_eggs_to_pit: 0,
    }),
    filaV4(refCero, {
      eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0, fertile_eggs_to_pit: 0,
    }),
  ]
  const subida = await subir(request, batch.id, {
    name: 'cutover_template_hatchery_v4.csv', mimeType: MIME_CSV, buffer: construirCsv(cabeceraCsv, filas),
  })
  const textoSubida = await subida.text()
  expect(subida.status(), textoSubida).toBe(200)
  const cuerpo = JSON.parse(textoSubida)
  expect(cuerpo.status).toBe('validated')
  expect(cuerpo.invalid_rows).toBe(0)
  expect(cuerpo.source_type).toBe('CSV')
  expect(cuerpo.template_version).toBe('v4')

  await cicloDeAprobacion(request, batch.id)
  const lotUnk = await loteDe(request, batch.id, refUnk)
  const lotCero = await loteDe(request, batch.id, refCero)
  // ── UI: UNKNOWN se pinta UNKNOWN y el cero conocido como 0 ──
  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(page.getByTestId('cutover-reconciliation')).toBeVisible()
  const celdaUnk = page.getByTestId(`cutover-non-incubable-total-${lotUnk}`)
  await expect(celdaUnk.locator('span').first()).toHaveText('UNKNOWN')
  await expect(celdaUnk.getByTestId('cutover-non-incubable-eggs_non_incubable_broken')).toContainText('UNKNOWN')
  await expect(celdaUnk.getByTestId('cutover-non-incubable-eggs_non_incubable_oversized')).toContainText('100')
  await expect(celdaUnk.getByTestId('cutover-non-incubable-eggs_non_incubable_dirty')).toContainText('80')
  const celdaCero = page.getByTestId(`cutover-non-incubable-total-${lotCero}`)
  await expect(celdaCero.locator('span').first()).toHaveText('0')
  await expect(celdaCero.getByTestId('cutover-non-incubable-eggs_non_incubable_broken')).toContainText('0')
  await expect(page.getByTestId('cutover-th-eggs-discarded')).toHaveCount(0)
  await page.screenshot({ path: `${PNG}/p03_csv_reconciliacion.png`, fullPage: true })

  // ── API: UNKNOWN no se degrada a 0 y el cero conocido sí es 0 ──
  const rec = await reconciliacion(request, batch.id)
  expect(rec.source.template_version).toBe('v4')
  expect(rec.source.type).toBe('CSV')
  const unk = loteRec(rec, refUnk).opening.hatchery
  expect(unk.eggs_non_incubable_oversized).toBe(100)
  expect(unk.eggs_non_incubable_dirty).toBe(80)
  expect(unk.eggs_non_incubable_broken).toBeNull()
  expect(unk.eggs_non_incubable_broken_status).toBe('UNKNOWN')
  expect(unk.eggs_non_incubable_total, 'D-3: nunca una suma parcial').toBeNull()
  expect(unk.eggs_non_incubable_total_status).toBe('UNKNOWN')
  expect(loteRec(rec, refUnk).current.eggs_available_hatchery, 'saldo no determinable').toBeNull()
  const cero = loteRec(rec, refCero).opening.hatchery
  expect(cero.eggs_non_incubable_oversized).toBe(0)
  expect(cero.eggs_non_incubable_dirty).toBe(0)
  expect(cero.eggs_non_incubable_broken).toBe(0)
  expect(cero.eggs_non_incubable_broken_status).toBe('KNOWN')
  expect(cero.eggs_non_incubable_total).toBe(0)
  expect(cero.eggs_non_incubable_total_status).toBe('KNOWN')
  // `egg_origin` (SPEC 009) no forma parte de la proyección de reconciliación de la apertura: se
  // comprueba en la fila normalizada del batch, que sí expone todas las columnas del contrato v4.
  const prevCero = (await (await request.get(`${API}/cutover-batches/${batch.id}/preview`, { headers: cab })).json())
    .rows.find((f: any) => f.legacy_lot_code === refCero)
  expect(prevCero.values.egg_origin).toEqual({ value: 'internal', status: 'KNOWN' })
  // Fosa en cero conocido ⇒ el derivado sí existe y el saldo es 10 000 − 9 000 − 0.
  expect(cero.eggs_in_process).toBe(9000)
  expect(loteRec(rec, refCero).current.eggs_available_hatchery).toBe(1000)

  ev['03'] = {
    batch: batch.id, unk: { lote: lotUnk, opening: unk }, cero: { lote: lotCero, opening: cero },
    columnas_csv: cabeceraCsv.split(';').length,
  }
})
test('E2E-V4-04 negativos, decimales, texto, N/A y fosa > recibidos: filas inválidas con su mensaje y batch no aprobable', async ({ page, request }) => {
  const batch = await crearBatch(request, 34)
  const plantilla = await (await plantillaDe(request, batch.id, 'xlsx')).body()

  // D-6/AC-V4-05 y AC-V4-08: un caso por fila, con el único defecto en el campo indicado.
  const casos = [
    { clave: 'NEG', campo: 'eggs_non_incubable_dirty', valor: -5, codigo: 'NEGATIVE_VALUE' },
    { clave: 'DEC', campo: 'eggs_non_incubable_dirty', valor: 1.5, codigo: 'INVALID_INTEGER' },
    { clave: 'TXT', campo: 'eggs_non_incubable_dirty', valor: 'abc', codigo: 'INVALID_INTEGER' },
    { clave: 'NA', campo: 'eggs_non_incubable_dirty', valor: 'N/A', codigo: 'NOT_APPLICABLE_NOT_ALLOWED' },
    { clave: 'FOSA', campo: 'fertile_eggs_to_pit', valor: 20000, codigo: 'CONSISTENCY_MISMATCH' },
  ]
  const filas = casos.map(caso => filaV4(`E2E-V4-${s}-${caso.clave}`, {
    eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0, fertile_eggs_to_pit: 0,
    [caso.campo]: caso.valor,
  }))
  const subida = await subir(request, batch.id, {
    name: 'cutover_template_hatchery_v4_negativos.xlsx', mimeType: MIME_XLSX, buffer: rellenarPlantilla(plantilla, filas),
  })
  const texto = await subida.text()
  expect(subida.status(), texto).toBe(200)
  const cuerpo = JSON.parse(texto)
  expect(cuerpo.valid_rows).toBe(0)
  expect(cuerpo.invalid_rows).toBe(casos.length)
  expect(cuerpo.status, 'un batch con filas inválidas no queda validado').toBe('validating')
  // ── API: un error por fila en el campo correcto, con mensaje (no un código suelto) ──
  const validacion = await (await request.get(`${API}/cutover-batches/${batch.id}/validation`, { headers: cab })).json()
  expect(validacion.invalid_rows).toBe(casos.length)
  const encontrados: any[] = []
  for (const [i, caso] of casos.entries()) {
    const fila = i + 2 // la fila 1 de `Datos` es la cabecera
    const error = validacion.errors.find((e: any) => e.row_number === fila && e.field === caso.campo)
    expect(error, `fila ${fila} · ${caso.campo}: ${JSON.stringify(validacion.errors)}`).toBeTruthy()
    expect(error.error_code).toBe(caso.codigo)
    expect(String(error.message ?? '').length).toBeGreaterThan(8)
    encontrados.push({ fila, campo: error.field, codigo: error.error_code, mensaje: error.message, recibido: error.received_value })
  }

  // ── No se puede aprobar ni aplicar mientras haya filas inválidas ──
  const submit = await request.post(`${API}/cutover-batches/${batch.id}/submit`, { headers: cab })
  expect(submit.status(), await submit.text()).toBe(409)
  const approve = await request.post(`${API}/cutover-batches/${batch.id}/approve`, { headers: cabAprobador })
  expect(approve.status(), await approve.text()).toBe(409)
  const apply = await request.post(`${API}/cutover-batches/${batch.id}/apply`, { headers: cab })
  expect(apply.status(), await apply.text()).toBe(409)

  // ── UI: los mensajes por fila se ven y no hay CTA de envío ──
  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batch.id}`)
  const erroresUI = page.getByTestId('cutover-errors')
  await expect(erroresUI).toBeVisible()
  for (const caso of casos) await expect(erroresUI).toContainText(caso.codigo)
  await expect(erroresUI).toContainText('El valor no puede ser negativo.')
  await expect(erroresUI).toContainText('huevos fértiles a fosa')
  await expect(page.getByRole('button', { name: /Enviar a aprobación|Submit for approval/ })).toHaveCount(0)
  // AC81 se cumple con el botón **bloqueado** (existe, deshabilitado), no con su ausencia.
  const aplicarUI = page.getByRole('button', { name: /^Aplicar$|^Apply$/ })
  await expect(aplicarUI).toHaveCount(1)
  await expect(aplicarUI).toBeDisabled()
  await page.screenshot({ path: `${PNG}/p04_negativos.png`, fullPage: true })

  ev['04'] = {
    batch: batch.id, invalidas: cuerpo.invalid_rows, errores: encontrados,
    bloqueo: { submit: submit.status(), approve: approve.status(), apply: apply.status() },
  }
})
test('E2E-V4-05 cabecera ajena e histórica: eggs_discarded se rechaza y la plantilla v3 pide la v4', async ({ request }) => {
  // ── (a) cabecera V4 + columna ajena `eggs_discarded` ⇒ rechazo (AC-V4-03) ──
  const batchA = await crearBatch(request, 37)
  const plantilla = await (await plantillaDe(request, batchA.id, 'xlsx')).body()
  const conAjena = conColumnaAjena(plantilla, 'eggs_discarded', 100)
  const r1 = await subir(request, batchA.id, {
    name: 'cutover_template_hatchery_v4_columna_ajena.xlsx', mimeType: MIME_XLSX, buffer: conAjena,
  })
  const t1 = await r1.text()
  expect(r1.status(), t1).toBe(422)
  expect(t1).toContain('HEADER_UNKNOWN')
  expect(t1).toContain('eggs_discarded')
  const estadoA = await (await request.get(`${API}/cutover-batches/${batchA.id}`, { headers: cab })).json()
  expect(estadoA.status).toBe('draft')
  expect(estadoA.total_rows).toBe(0)

  // ── (b) archivo v3 (Meta v3 / CUTOVER_HATCHERY_V3) ⇒ rechazo con «descargue la v4» (AC-V4-04) ──
  const batchB = await crearBatch(request, 38)
  const v3 = degradarAHistoricosV3(plantilla)
  const libroV3 = leerPlantilla(v3)
  expect(libroV3.meta.template_version, 'el archivo degradado es un v3 real').toBe('v3')
  expect(libroV3.meta.schema_id).toBe('CUTOVER_HATCHERY_V3')
  expect(libroV3.cabecera).toContain('eggs_discarded')
  const r2 = await subir(request, batchB.id, {
    name: 'cutover_template_hatchery_v3.xlsx', mimeType: MIME_XLSX, buffer: v3,
  })
  const t2 = await r2.text()
  expect(r2.status(), t2).toBe(422)
  expect(t2).toContain('TEMPLATE_VERSION_UNSUPPORTED')
  expect(t2).toMatch(/v4/)
  expect(t2).toContain('descargue la plantilla v4')
  const estadoB = await (await request.get(`${API}/cutover-batches/${batchB.id}`, { headers: cab })).json()
  expect(estadoB.status).toBe('draft')
  expect(estadoB.total_rows).toBe(0)
  // El rechazo no deja nada aprobable.
  const submitB = await request.post(`${API}/cutover-batches/${batchB.id}/submit`, { headers: cab })
  expect(submitB.status()).toBe(409)

  ev['05'] = {
    columna_ajena: { batch: batchA.id, status: r1.status(), mensaje: t1.slice(0, 300) },
    historica_v3: { batch: batchB.id, status: r2.status(), mensaje: t2.slice(0, 300) },
    cabecera_v3: libroV3.cabecera,
  }
})
test('E2E-V4-06 BR-03 post-corte: con 300 no incubables el saldo es 700 (no 1 000): 701 se rechaza y 700 se acepta', async ({ request }) => {
  const batch = await crearBatch(request, 41)
  const plantilla = await (await plantillaDe(request, batch.id, 'xlsx')).body()
  const ref = `E2E-V4-${s}-BR03`
  const subida = await subir(request, batch.id, {
    name: 'cutover_template_hatchery_v4_br03.xlsx', mimeType: MIME_XLSX,
    buffer: rellenarPlantilla(plantilla, [filaV4(ref, {
      eggs_non_incubable_oversized: 300, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0, fertile_eggs_to_pit: 0,
    })]),
  })
  expect(subida.status(), await subida.text()).toBe(200)
  await cicloDeAprobacion(request, batch.id)
  const lotId = await loteDe(request, batch.id, ref)

  const cargar = (cantidad: number) => request.post(`${API}/operations`, { headers: cab, data: {
    lot_id: lotId, event_type: 'incubation_load', event_date: haceDias(7),
    hatchery_params: [{ quantity_loaded: cantidad }],
  } })

  // 701 sobre 700 disponibles: rechazado por BR-03, y el mensaje declara el saldo YA descontado.
  const excede = await cargar(701)
  const textoExcede = await excede.text()
  expect(excede.status(), textoExcede).toBe(400)
  const cuerpoExcede = JSON.parse(textoExcede)
  expect(cuerpoExcede.rule).toBe('BR-03')
  expect(JSON.stringify(cuerpoExcede)).toContain('700')

  // 700 = recibidos − cargados − no incubables conocidos: aceptado.
  const justo = await cargar(700)
  expect(justo.status(), await justo.text()).toBe(201)

  // Saldo agotado: un huevo más tampoco entra (el saldo llegó exactamente a 0, no a 300).
  const resto = await cargar(1)
  expect(resto.status(), await resto.text()).toBe(400)
  expect((await resto.json()).rule).toBe('BR-03')

  const rec = await reconciliacion(request, batch.id)
  const lote = loteRec(rec, ref)
  expect(lote.opening.hatchery.eggs_non_incubable_total).toBe(300)
  expect(lote.post.eggs_loaded).toBe(700)
  expect(lote.current.eggs_available_hatchery).toBe(0)
  // D-23: en proceso = set − transferred (9 000) y, tras el post-corte, más lo
  // cargado (700) menos lo transferido (0) ⇒ 9 700. Nunca 9 000 − 700 ni un descuento del no incubable.
  expect(lote.opening.hatchery.eggs_in_process).toBe(9000)
  expect(lote.current.eggs_in_process).toBe(9700)

  ev['06'] = {
    batch: batch.id, lote: lotId, ref,
    br03: { setecientos_uno: excede.status(), setecientos: justo.status(), uno_mas: resto.status(), mensaje: cuerpoExcede.detail ?? cuerpoExcede },
    current: lote.current, opening: lote.opening.hatchery,
  }
})
