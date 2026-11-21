/**
 * SPEC 018 §7 · AMENDMENT `OD-HATCH-V4-01 = RATIFIED` (2026-11-21) — la fosa es POST-CARGA.
 *
 * Certifica las pruebas obligatorias del mandato `GA-HATCHERY-V4-OD-FERTILE-EGGS-TO-PIT` sobre la
 * incubadora V4, por API y por interfaz:
 *
 * - **H4-FOSA-01** recibidos 10 000 / cargados 9 000 / transferidos 8 000 / fosa 100 ⇒ en proceso 900.
 * - **H4-FOSA-02** fosa 1 000 ⇒ en proceso 0 (8 000 + 1 000 = 9 000: el tope, válido).
 * - **H4-FOSA-03** transferidos 8 000 + fosa 1 001 > 9 000 ⇒ `CONSISTENCY_MISMATCH` y nada aprobable.
 * - **H4-FOSA-04** fosa 9 001 > cargados 9 000 ⇒ error; fosa 9 000 es válida (AC-V4-15).
 * - **H4-FOSA-05** fosa vacía por CSV ⇒ en proceso UNKNOWN en API y «UNKNOWN» en la UI (nunca 0).
 * - **H4-FOSA-06** fosa 0 conocido ⇒ en proceso = cargados − transferidos = 1 000 (KNOWN).
 * - **H4-FOSA-07** sin doble conteo: 500/300/200 + set 9 000 + fosa 100 + transferidos 8 000 +
 *   recibidos 10 000 ⇒ disponible 0 y en proceso 900; BR-03 no resta la fosa (una carga de 1 se
 *   rechaza con BR-03 porque el saldo es exactamente 0).
 *
 * La fosa **nunca** suma a los no incubables ni a los descartados V3 (D-5/D-12/D-14/D-15).
 * Evidencia (JSON saneado + capturas, sin tokens) en
 * `audit/ga-hatchery-v4-od01/evidence/e2e_od01/`.
 */
import { expect, test, type APIRequestContext } from '@playwright/test'
import { mkdirSync, writeFileSync } from 'node:fs'
import { API, cabeceraAdmin, cabeceraAprobador, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'
import {
  asegurarFases, construirCsv, corteHaceDias, crearMaestrosCutover, filasPorBu, habilitarCutoverEnRoles,
  habilitarUnidad, haceDias, rellenarPlantilla, type MaestrosCutover,
} from '../test-support/cutover'

test.describe.configure({ mode: 'serial' })

const EV = 'audit/ga-hatchery-v4-od01/evidence/e2e_od01'
const PNG = `${EV}/screenshots`
const MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const MIME_CSV = 'text/csv'

const ev: Record<string, any> = {}
let cab: { Authorization: string }
let cabAprobador: { Authorization: string }
let maestros: MaestrosCutover
let s: string

/** Fila V4 canónica de la BU (recibidos 10 000 / cargados 9 000 / transferidos 0 / fosa 25). */
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

/** Sube una única fila XLSX v4 (plantilla descargada del batch) y devuelve el cuerpo normalizado. */
async function subirFilaXlsx(request: APIRequestContext, batchId: number, filas: Record<string, unknown>[]) {
  const plantilla = await (await plantillaDe(request, batchId, 'xlsx')).body()
  const subida = await subir(request, batchId, {
    name: 'cutover_template_hatchery_v4_fosa.xlsx', mimeType: MIME_XLSX, buffer: rellenarPlantilla(plantilla, filas),
  })
  const texto = await subida.text()
  expect(subida.status(), texto).toBe(200)
  return JSON.parse(texto)
}

const validacion = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/validation`, { headers: cab })).json()

const preview = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/preview`, { headers: cab })).json()

const reconciliacion = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/reconciliation`, { headers: cab })).json()

const loteRec = (rec: any, ref: string) => rec.lots.find((l: any) => l.legacy_lot_code === ref)

/** Submit (admin) → approve (aprobador) → apply (admin), como los demás specs de proceso. */
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

/** `lot_id` de la fila migrada, por la API de items del batch. */
async function loteDe(request: APIRequestContext, batchId: number, ref: string): Promise<number> {
  const items = await (await request.get(`${API}/cutover-batches/${batchId}/items`, { headers: cab })).json()
  const fila = items.items.find((i: any) => i.legacy_lot_reference === ref)
  expect(fila, `la fila ${ref} debe haberse migrado`).toBeTruthy()
  expect(fila.validation_status, JSON.stringify(fila)).toBe('applied')
  return fila.lot_id as number
}

/** Flujo completo de una fila válida: subir, aprobar/aplicar y devolver su reconciliación. */
async function aplicarFila(request: APIRequestContext, corteDias: number, ref: string, extra: Record<string, unknown>) {
  const batch = await crearBatch(request, corteDias)
  const cuerpo = await subirFilaXlsx(request, batch.id, [filaV4(ref, extra)])
  // Con errores por fila se informa el detalle del contrato, no solo el estado del batch.
  const errores = cuerpo.status === 'validated' ? null : await validacion(request, batch.id)
  expect(cuerpo.status, JSON.stringify(errores ?? cuerpo)).toBe('validated')
  expect(cuerpo.invalid_rows).toBe(0)
  await cicloDeAprobacion(request, batch.id)
  const lotId = await loteDe(request, batch.id, ref)
  const rec = await reconciliacion(request, batch.id)
  return { batch, lotId, rec, lote: loteRec(rec, ref) }
}

/** Fila de la reconciliación en la UI, con la celda de «en proceso» y la de la fosa ya localizadas. */
async function filaEnUI(page: any, batchId: number, ref: string, lotId: number) {
  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batchId}`)
  await expect(page.getByTestId('cutover-reconciliation')).toBeVisible()
  const fila = page.getByTestId('cutover-reconciliation').locator('tbody tr').filter({ hasText: ref })
  await expect(fila).toHaveCount(1)
  return {
    fila,
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
  ev.regla = 'SPEC 018 §7 · D-12: eggs_in_process = set − transferred − fertile_eggs_to_pit (solo si los tres KNOWN)'
  ev.maestros = maestros
})

test.afterAll(() => {
  ev.fin = new Date().toISOString()
  mkdirSync(PNG, { recursive: true })
  writeFileSync(`${EV}/e2e_spec018b_fosa_od01.json`, JSON.stringify(ev, null, 2))
})

test('H4-FOSA-01 recibidos 10 000 / cargados 9 000 / transferidos 8 000 / fosa 100 ⇒ en proceso 900', async ({ page, request }) => {
  test.setTimeout(240_000)
  const ref = `E2E-OD01-${s}-F01`
  const { batch, lotId, lote } = await aplicarFila(request, 46, ref, {
    eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
    eggs_transferred: 8000, fertile_eggs_to_pit: 100,
  })
  const h = lote.opening.hatchery
  expect(h.eggs_received).toBe(10000)
  expect(h.eggs_set).toBe(9000)
  expect(h.eggs_transferred).toBe(8000)
  expect(h.fertile_eggs_to_pit).toBe(100)
  // D-12: 9 000 − 8 000 − 100 = 900 (la fosa resta porque es post-carga).
  expect(h.eggs_in_process).toBe(900)
  expect(lote.current.eggs_in_process).toBe(900)

  const ui = await filaEnUI(page, batch.id, ref, lotId)
  await expect(ui.enProceso).toContainText('900')
  await expect(ui.fosa).toHaveText('100')
  // La fosa es métrica SEPARADA: el total no incubable es 0 (ceros conocidos) y no la incluye.
  await expect(ui.totalNoIncubables.locator('span').first()).toHaveText('0')
  await expect(page.getByTestId('cutover-th-eggs-discarded')).toHaveCount(0)
  await page.screenshot({ path: `${PNG}/h4_fosa_01.png`, fullPage: true })

  ev['H4-FOSA-01'] = { batch: batch.id, lote: lotId, ref, opening: h, current: lote.current }
})

test('H4-FOSA-02 fosa 1 000 ⇒ en proceso 0 (8 000 + 1 000 = 9 000, tope exacto válido)', async ({ page, request }) => {
  test.setTimeout(240_000)
  const ref = `E2E-OD01-${s}-F02`
  const { batch, lotId, lote } = await aplicarFila(request, 45, ref, {
    eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
    eggs_transferred: 8000, fertile_eggs_to_pit: 1000,
  })
  expect(lote.opening.hatchery.fertile_eggs_to_pit).toBe(1000)
  expect(lote.opening.hatchery.eggs_in_process).toBe(0)
  expect(lote.current.eggs_in_process).toBe(0)

  const ui = await filaEnUI(page, batch.id, ref, lotId)
  await expect(ui.enProceso).toHaveText('0')
  await expect(ui.fosa).toHaveText(/1[.,]000/)
  await page.screenshot({ path: `${PNG}/h4_fosa_02.png`, fullPage: true })

  ev['H4-FOSA-02'] = { batch: batch.id, lote: lotId, ref, opening: lote.opening.hatchery, current: lote.current }
})

test('H4-FOSA-03 transferidos 8 000 + fosa 1 001 > 9 000 ⇒ CONSISTENCY_MISMATCH y nada que aprobar', async ({ page, request }) => {
  const ref = `E2E-OD01-${s}-F03`
  const batch = await crearBatch(request, 44)
  const cuerpo = await subirFilaXlsx(request, batch.id, [filaV4(ref, {
    eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
    eggs_transferred: 8000, fertile_eggs_to_pit: 1001,
  })])
  expect(cuerpo.invalid_rows).toBe(1)
  expect(cuerpo.valid_rows).toBe(0)
  expect(cuerpo.status, 'un batch con filas inválidas no queda validado').toBe('validating')

  const val = await validacion(request, batch.id)
  const error = val.errors.find((e: any) => e.field === 'fertile_eggs_to_pit')
  expect(error, JSON.stringify(val.errors)).toBeTruthy()
  expect(error.error_code).toBe('CONSISTENCY_MISMATCH')
  expect(String(error.message ?? '')).toMatch(/transferidos|fosa|cargados/i)

  // Nada aprobable: no hay envío posible con una fila inválida.
  const submit = await request.post(`${API}/cutover-batches/${batch.id}/submit`, { headers: cab })
  expect(submit.status(), await submit.text()).toBe(409)

  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batch.id}`)
  const erroresUI = page.getByTestId('cutover-errors')
  await expect(erroresUI).toBeVisible()
  await expect(erroresUI).toContainText('CONSISTENCY_MISMATCH')
  await page.screenshot({ path: `${PNG}/h4_fosa_03.png`, fullPage: true })

  ev['H4-FOSA-03'] = {
    batch: batch.id, ref, status_batch: cuerpo.status, invalidas: cuerpo.invalid_rows,
    error: { campo: error.field, codigo: error.error_code, mensaje: error.message, recibido: error.received_value },
    submit: submit.status(),
  }
})

test('H4-FOSA-04 fosa 9 001 > cargados 9 000 ⇒ error; fosa 9 000 es válida (transferidos UNKNOWN)', async ({ request }) => {
  const refMal = `E2E-OD01-${s}-F04-MAL`
  const refBien = `E2E-OD01-${s}-F04-BIEN`
  const batch = await crearBatch(request, 43)
  const cuerpo = await subirFilaXlsx(request, batch.id, [
    filaV4(refMal, {
      eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
      eggs_transferred: null, fertile_eggs_to_pit: 9001,
    }),
    filaV4(refBien, {
      eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
      eggs_transferred: null, fertile_eggs_to_pit: 9000,
    }),
  ])
  expect(cuerpo.total_rows).toBe(2)
  expect(cuerpo.invalid_rows).toBe(1)
  expect(cuerpo.valid_rows).toBe(1)

  const val = await validacion(request, batch.id)
  // Fila 2 = la primera de `Datos` (la 1 es la cabecera).
  const error = val.errors.find((e: any) => e.row_number === 2 && e.field === 'fertile_eggs_to_pit')
  expect(error, JSON.stringify(val.errors)).toBeTruthy()
  expect(error.error_code).toBe('CONSISTENCY_MISMATCH')
  expect(val.errors.filter((e: any) => e.row_number === 3), 'fosa = cargados es válida').toHaveLength(0)

  // La fila válida deriva UNKNOWN (transferidos UNKNOWN) pero conserva la fosa capturada.
  const prev = await preview(request, batch.id)
  const filaBien = prev.rows.find((f: any) => f.legacy_lot_code === refBien)
  expect(filaBien.values.fertile_eggs_to_pit).toEqual({ value: 9000, status: 'KNOWN' })
  expect(filaBien.derived.eggs_in_process, 'falta un KNOWN ⇒ UNKNOWN, ni 0 ni 9 000').toBeNull()
  const filaMal = prev.rows.find((f: any) => f.legacy_lot_code === refMal)
  expect(filaMal.status).toBe('invalid')

  ev['H4-FOSA-04'] = {
    batch: batch.id, mal: refMal, bien: refBien,
    error: { fila: error.row_number, campo: error.field, codigo: error.error_code, mensaje: error.message },
    valida: { fosa: filaBien.values.fertile_eggs_to_pit, en_proceso: filaBien.derived.eggs_in_process },
  }
})

test('H4-FOSA-05 fosa vacía por CSV ⇒ en proceso UNKNOWN en la API y «UNKNOWN» en la UI', async ({ page, request }) => {
  test.setTimeout(240_000)
  const ref = `E2E-OD01-${s}-F05`
  const batch = await crearBatch(request, 42)
  const csv = await plantillaDe(request, batch.id, 'csv')
  const cabeceraCsv = (await csv.body()).toString('utf8').replace(/^\uFEFF/, '').split('\n')[0].trim()
  const subida = await subir(request, batch.id, {
    name: 'cutover_template_hatchery_v4_fosa_vacia.csv', mimeType: MIME_CSV,
    buffer: construirCsv(cabeceraCsv, [filaV4(ref, {
      eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
      eggs_transferred: 8000, fertile_eggs_to_pit: null,
    })]),
  })
  const cuerpo = JSON.parse(await subida.text())
  expect(subida.status(), JSON.stringify(cuerpo)).toBe(200)
  expect(cuerpo.invalid_rows).toBe(0)
  await cicloDeAprobacion(request, batch.id)
  const lotId = await loteDe(request, batch.id, ref)
  const rec = await reconciliacion(request, batch.id)
  const lote = loteRec(rec, ref)
  expect(lote.opening.hatchery.fertile_eggs_to_pit).toBeNull()
  expect(lote.opening.hatchery.fertile_eggs_to_pit_status).toBe('UNKNOWN')
  expect(lote.opening.hatchery.eggs_in_process, 'un UNKNOWN nunca se toma por 0 (jamás 1 000)').toBeNull()
  expect(lote.current.eggs_in_process).toBeNull()

  const ui = await filaEnUI(page, batch.id, ref, lotId)
  await expect(ui.enProceso).toHaveText('UNKNOWN')
  await expect(ui.enProceso).not.toContainText('0')
  await expect(ui.fosa).toHaveText('UNKNOWN')
  await page.screenshot({ path: `${PNG}/h4_fosa_05.png`, fullPage: true })

  ev['H4-FOSA-05'] = { batch: batch.id, lote: lotId, ref, opening: lote.opening.hatchery, current: lote.current }
})

test('H4-FOSA-06 fosa 0 conocido ⇒ en proceso = cargados − transferidos = 1 000 (KNOWN)', async ({ page, request }) => {
  test.setTimeout(240_000)
  const ref = `E2E-OD01-${s}-F06`
  const { batch, lotId, lote } = await aplicarFila(request, 40, ref, {
    eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
    eggs_transferred: 8000, fertile_eggs_to_pit: 0,
  })
  expect(lote.opening.hatchery.fertile_eggs_to_pit).toBe(0)
  expect(lote.opening.hatchery.fertile_eggs_to_pit_status).toBe('KNOWN')
  expect(lote.opening.hatchery.eggs_in_process, '9 000 − 8 000 − 0').toBe(1000)
  expect(lote.current.eggs_in_process).toBe(1000)

  const ui = await filaEnUI(page, batch.id, ref, lotId)
  await expect(ui.enProceso).toHaveText(/1[.,]000/)
  await expect(ui.enProceso).not.toHaveText('UNKNOWN')
  await expect(ui.fosa).toHaveText('0')
  await page.screenshot({ path: `${PNG}/h4_fosa_06.png`, fullPage: true })

  ev['H4-FOSA-06'] = { batch: batch.id, lote: lotId, ref, opening: lote.opening.hatchery, current: lote.current }
})

test('H4-FOSA-07 sin doble conteo: 500/300/200 + fosa 100 ⇒ disponible 0, en proceso 900 y BR-03 intacta', async ({ page, request }) => {
  test.setTimeout(240_000)
  const ref = `E2E-OD01-${s}-F07`
  const { batch, lotId, lote } = await aplicarFila(request, 39, ref, {
    eggs_received: 10000, eggs_set: 9000,
    eggs_non_incubable_oversized: 500, eggs_non_incubable_dirty: 300, eggs_non_incubable_broken: 200,
    eggs_transferred: 8000, fertile_eggs_to_pit: 100,
  })
  const h = lote.opening.hatchery
  expect(h.eggs_non_incubable_total).toBe(1000)
  expect(h.fertile_eggs_to_pit).toBe(100)
  // D-14: el saldo es received − set − Σ(no incubables KNOWN) = 0; la fosa NO se resta aquí.
  expect(lote.current.eggs_available_hatchery, 'BR-03 no resta la fosa').toBe(0)
  // AC-V4-18: en proceso 900, ni −100 (fosa contada dos veces) ni 800.
  expect(h.eggs_in_process).toBe(900)
  expect(lote.current.eggs_in_process).toBe(900)

  // BR-03 permite exactamente el saldo: con 0 disponible, una carga de 1 se rechaza.
  const carga = await request.post(`${API}/operations`, { headers: cab, data: {
    lot_id: lotId, event_type: 'incubation_load', event_date: haceDias(7),
    hatchery_params: [{ quantity_loaded: 1 }],
  } })
  const textoCarga = await carga.text()
  expect(carga.status(), textoCarga).toBe(400)
  expect(JSON.parse(textoCarga).rule).toBe('BR-03')

  const ui = await filaEnUI(page, batch.id, ref, lotId)
  await expect(ui.enProceso).toContainText('900')
  await expect(ui.fosa).toHaveText('100')
  await expect(ui.totalNoIncubables.locator('span').first()).toHaveText(/1[.,]000/)
  await expect(ui.fila.locator('td').nth(4), 'D-14: saldo 0 (ni −1 000 ni 900)').toHaveText('0')
  await expect(page.getByTestId('cutover-th-eggs-discarded')).toHaveCount(0)
  await page.screenshot({ path: `${PNG}/h4_fosa_07.png`, fullPage: true })

  ev['H4-FOSA-07'] = {
    batch: batch.id, lote: lotId, ref, opening: h, current: lote.current,
    br03: { carga_1: carga.status(), regla: JSON.parse(textoCarga).rule },
  }
})
