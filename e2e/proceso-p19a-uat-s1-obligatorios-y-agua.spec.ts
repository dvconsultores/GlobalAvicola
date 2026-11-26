import { test, expect } from '@playwright/test';
import * as fs from 'node:fs';
import { LOTE_DE_VACUNA, API, cabeceraAdmin, crearEscenario, crearMaestros, hoy, sufijo } from '../test-support/e2e-api';
import { entrar } from '../test-support/auth';

test.describe.configure({ mode: 'serial' });
const DIR = 'audit/ga-uat-breeder-cria-s1-2026-11-10/evidence'
const CAPTURAS = `${DIR}/screenshots`

let admin: Record<string, string>
let esc: any
let maestros: any
let vacuna = ''
let medicamento = ''
let breederAntes = true
let habilitadoAqui = false
let idAgua = 0
let detalleAgua: any = null
const evidencia: Record<string, any> = {
  spec: '015-breeder-cria-uat-s1',
  generado: new Date().toISOString(),
  ui: {} as Record<string, any>,
  agua: {} as Record<string, any>,
  api: {} as Record<string, any>,
}

async function guardar(page: any) {
  await page.locator('#operation-form button[type="submit"]').click()
}

function contarPosts(page: any) {
  const estado = { n: 0 }
  page.on('request', (req: any) => {
    if (req.method() === 'POST' && new URL(req.url()).pathname === '/api/v1/operations') estado.n += 1
  })
  return estado
}

async function sinTextoCrudo(page: any) {
  await expect(page.locator('body')).not.toContainText(
    /water_consumption|Input should|Field required|RR-\d|BR-\d|B05/,
  )
}
test.beforeAll(async ({ request }) => {
  admin = await cabeceraAdmin(request)
  const u = await request.get(`${API}/business-units`, { headers: admin })
  expect(u.status(), 'GET /business-units').toBe(200)
  breederAntes = Boolean(((await u.json()) as any[]).find(x => x.code === 'breeder')?.is_enabled)
  if (!breederAntes) {
    await request.patch(`${API}/business-units/breeder/enable`, { headers: admin })
    habilitadoAqui = true
  }
  esc = await crearEscenario(request, admin, 'S1P19A', 'breeder')
  maestros = await crearMaestros(request, admin, 'S1P19A')
  const nombre = async (ruta: string, id: number) => {
    const r = await request.get(`${API}${ruta}`, { headers: admin })
    expect(r.status(), ruta).toBe(200)
    return ((await r.json()) as any[]).find(x => x.id === id)?.name ?? ''
  }
  vacuna = await nombre('/masters/vaccines?limit=100', maestros.vacunaId)
  medicamento = await nombre('/masters/medications?limit=100', maestros.medicamentoId)
  expect(vacuna && medicamento, 'catálogos con los maestros').toBeTruthy()
  const rec = await request.post(`${API}/operations`, { headers: admin, data: {
    event_type: 'bird_reception', lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
    event_date: hoy(), received_total: 1000, dead_on_arrival: 15, rejected_on_arrival: 5,
    bird_movements: [{ sex: 'male', quantity: 100, avg_weight: 2.0 },
      { sex: 'female', quantity: 880, avg_weight: 1.8 }],
  } })
  expect(rec.status(), `recepción: ${await rec.text()}`).toBe(201)
})
test.afterAll(async ({ request }) => {
  if (habilitadoAqui) {
    await request.patch(`${API}/business-units/breeder/disable`, { headers: admin })
  }
  evidencia.escenario = esc
  evidencia.breeder = { antes: breederAntes, habilitadoPorElTest: habilitadoAqui }
  evidencia.agua = { ...(evidencia.agua ?? {}), id: idAgua, detalle: detalleAgua }
  evidencia.catalogos = { vacuna, medicamento, maestros }
  fs.mkdirSync(CAPTURAS, { recursive: true })
  fs.writeFileSync(
    `${DIR}/e2e_p19a_obligatorios_agua.json`,
    JSON.stringify(evidencia, null, 2),
  )
})
const esperarPost = (page: any) =>
  page.waitForResponse((r: any) =>
    r.request().method() === 'POST' && new URL(r.url()).pathname === '/api/v1/operations')

async function abrir(page: any, tipo: string) {
  await page.goto(`/operations/new?lot_id=${esc.lotId}&type=${tipo}`)
  await expect(page.locator('#operation-form button[type="submit"]')).toBeVisible({ timeout: 20_000 })
}

test('P19-1a · pesaje: sin peso no hay POST; con peso, 201', async ({ page }) => {
  await entrar(page, 'admin')
  const posts = contarPosts(page)
  await abrir(page, 'weight_recording')
  await guardar(page)
  await expect(page.getByText('Registre el peso promedio de al menos un sexo (mayor a cero).')).toBeVisible()
  expect(posts.n, 'pesaje vacío: 0 POST').toBe(0)
  await sinTextoCrudo(page)
  await page.locator('input[name="bird_movements.0.avg_weight"]').fill('2100')
  const respuesta = esperarPost(page)
  await guardar(page)
  const r = await respuesta
  expect(r.status(), 'pesaje con dato').toBe(201)
  await expect(page.getByText('Registro guardado exitosamente').first()).toBeVisible()
  await sinTextoCrudo(page)
  evidencia.ui.pesaje = { vacio: 'inline, 0 POST', guardado: r.status() }
})
async function elegir(page: any, marcador: string, nombre: string) {
  await page.getByRole('button', { name: marcador }).first().click()
  const buscar = page.getByPlaceholder(/Buscar/i).first()
  if (await buscar.count()) await buscar.fill(nombre)
  await page.getByRole('button', { name: nombre, exact: true }).first().click()
}

test('P19-1b · vacunación: sin vacuna no hay POST; con vacuna, 201', async ({ page }) => {
  await entrar(page, 'admin')
  const posts = contarPosts(page)
  await abrir(page, 'vaccination')
  await guardar(page)
  await expect(page.getByText('Seleccione la vacuna aplicada.')).toBeVisible()
  expect(posts.n, 'vacunación vacía: 0 POST').toBe(0)
  await sinTextoCrudo(page)
  await elegir(page, 'Seleccionar vacuna...', vacuna)
  // `RR-31` (`OD-S2-05`): con vacuna pero sin lote tampoco hay POST.
  await guardar(page)
  await expect(page.getByText('Ingrese el lote de la vacuna aplicada')).toBeVisible()
  expect(posts.n, 'vacunación sin lote: 0 POST').toBe(0)
  await page.locator('input[name="vaccine_lot_number"]').first().fill(LOTE_DE_VACUNA)
  const respuesta = esperarPost(page)
  await guardar(page)
  const r = await respuesta
  expect(r.status(), 'vacunación con vacuna').toBe(201)
  await expect(page.getByText('Registro guardado exitosamente').first()).toBeVisible()
  await sinTextoCrudo(page)
  evidencia.ui.vacunacion = { vacio: 'mensaje inline, 0 POST', guardado: r.status(), vacuna }
})
test('P19-1c · medicación: sin medicamento no hay POST; con medicamento, 201', async ({ page }) => {
  await entrar(page, 'admin')
  const posts = contarPosts(page)
  await abrir(page, 'medication')
  await guardar(page)
  await expect(page.getByText('Seleccione el medicamento aplicado.')).toBeVisible()
  expect(posts.n, 'medicación vacía: 0 POST').toBe(0)
  await sinTextoCrudo(page)
  await elegir(page, 'Seleccionar medicamento...', medicamento)
  const respuesta = esperarPost(page)
  await guardar(page)
  const r = await respuesta
  expect(r.status(), 'medicación con medicamento').toBe(201)
  await expect(page.getByText('Registro guardado exitosamente').first()).toBeVisible()
  await sinTextoCrudo(page)
  evidencia.ui.medicacion = { vacio: 'mensaje inline, 0 POST', guardado: r.status(), medicamento }
})
test('P19-1d · alimento: sin kg no hay POST; con kg, 201', async ({ page }) => {
  await entrar(page, 'admin')
  const posts = contarPosts(page)
  await abrir(page, 'feed_registration')
  await guardar(page)
  await expect(page.getByText('Registre la cantidad de alimento (kg) mayor a cero.')).toBeVisible()
  expect(posts.n, 'alimento vacío: 0 POST').toBe(0)
  await sinTextoCrudo(page)
  await page.locator('input[name="feed_movements.0.quantity_kg"]').fill('12.5')
  // `RR-33` (`OD-S2-07`): con kilos pero sin tipo de alimento tampoco hay POST.
  await guardar(page)
  await expect(page.getByText('Seleccione el tipo de alimento')).toBeVisible()
  expect(posts.n, 'alimento sin tipo: 0 POST').toBe(0)
  await page.locator('select[name="feed_movements.0.feed_type_id"]').selectOption(String(maestros.alimentoId))
  const respuesta = esperarPost(page)
  await guardar(page)
  const r = await respuesta
  expect(r.status(), 'alimento con kg').toBe(201)
  await expect(page.getByText('Registro guardado exitosamente').first()).toBeVisible()
  await sinTextoCrudo(page)
  evidencia.ui.alimento = { vacio: 'mensaje inline, 0 POST', guardado: r.status() }
})
test('P19-1e · salida sin transporte por API: 201', async ({ request }) => {
  const r = await request.post(`${API}/operations`, { headers: admin, data: {
    event_type: 'bird_exit', lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
    event_date: hoy(), bird_movements: [{ sex: 'male', quantity: 5 }],
  } })
  expect(r.status(), `salida sin transporte: ${await r.text()}`).toBe(201)
  evidencia.api.salidaSinTransporte = { id: (await r.json()).id, status: 201 }
})
test('P19-2a · agua: vacío y 0 quedan bloqueados sin POST', async ({ page }) => {
  await entrar(page, 'admin')
  const posts = contarPosts(page)
  await abrir(page, 'water_consumption')
  const litros = page.locator('input[name="water_liters"]')
  await expect(litros, 'los litros están a la vista').toBeVisible()
  await guardar(page)
  await expect(page.getByText('Registre los litros de agua (mayor a cero).')).toBeVisible()
  expect(posts.n, 'agua vacía: 0 POST').toBe(0)
  await sinTextoCrudo(page)
  fs.mkdirSync(CAPTURAS, { recursive: true })
  await page.screenshot({ path: `${CAPTURAS}/p19_agua_vacio.png`, fullPage: true })

  await litros.fill('0')
  await guardar(page)
  const inline = (await page.getByText('Registre los litros de agua (mayor a cero).').count()) > 0
  const nativo = !(await litros.evaluate((el: any) => el.checkValidity()))
  expect(posts.n, 'agua con 0: 0 POST').toBe(0)
  expect(inline || nativo, 'el 0 queda bloqueado (mensaje inline o campo inválido)').toBeTruthy()
  await sinTextoCrudo(page)
  evidencia.ui.agua = { vacio: 'mensaje inline, 0 POST', cero: 'bloqueado, 0 POST' }
})
test('P19-2b · agua: 120.5 se guarda con 201', async ({ page }) => {
  await entrar(page, 'admin')
  await abrir(page, 'water_consumption')
  await page.locator('input[name="water_liters"]').fill('120.5')
  const respuesta = esperarPost(page)
  await guardar(page)
  const r = await respuesta
  expect(r.status(), 'agua con 120.5').toBe(201)
  idAgua = (await r.json()).id
  expect(idAgua, 'el evento guardado tiene id').toBeTruthy()
  await expect(page.getByText('Registro guardado exitosamente').first()).toBeVisible()
  await sinTextoCrudo(page)
  evidencia.ui.agua = { ...(evidencia.ui.agua ?? {}), litros: 120.5, guardado: r.status(), id: idAgua }
})
test('P19-2c · agua: el historial y el detalle muestran el evento', async ({ page, request }) => {
  await entrar(page, 'admin')
  await page.goto('/operations')
  const filtro = page.getByTestId('operation-filter-lot-code')
  await filtro.pressSequentially(esc.codigo.toLowerCase(), { delay: 30 })
  await page.waitForTimeout(800)
  const fila = page.getByTestId(`operation-row-${idAgua}`)
  await expect(fila, 'el evento aparece al filtrar').toBeVisible()
  await sinTextoCrudo(page)
  await page.goto(`/operations/${idAgua}`)
  await expect(page.getByText(esc.codigo).first(), 'el detalle muestra el lote').toBeVisible()
  await expect(page.getByText(/120\.5/).first(), 'el detalle muestra 120.5').toBeVisible()
  await sinTextoCrudo(page)
  detalleAgua = await (await request.get(`${API}/operations/${idAgua}`, { headers: admin })).json()
  expect(detalleAgua.water_liters).toBe(120.5)
  fs.mkdirSync(CAPTURAS, { recursive: true })
  await page.screenshot({ path: `${CAPTURAS}/p19_agua_detalle.png`, fullPage: true })
  evidencia.ui.agua = { ...(evidencia.ui.agua ?? {}), capturas: [
    `${CAPTURAS}/p19_agua_vacio.png`, `${CAPTURAS}/p19_agua_detalle.png`] }
})
// <!--CHUNK-->
