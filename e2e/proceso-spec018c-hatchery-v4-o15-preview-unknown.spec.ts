/**
 * SPEC 018 §8 · RESIDUAL O-15 — agregado del preview y semántica UNKNOWN (AC-O15-07).
 *
 * Certifica por API y por interfaz que el **preview** de un batch de incubadora nunca presenta una
 * suma parcial como si fuera el total (D-18/D-19/D-20):
 *
 * - **E2E-O15-01** dos procesos en el mismo batch: A (10 000 / 9 000 / transferidos 8 100 ⇒ en proceso
 *   900) y B (idéntico pero `eggs_transferred` **vacío** ⇒ UNKNOWN; desde SPEC 018 §9 · OD-HATCH-V4-02
 *   la fosa es PRE-CARGA y ya no interviene en «en proceso»). La fila A muestra
 *   900, la fila B «UNKNOWN», el chip total «UNKNOWN» (jamás 900) y la API publica
 *   `eggs_in_process = null` con `eggs_in_process_status = 'UNKNOWN'` y `eggs_in_process_unknown_rows = 1`.
 * - **E2E-O15-02** completar el UNKNOWN con un **0 conocido**: se vuelve a subir al **mismo batch**
 *   (el batch sigue en estado `validated`, que es cargable: la subida recrea el staging) ⇒ la fila B
 *   pasa a 1 000, el chip al total 1 900 y la API a `KNOWN`.
 * - **E2E-O15-03** control de cero: una sola fila con fosa 0 conocido y transferidos 9 000 ⇒ en
 *   proceso 0, que se ve como **0** (ni UNKNOWN ni celda vacía).
 *
 * Los cortes son propios (47 y 49 días atrás), posteriores a las fechas de la fila canónica de la BU
 * (recepción 50 / carga 48 días atrás) para no caer en `DATE_ORDER_INVALID`, y distintos de los que
 * usan los specs 018/018b. La evidencia (JSON saneado + capturas, sin tokens) queda en
 * `audit/ga-hatchery-v4-o15/evidence/e2e_o15/`.
 */
import { expect, test, type APIRequestContext } from '@playwright/test'
import { mkdirSync, writeFileSync } from 'node:fs'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'
import {
  asegurarFases, corteHaceDias, crearMaestrosCutover, filasPorBu, habilitarCutoverEnRoles,
  habilitarUnidad, haceDias, rellenarPlantilla, type MaestrosCutover,
} from '../test-support/cutover'

test.describe.configure({ mode: 'serial' })

const EV = 'audit/ga-hatchery-v4-o15/evidence/e2e_o15'
const PNG = `${EV}/screenshots`
const MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

const ev: Record<string, any> = {}
let cab: { Authorization: string }
let maestros: MaestrosCutover
let s: string

/** Fila V4 canónica de la BU (recibidos 10 000 / cargados 9 000); cada escenario añade su desglose. */
const filaV4 = (ref: string, extra: Record<string, unknown> = {}): Record<string, unknown> => ({
  ...filasPorBu('hatchery', maestros, ref)[0], ...extra,
})

/**
 * Fila con no incubables y fosa en 0 conocido y transferidos `8 000 + valor` (o vacío si `valor` es
 * `null`) ⇒ en proceso = 9 000 − transferidos (SPEC 018 §9 · D-23: `set − transferred`). `valor` 100 ⇒
 * 900; `0` ⇒ 1 000; `null` ⇒ UNKNOWN. La fosa (PRE-CARGA) ya no vuelve UNKNOWN el en proceso.
 */
const filaConFosa = (ref: string, valor: number | null): Record<string, unknown> => filaV4(ref, {
  eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
  eggs_transferred: valor === null ? null : 8000 + valor, fertile_eggs_to_pit: 0,
})

/** Batch nuevo por API. Cada escenario usa un corte propio: la misma carga y corte es DUPLICATE_UPLOAD. */
async function crearBatch(request: APIRequestContext, corteDias: number): Promise<any> {
  const r = await request.post(`${API}/cutover-batches`, { headers: cab, data: {
    business_unit: 'hatchery', cutover_datetime: corteHaceDias(corteDias),
  } })
  const texto = await r.text()
  expect(r.status(), texto).toBe(201)
  return JSON.parse(texto)
}

/** Sube filas XLSX sobre la **plantilla descargada del batch** (nunca se fabrica la cabecera). */
async function subirFilasXlsx(request: APIRequestContext, batchId: number, filas: Record<string, unknown>[], nombre: string) {
  const plantilla = await request.get(`${API}/cutover-templates/hatchery?format=xlsx&batch_id=${batchId}`, { headers: cab })
  expect(plantilla.status(), await plantilla.text()).toBe(200)
  const subida = await request.post(`${API}/cutover-batches/${batchId}/upload`, {
    headers: cab,
    multipart: { file: { name: nombre, mimeType: MIME_XLSX, buffer: rellenarPlantilla(await plantilla.body(), filas) } },
  })
  const texto = await subida.text()
  expect(subida.status(), texto).toBe(200)
  const cuerpo = JSON.parse(texto)
  if (cuerpo.invalid_rows > 0) {
    // Sin esto un rojo del parser/validador se queda en «0 filas válidas» sin decir por qué.
    const detalle = await request.get(`${API}/cutover-batches/${batchId}/validation`, { headers: cab })
    throw new Error(`carga con filas inválidas: ${await detalle.text()}`)
  }
  return cuerpo
}

const preview = async (request: APIRequestContext, batchId: number) =>
  (await request.get(`${API}/cutover-batches/${batchId}/preview`, { headers: cab })).json()

/** `row_number` del preview por referencia de lote (la clave de los `data-testid` de la celda). */
const filasPorRef = (prev: any): Record<string, any> =>
  Object.fromEntries(prev.rows.map((f: any) => [f.legacy_lot_code, f]))

/**
 * Abre la pantalla de Cargas Iniciales con el preview del batch (`?batch=`) y devuelve los
 * localizadores de las piezas de O-15: contenedor, chip del total y la celda derivada por fila.
 */
async function abrirPreview(page: any, batchId: number) {
  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batchId}`)
  const contenedor = page.getByTestId('cutover-preview')
  await expect(contenedor).toBeVisible()
  return {
    contenedor,
    chip: page.getByTestId('cutover-chip-eggs-in-process'),
    cabecera: page.getByTestId('cutover-th-preview-in-process'),
    celda: (rowNumber: number) => page.getByTestId(`cutover-preview-in-process-${rowNumber}`),
    total: (rowNumber: number) => page.getByTestId(`cutover-preview-total-${rowNumber}`),
  }
}

test.beforeAll(async ({ request }) => {
  mkdirSync(PNG, { recursive: true })
  cab = await cabeceraAdmin(request)
  await habilitarCutoverEnRoles(request, cab)
  await habilitarUnidad(request, cab, 'hatchery')
  await asegurarFases(request, cab)
  maestros = await crearMaestrosCutover(request, cab, 'hatchery')
  s = sufijo().toUpperCase()
  ev.inicio = new Date().toISOString()
  ev.regla = 'SPEC 018 §8 · D-18/D-19/D-20: el total de una métrica con UNKNOWN es UNKNOWN (null), nunca una suma parcial'
  ev.maestros = maestros
})

test.afterAll(() => {
  ev.fin = new Date().toISOString()
  mkdirSync(PNG, { recursive: true })
  writeFileSync(`${EV}/e2e_spec018c_o15.json`, JSON.stringify(ev, null, 2))
})

test('E2E-O15-01 dos procesos (A conocido, B con transferidos vacío) ⇒ fila A 900, fila B UNKNOWN y chip UNKNOWN', async ({ page, request }) => {
  test.setTimeout(240_000)
  const refA = `E2E-O15-${s}-A`
  const refB = `E2E-O15-${s}-B`
  const batch = await crearBatch(request, 47)

  const cuerpo = await subirFilasXlsx(request, batch.id, [
    filaConFosa(refA, 100),
    filaConFosa(refB, null),
  ], 'cutover_template_hatchery_v4_o15_a_b.xlsx')
  expect(cuerpo.valid_rows, JSON.stringify(cuerpo)).toBe(2)
  expect(cuerpo.invalid_rows, 'las dos filas deben ser válidas').toBe(0)

  // API: el agregado del lote propaga UNKNOWN (nunca la suma parcial 900 + 0).
  const prev = await preview(request, batch.id)
  expect(prev.summary.eggs_in_process, 'una fila UNKNOWN ⇒ el total es UNKNOWN, jamás 900').toBeNull()
  expect(prev.summary.eggs_in_process_status).toBe('UNKNOWN')
  expect(prev.summary.eggs_in_process_unknown_rows).toBe(1)
  const porRef = filasPorRef(prev)
  expect(porRef[refA].derived.eggs_in_process, '9 000 − 8 000 − 100').toBe(900)
  expect(porRef[refB].derived.eggs_in_process, 'transferidos UNKNOWN ⇒ en proceso UNKNOWN').toBeNull()
  const rowA = porRef[refA].row_number
  const rowB = porRef[refB].row_number

  // UI: la fila UNKNOWN se ve como UNKNOWN y el chip no publica la suma parcial.
  const ui = await abrirPreview(page, batch.id)
  await expect(ui.cabecera, 'columna derivada «Huevos en proceso»').toHaveCount(1)
  await expect(ui.celda(rowA)).toHaveText(/900/)
  await expect(ui.celda(rowA)).not.toHaveText('UNKNOWN')
  await expect(ui.celda(rowB)).toHaveText('UNKNOWN')
  await expect(ui.chip).toContainText('UNKNOWN')
  await expect(ui.chip, 'el chip no puede enseñar 900 (suma parcial) como total').not.toContainText(/900/)
  await expect(ui.chip).not.toContainText(/1[.,]900/)
  await page.screenshot({ path: `${PNG}/e2e_o15_01_preview_unknown.png`, fullPage: true })

  ev['E2E-O15-01'] = {
    batch: batch.id, filas: { A: refA, B: refB }, row_numbers: { A: rowA, B: rowB },
    validacion: { total: cuerpo.total_rows, validas: cuerpo.valid_rows, invalidas: cuerpo.invalid_rows },
    summary: {
      eggs_in_process: prev.summary.eggs_in_process,
      eggs_in_process_status: prev.summary.eggs_in_process_status,
      eggs_in_process_unknown_rows: prev.summary.eggs_in_process_unknown_rows,
    },
    derivados: { A: porRef[refA].derived.eggs_in_process, B: porRef[refB].derived.eggs_in_process },
    ui: { chip: (await ui.chip.innerText()).trim(), A: (await ui.celda(rowA).innerText()).trim(), B: (await ui.celda(rowB).innerText()).trim() },
  }
})

test('E2E-O15-02 completar el UNKNOWN con 0 conocido (re-subida al MISMO batch) ⇒ fila B 1 000 y chip 1 900', async ({ page, request }) => {
  test.setTimeout(240_000)
  const refA = `E2E-O15-${s}-A`
  const refB = `E2E-O15-${s}-B`
  // Camino elegido: **re-subida al mismo batch**. `subir_y_validar` acepta los estados
  // DRAFT/VALIDATING/VALIDATED y recrea el staging de forma idempotente, así que un batch validado y
  // no enviado admite una carga corregida; no hace falta un segundo batch con otro corte.
  // El corte de este escenario es propio (48 días atrás, distinto del de O15-01) para que la misma
  // carga no caiga en DUPLICATE_UPLOAD entre dos batches y para no pisar los cortes de 018/018b.
  const batch = await crearBatch(request, 48)

  const primera = await subirFilasXlsx(request, batch.id, [filaConFosa(refA, 100), filaConFosa(refB, null)],
    'cutover_template_hatchery_v4_o15_a_b.xlsx')
  expect(primera.invalid_rows, JSON.stringify(primera)).toBe(0)
  const antes = await preview(request, batch.id)
  expect(antes.summary.eggs_in_process_status).toBe('UNKNOWN')
  expect(antes.summary.eggs_in_process).toBeNull()

  const segunda = await subirFilasXlsx(request, batch.id, [filaConFosa(refA, 100), filaConFosa(refB, 0)],
    'cutover_template_hatchery_v4_o15_a_b_corregido.xlsx')
  expect(segunda.valid_rows, JSON.stringify(segunda)).toBe(2)
  expect(segunda.invalid_rows).toBe(0)

  const despues = await preview(request, batch.id)
  expect(despues.summary.eggs_in_process, '900 + (9 000 − 8 000 − 0) = 1 900').toBe(1900)
  expect(despues.summary.eggs_in_process_status).toBe('KNOWN')
  expect(despues.summary.eggs_in_process_unknown_rows).toBe(0)
  const porRef = filasPorRef(despues)
  expect(porRef[refA].derived.eggs_in_process).toBe(900)
  expect(porRef[refB].derived.eggs_in_process, 'transferidos 8 000 conocidos ⇒ set − transferidos').toBe(1000)
  const rowA = porRef[refA].row_number
  const rowB = porRef[refB].row_number

  const ui = await abrirPreview(page, batch.id)
  await expect(ui.celda(rowA)).toHaveText(/900/)
  await expect(ui.celda(rowB)).toHaveText(/1[.,]000/)
  await expect(ui.celda(rowB)).not.toHaveText('UNKNOWN')
  await expect(ui.chip, 'el chip pasa al total numérico 1 900').toContainText(/1[.,]900/)
  await expect(ui.chip).not.toContainText('UNKNOWN')
  await page.screenshot({ path: `${PNG}/e2e_o15_02_preview_completado.png`, fullPage: true })

  ev['E2E-O15-02'] = {
    batch: batch.id,
    camino: 're-subida al MISMO batch (estados cargables DRAFT/VALIDATING/VALIDATED: el staging se recrea)',
    filas: { A: refA, B: refB }, row_numbers: { A: rowA, B: rowB },
    antes: { eggs_in_process: antes.summary.eggs_in_process, status: antes.summary.eggs_in_process_status },
    despues: {
      eggs_in_process: despues.summary.eggs_in_process,
      eggs_in_process_status: despues.summary.eggs_in_process_status,
      eggs_in_process_unknown_rows: despues.summary.eggs_in_process_unknown_rows,
    },
    derivados: { A: porRef[refA].derived.eggs_in_process, B: porRef[refB].derived.eggs_in_process },
    ui: { chip: (await ui.chip.innerText()).trim(), A: (await ui.celda(rowA).innerText()).trim(), B: (await ui.celda(rowB).innerText()).trim() },
  }
})

test('E2E-O15-03 control de cero: una fila con fosa 0 y transferidos 9 000 ⇒ en proceso 0 (chip y fila en 0)', async ({ page, request }) => {
  test.setTimeout(240_000)
  const ref = `E2E-O15-${s}-C`
  const batch = await crearBatch(request, 49)
  const cuerpo = await subirFilasXlsx(request, batch.id, [filaV4(ref, {
    // Fechas propias (más antiguas que las canónicas) para que el corte de 49 días atrás quede
    // **después** de la carga: con las canónicas (carga 48 días atrás) el corte sería anterior y la
    // fila caería en `DATE_ORDER_INVALID`.
    reception_date: haceDias(56), set_date: haceDias(54), expected_hatch_date: haceDias(33),
    eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
    eggs_transferred: 9000, fertile_eggs_to_pit: 0,
  })], 'cutover_template_hatchery_v4_o15_cero.xlsx')
  expect(cuerpo.valid_rows, JSON.stringify(cuerpo)).toBe(1)
  expect(cuerpo.invalid_rows).toBe(0)

  const prev = await preview(request, batch.id)
  expect(prev.summary.eggs_in_process, 'un cero conocido es 0, no UNKNOWN (D-18)').toBe(0)
  expect(prev.summary.eggs_in_process_status).toBe('KNOWN')
  expect(prev.summary.eggs_in_process_unknown_rows).toBe(0)
  const porRef = filasPorRef(prev)
  expect(porRef[ref].derived.eggs_in_process).toBe(0)
  const row = porRef[ref].row_number

  const ui = await abrirPreview(page, batch.id)
  await expect(ui.celda(row), 'la fila muestra 0').toHaveText('0')
  await expect(ui.chip, 'el chip muestra 0, no UNKNOWN').toContainText(/:\s*0$/)
  await expect(ui.chip).not.toContainText('UNKNOWN')
  await page.screenshot({ path: `${PNG}/e2e_o15_03_preview_cero.png`, fullPage: true })

  ev['E2E-O15-03'] = {
    batch: batch.id, fila: ref, row_number: row,
    summary: {
      eggs_in_process: prev.summary.eggs_in_process,
      eggs_in_process_status: prev.summary.eggs_in_process_status,
      eggs_in_process_unknown_rows: prev.summary.eggs_in_process_unknown_rows,
    },
    derivado: porRef[ref].derived.eggs_in_process,
    ui: { chip: (await ui.chip.innerText()).trim(), fila: (await ui.celda(row).innerText()).trim() },
  }
})
