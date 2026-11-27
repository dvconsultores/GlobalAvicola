/**
 * SPEC 018 §10 · BR-03 UNKNOWN FAIL-SAFE — el saldo para cargar es exacto o no autoriza nada.
 *
 * Flujo operativo real (mandato §24): carga inicial V4 con «sucio» vacío ⇒ saldo UNKNOWN en preview y
 * reconciliación ⇒ aprobar/aplicar ⇒ una carga de incubación posterior se DENIEGA con mensaje funcional
 * ⇒ corrección gobernada de la apertura (`dirty = 0`, motivo, auditada) ⇒ saldo exacto 1 000 ⇒ una carga
 * dentro del saldo entra y la que lo excede no ⇒ recarga y re-login conservan el saldo.
 *
 * Evidencia (JSON saneado + capturas, sin tokens) en `audit/ga-hatchery-v4-br03-unknown-failsafe/evidence/e2e_br03/`.
 */
import { expect, test, type APIRequestContext } from '@playwright/test'
import { mkdirSync, writeFileSync } from 'node:fs'
import { API, cabeceraAdmin, cabeceraAprobador, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'
import {
  asegurarFases, corteHaceDias, crearMaestrosCutover, filasPorBu, habilitarCutoverEnRoles,
  habilitarUnidad, haceDias, rellenarPlantilla, type MaestrosCutover,
} from '../test-support/cutover'

test.describe.configure({ mode: 'serial' })

const EV = 'audit/ga-hatchery-v4-br03-unknown-failsafe/evidence/e2e_br03'
const PNG = `${EV}/screenshots`
const MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const MENSAJE = 'No se puede determinar el saldo disponible para cargar'

const ev: Record<string, any> = {}
let cab: { Authorization: string }
let cabAprobador: { Authorization: string }
let maestros: MaestrosCutover
let s: string

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
  ev.regla = 'SPEC 018 §10 · saldo de apertura exacto (los seis KNOWN) o UNKNOWN; con UNKNOWN BR-03 no autoriza cargas'
})

test.afterAll(() => {
  ev.fin = new Date().toISOString()
  mkdirSync(PNG, { recursive: true })
  writeFileSync(`${EV}/e2e_spec018e_br03_unknown.json`, JSON.stringify(ev, null, 2))
})

const reconciliacion = async (request: APIRequestContext, batchId: number, cabecera = cab) =>
  (await request.get(`${API}/cutover-batches/${batchId}/reconciliation`, { headers: cabecera })).json()

test('E2E-BR03-01 «sucio» vacío bloquea BR-03 hasta la corrección gobernada; luego el saldo es exacto', async ({ page, browser, request }) => {
  test.setTimeout(300_000)
  const ref = `E2E-BR03-${s}`

  // ── 1 · carga inicial V4 con `dirty` vacío (10 000 / 8 500 / 200 / — / 100 / fosa 200) ──
  const crear = await request.post(`${API}/cutover-batches`, { headers: cab, data: {
    business_unit: 'hatchery', cutover_datetime: corteHaceDias(42),
  } })
  expect(crear.status(), await crear.text()).toBe(201)
  const batch = await crear.json()
  const plantilla = await (await request.get(
    `${API}/cutover-templates/hatchery?format=xlsx&batch_id=${batch.id}`, { headers: cab })).body()
  const fila = {
    ...filasPorBu('hatchery', maestros, ref)[0],
    eggs_received: 10000, eggs_set: 8500, eggs_non_incubable_oversized: 200, eggs_non_incubable_dirty: null,
    eggs_non_incubable_broken: 100, fertile_eggs_to_pit: 200, eggs_transferred: 0,
  }
  const subida = await request.post(`${API}/cutover-batches/${batch.id}/upload`, { headers: cab, multipart: {
    file: { name: 'cutover_template_hatchery_v4_br03.xlsx', mimeType: MIME_XLSX, buffer: rellenarPlantilla(plantilla, [fila]) },
  } })
  const cuerpo = JSON.parse(await subida.text())
  expect(subida.status(), JSON.stringify(cuerpo)).toBe(200)
  expect(cuerpo.invalid_rows, 'la suma conocida 9 000 ≤ 10 000: la fila es válida').toBe(0)

  // ── 2 · preview: saldo UNKNOWN (nunca 1 000) ──
  const prev = await (await request.get(`${API}/cutover-batches/${batch.id}/preview`, { headers: cab })).json()
  const filaPrev = prev.rows.find((f: any) => f.legacy_lot_code === ref)
  expect(filaPrev.derived.eggs_available_to_set).toBeNull()
  await entrar(page, 'admin')
  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(page.getByTestId(`cutover-preview-available-${filaPrev.row_number}`)).not.toContainText(/\d/)
  await page.screenshot({ path: `${PNG}/br03_01_preview_unknown.png`, fullPage: true })

  // ── 3 · aprobar (otro actor) y aplicar ──
  expect((await request.post(`${API}/cutover-batches/${batch.id}/submit`, { headers: cab })).status()).toBe(200)
  expect((await request.post(`${API}/cutover-batches/${batch.id}/approve`, { headers: cabAprobador })).status()).toBe(200)
  const aplicar = await request.post(`${API}/cutover-batches/${batch.id}/apply`, { headers: cab })
  expect(aplicar.status(), await aplicar.text()).toBe(200)
  let lote = (await reconciliacion(request, batch.id)).lots.find((l: any) => l.legacy_lot_code === ref)
  expect(lote.current.eggs_available_hatchery, 'reconciliación: saldo UNKNOWN').toBeNull()
  const lotId = lote.lot_id as number
  const openingId = lote.opening_id as number
  expect(typeof openingId).toBe('number')

  // ── 4 · nueva carga ⇒ DENY con mensaje funcional (sin nombres técnicos) ──
  const cargar = (cantidad: number) => request.post(`${API}/operations`, { headers: cab, data: {
    lot_id: lotId, event_type: 'incubation_load', event_date: haceDias(7),
    hatchery_params: [{ quantity_loaded: cantidad }],
  } })
  const bloqueada = await cargar(1)
  const cuerpoBloqueo = JSON.parse(await bloqueada.text())
  expect(bloqueada.status(), JSON.stringify(cuerpoBloqueo)).toBe(400)
  expect(cuerpoBloqueo.rule).toBe('CUTOVER_BALANCE_INCOMPLETE')
  expect(cuerpoBloqueo.detail).toContain(MENSAJE)
  expect(cuerpoBloqueo.detail).not.toMatch(/None|null|UNKNOWN|CUTOVER_BALANCE_INCOMPLETE|eggs_/)

  // ── 5 · corrección gobernada: `dirty = 0` (motivo obligatorio, auditada, conserva el original) ──
  const correccion = await request.post(`${API}/opening-balances/${openingId}/corrections`, { headers: cab, data: {
    field: 'eggs_non_incubable_dirty', new_value: 0, reason: 'Se confirma que no hubo huevos sucios al corte',
  } })
  const cuerpoCorreccion = JSON.parse(await correccion.text())
  expect(correccion.status(), JSON.stringify(cuerpoCorreccion)).toBe(201)
  expect(cuerpoCorreccion.old_value, 'el original era UNKNOWN').toBeNull()
  expect(cuerpoCorreccion.new_value).toBe('0')

  // ── 6 · reconciliar: saldo exacto 10 000 − 8 500 − 200 − 0 − 100 − 200 = 1 000 ──
  lote = (await reconciliacion(request, batch.id)).lots.find((l: any) => l.legacy_lot_code === ref)
  expect(lote.opening.hatchery.eggs_non_incubable_dirty_status).toBe('KNOWN')
  expect(lote.current.eggs_available_hatchery).toBe(1000)

  // ── 7-8 · carga dentro del saldo ⇒ ALLOW; exceder el resto ⇒ DENY (BR-03) ──
  const dentro = await cargar(600)
  expect(dentro.status(), await dentro.text()).toBe(201)
  const excede = await cargar(401)
  const cuerpoExcede = JSON.parse(await excede.text())
  expect(excede.status(), JSON.stringify(cuerpoExcede)).toBe(400)
  expect(cuerpoExcede.rule).toBe('BR-03')
  lote = (await reconciliacion(request, batch.id)).lots.find((l: any) => l.legacy_lot_code === ref)
  expect(lote.current.eggs_available_hatchery).toBe(400)

  // ── 9 · recarga ──
  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(page.getByTestId(`cutover-eggs-available-${lotId}`)).toHaveText('400')
  await page.reload()
  await expect(page.getByTestId(`cutover-eggs-available-${lotId}`)).toHaveText('400')
  await page.screenshot({ path: `${PNG}/br03_01_reconciliacion.png`, fullPage: true })

  // ── 10 · re-login ──
  const ctx = await browser.newContext()
  const nueva = await ctx.newPage()
  await entrar(nueva, 'admin')
  await nueva.goto(`/cutover?batch=${batch.id}`)
  await expect(nueva.getByTestId(`cutover-eggs-available-${lotId}`)).toHaveText('400')
  await nueva.screenshot({ path: `${PNG}/br03_01_relogin.png`, fullPage: true })
  await ctx.close()
  const recNueva = (await reconciliacion(request, batch.id, await cabeceraAdmin(request))).lots
    .find((l: any) => l.legacy_lot_code === ref)
  expect(recNueva.current.eggs_available_hatchery).toBe(400)

  ev['BR03-01'] = {
    batch: batch.id, lote: lotId, opening_id: openingId, ref,
    bloqueo: { status: bloqueada.status(), rule: cuerpoBloqueo.rule, detail: cuerpoBloqueo.detail },
    correccion: { old_value: cuerpoCorreccion.old_value, new_value: cuerpoCorreccion.new_value },
    carga_600: dentro.status(), carga_401: { status: excede.status(), rule: cuerpoExcede.rule },
    saldo_final: recNueva.current.eggs_available_hatchery,
  }
})
