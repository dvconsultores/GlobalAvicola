/**
 * SPEC 006 · flujo E2E de «Cargas Iniciales» por la interfaz, común a las cuatro BU.
 *
 * login → Cargas Iniciales → elegir BU → fecha de corte → crear carga → descargar plantilla
 * (XLSX o CSV, la de ESA carga) → rellenar fixture → subir → validación 0 errores → preview →
 * enviar → cambiar de actor → aprobar → aplicar → reconciliación → navegar a la entidad
 * operativa → primer evento post-corte → verificar resultado. Nada se certifica por transitividad:
 * cada spec llama a `flujoPorBu` con su BU y guarda su propio journal.
 */
import { expect, type APIRequestContext, type Browser, type Page } from '@playwright/test'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { entrar } from './auth'
import { API, cabeceraAdmin, cabeceraAprobador, sufijo } from './e2e-api'
import {
  asegurarFases, construirCsv, corteParaInput, crearMaestrosCutover, filasPorBu, habilitarCutoverEnRoles,
  habilitarUnidad, primerEventoPostCorte, rellenarPlantilla, type Bu,
} from './cutover'

const JOURNAL_DIR = resolve(process.cwd(), 'test-results', 'spec-006')
const DIAS_CORTE = 30

function journal(nombre: string, payload: unknown) {
  mkdirSync(JOURNAL_DIR, { recursive: true })
  writeFileSync(resolve(JOURNAL_DIR, `${nombre}.json`), JSON.stringify(payload, null, 2))
}

async function descargar(page: Page, boton: RegExp): Promise<Buffer> {
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: boton }).click(),
  ])
  const ruta = await download.path()
  expect(ruta, 'la descarga debe producir un archivo').toBeTruthy()
  return readFileSync(ruta as string)
}

/**
 * GA-CUTOVER-S3-01 · regresión visual: un botón `primary` debe pintar fondo de marca.
 *
 * Si falta el bloque `@theme` con `--color-brand-500` en `index.css`, Tailwind v4 no genera
 * `bg-brand-500` y el botón queda transparente con texto blanco (invisible). Se verifica el
 * estilo COMPUTADO (no la clase): ni transparente ni blanco, y con el teal de marca (#5a9bba).
 */
async function verificarFondoPrimary(page: Page, boton: RegExp, paso: string) {
  const el = page.getByRole('button', { name: boton }).first()
  await expect(el, `${paso}: el botón primary debe estar visible`).toBeVisible()
  const bg = await el.evaluate(n => getComputedStyle(n).backgroundColor)
  expect(bg, `${paso}: el fondo del botón primary no puede ser transparente`).not.toBe('rgba(0, 0, 0, 0)')
  expect(bg, `${paso}: el fondo del botón primary no puede ser transparente`).not.toBe('transparent')
  const canales = bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/)
  if (!canales) throw new Error(`${paso}: background-color computado inesperado (${bg})`)
  const [r, g, b] = [Number(canales[1]), Number(canales[2]), Number(canales[3])]
  expect(r + g + b, `${paso}: el fondo del botón primary no puede ser blanco (${bg})`).toBeLessThan(700)
  // Teal de marca #5a9bba = rgb(90, 155, 186): componente azul dominante sobre rojo y verde.
  expect(r, `${paso}: fondo no es el teal de marca (${bg})`).toBeLessThan(g)
  expect(g, `${paso}: fondo no es el teal de marca (${bg})`).toBeLessThan(b)
}

export interface OpcionesFlujo {
  bu: Bu
  formato: 'xlsx' | 'csv'
  /** Anchos de pantalla a certificar sin desborde horizontal (mandato §36). */
  anchos?: number[]
}

export async function flujoPorBu(page: Page, browser: Browser, request: APIRequestContext, opciones: OpcionesFlujo) {
  const { bu, formato } = opciones
  const pasos: Record<string, unknown> = { bu, formato, inicio: new Date().toISOString() }

  // ── Precondiciones por API (permisos, BU habilitada, fases, maestros del escenario) ──
  const cab = await cabeceraAdmin(request)
  await habilitarCutoverEnRoles(request, cab)
  await habilitarUnidad(request, cab, bu)
  await asegurarFases(request, cab)
  const maestros = await crearMaestrosCutover(request, cab, bu)
  const ref = `E2E-${bu.toUpperCase()}-${sufijo().toUpperCase()}`
  pasos.maestros = maestros
  pasos.ref = ref

  // ── 1 · login y pantalla ──
  await entrar(page, 'admin')
  await page.goto('/cutover')
  await expect(page.getByLabel(/Unidad de negocio|Business unit/)).toBeVisible()

  // ── 2 · BU + corte + crear carga ──
  await page.getByLabel(/Unidad de negocio|Business unit/).selectOption(bu)
  await page.getByLabel(/Fecha y hora de corte|Cutover date/).fill(corteParaInput(DIAS_CORTE))

  // 2.0 · GA-CUTOVER-S3-01: el CTA primary de la pantalla pinta fondo de marca (regresión visual).
  await verificarFondoPrimary(page, /^Descargar plantilla$|^Download template$/, 'descarga temprana')
  pasos.fondo_primary = 'ok'

  // 2.a · SPEC 010: la plantilla es descubrible y descargable ANTES de crear la carga.
  const plantillaTemprana = await descargar(page, /^Descargar plantilla$|^Download template$/)
  expect(plantillaTemprana.length, 'la plantilla temprana debe descargarse').toBeGreaterThan(0)
  pasos.plantilla_temprana = { bytes: plantillaTemprana.length }

  const creado = page.waitForResponse(r => r.url().includes('/cutover-batches') && r.request().method() === 'POST')
  await page.getByRole('button', { name: /Crear carga|Create load/ }).click()
  const batch = await (await creado).json()
  expect(batch.business_unit).toBe(bu)
  pasos.batch = batch
  const cabecera = page.getByTestId('cutover-batch-header')
  await expect(cabecera).toBeVisible()
  await expect(cabecera).toContainText(`#${batch.id}`)

  // ── 3 · descargar la plantilla de ESA carga (el servidor fija la BU por batch_id) ──
  const esperaPlantilla = page.waitForResponse(r => r.url().includes(`/cutover-templates/${bu}`) && r.url().includes(`batch_id=${batch.id}`))
  const plantilla = await descargar(page, formato === 'csv' ? /Descargar plantilla CSV|Download CSV template/ : /Descargar plantilla Excel|Download Excel template/)
  const respPlantilla = await esperaPlantilla
  expect(respPlantilla.status()).toBe(200)
  pasos.plantilla = { bytes: plantilla.length, contentType: respPlantilla.headers()['content-type'] }

  // ── 4 · rellenar y subir ──
  const filas = filasPorBu(bu, maestros, ref)
  const archivo = formato === 'csv'
    ? { name: 'carga.csv', mimeType: 'text/csv', buffer: construirCsv(plantilla.toString('utf8'), filas) }
    : { name: `cutover_template_${bu}_v2.xlsx`, mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', buffer: rellenarPlantilla(plantilla, filas) }
  const subida = page.waitForResponse(r => r.url().includes('/upload'))
  await page.getByTestId('cutover-file-input').setInputFiles(archivo)
  const respSubida = await subida
  const cuerpoSubida = await respSubida.json()
  pasos.upload = { status: respSubida.status(), body: cuerpoSubida }
  expect(respSubida.status(), JSON.stringify(cuerpoSubida)).toBe(200)
  expect(cuerpoSubida.status).toBe('validated')
  expect(cuerpoSubida.invalid_rows).toBe(0)
  expect(cuerpoSubida.source_type).toBe(formato.toUpperCase())

  // ── 5 · validación 0 errores + preview por BU ──
  await expect(page.getByTestId('cutover-errors')).toHaveCount(0)
  const preview = page.getByTestId('cutover-preview')
  await expect(preview).toBeVisible()
  await expect(preview).toContainText(ref)
  if (bu === 'hatchery') await expect(preview).toContainText(/10[.,]000/)
  else await expect(preview).toContainText(/10[.,]000/)
  pasos.preview = await preview.innerText()

  // Responsive (mandato §36): sin desborde horizontal en 360 / 390 / escritorio.
  for (const ancho of opciones.anchos ?? [360, 390, 1280]) {
    await page.setViewportSize({ width: ancho, height: 900 })
    const desborde = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(desborde, `desborde horizontal a ${ancho}px`).toBeLessThanOrEqual(1)
  }
  await page.setViewportSize({ width: 1280, height: 900 })

  // ── 6 · enviar a aprobación ──
  const envio = page.waitForResponse(r => r.url().includes('/submit'))
  await page.getByRole('button', { name: /Enviar a aprobación|Submit for approval/ }).click()
  expect((await envio).status()).toBe(200)
  await expect(cabecera).toContainText(/Pendiente de aprobación|Pending approval/)

  // ── 7 · cambiar de actor: el aprobador aprueba por la interfaz ──
  const contextoAprobador = await browser.newContext()
  const pagina2 = await contextoAprobador.newPage()
  await entrar(pagina2, 'approver')
  await pagina2.goto(`/cutover?batch=${batch.id}`)
  await expect(pagina2.getByTestId('cutover-batch-header')).toContainText(`#${batch.id}`)
  const aprobacion = pagina2.waitForResponse(r => r.url().includes('/approve'))
  await pagina2.getByRole('button', { name: /^Aprobar$|^Approve$/ }).click()
  expect((await aprobacion).status()).toBe(200)
  await expect(pagina2.getByTestId('cutover-batch-header')).toContainText(/Aprobado|Approved/)
  await contextoAprobador.close()

  // ── 8 · aplicar (la carga sobrevive a la recarga: ?batch=) ──
  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(cabecera).toContainText(/Aprobado|Approved/)
  // GA-CUTOVER-S3-01: el CTA «Aplicar» (primary) también pinta fondo de marca.
  await verificarFondoPrimary(page, /^Aplicar$|^Apply$/, 'aplicar')
  const aplicacion = page.waitForResponse(r => r.url().includes('/apply'))
  await page.getByRole('button', { name: /^Aplicar$|^Apply$/ }).click()
  const respApply = await aplicacion
  expect(respApply.status(), await respApply.text()).toBe(200)
  await expect(cabecera).toContainText(/Aplicado|Applied/)

  // ── 9 · reconciliación visible y lotes creados ──
  const reconciliacion = page.getByTestId('cutover-reconciliation')
  await expect(reconciliacion).toBeVisible()
  await expect(reconciliacion).toContainText(ref)
  await expect(page.getByTestId('cutover-applied')).toBeVisible()
  const items = await (await request.get(`${API}/cutover-batches/${batch.id}/items`, { headers: cab })).json()
  const lotId = items.items.find((i: any) => i.legacy_lot_reference === ref).lot_id as number
  const recAntes = await (await request.get(`${API}/cutover-batches/${batch.id}/reconciliation`, { headers: cab })).json()
  pasos.reconciliacion_antes = recAntes

  // ── 10 · navegar a la entidad operativa (lote migrado) ──
  await page.getByRole('link', { name: /Ver lote|View lot/ }).first().click()
  await expect(page).toHaveURL(new RegExp(`/lots/${lotId}$`))
  await expect(page.getByText(ref).first()).toBeVisible()
  await page.goBack()
  await page.getByRole('link', { name: /Registrar primer evento|Record first event/ }).first().click()
  await expect(page).toHaveURL(new RegExp(`/operations/new\\?lot_id=${lotId}$`))

  // ── 11 · primer evento post-corte real y verificación en la reconciliación ──
  const evento = await primerEventoPostCorte(request, cab, bu, lotId, maestros)
  const cuerpoEvento = await evento.text()
  pasos.primer_evento = { status: evento.status(), body: cuerpoEvento.slice(0, 400) }
  expect(evento.status(), cuerpoEvento).toBe(201)
  const rec = await (await request.get(`${API}/cutover-batches/${batch.id}/reconciliation`, { headers: cab })).json()
  const fila = rec.lots.find((l: any) => l.lot_id === lotId)
  pasos.reconciliacion_despues = fila
  if (bu === 'hatchery') {
    expect(fila.post.eggs_loaded).toBe(1000)
    expect(fila.current.eggs_available_hatchery).toBe(0)
    expect(fila.current.eggs_in_process).toBe(9900)
  } else if (bu === 'breeder') {
    expect(fila.post.eggs_collected).toBe(7000)
    expect(fila.lifetime.egg_production).toBe(187000)
    expect(fila.current_live).toBe(10000)
  } else {
    expect(fila.opening.live).toBe(10000)
    expect(fila.post.mortality).toBe(35)
    expect(fila.current_live).toBe(9965)
    expect(fila.current_live).not.toBe(9465)
    expect(fila.lifetime.mortality).toBe(bu === 'broiler' ? 335 : 535)
  }
  // CUT-GL-02: un evento con fecha del corte se rechaza determinísticamente. La fecha civil del corte
  // es la que persistió el backend (el input datetime-local se convierte a UTC en la pantalla).
  const fechaCorte = String(batch.cutover_datetime).slice(0, 10)
  const retro = await request.post(`${API}/operations`, { headers: cab, data: {
    lot_id: lotId, event_type: bu === 'hatchery' ? 'incubation_load' : 'mortality_recording',
    event_date: fechaCorte,
    ...(bu === 'hatchery' ? { hatchery_params: [{ quantity_loaded: 1 }] }
      : { bird_movements: [{ sex: bu === 'broiler' ? 'mixed' : 'female', quantity: 1, avg_weight: 1000 }] }),
  } })
  const cuerpoRetro = await retro.json()
  pasos.cut_gl_02 = { status: retro.status(), body: cuerpoRetro }
  expect(retro.status()).toBe(400)
  expect(cuerpoRetro.rule).toBe('CUT-GL-02')

  // La pantalla refleja el post-corte tras recargar.
  await page.goto(`/cutover?batch=${batch.id}`)
  await expect(page.getByTestId('cutover-reconciliation')).toContainText(ref)
  pasos.fin = new Date().toISOString()
  journal(`e2e-${bu}-${formato}`, pasos)
  return { batch, lotId, fila }
}

/** La misma cabecera del aprobador que usan los specs de proceso (para pruebas auxiliares). */
export { cabeceraAprobador }
