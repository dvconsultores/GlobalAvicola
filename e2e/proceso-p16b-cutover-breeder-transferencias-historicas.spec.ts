/**
 * P-16-B · REPRODUCTORAS — Cargas Iniciales v3 (SPEC 014): transferencias históricas.
 */
import { expect, test } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'
import {
  asegurarFases, corteHaceDias, corteParaInput, crearMaestrosCutover, filasPorBu,
  habilitarCutoverEnRoles, habilitarUnidad, haceDias, rellenarPlantilla,
} from '../test-support/cutover'

const PY = resolve('backend/.venv/bin/python')
const MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const NUEVAS = ['historical_transfers_in_males', 'historical_transfers_in_females',
  'historical_transfers_out_males', 'historical_transfers_out_females']

/** Lee un libro con openpyxl (la misma librería con la que `rellenarPlantilla` escribe). */
const LEER = `
import json, sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1])
meta = {str(f[0]).strip(): f[1] for f in wb["Meta"].iter_rows(values_only=True) if f and f[0]}
cab = [c.value for c in wb["Datos"][1] if c.value is not None]
print(json.dumps({"meta": meta, "cabecera": cab}, default=str))
`

/** Degrada la plantilla descargada a la «v2» anterior: Meta retrocedida y sin las 4 columnas. */
const DEGRADAR = `
import json, sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1])
for f in wb["Meta"].iter_rows(min_row=2):
    if str(f[0].value) == "template_version": f[1].value = "v2"
    elif str(f[0].value) == "schema_id": f[1].value = "CUTOVER_BREEDER_V2"
hoja = wb["Datos"]
fuera = [i for i, c in enumerate(hoja[1], start=1) if c.value in json.loads(sys.argv[3])]
for i in sorted(fuera, reverse=True): hoja.delete_cols(i)
wb.save(sys.argv[2])
`

function leerLibro(contenido: Buffer): { meta: Record<string, unknown>; cabecera: string[] } {
  const dir = mkdtempSync(join(tmpdir(), 'ga-ht-'))
  const entrada = join(dir, 'in.xlsx')
  writeFileSync(entrada, contenido)
  return JSON.parse(execFileSync(PY, ['-c', LEER, entrada], { encoding: 'utf8' }))
}

function degradarABreederV2(contenido: Buffer): Buffer {
  const dir = mkdtempSync(join(tmpdir(), 'ga-ht-'))
  writeFileSync(join(dir, 'v3.xlsx'), contenido)
  execFileSync(PY, ['-c', DEGRADAR, join(dir, 'v3.xlsx'), join(dir, 'v2.xlsx'), JSON.stringify(NUEVAS)])
  return readFileSync(join(dir, 'v2.xlsx'))
}

test.describe('P-16 · Cargas Iniciales v3 — reproductoras con transferencias históricas', () => {
  test('breeder: ORI/REC/UNK por la UI, reconciliación sin doble conteo y rechazo de la v2', async ({ page, browser, request }) => {
    test.setTimeout(240_000)
    const j: Record<string, unknown> = { spec: '014', inicio: new Date().toISOString() }

    // ── 1 · precondiciones por API (permisos, BU, fases, maestros) ──
    const cab = await cabeceraAdmin(request)
    await habilitarCutoverEnRoles(request, cab)
    await habilitarUnidad(request, cab, 'breeder')
    await asegurarFases(request, cab)
    const maestros = await crearMaestrosCutover(request, cab, 'breeder')
    const s = sufijo().toUpperCase()

    const ori = `E2E-HT-${s}-ORI`
    const rec = `E2E-HT-${s}-REC`
    const unk = `E2E-HT-${s}-UNK`
    const base = filasPorBu('breeder', maestros, ori)[0]
    const fila = (ref: string, extra: Record<string, unknown>) => ({ ...base, legacy_lot_code: ref, ...extra })
    // Hembras del origen: 9 500 alojadas − 450 mortalidad − 50 descartes = 9 000 vivas.
    const HEMBRAS = {
      birds_placed_females: 9500, historical_mortality_females: 450, historical_culls_females: 50,
      historical_transfers_in_females: 0, historical_transfers_out_females: 0, live_females: 9000,
    }

    const filas = [
      // ORIGEN: 1 300 + 0 − 165 − 0 − 300 = 835 machos vivos.
      fila(ori, {
        birds_placed_males: 1300, historical_mortality_males: 165, historical_culls_males: 0,
        historical_transfers_in_males: 0, historical_transfers_out_males: 300, live_males: 835, ...HEMBRAS,
      }),
      // RECEPTOR: 1 000 + 300 − 100 − 20 − 0 = 1 180 machos; hembras 9 000 − 450 = 8 550.
      fila(rec, {
        birds_placed_males: 1000, historical_transfers_in_males: 300, historical_mortality_males: 100,
        historical_culls_males: 20, historical_transfers_out_males: 0, live_males: 1180,
        birds_placed_females: 9000, historical_transfers_in_females: 0,
        historical_mortality_females: 450, historical_culls_females: 0,
        historical_transfers_out_females: 0, live_females: 8550,
      }),

      // DESCONOCIDO: `historical_transfers_out_males` vacío ⇒ UNKNOWN y saldo no verificable.
      fila(unk, {
        birds_placed_males: 1300, historical_mortality_males: 165, historical_culls_males: 0,
        historical_transfers_in_males: 0, live_males: 900, ...HEMBRAS,
      }),
    ]

    // ── 2 · la pantalla: BU, corte y carga nueva ──
    await entrar(page, 'admin')
    await page.goto('/cutover')
    await page.getByLabel(/Unidad de negocio|Business unit/).selectOption('breeder')
    await page.getByLabel(/Fecha y hora de corte|Cutover date/).fill(corteParaInput(30))
    const creado = page.waitForResponse(r => r.url().includes('/cutover-batches') && r.request().method() === 'POST')
    await page.getByRole('button', { name: /Crear carga|Create load/ }).click()
    const batch = await (await creado).json()
    expect(batch.business_unit).toBe('breeder')
    const cabecera = page.getByTestId('cutover-batch-header')
    await expect(cabecera).toContainText(`#${batch.id}`)

    // ── 3 · la plantilla de ESA carga es v3 (Meta + las 4 columnas nuevas) ──
    const [descarga] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: /Descargar plantilla Excel|Download Excel template/ }).click(),
    ])
    const plantilla = readFileSync(await descarga.path())
    const libro = leerLibro(plantilla)
    expect(libro.meta.template_version, 'la plantilla de la carga debe ser v3').toBe('v3')
    expect(libro.meta.schema_id).toBe('CUTOVER_BREEDER_V3')
    for (const col of NUEVAS) expect(libro.cabecera, `columna ${col} en Datos`).toContain(col)
    j.plantilla = { bytes: plantilla.length, meta: libro.meta }

    // ── 4 · rellenar y subir por la interfaz ──
    const archivo = {
      name: 'cutover_template_breeder_v3.xlsx', mimeType: MIME_XLSX,
      buffer: rellenarPlantilla(plantilla, filas),
    }
    const subida = page.waitForResponse(r => r.url().includes('/upload'))
    await page.getByTestId('cutover-file-input').setInputFiles(archivo)
    const respSubida = await subida
    const cuerpo = await respSubida.json()
    expect(respSubida.status(), JSON.stringify(cuerpo)).toBe(200)
    expect(cuerpo.status).toBe('validated')
    expect(cuerpo.invalid_rows).toBe(0)
    expect(cuerpo.source_type).toBe('XLSX')
    await expect(page.getByTestId('cutover-errors')).toHaveCount(0)

    // ── 5 · preview por la UI y por API (un solo saldo no verificable: UNK) ──
    const preview = page.getByTestId('cutover-preview')
    await expect(preview).toBeVisible()
    for (const ref of [ori, rec, unk]) await expect(preview).toContainText(ref)
    const prev = await (await request.get(`${API}/cutover-batches/${batch.id}/preview`, { headers: cab })).json()
    const der = (ref: string) => prev.rows.find((f: any) => f.legacy_lot_code === ref).derived.balance_check
    j.preview = { summary: prev.summary, balance: [der(ori), der(rec), der(unk)] }
    expect(prev.summary.balance_not_fully_verifiable_rows).toBe(1)
    expect(der(unk)).toEqual({ males: 'NOT_FULLY_VERIFIABLE', females: 'CONSISTENT' })
    expect(der(ori).males).toBe('CONSISTENT')
    expect(der(rec).males).toBe('CONSISTENT')

    // ── 6 · enviar, aprobar con OTRO actor y aplicar ──
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
    for (const ref of [ori, rec, unk]) await expect(reconciliacion).toContainText(ref)
    await expect(page.getByTestId('cutover-applied')).toBeVisible()

    // ── 7 · los tres lotes creados y su opening (transferencias persistidas) ──
    const items = await (await request.get(`${API}/cutover-batches/${batch.id}/items`, { headers: cab })).json()
    const lote = (ref: string) => items.items.find((i: any) => i.legacy_lot_reference === ref)?.lot_id as number
    const [idOri, idRec, idUnk] = [lote(ori), lote(rec), lote(unk)]
    expect([idOri, idRec, idUnk].every(Boolean), JSON.stringify(items.items)).toBe(true)
    const ob = async (id: number) =>
      (await (await request.get(`${API}/lots/${id}`, { headers: cab })).json()).opening_balance
    const [bOri, bRec, bUnk] = [await ob(idOri), await ob(idRec), await ob(idUnk)]
    j.lotes = { ori: bOri, rec: bRec, unk: bUnk }
    expect(bOri.initial_male_count).toBe(835)
    expect(bOri.initial_female_count).toBe(9000)
    expect(bOri.placed_male_count).toBe(1300)
    expect(bOri.accumulated_transfers_out_male).toBe(300)
    expect(bOri.accumulated_transfers_in_male).toBe(0)
    expect(bOri.transfers_in_status).toBe('KNOWN')
    expect(bOri.transfers_out_status).toBe('KNOWN')
    expect(bOri.template_version).toBe('v3')

    expect(bRec.initial_male_count).toBe(1180)
    expect(bRec.placed_male_count).toBe(1000)
    expect(bRec.accumulated_transfers_in_male).toBe(300)
    expect(bRec.accumulated_transfers_out_male).toBe(0)
    // UNKNOWN no se degrada a «0 conocido»: NULL y estado UNKNOWN.
    expect(bUnk.accumulated_transfers_out_male).toBeNull()
    expect(bUnk.transfers_out_status).toBe('UNKNOWN')

    // ── 8 · un evento post-corte en el ORIGEN no vuelve a restar lo transferido ──
    const mov = await request.post(`${API}/operations`, { headers: cab, data: {
      lot_id: idOri, event_type: 'mortality_recording', event_date: haceDias(7),
      bird_movements: [{ sex: 'male', quantity: 15, avg_weight: 3600 }],
    } })
    expect(mov.status(), await mov.text()).toBe(201)
    const recApi = `${API}/cutover-batches/${batch.id}/reconciliation`
    const rec1 = await (await request.get(recApi, { headers: cab })).json()
    const loteRec = (ref: string, fuente: any) => fuente.lots.find((l: any) => l.legacy_lot_code === ref)
    const [rOri, rRec, rUnk] = [loteRec(ori, rec1), loteRec(rec, rec1), loteRec(unk, rec1)]
    j.reconciliacion = { ori: rOri, rec: rRec, unk: rUnk }
    expect(rOri.opening.live).toBe(9835)
    expect(rOri.post.mortality).toBe(15)
    expect(rOri.current_live).toBe(9820)
    expect(rOri.current_live).toBe(rOri.opening.live - 15)
    expect(rOri.opening.historical_transfers_out).toBe(300)
    expect(rOri.opening.historical_transfers_in).toBe(0)
    expect(rOri.opening.transfers_out_status).toBe('KNOWN')
    expect(rOri.opening.transfers_in_status).toBe('KNOWN')
    expect(rRec.opening.historical_transfers_in).toBe(300)
    expect(rRec.current_live).toBe(1180 + 8550)
    expect(rUnk.opening.historical_transfers_out).toBeNull()
    expect(rUnk.opening.transfers_out_status).toBe('UNKNOWN')
    // ── 9 · refresco y re-login: la reconciliación es persistente ──
    await page.reload()
    await expect(page.getByTestId('cutover-reconciliation')).toBeVisible()
    for (const ref of [ori, rec, unk]) await expect(page.getByTestId('cutover-reconciliation')).toContainText(ref)
    const ctx2 = await browser.newContext()
    const p3 = await ctx2.newPage()
    await entrar(p3, 'admin')
    await p3.goto(`/cutover?batch=${batch.id}`)
    await expect(p3.getByTestId('cutover-batch-header')).toContainText(/Aplicado|Applied/)
    for (const ref of [ori, rec, unk]) await expect(p3.getByTestId('cutover-reconciliation')).toContainText(ref)
    await ctx2.close()
    const cab2 = await cabeceraAdmin(request)
    const rec2 = await (await request.get(recApi, { headers: cab2 })).json()
    j.persistencia = { ori: loteRec(ori, rec2).current_live, rec: loteRec(rec, rec2).current_live }
    expect(loteRec(ori, rec2).current_live).toBe(9820)
    expect(loteRec(rec, rec2).current_live).toBe(9730)
    // ── 10 · negativo: la plantilla v2 anterior se rechaza con «descargue la v3» ──
    const b2 = await request.post(`${API}/cutover-batches`, { headers: cab, data: {
      business_unit: 'breeder', cutover_datetime: corteHaceDias(31),
    } })
    const texto2 = await b2.text()
    expect(b2.status(), texto2).toBe(201)
    const batch2 = JSON.parse(texto2)
    const v2 = degradarABreederV2(plantilla)
    j.plantillaV2 = { bytes: v2.length }
    const rechazo = await request.post(`${API}/cutover-batches/${batch2.id}/upload`, {
      headers: cab,
      multipart: { file: { name: 'cutover_template_breeder_v2.xlsx', mimeType: MIME_XLSX, buffer: v2 } },
    })
    const textoRechazo = await rechazo.text()
    j.rechazoV2 = { status: rechazo.status() }
    expect(rechazo.status(), textoRechazo).toBe(422)
    expect(textoRechazo).toContain('TEMPLATE_VERSION_UNSUPPORTED')
    expect(textoRechazo).toContain('v3')
    // ── 11 · journal sanitizado (solo cifras y códigos, sin secretos) ──
    j.fin = new Date().toISOString()
    mkdirSync('test-results/spec-014', { recursive: true })
    writeFileSync('test-results/spec-014/e2e-breeder-transferencias.json', JSON.stringify(j, null, 2))
  })
})

