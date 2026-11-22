/**
 * SPEC 019 · PROGENITORAS V3 — Cargas Iniciales v3 con transferencias históricas (E2E de proceso).
 *
 * Certifica el contrato real de Abuelas (ya v3 desde SPEC 014) con la forma del mandato §38/§39:
 * **una** carga con **tres** lotes y **una** plantilla descargada del propio batch.
 *
 *   lote A · CRIA, sin transferencias  → vivas = alojadas − mortalidad − descartes
 *   lote B · CRIA, origen de la conformación → alojadas + 0 − mort − descartes − salida = vivas
 *   lote C · PROD, destino              → 0 + entradas − 0 − 0 − 0 = vivas   (Σ salidas de B)
 *
 * - **E2E-GP-01** (AC-GP-10) ciclo completo por la interfaz: crear carga con corte, descargar la
 *   plantilla de ESA carga y leer `Meta` (v3 / CUTOVER_GRANDPARENT_V3 / grandparent), `Instrucciones`
 *   (las cuatro transferencias y los textos refinados: «efectivamente» en `birds_placed`, «NO es una
 *   transferencia» en transferencias y en la fase) y la cabecera de `Datos`; rellenar los tres lotes,
 *   subir, validar (0 errores y veredicto CONSISTENT por sexo para A, B y C), preview por UI con las
 *   etiquetas en español, enviar, aprobar con OTRO actor, aplicar, localizar los tres lotes,
 *   reconciliación por API (`opening.live_males|females`, `historical_transfers_in|out_males|females`),
 *   `B.out == C.in` por sexo **como aserción de la prueba** (D-5: no es regla de producto), sin doble
 *   conteo, fases CRIA/PROD intactas, y refresco + re-login.
 * - **E2E-GP-02** (AC-GP-07) post-corte sobre el lote B aplicado: una mortalidad posterior al corte no
 *   vuelve a restar lo histórico transferido; el lote destino C admite además un evento propio.
 * - **E2E-GP-03** (AC-GP-06/09) por CSV con la cabecera del batch: transferencias y mortalidad vacías
 *   ⇒ UNKNOWN válido, verdict NOT_FULLY_VERIFIABLE, `null` en la reconciliación (jamás 0) y UNKNOWN
 *   visible en el preview; y un archivo con negativa / decimal / saldo inconsistente ⇒ errores por fila
 *   con su código y el batch no se envía a aprobación.
 * - **E2E-GP-04** (AC-GP-08) una plantilla Meta v2 de grandparent se rechaza indicando v3, y la fila
 *   diagnóstica de sexaje (reclasificación M→H) marca CONSISTENCY_MISMATCH mientras la variante como
 *   descarte de machos valida (OD-GP-SEXAGE-01 RATIFICADA = HISTORICAL_CULL: el error de sexaje que
 *   saca el ave del lote es un descarte y la reclasificación no se representa: el sistema la detecta
 *   como inconsistencia en lugar de corregir el sexo).
 *
 * Cada test usa un corte propio (la misma carga y corte es DUPLICATE_UPLOAD) y ninguna fecha literal:
 * todas se derivan de `haceDias`. La evidencia saneada (cifras y códigos, sin tokens ni DSN) queda en
 * `audit/ga-cutover-grandparent-v3/evidence/e2e_spec019/`.
 */
import { expect, test, type APIRequestContext, type Page } from '@playwright/test'
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

const EV = 'audit/ga-cutover-grandparent-v3/evidence/e2e_spec019'
const PNG = `${EV}/screenshots`
const PY = resolve('backend/.venv/bin/python')
const MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const MIME_CSV = 'text/csv'

/** Las cuatro transferencias canónicas del contrato v3 (idénticas a Breeder V3). */
const TRANSFERENCIAS = ['historical_transfers_in_males', 'historical_transfers_in_females',
  'historical_transfers_out_males', 'historical_transfers_out_females']

/** Etiquetas i18n (es) del preview: nunca el nombre técnico de la columna. */
const ETIQUETAS = {
  historical_transfers_in_males: 'Transf. hist. entrada machos',
  historical_transfers_in_females: 'Transf. hist. entrada hembras',
  historical_transfers_out_males: 'Transf. hist. salida machos',
  historical_transfers_out_females: 'Transf. hist. salida hembras',
}

/** Degrada la plantilla descargada a la «v2» anterior: Meta retrocedida y sin las cuatro columnas. */
const DEGRADAR = `
import json, sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1])
for f in wb["Meta"].iter_rows(min_row=2):
    if str(f[0].value) == "template_version": f[1].value = "v2"
    elif str(f[0].value) == "schema_id": f[1].value = "CUTOVER_GRANDPARENT_V2"
hoja = wb["Datos"]
fuera = [i for i, c in enumerate(hoja[1], start=1) if c.value in json.loads(sys.argv[3])]
for i in sorted(fuera, reverse=True): hoja.delete_cols(i)
wb.save(sys.argv[2])
`

interface Balance {
  placed: [number, number]
  mort: [number, number]
  culls: [number, number]
  entradas: [number, number]
  salidas: [number, number]
  live: [number, number]
}

/** Los tres lotes del escenario, con las cifras del mandato §38/§39. */
const LOTE_A: Balance = { placed: [100, 1000], mort: [5, 30], culls: [0, 20], entradas: [0, 0], salidas: [0, 0], live: [95, 950] }
const LOTE_B: Balance = { placed: [100, 1000], mort: [4, 26], culls: [6, 24], entradas: [0, 0], salidas: [40, 600], live: [50, 350] }
const LOTE_C: Balance = { placed: [0, 0], mort: [0, 0], culls: [0, 0], entradas: [40, 600], salidas: [0, 0], live: [40, 600] }

const ev: Record<string, any> = {}
let cab: { Authorization: string }
let cabAprobador: { Authorization: string }
let maestros: MaestrosCutover
let fases: Record<string, number>
let s: string

function balanceFilas(b: Balance): Record<string, unknown> {
  return {
    birds_placed_males: b.placed[0], birds_placed_females: b.placed[1],
    historical_mortality_males: b.mort[0], historical_mortality_females: b.mort[1],
    historical_culls_males: b.culls[0], historical_culls_females: b.culls[1],
    historical_transfers_in_males: b.entradas[0], historical_transfers_in_females: b.entradas[1],
    historical_transfers_out_males: b.salidas[0], historical_transfers_out_females: b.salidas[1],
    live_males: b.live[0], live_females: b.live[1],
  }
}

const filaGp = (ref: string): Record<string, unknown> => ({ ...filasPorBu('grandparent', maestros, ref)[0] })

/** Fila de cría/levante: la fase CRIA no admite métricas de producción de huevo (van UNKNOWN). */
const cria = (ref: string, balance: Balance): Record<string, unknown> => ({
  ...filaGp(ref), productive_phase_code: 'CRIA',
  real_start_date: haceDias(200), phase_start_date: null,
  accumulated_egg_production: null, accumulated_eggs_to_hatchery: null,
  ...balanceFilas(balance),
})

/** Fila de producción: la fase PROD empieza después del inicio real del lote y antes del corte. */
const produccion = (ref: string, balance: Balance): Record<string, unknown> => ({
  ...filaGp(ref), productive_phase_code: 'PROD',
  real_start_date: haceDias(210), phase_start_date: haceDias(90),
  ...balanceFilas(balance),
})

/** La ecuación del contrato, por sexo: alojadas + entradas − mortalidad − descartes − salidas. */
const ecuacion = (b: Balance, sexo: 0 | 1): number =>
  b.placed[sexo] + b.entradas[sexo] - b.mort[sexo] - b.culls[sexo] - b.salidas[sexo]
/** Batch nuevo por API. Cada escenario estrena corte: la misma carga y corte es DUPLICATE_UPLOAD. */
async function crearBatch(request: APIRequestContext, corteDias: number): Promise<any> {
  const r = await request.post(`${API}/cutover-batches`, { headers: cab, data: {
    business_unit: 'grandparent', cutover_datetime: corteHaceDias(corteDias),
  } })
  const texto = await r.text()
  expect(r.status(), texto).toBe(201)
  return JSON.parse(texto)
}

async function subir(request: APIRequestContext, batchId: number, archivo: { name: string; mimeType: string; buffer: Buffer }) {
  const subida = await request.post(`${API}/cutover-batches/${batchId}/upload`, { headers: cab, multipart: { file: archivo } })
  const texto = await subida.text()
  expect(subida.status(), texto).toBe(200)
  const cuerpo = JSON.parse(texto)
  if (cuerpo.invalid_rows > 0) {
    // Un rojo del validador se explica solo: se adjunta el informe por fila/campo/código.
    const detalle = await request.get(`${API}/cutover-batches/${batchId}/validation`, { headers: cab })
    cuerpo.errores = JSON.parse(await detalle.text()).errors
  }
  return cuerpo
}

/** Sube filas XLSX sobre la **plantilla descargada del batch** (nunca se fabrica la cabecera). */
async function subirFilasXlsx(request: APIRequestContext, batchId: number, filas: Record<string, unknown>[], nombre: string) {
  const plantilla = await request.get(`${API}/cutover-templates/grandparent?format=xlsx&batch_id=${batchId}`, { headers: cab })
  expect(plantilla.status(), await plantilla.text()).toBe(200)
  return subir(request, batchId, {
    name: nombre, mimeType: MIME_XLSX, buffer: rellenarPlantilla(await plantilla.body(), filas),
  })
}

/** Sube filas CSV con la **misma cabecera** que sirve el servidor para esa BU. */
async function subirFilasCsv(request: APIRequestContext, batchId: number, filas: Record<string, unknown>[], nombre: string) {
  const cabeceraCsv = await request.get(`${API}/cutover-templates/grandparent?format=csv&batch_id=${batchId}`, { headers: cab })
  expect(cabeceraCsv.status(), await cabeceraCsv.text()).toBe(200)
  return subir(request, batchId, {
    name: nombre, mimeType: MIME_CSV, buffer: construirCsv(await cabeceraCsv.text(), filas),
  })
}

const previewDe = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/preview`, { headers: cab })).json()

const reconciliacionDe = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/reconciliation`, { headers: cab })).json()

const porRef = (prev: any): Record<string, any> =>
  Object.fromEntries(prev.rows.map((f: any) => [f.legacy_lot_code, f]))

const filaRec = (rec: any, ref: string) => rec.lots.find((l: any) => l.legacy_lot_code === ref)

/** Fila (número de Excel) de una referencia: la cabecera es la fila 1, la primera carga la 2. */
const porRow = (filas: Record<string, unknown>[], ref: string): number =>
  filas.findIndex(f => f.legacy_lot_code === ref) + 2

/** Lotes creados por el batch: `lot_id` por referencia de legado. */
async function lotesPorRef(request: APIRequestContext, batchId: number): Promise<Record<string, number>> {
  const items = await (await request.get(`${API}/cutover-batches/${batchId}/items`, { headers: cab })).json()
  const mapa: Record<string, number> = {}
  for (const item of items.items) {
    if (item.lot_id) mapa[item.legacy_lot_reference] = item.lot_id
  }
  return mapa
}

/** Lote con su opening balance y sus fases (la fase declarada en la carga, ya aplicada). */
async function loteConFases(request: APIRequestContext, lotId: number) {
  const r = await request.get(`${API}/lots/${lotId}`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  return r.json()
}

/** Ciclo de aprobación por API (el aprobador es OTRO actor: la segregación es del producto). */
async function aprobarYAplicar(request: APIRequestContext, batchId: number) {
  const envio = await request.post(`${API}/cutover-batches/${batchId}/submit`, { headers: cab })
  expect(envio.status(), await envio.text()).toBe(200)
  const aprobacion = await request.post(`${API}/cutover-batches/${batchId}/approve`, { headers: cabAprobador })
  expect(aprobacion.status(), await aprobacion.text()).toBe(200)
  const aplicacion = await request.post(`${API}/cutover-batches/${batchId}/apply`, { headers: cab })
  expect(aplicacion.status(), await aplicacion.text()).toBe(200)
  return aplicacion
}

/** Tabla del preview (≥ sm): cabeceras y celdas alineadas por índice. */
async function tablaPreview(page: Page) {
  const tabla = page.getByTestId('cutover-preview').locator('table').first()
  const cabeceras = (await tabla.locator('thead th').allInnerTexts()).map(x => x.trim())
  const filas: string[][] = []
  const total = await tabla.locator('tbody tr').count()
  for (let i = 0; i < total; i++) {
    filas.push((await tabla.locator('tbody tr').nth(i).locator('td').allInnerTexts()).map(x => x.trim()))
  }
  const columna = (nombre: string) => cabeceras.findIndex(c => c === nombre)
  return {
    cabeceras, filas, columna,
    celda: (indice: number, nombre: string) => filas[indice]?.[columna(nombre)] ?? '',
  }
}

test.beforeAll(async ({ request }) => {
  mkdirSync(PNG, { recursive: true })
  cab = await cabeceraAdmin(request)
  cabAprobador = await cabeceraAprobador(request)
  await habilitarCutoverEnRoles(request, cab)
  await habilitarUnidad(request, cab, 'grandparent')
  fases = await asegurarFases(request, cab)
  maestros = await crearMaestrosCutover(request, cab, 'grandparent')
  s = sufijo().toUpperCase()
  ev.inicio = new Date().toISOString()
  ev.spec = '019'
  ev.regla = 'vivas = alojadas + entradas − mortalidad − descartes − salidas (por sexo, solo si los seis son KNOWN)'
  ev.maestros = { farmCode: maestros.farmCode, houseName: maestros.houseName, lineCode: maestros.lineCode }
})
/** Plantilla degradada a la «v2» anterior (Meta y sin las cuatro columnas de transferencias). */
function degradarAGrandparentV2(contenido: Buffer): Buffer {
  const dir = mkdtempSync(join(tmpdir(), 'ga-gp19-'))
  writeFileSync(join(dir, 'v3.xlsx'), contenido)
  execFileSync(PY, ['-c', DEGRADAR, join(dir, 'v3.xlsx'), join(dir, 'v2.xlsx'), JSON.stringify(TRANSFERENCIAS)])
  return readFileSync(join(dir, 'v2.xlsx'))
}

test('E2E-GP-01 ciclo completo por UI: tres lotes, plantilla v3 del batch, preview, aprobación, apply y reconciliación por sexo', async ({ page, browser, request }) => {
  test.setTimeout(300_000)
  const refA = `E2E-GP-A-${s}`
  const refB = `E2E-GP-B-${s}`
  const refC = `E2E-GP-C-${s}`
  const CORTE = 55
  const j: Record<string, any> = {}

  // ── 1-2 · la pantalla: BU progenitoras, corte propio y carga nueva ──
  await entrar(page, 'admin')
  await page.goto('/cutover')
  await page.getByLabel(/Unidad de negocio|Business unit/).selectOption('grandparent')
  await page.getByLabel(/Fecha y hora de corte|Cutover date/).fill(corteParaInput(CORTE))
  const creado = page.waitForResponse(r => r.url().includes('/cutover-batches') && r.request().method() === 'POST')
  await page.getByRole('button', { name: /Crear carga|Create load/ }).click()
  const batch = await (await creado).json()
  expect(batch.business_unit).toBe('grandparent')
  const cabecera = page.getByTestId('cutover-batch-header')
  await expect(cabecera).toContainText(`#${batch.id}`)

  // ── 3 · la plantilla de ESA carga: Meta, Instrucciones y las cuatro columnas de Datos ──
  const [descarga] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: /Descargar plantilla Excel|Download Excel template/ }).click(),
  ])
  const plantilla = readFileSync(await descarga.path())
  const libro = leerPlantilla(plantilla)
  expect(libro.meta.template_version, 'la plantilla de Progenitoras es v3').toBe('v3')
  expect(libro.meta.schema_id).toBe('CUTOVER_GRANDPARENT_V3')
  expect(libro.meta.business_unit).toBe('grandparent')
  for (const col of TRANSFERENCIAS) expect(libro.cabecera, `columna ${col} en Datos`).toContain(col)
  // Instrucciones: las cuatro transferencias explicadas y los textos refinados de Progenitoras.
  for (const campo of TRANSFERENCIAS) {
    expect(libro.instrucciones[campo], `Instrucciones de ${campo}`).toBeTruthy()
    expect(libro.instrucciones[campo].significado).toContain('NO es una transferencia')
  }
  expect(libro.instrucciones.birds_placed_males.significado).toContain('efectivamente')
  expect(libro.instrucciones.birds_placed_females.significado).toContain('efectivamente')
  expect(libro.instrucciones.productive_phase_code.significado).toContain('NO es una transferencia')
  expect(libro.instrucciones.historical_culls_males.significado).toContain('selección')
  j.plantilla = {
    bytes: plantilla.length, meta: libro.meta,
    transferencias_en_datos: TRANSFERENCIAS.filter(c => libro.cabecera.includes(c)),
    instrucciones: Object.fromEntries(TRANSFERENCIAS.map(c => [c, libro.instrucciones[c].significado])),
  }
  await page.screenshot({ path: `${PNG}/e2e_gp_01_pantalla_carga.png`, fullPage: true })

  // ── 4 · rellenar los tres lotes y subir por la interfaz ──
  const filas = [cria(refA, LOTE_A), cria(refB, LOTE_B), produccion(refC, LOTE_C)]
  const archivo = { name: 'cutover_template_grandparent_v3.xlsx', mimeType: MIME_XLSX, buffer: rellenarPlantilla(plantilla, filas) }
  const subida = page.waitForResponse(r => r.url().includes('/upload'))
  await page.getByTestId('cutover-file-input').setInputFiles(archivo)
  const respSubida = await subida
  const cuerpo = await respSubida.json()
  expect(respSubida.status(), JSON.stringify(cuerpo)).toBe(200)
  expect(cuerpo.status).toBe('validated')
  expect(cuerpo.invalid_rows).toBe(0)
  expect(cuerpo.valid_rows).toBe(3)
  expect(cuerpo.source_type).toBe('XLSX')
  await expect(page.getByTestId('cutover-errors')).toHaveCount(0)
  j.validacion = { filas: cuerpo.valid_rows, invalidas: cuerpo.invalid_rows, estado: cuerpo.status }

  // ── 5 · balance CONSISTENT por sexo para A, B y C (API) ──
  const prev = await previewDe(request, batch.id)
  const prevRef = porRef(prev)
  for (const ref of [refA, refB, refC]) {
    expect(prevRef[ref], `fila ${ref} en el preview`).toBeTruthy()
    expect(prevRef[ref].derived.balance_check.males, `${ref} machos`).toBe('CONSISTENT')
    expect(prevRef[ref].derived.balance_check.females, `${ref} hembras`).toBe('CONSISTENT')
  }
  j.preview_api = Object.fromEntries([refA, refB, refC].map(r => [r, prevRef[r].derived.balance_check]))

  // ── 6 · preview por la UI: etiquetas en español y los valores de cada lote ──
  const ui = await tablaPreview(page)
  for (const campo of TRANSFERENCIAS) {
    expect(ui.columna(ETIQUETAS[campo]), `cabecera ${ETIQUETAS[campo]}`).toBeGreaterThan(0)
  }
  await expect(page.getByTestId('cutover-preview')).not.toContainText('historical_transfers_in_males')
  const indice = (ref: string) => prev.rows.findIndex((f: any) => f.legacy_lot_code === ref)
  expect(ui.celda(indice(refA), ETIQUETAS.historical_transfers_out_males), 'A no transfiere').toBe('0')
  expect(ui.celda(indice(refB), ETIQUETAS.historical_transfers_out_males), 'B saca 40 machos').toBe('40')
  expect(ui.celda(indice(refB), ETIQUETAS.historical_transfers_out_females), 'B saca 600 hembras').toBe('600')
  expect(ui.celda(indice(refC), ETIQUETAS.historical_transfers_in_males), 'C recibe 40 machos').toBe('40')
  expect(ui.celda(indice(refC), ETIQUETAS.historical_transfers_in_females), 'C recibe 600 hembras').toBe('600')
  j.preview_ui = { cabeceras: ui.cabeceras.filter(c => c.includes('Transf.')), filas: ui.filas.length }
  await page.screenshot({ path: `${PNG}/e2e_gp_01_preview_transferencias.png`, fullPage: true })

  // ── 7 · enviar a aprobación, aprobar con OTRO actor y aplicar ──
  const envio = page.waitForResponse(r => r.url().includes('/submit'))
  await page.getByRole('button', { name: /Enviar a aprobación|Submit for approval/ }).click()
  expect((await envio).status()).toBe(200)
  await expect(cabecera).toContainText(/Pendiente de aprobación|Pending approval/)
  const ctxAprobador = await browser.newContext()
  const p2 = await ctxAprobador.newPage()
  await entrar(p2, 'approver')
  await p2.goto(`/cutover?batch=${batch.id}`)
  await expect(p2.getByTestId('cutover-batch-header')).toContainText(`#${batch.id}`)
  const aprobacion = p2.waitForResponse(r => r.url().includes('/approve'))
  await p2.getByRole('button', { name: /^Aprobar$|^Approve$/ }).click()
  expect((await aprobacion).status()).toBe(200)
  await expect(p2.getByTestId('cutover-batch-header')).toContainText(/Aprobado|Approved/)
  await ctxAprobador.close()

  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(cabecera).toContainText(/Aprobado|Approved/)
  const aplicacion = page.waitForResponse(r => r.url().includes('/apply'))
  await page.getByRole('button', { name: /^Aplicar$|^Apply$/ }).click()
  const respApply = await aplicacion
  const textoApply = await respApply.text()
  expect(respApply.status(), textoApply).toBe(200)
  await expect(cabecera).toContainText(/Aplicado|Applied/)
  const reconciliacion = page.getByTestId('cutover-reconciliation')
  await expect(reconciliacion).toBeVisible()
  for (const ref of [refA, refB, refC]) await expect(reconciliacion).toContainText(ref)
  await expect(page.getByTestId('cutover-applied')).toBeVisible()
  await page.screenshot({ path: `${PNG}/e2e_gp_01_reconciliacion.png`, fullPage: true })

  // ── 8 · localizar los tres lotes: opening por sexo y fases declaradas ──
  const lotes = await lotesPorRef(request, batch.id)
  for (const ref of [refA, refB, refC]) expect(lotes[ref], `lote ${ref}`).toBeTruthy()
  const [loteA, loteB, loteC] = [await loteConFases(request, lotes[refA]), await loteConFases(request, lotes[refB]),
    await loteConFases(request, lotes[refC])]
  const ob = (lote: any) => lote.opening_balance
  j.lotes = { ids: { A: lotes[refA], B: lotes[refB], C: lotes[refC] }, A: ob(loteA), B: ob(loteB), C: ob(loteC) }

  // Alojadas, mortalidad y descartes de cada lote, intactos.
  expect([ob(loteA).placed_male_count, ob(loteA).placed_female_count]).toEqual([100, 1000])
  expect([ob(loteA).accumulated_mortality_male, ob(loteA).accumulated_mortality_female]).toEqual([5, 30])
  expect([ob(loteA).accumulated_culls_male, ob(loteA).accumulated_culls_female]).toEqual([0, 20])
  expect([ob(loteB).placed_male_count, ob(loteB).placed_female_count]).toEqual([100, 1000])
  expect([ob(loteB).accumulated_mortality_male, ob(loteB).accumulated_mortality_female]).toEqual([4, 26])
  expect([ob(loteB).accumulated_culls_male, ob(loteB).accumulated_culls_female]).toEqual([6, 24])
  expect([ob(loteC).placed_male_count, ob(loteC).placed_female_count]).toEqual([0, 0])
  expect([ob(loteC).accumulated_mortality_male, ob(loteC).accumulated_mortality_female]).toEqual([0, 0])
  expect([ob(loteC).accumulated_culls_male, ob(loteC).accumulated_culls_female]).toEqual([0, 0])

  // Las cuatro transferencias persistidas por sexo, con sus estados KNOWN.
  expect([ob(loteA).accumulated_transfers_in_male, ob(loteA).accumulated_transfers_in_female]).toEqual([0, 0])
  expect([ob(loteA).accumulated_transfers_out_male, ob(loteA).accumulated_transfers_out_female]).toEqual([0, 0])
  expect([ob(loteB).accumulated_transfers_in_male, ob(loteB).accumulated_transfers_in_female]).toEqual([0, 0])
  expect([ob(loteB).accumulated_transfers_out_male, ob(loteB).accumulated_transfers_out_female]).toEqual([40, 600])
  expect([ob(loteC).accumulated_transfers_in_male, ob(loteC).accumulated_transfers_in_female]).toEqual([40, 600])
  expect([ob(loteC).accumulated_transfers_out_male, ob(loteC).accumulated_transfers_out_female]).toEqual([0, 0])
  for (const lote of [loteA, loteB, loteC]) {
    expect([ob(lote).transfers_in_status, ob(lote).transfers_out_status]).toEqual(['KNOWN', 'KNOWN'])
    expect(ob(lote).template_version).toBe('v3')
  }

  // Vivas por sexo: las del escenario, y la ecuación cuadra en cada lote (sin doble conteo).
  expect([ob(loteA).initial_male_count, ob(loteA).initial_female_count]).toEqual([95, 950])
  expect([ob(loteB).initial_male_count, ob(loteB).initial_female_count]).toEqual([50, 350])
  expect([ob(loteC).initial_male_count, ob(loteC).initial_female_count]).toEqual([40, 600])
  const sumaVivas = [ob(loteA), ob(loteB), ob(loteC)].reduce((acc, o) => acc + o.initial_male_count + o.initial_female_count, 0)
  const sumaEcuacion = [LOTE_A, LOTE_B, LOTE_C].reduce((acc, b) => acc + ecuacion(b, 0) + ecuacion(b, 1), 0)
  expect(sumaVivas, 'Σ vivas = Σ (alojadas + entradas − mort − descartes − salidas)').toBe(sumaEcuacion)
  j.suma_vivas = sumaVivas

  // Fase declarada y aplicada: CRIA en A y B, PROD en C (fase ≠ transferencia).
  const activa = (lote: any) => lote.phases.find((p: any) => p.is_active)?.phase_id
  expect(activa(loteA)).toBe(fases.CRIA)
  expect(activa(loteB)).toBe(fases.CRIA)
  expect(activa(loteC)).toBe(fases.PROD)
  j.fases = { A: activa(loteA), B: activa(loteB), C: activa(loteC) }

  // ── 9 · reconciliación por API: claves por sexo y conformación B.out == C.in ──
  const rec = await reconciliacionDe(request, batch.id)
  const [rA, rB, rC] = [filaRec(rec, refA), filaRec(rec, refB), filaRec(rec, refC)]
  j.reconciliacion = { A: rA.opening, B: rB.opening, C: rC.opening }
  expect([rA.opening.live_males, rA.opening.live_females]).toEqual([95, 950])
  expect([rB.opening.live_males, rB.opening.live_females]).toEqual([50, 350])
  expect([rC.opening.live_males, rC.opening.live_females]).toEqual([40, 600])
  expect([rA.opening.historical_transfers_in_males, rA.opening.historical_transfers_out_males]).toEqual([0, 0])
  expect([rB.opening.historical_transfers_out_males, rB.opening.historical_transfers_out_females]).toEqual([40, 600])
  expect([rC.opening.historical_transfers_in_males, rC.opening.historical_transfers_in_females]).toEqual([40, 600])
  // Conformación: aserción de la PRUEBA (D-5: la reconciliación cruzada entre lotes NO es regla de producto).
  expect(rB.opening.historical_transfers_out_males, 'Σ salidas de B = entradas de C (machos)').toBe(rC.opening.historical_transfers_in_males)
  expect(rB.opening.historical_transfers_out_females, 'Σ salidas de B = entradas de C (hembras)').toBe(rC.opening.historical_transfers_in_females)
  expect(rA.post.mortality + rB.post.mortality + rC.post.mortality, 'sin eventos post-corte todavía').toBe(0)
  expect([rA.current_live, rB.current_live, rC.current_live]).toEqual([1045, 400, 640])

  // ── 10 · refresco y re-login: la reconciliación es persistente ──
  await page.reload()
  await expect(page.getByTestId('cutover-reconciliation')).toBeVisible()
  for (const ref of [refA, refB, refC]) await expect(page.getByTestId('cutover-reconciliation')).toContainText(ref)
  const ctx2 = await browser.newContext()
  const p3 = await ctx2.newPage()
  await entrar(p3, 'admin')
  await p3.goto(`/cutover?batch=${batch.id}`)
  await expect(p3.getByTestId('cutover-batch-header')).toContainText(/Aplicado|Applied/)
  for (const ref of [refA, refB, refC]) await expect(p3.getByTestId('cutover-reconciliation')).toContainText(ref)
  await ctx2.close()
  const cab2 = await cabeceraAdmin(request)
  const rec2 = await (await request.get(`${API}/cutover-batches/${batch.id}/reconciliation`, { headers: cab2 })).json()
  j.persistencia = { A: filaRec(rec2, refA).current_live, B: filaRec(rec2, refB).current_live, C: filaRec(rec2, refC).current_live }
  expect(j.persistencia).toEqual({ A: 1045, B: 400, C: 640 })

  ev['E2E-GP-01'] = { batch: batch.id, corte_dias: CORTE, refs: { A: refA, B: refB, C: refC }, ...j }
})

test('E2E-GP-02 post-corte: la mortalidad posterior no vuelve a restar lo transferido (lotes B y C)', async ({ request }) => {
  test.setTimeout(180_000)
  const refB = `E2E-GP02-B-${s}`
  const refC = `E2E-GP02-C-${s}`
  const j: Record<string, any> = {}

  const batch = await crearBatch(request, 57)
  const subido = await subirFilasXlsx(request, batch.id, [cria(refB, LOTE_B), produccion(refC, LOTE_C)], 'cutover_grandparent_v3_post_corte.xlsx')
  expect(subido.invalid_rows, JSON.stringify(subido)).toBe(0)
  expect(subido.valid_rows).toBe(2)
  await aprobarYAplicar(request, batch.id)
  const lotes = await lotesPorRef(request, batch.id)
  const [idB, idC] = [lotes[refB], lotes[refC]]

  const antes = await reconciliacionDe(request, batch.id)
  expect(filaRec(antes, refB).current_live).toBe(400)
  expect(filaRec(antes, refC).current_live).toBe(640)

  // ── mortalidad POSTERIOR al corte en el lote origen (3 machos) ──
  const mov = await request.post(`${API}/operations`, { headers: cab, data: {
    lot_id: idB, event_type: 'mortality_recording', event_date: haceDias(7),
    bird_movements: [{ sex: 'male', quantity: 3, avg_weight: 3600 }],
  } })
  expect(mov.status(), await mov.text()).toBe(201)

  const despues = await reconciliacionDe(request, batch.id)
  const b = filaRec(despues, refB)
  j.lote_B = { opening: b.opening, post: b.post, current_live: b.current_live }
  expect(b.post.mortality).toBe(3)
  expect(b.current_live, 'apertura − 3 observadas después del corte').toBe(397)
  expect(b.current_live).toBe(b.opening.live - 3)
  // Lo histórico NO se descuenta otra vez: ni la salida de 640 ni nada anterior al corte.
  expect(b.opening.historical_transfers_out_males).toBe(40)
  expect(b.opening.historical_transfers_out_females).toBe(600)
  expect(b.current_live, 'no se resta la salida histórica').not.toBe(b.opening.live - 3 - 640)
  expect(b.opening.live).toBe(400)

  // ── el lote destino (PROD) admite un evento propio y coherente con su saldo ──
  const baja = await request.post(`${API}/operations`, { headers: cab, data: {
    lot_id: idC, event_type: 'mortality_recording', event_date: haceDias(5),
    bird_movements: [{ sex: 'male', quantity: 2, avg_weight: 3400 }],
  } })
  expect(baja.status(), await baja.text()).toBe(201)
  const final = await reconciliacionDe(request, batch.id)
  const c = filaRec(final, refC)
  j.lote_C = { opening: c.opening, post: c.post, current_live: c.current_live }
  expect(c.post.mortality).toBe(2)
  expect(c.current_live).toBe(638)
  expect(c.current_live).toBe(c.opening.live - 2)
  expect([c.opening.historical_transfers_in_males, c.opening.historical_transfers_in_females]).toEqual([40, 600])
  expect(filaRec(final, refB).current_live, 'B sigue en 397').toBe(397)
  j.lote_B_final = filaRec(final, refB).current_live

  ev['E2E-GP-02'] = { batch: batch.id, corte_dias: 57, refs: { B: refB, C: refC }, ...j }
})

test('E2E-GP-03 CSV: UNKNOWN no se inventa como 0 (preview y reconciliación) y los errores por fila bloquean el envío', async ({ page, request }) => {
  test.setTimeout(240_000)
  const j: Record<string, any> = {}
  const refUnk = `E2E-GP03-UNK-${s}`

  // ── a · UNKNOWN válido: transferencias y mortalidad histórica VACÍAS ──
  const batch = await crearBatch(request, 59)
  const sinDato: Record<string, unknown> = {
    ...cria(refUnk, { ...LOTE_A, mort: [0, 0] }),
    historical_mortality_males: null, historical_mortality_females: null,
    historical_transfers_in_males: null, historical_transfers_in_females: null,
    historical_transfers_out_males: null, historical_transfers_out_females: null,
    live_males: 95, live_females: 950,
  }
  const subido = await subirFilasCsv(request, batch.id, [sinDato], 'cutover_grandparent_v3_unknown.csv')
  expect(subido.invalid_rows, JSON.stringify(subido)).toBe(0)
  expect(subido.valid_rows).toBe(1)
  expect(subido.status).toBe('validated')
  expect(subido.source_type).toBe('CSV')

  const prev = await previewDe(request, batch.id)
  const filaUnk = porRef(prev)[refUnk]
  expect(filaUnk.derived.balance_check).toEqual({ males: 'NOT_FULLY_VERIFIABLE', females: 'NOT_FULLY_VERIFIABLE' })
  j.unknown = { batch: batch.id, verdict: filaUnk.derived.balance_check }

  // El preview muestra UNKNOWN (jamás un 0 inventado) en las cuatro transferencias.
  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(page.getByTestId('cutover-preview')).toBeVisible()
  const ui = await tablaPreview(page)
  const indice = prev.rows.findIndex((f: any) => f.legacy_lot_code === refUnk)
  for (const campo of TRANSFERENCIAS) {
    const celda = ui.celda(indice, ETIQUETAS[campo])
    expect(celda, `${campo} debe declararse UNKNOWN`).toContain('UNKNOWN')
    expect(celda, `${campo} no inventa un 0`).not.toBe('0')
  }
  j.unknown.ui = Object.fromEntries(TRANSFERENCIAS.map(c => [c, ui.celda(indice, ETIQUETAS[c])]))
  await page.screenshot({ path: `${PNG}/e2e_gp_03_preview_unknown.png`, fullPage: true })

  await aprobarYAplicar(request, batch.id)
  const rec = await reconciliacionDe(request, batch.id)
  const rUnk = filaRec(rec, refUnk)
  j.unknown.opening = rUnk.opening
  expect(rUnk.opening.historical_transfers_in_males).toBeNull()
  expect(rUnk.opening.historical_transfers_in_females).toBeNull()
  expect(rUnk.opening.historical_transfers_out_males).toBeNull()
  expect(rUnk.opening.historical_transfers_out_females).toBeNull()
  expect([rUnk.opening.transfers_in_status, rUnk.opening.transfers_out_status]).toEqual(['UNKNOWN', 'UNKNOWN'])
  expect([rUnk.opening.historical_mortality, rUnk.opening.mortality_status]).toEqual([null, 'UNKNOWN'])
  expect([rUnk.opening.live_males, rUnk.opening.live_females]).toEqual([95, 950])

  // ── b · negativa, decimal y saldo inconsistente: errores por fila y envío bloqueado ──
  const batchErr = await crearBatch(request, 61)
  const base = cria(`E2E-GP03-ERR-${s}`, LOTE_A)
  const mala = (ref: string, extra: Record<string, unknown>) => ({ ...base, legacy_lot_code: ref, ...extra })
  const filasErr = [
    mala(`E2E-GP03-NEG-${s}`, { historical_transfers_out_males: -40 }),
    mala(`E2E-GP03-DEC-${s}`, { historical_transfers_in_males: 12.5 }),
    mala(`E2E-GP03-INC-${s}`, {
      birds_placed_males: 100, historical_mortality_males: 0, historical_culls_males: 0,
      historical_transfers_in_males: 0, historical_transfers_out_males: 0, live_males: 95,
    }),
  ]
  const conErrores = await subirFilasCsv(request, batchErr.id, filasErr, 'cutover_grandparent_v3_errores.csv')
  expect(conErrores.invalid_rows, JSON.stringify(conErrores)).toBe(3)
  expect(conErrores.status).toBe('validating')
  const errores = conErrores.errores as any[]
  const codigo = (ref: string) => errores.filter(e => e.row_number === porRow(filasErr, ref))
  j.errores = errores.map(e => ({ fila: e.row_number, campo: e.field, codigo: e.error_code }))
  expect(codigo(`E2E-GP03-NEG-${s}`).some(e => e.error_code === 'NEGATIVE_VALUE')).toBe(true)
  expect(codigo(`E2E-GP03-DEC-${s}`).some(e => e.error_code === 'INVALID_INTEGER')).toBe(true)
  expect(codigo(`E2E-GP03-INC-${s}`).some(e => e.error_code === 'CONSISTENCY_MISMATCH')).toBe(true)

  const envio = await request.post(`${API}/cutover-batches/${batchErr.id}/submit`, { headers: cab })
  const textoEnvio = await envio.text()
  j.envio_bloqueado = { status: envio.status(), detalle: textoEnvio.slice(0, 200) }
  expect(envio.status(), textoEnvio).toBe(409)
  expect(textoEnvio).toContain('BATCH_STATE_INVALID')
  const detalleBatch = await (await request.get(`${API}/cutover-batches/${batchErr.id}`, { headers: cab })).json()
  expect(detalleBatch.status).toBe('validating')

  ev['E2E-GP-03'] = { batch_unknown: batch.id, batch_errores: batchErr.id, ...j }
})

test('E2E-GP-04 plantilla v2 rechazada y sexaje diagnóstico: reclasificación inconsciente, descarte válido', async ({ request }) => {
  test.setTimeout(180_000)
  const j: Record<string, any> = {}

  // ── a · una plantilla Meta v2 de grandparent se rechaza indicando la v3 ──
  const batchV2 = await crearBatch(request, 63)
  const plantillaV3 = await request.get(`${API}/cutover-templates/grandparent?format=xlsx&batch_id=${batchV2.id}`, { headers: cab })
  expect(plantillaV3.status(), await plantillaV3.text()).toBe(200)
  const v2 = degradarAGrandparentV2(await plantillaV3.body())
  const rechazo = await request.post(`${API}/cutover-batches/${batchV2.id}/upload`, {
    headers: cab,
    multipart: { file: { name: 'cutover_template_grandparent_v2.xlsx', mimeType: MIME_XLSX, buffer: v2 } },
  })
  const textoRechazo = await rechazo.text()
  j.rechazo_v2 = { status: rechazo.status(), detalle: textoRechazo.slice(0, 300) }
  expect(rechazo.status(), textoRechazo).toBe(422)
  expect(textoRechazo).toContain('TEMPLATE_VERSION_UNSUPPORTED')
  expect(textoRechazo).toContain('v3')

  // ── b · sexaje: RATIFICADO como descarte (OD-GP-SEXAGE-01); la reclasificación M→H no la representa el
  //        contrato y el sistema la marca como inconsistencia en lugar de corregir el sexo ──
  const batchSex = await crearBatch(request, 65)
  const refSex = `E2E-GP04-SEXAJE-${s}`
  const reclasificacion = produccion(refSex, {
    ...LOTE_A, placed: [100, 1000], mort: [0, 0], culls: [0, 0], entradas: [0, 0], salidas: [0, 0], live: [90, 1010],
  })
  const diagnostico = await subirFilasXlsx(request, batchSex.id, [reclasificacion], 'cutover_grandparent_v3_sexaje_reclasificacion.xlsx')
  expect(diagnostico.invalid_rows, JSON.stringify(diagnostico)).toBe(1)
  const errores = diagnostico.errores as any[]
  j.sexaje_reclasificacion = errores.map(e => ({ campo: e.field, codigo: e.error_code, mensaje: e.message }))
  expect(errores.some(e => e.error_code === 'CONSISTENCY_MISMATCH' && e.field === 'live_males'),
    'machos: 100 − 0 − 0 = 100 ≠ 90 (OD-GP-SEXAGE-01)').toBe(true)
  expect(errores.some(e => e.error_code === 'CONSISTENCY_MISMATCH' && e.field === 'live_females'),
    'hembras: 1000 − 0 − 0 = 1000 ≠ 1010 (OD-GP-SEXAGE-01)').toBe(true)

  // La variante como DESCARTE de machos sí valida: con OD-GP-SEXAGE-01 RATIFICADA (HISTORICAL_CULL) el error de
  // sexaje que saca el ave del lote ES un descarte, único modelo que el contrato representa. No hay métrica aparte.
  const descarte = produccion(refSex, {
    ...LOTE_A, placed: [100, 1000], mort: [0, 0], culls: [10, 0], entradas: [0, 0], salidas: [0, 0], live: [90, 1000],
  })
  const variante = await subirFilasXlsx(request, batchSex.id, [descarte], 'cutover_grandparent_v3_sexaje_descarte.xlsx')
  expect(variante.invalid_rows, JSON.stringify(variante)).toBe(0)
  expect(variante.valid_rows).toBe(1)
  expect(variante.status).toBe('validated')
  const prev = await previewDe(request, batchSex.id)
  expect(porRef(prev)[refSex].derived.balance_check).toEqual({ males: 'CONSISTENT', females: 'CONSISTENT' })
  j.sexaje_descarte = { verdict: porRef(prev)[refSex].derived.balance_check, estado: variante.status }

  ev['E2E-GP-04'] = { batch_v2: batchV2.id, batch_sexaje: batchSex.id, ...j }
})

test.afterAll(async () => {
  ev.fin = new Date().toISOString()
  mkdirSync(EV, { recursive: true })
  writeFileSync(`${EV}/e2e-spec019-grandparent-v3-transferencias.json`, JSON.stringify(ev, null, 2))
})

