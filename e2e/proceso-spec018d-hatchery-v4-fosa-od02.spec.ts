/**
 * SPEC 018 §9 · AMENDMENT `OD-HATCH-V4-02 = RATIFIED` (2026-11-26) — la fosa es PRE-CARGA.
 *
 * Sustituye a la E2E de OD-HATCH-V4-01 (fosa post-carga, SUPERSEDED). Evidencia de la usuaria
 * funcional: los huevos fértiles a fosa se descuentan de los **recibidos**; al cargar, ya se descontaron.
 *
 * - **E2E-OD02-01** flujo completo (§31 del mandato): plantilla v4 del batch con la instrucción nueva
 *   («antes de la carga en incubadora», sin «ovoscopia»), carga 10 000 / 8 500 / 200 / 200 / 100 /
 *   fosa 200 / transferidos 8 000, preview en dos etapas (saldo disponible 800, en proceso 500 y no
 *   300), aprobación con otro actor, aplicación, reconciliación, BR-03 operativo (801 se rechaza, 800
 *   entra), recarga y re-login.
 * - **E2E-OD02-02** negativos: suma pre-carga > recibidos (incluso cuando solo la fosa la rompe) y
 *   fosa > recibidos ⇒ `CONSISTENCY_MISMATCH`; la igualdad es válida.
 * - **E2E-OD02-03** fosa vacía (CSV) ⇒ saldo disponible UNKNOWN en API y UI; en proceso sigue numérico.
 * - **E2E-OD02-04** transferidos = cargados con fosa 500 ⇒ válido y en proceso 0 (la fosa no
 *   participa en `transferred ≤ set`).
 *
 * Evidencia (JSON saneado + capturas, sin tokens) en `audit/ga-hatchery-v4-od02-pit-preload/evidence/e2e_od02/`.
 */
import { expect, test, type APIRequestContext } from '@playwright/test'
import { mkdirSync, writeFileSync } from 'node:fs'
import { API, cabeceraAdmin, cabeceraAprobador, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'
import {
  asegurarFases, construirCsv, corteHaceDias, crearMaestrosCutover, filasPorBu, habilitarCutoverEnRoles,
  habilitarUnidad, haceDias, leerPlantilla, rellenarPlantilla, type MaestrosCutover,
} from '../test-support/cutover'

test.describe.configure({ mode: 'serial' })

const EV = 'audit/ga-hatchery-v4-od02-pit-preload/evidence/e2e_od02'
const PNG = `${EV}/screenshots`
const MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const MIME_CSV = 'text/csv'

const ev: Record<string, any> = {}
let cab: { Authorization: string }
let cabAprobador: { Authorization: string }
let maestros: MaestrosCutover
let s: string

/** Caso del mandato: 10 000 recibidos, 8 500 cargados, 200 + 200 + 100 no incubables y 200 a fosa. */
const CASO = {
  eggs_received: 10000, eggs_set: 8500,
  eggs_non_incubable_oversized: 200, eggs_non_incubable_dirty: 200, eggs_non_incubable_broken: 100,
  fertile_eggs_to_pit: 200, eggs_transferred: 8000,
}

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

async function subirFilasXlsx(request: APIRequestContext, batchId: number, filas: Record<string, unknown>[]) {
  const plantilla = await (await plantillaDe(request, batchId, 'xlsx')).body()
  const subida = await subir(request, batchId, {
    name: 'cutover_template_hatchery_v4_fosa_od02.xlsx', mimeType: MIME_XLSX, buffer: rellenarPlantilla(plantilla, filas),
  })
  const texto = await subida.text()
  expect(subida.status(), texto).toBe(200)
  return JSON.parse(texto)
}

const validacion = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/validation`, { headers: cab })).json()

const preview = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/preview`, { headers: cab })).json()

const reconciliacion = async (request: APIRequestContext, batchId: number, cabecera = cab) =>
  (await request.get(`${API}/cutover-batches/${batchId}/reconciliation`, { headers: cabecera })).json()

const loteRec = (rec: any, ref: string) => rec.lots.find((l: any) => l.legacy_lot_code === ref)

/** Submit (admin) → approve (aprobador, otro actor) → apply (admin). */
async function cicloDeAprobacion(request: APIRequestContext, batchId: number) {
  const envio = await request.post(`${API}/cutover-batches/${batchId}/submit`, { headers: cab })
  expect(envio.status(), await envio.text()).toBe(200)
  const aprobacion = await request.post(`${API}/cutover-batches/${batchId}/approve`, { headers: cabAprobador })
  expect(aprobacion.status(), await aprobacion.text()).toBe(200)
  const aplicacion = await request.post(`${API}/cutover-batches/${batchId}/apply`, { headers: cab })
  const texto = await aplicacion.text()
  expect(aplicacion.status(), texto).toBe(200)
  expect(JSON.parse(texto).template_version).toBe('v4')
}

async function loteDe(request: APIRequestContext, batchId: number, ref: string): Promise<number> {
  const items = await (await request.get(`${API}/cutover-batches/${batchId}/items`, { headers: cab })).json()
  const fila = items.items.find((i: any) => i.legacy_lot_reference === ref)
  expect(fila, `la fila ${ref} debe haberse migrado`).toBeTruthy()
  expect(fila.validation_status, JSON.stringify(fila)).toBe('applied')
  return fila.lot_id as number
}

/** Celdas de la reconciliación en la UI para un lote. */
function celdas(page: any, lotId: number) {
  return {
    disponible: page.getByTestId(`cutover-eggs-available-${lotId}`),
    enProceso: page.getByTestId(`cutover-eggs-in-process-${lotId}`),
    fosa: page.getByTestId(`cutover-fertile-pit-${lotId}`),
    totalNoIncubables: page.getByTestId(`cutover-non-incubable-total-${lotId}`),
  }
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
  ev.regla = 'SPEC 018 §9 · OD-HATCH-V4-02: fosa PRE-CARGA; set + no incubables + fosa ≤ received; '
    + 'eggs_in_process = set − transferred; saldo disponible = received − set − no incubables − fosa (todo KNOWN)'
  ev.maestros = maestros
})

test.afterAll(() => {
  ev.fin = new Date().toISOString()
  mkdirSync(PNG, { recursive: true })
  writeFileSync(`${EV}/e2e_spec018d_fosa_od02.json`, JSON.stringify(ev, null, 2))
})

test('E2E-OD02-01 flujo completo: instrucción nueva, fosa pre-carga, saldo 800, en proceso 500, BR-03, recarga y re-login', async ({ page, browser, request }) => {
  test.setTimeout(300_000)
  const ref = `E2E-OD02-${s}-F01`
  const batch = await crearBatch(request, 47)

  // ── 1-2 · plantilla v4 del batch con la instrucción nueva de la fosa ──
  const plantilla = await (await plantillaDe(request, batch.id, 'xlsx')).body()
  const libro = leerPlantilla(plantilla)
  expect(libro.meta.template_version).toBe('v4')
  expect(libro.meta.schema_id).toBe('CUTOVER_HATCHERY_V4')
  expect(libro.cabecera.length, 'sin cambio de columnas').toBe(23)
  const instruccion = String(libro.instrucciones['fertile_eggs_to_pit']?.significado ?? '')
  expect(instruccion).toContain('antes de la carga en incubadora')
  expect(instruccion).toContain('ya no forma parte de los huevos cargados')
  expect(instruccion, 'la redacción post-carga queda obsoleta').not.toMatch(/ovoscopia|durante la incubaci/i)

  // ── 3 · cargar datos con fosa pre-carga ──
  const subida = await subirFilasXlsx(request, batch.id, [filaV4(ref, CASO)])
  const errores = subida.status === 'validated' ? null : await validacion(request, batch.id)
  expect(subida.status, JSON.stringify(errores ?? subida)).toBe('validated')
  expect(subida.invalid_rows).toBe(0)

  // ── 4-6 · preview (API y UI): saldo 800 y en proceso 500, en dos etapas ──
  const prev = await preview(request, batch.id)
  const filaPrev = prev.rows.find((f: any) => f.legacy_lot_code === ref)
  expect(filaPrev.derived.eggs_available_to_set, '10 000 − 8 500 − 500 − 200').toBe(800)
  expect(filaPrev.derived.eggs_in_process, '8 500 − 8 000 (la fosa no resta)').toBe(500)
  expect(filaPrev.derived.eggs_in_process, 'sin doble conteo').not.toBe(300)
  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(page.getByTestId('cutover-preview')).toContainText(ref)
  await expect(page.getByTestId('cutover-preview-stages')).toContainText(/Pre-carga/)
  await expect(page.getByTestId(`cutover-preview-available-${filaPrev.row_number}`)).toHaveText('800')
  await expect(page.getByTestId(`cutover-preview-in-process-${filaPrev.row_number}`)).toHaveText('500')
  await page.screenshot({ path: `${PNG}/od02_01_preview.png`, fullPage: true })

  // ── 7-8 · aprobar (otro actor) y aplicar ──
  await cicloDeAprobacion(request, batch.id)
  const lotId = await loteDe(request, batch.id, ref)

  // ── 9 · reconciliar: apertura y saldo actual ──
  const lote = loteRec(await reconciliacion(request, batch.id), ref)
  const h = lote.opening.hatchery
  expect(h.fertile_eggs_to_pit).toBe(200)
  expect(h.fertile_eggs_to_pit_status).toBe('KNOWN')
  expect(h.eggs_non_incubable_total, 'la fosa no es un no incubable').toBe(500)
  expect(h.eggs_discarded_status, 'ni un descartado V3').toBe('NOT_APPLICABLE')
  expect(h.eggs_in_process).toBe(500)
  expect(lote.current.eggs_in_process).toBe(500)
  expect(lote.current.eggs_available_hatchery).toBe(800)

  // ── 10 · reporte de reconciliación en la UI ──
  await page.goto(`/cutover?batch=${batch.id}`)
  const ui = celdas(page, lotId)
  await expect(ui.disponible).toHaveText('800')
  await expect(ui.enProceso).toHaveText('500')
  await expect(ui.fosa).toHaveText('200')
  await page.screenshot({ path: `${PNG}/od02_01_reconciliacion.png`, fullPage: true })

  // BR-03 operativo: el saldo con el que se carga ya descontó no incubables y fosa ⇒ 801 no, 800 sí.
  const cargar = (cantidad: number) => request.post(`${API}/operations`, { headers: cab, data: {
    lot_id: lotId, event_type: 'incubation_load', event_date: haceDias(7),
    hatchery_params: [{ quantity_loaded: cantidad }],
  } })
  const excede = await cargar(801)
  const textoExcede = await excede.text()
  expect(excede.status(), textoExcede).toBe(400)
  expect(JSON.parse(textoExcede).rule).toBe('BR-03')
  const justo = await cargar(800)
  expect(justo.status(), await justo.text()).toBe(201)
  const despues = loteRec(await reconciliacion(request, batch.id), ref)
  expect(despues.current.eggs_available_hatchery, 'saldo agotado').toBe(0)
  expect(despues.current.eggs_in_process, '500 + 800 cargados post-corte').toBe(1300)

  // ── 11 · recarga ──
  await page.reload()
  await expect(celdas(page, lotId).disponible).toHaveText('0')
  await expect(celdas(page, lotId).enProceso).toHaveText(/1[.,]300/)
  await expect(celdas(page, lotId).fosa).toHaveText('200')

  // ── 12 · re-login con un contexto nuevo ──
  const ctxNuevo = await browser.newContext()
  const paginaNueva = await ctxNuevo.newPage()
  await entrar(paginaNueva, 'admin')
  await paginaNueva.goto(`/cutover?batch=${batch.id}`)
  await expect(celdas(paginaNueva, lotId).disponible).toHaveText('0')
  await expect(celdas(paginaNueva, lotId).enProceso).toHaveText(/1[.,]300/)
  await expect(celdas(paginaNueva, lotId).fosa).toHaveText('200')
  await paginaNueva.screenshot({ path: `${PNG}/od02_01_relogin.png`, fullPage: true })
  await ctxNuevo.close()
  const recNueva = loteRec(await reconciliacion(request, batch.id, await cabeceraAdmin(request)), ref)
  expect(recNueva.current.eggs_in_process).toBe(1300)

  ev['OD02-01'] = {
    batch: batch.id, lote: lotId, ref, instruccion,
    preview: { disponible: filaPrev.derived.eggs_available_to_set, en_proceso: filaPrev.derived.eggs_in_process },
    opening: h, current_antes: lote.current, current_despues: despues.current,
    br03: { ochocientos_uno: excede.status(), ochocientos: justo.status() },
  }
})

test('E2E-OD02-02 negativos: suma pre-carga > recibidos y fosa > recibidos se rechazan; la igualdad es válida', async ({ request }) => {
  test.setTimeout(240_000)
  const batch = await crearBatch(request, 46)
  const ceros = { eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0 }
  const filas = [
    // 9 000 + 500 + 400 + 200 + 100 = 10 200 > 10 000
    filaV4(`E2E-OD02-${s}-N1`, { eggs_received: 10000, eggs_set: 9000, eggs_non_incubable_oversized: 500,
      eggs_non_incubable_dirty: 400, eggs_non_incubable_broken: 200, fertile_eggs_to_pit: 100 }),
    // 9 000 + 300 + 300 + 200 = 9 800 cuadra; con fosa 300 ⇒ 10 100: la rompe la fosa
    filaV4(`E2E-OD02-${s}-N2`, { eggs_received: 10000, eggs_set: 9000, eggs_non_incubable_oversized: 300,
      eggs_non_incubable_dirty: 300, eggs_non_incubable_broken: 200, fertile_eggs_to_pit: 300 }),
    // fosa 10 001 > recibidos
    filaV4(`E2E-OD02-${s}-N3`, { eggs_received: 10000, eggs_set: 0, ...ceros, fertile_eggs_to_pit: 10001 }),
    // igualdad: 9 000 + 300 + 300 + 200 + 200 = 10 000 ⇒ válida y saldo 0
    filaV4(`E2E-OD02-${s}-OK`, { eggs_received: 10000, eggs_set: 9000, eggs_non_incubable_oversized: 300,
      eggs_non_incubable_dirty: 300, eggs_non_incubable_broken: 200, fertile_eggs_to_pit: 200 }),
  ]
  await subirFilasXlsx(request, batch.id, filas)
  const v = await validacion(request, batch.id)
  const errores = v.errors.map((e: any) => [e.row_number, e.field, e.error_code])
    .sort((a: any[], b: any[]) => a[0] - b[0])
  expect(errores).toEqual([
    [2, 'eggs_non_incubable_broken', 'CONSISTENCY_MISMATCH'],
    [3, 'fertile_eggs_to_pit', 'CONSISTENCY_MISMATCH'],
    [4, 'fertile_eggs_to_pit', 'CONSISTENCY_MISMATCH'],
  ])
  expect(v.valid_rows).toBe(1)
  expect(v.invalid_rows).toBe(3)
  const prev = await preview(request, batch.id)
  const ok = prev.rows.find((f: any) => f.legacy_lot_code === `E2E-OD02-${s}-OK`)
  expect(ok.derived.eggs_available_to_set).toBe(0)
  ev['OD02-02'] = { batch: batch.id, errores, valid_rows: v.valid_rows, invalid_rows: v.invalid_rows }
})

test('E2E-OD02-03 fosa vacía (CSV) ⇒ saldo disponible UNKNOWN; en proceso numérico', async ({ page, request }) => {
  test.setTimeout(240_000)
  const ref = `E2E-OD02-${s}-F03`
  const batch = await crearBatch(request, 45)
  const csv = await plantillaDe(request, batch.id, 'csv')
  const cabeceraCsv = (await csv.body()).toString('utf8')
  const subida = await subir(request, batch.id, {
    name: 'cutover_template_hatchery_v4_fosa_vacia.csv', mimeType: MIME_CSV,
    buffer: construirCsv(cabeceraCsv, [filaV4(ref, { ...CASO, fertile_eggs_to_pit: null })]),
  })
  const cuerpo = JSON.parse(await subida.text())
  expect(subida.status(), JSON.stringify(cuerpo)).toBe(200)
  expect(cuerpo.invalid_rows).toBe(0)
  const filaPrev = (await preview(request, batch.id)).rows.find((f: any) => f.legacy_lot_code === ref)
  expect(filaPrev.derived.eggs_available_to_set, 'nunca 1 000 con la fosa sin declarar').toBeNull()
  expect(filaPrev.derived.eggs_in_process).toBe(500)

  await cicloDeAprobacion(request, batch.id)
  const lotId = await loteDe(request, batch.id, ref)
  const lote = loteRec(await reconciliacion(request, batch.id), ref)
  expect(lote.opening.hatchery.fertile_eggs_to_pit_status).toBe('UNKNOWN')
  expect(lote.current.eggs_available_hatchery).toBeNull()
  expect(lote.current.eggs_in_process).toBe(500)

  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batch.id}`)
  const ui = celdas(page, lotId)
  await expect(ui.fosa).toHaveText('UNKNOWN')
  await expect(ui.disponible).not.toContainText(/\d/)
  await expect(ui.enProceso).toHaveText('500')
  await page.screenshot({ path: `${PNG}/od02_03_fosa_vacia.png`, fullPage: true })
  ev['OD02-03'] = { batch: batch.id, lote: lotId, ref, opening: lote.opening.hatchery, current: lote.current }
})

test('E2E-OD02-04 transferidos = cargados con fosa 500 ⇒ válido y en proceso 0 (la fosa no entra en la etapa post-carga)', async ({ request }) => {
  test.setTimeout(240_000)
  const ref = `E2E-OD02-${s}-F04`
  const batch = await crearBatch(request, 44)
  const subida = await subirFilasXlsx(request, batch.id, [filaV4(ref, {
    eggs_received: 10000, eggs_set: 9000, eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0,
    eggs_non_incubable_broken: 0, fertile_eggs_to_pit: 500, eggs_transferred: 9000,
  })])
  const errores = subida.status === 'validated' ? null : await validacion(request, batch.id)
  expect(subida.status, JSON.stringify(errores ?? subida)).toBe('validated')
  const filaPrev = (await preview(request, batch.id)).rows.find((f: any) => f.legacy_lot_code === ref)
  expect(filaPrev.derived.eggs_in_process).toBe(0)
  expect(filaPrev.derived.eggs_available_to_set, '10 000 − 9 000 − 0 − 500').toBe(500)
  ev['OD02-04'] = { batch: batch.id, ref, derivados: filaPrev.derived }
})
