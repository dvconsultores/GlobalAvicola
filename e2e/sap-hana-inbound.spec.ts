/**
 * SPEC 005 · SAP HANA Cloud READ ONLY inbound — E2E local con el doble de HANA.
 *
 * Aquí **no hay SAP**. El backend corre con `SAP_HANA_DRIVER=fake` (lo fija
 * `scripts_e2e.sh`), y la propia pantalla lo dice: «Simulador local (no es SAP)». Lo que se
 * certifica es el recorrido del producto:
 *
 *   Analista SAP → SAP Manager → estado → Sincronizar → job completado → referencias
 *     → recepción parcial contra la OC sincronizada → límite BR-18
 *     → la STO sincronizada queda disponible para el flujo que la consume
 *
 * La OC del dataset es `4500000001`: hembras 1000 UN + machos 150 UN = 1150 ordenadas.
 */
import { test, expect, type APIRequestContext, type Page } from '@playwright/test'
import { API, cabeceraAdmin, crearEscenario, hoy, registrar, sufijo } from '../test-support/e2e-api'

const BASE = `${API}/sap/inbound`
const OC = '4500000001'
const ORDENADO = 1150
const STO = '4900000001'

test.describe.configure({ mode: 'serial' })

/** Mapping de la empresa de pruebas: sociedad 1000 y centro 1100 (el 1200 se deja sin mapear). */
async function mapear(request: APIRequestContext, cab: any, cuerpo: Record<string, unknown>) {
  const r = await request.put(`${BASE}/mappings`, { headers: cab, data: cuerpo })
  expect(r.status(), `mapping ${JSON.stringify(cuerpo)}: ${await r.text()}`).toBe(200)
}

/** Un Analista SAP propio del escenario: la siembra de pruebas no trae ninguno. */
async function crearAnalistaSap(request: APIRequestContext, cab: any) {
  const roles = await (await request.get(`${API}/roles`, { headers: cab })).json()
  const rol = roles.find((r: any) => r.name === 'TEST Analista SAP')
  expect(rol, 'la siembra debe traer el rol «TEST Analista SAP»').toBeTruthy()
  const yo = await (await request.get(`${API}/me`, { headers: cab })).json()

  const usuario = `sap_e2e_${sufijo()}`
  const clave = `Sap-${sufijo()}-${sufijo()}`
  const alta = await request.post(`${API}/users`, {
    headers: cab,
    data: {
      username: usuario, email: `${usuario}@example.com`, first_name: 'Analista', last_name: 'SAP',
      password: clave, role_id: rol.id, company_id: yo.company_id, view_type: 'web',
    },
  })
  expect(alta.status(), `alta del analista: ${await alta.text()}`).toBe(201)
  const sesion = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
  expect(sesion.status()).toBe(200)
  return { usuario, clave, cabecera: { Authorization: `Bearer ${(await sesion.json()).access_token}` } }
}

async function entrar(page: Page, usuario: string, clave: string) {
  await page.goto('/login')
  await page.getByLabel(/usuario|username/i).fill(usuario).catch(async () => {
    await page.locator('input[name="username"], input#login-username').first().fill(usuario)
  })
  await page.locator('input[type="password"]').first().fill(clave)
  await page.locator('button[type="submit"]').first().click()
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 20_000 })
}

test.describe('SPEC 005 · SAP HANA inbound (solo lectura, doble local)', () => {
  let analista: Awaited<ReturnType<typeof crearAnalistaSap>>

  test.beforeAll(async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    await mapear(request, cab, { entity_type: 'COMPANY_CODE', sap_key: '1000' })
    await mapear(request, cab, { entity_type: 'PLANT', sap_key: '1100', parent_sap_key: '1000' })
    analista = await crearAnalistaSap(request, cab)
  })

  test('readiness: el conector se declara simulado, de solo lectura y sin secretos', async ({ request }) => {
    const r = await request.get(`${BASE}/readiness`, { headers: analista.cabecera })
    expect(r.status()).toBe(200)
    const d = await r.json()
    expect(d.phase).toBe('READ_ONLY_INBOUND')
    expect(d.configured).toBe(true)
    expect(d.simulated).toBe(true)
    expect(d.write_operations_allowed).toBe(false)
    expect(d.outbound_enabled).toBe(false)
    expect(JSON.stringify(d)).not.toMatch(/fake-local|fake\.invalid/)
  })

  test('Analista SAP: SAP Manager → estado → Sincronizar → job completado → registros', async ({ page }) => {
    await entrar(page, analista.usuario, analista.clave)
    await page.goto('/sap')

    const estado = page.getByTestId('sap-inbound-status')
    await expect(estado).toBeVisible({ timeout: 20_000 })
    await expect(estado).toHaveAttribute('data-status', 'SIMULATED_CONNECTED')
    await expect(estado).toContainText(/Simulador local|Local simulator/)

    // Fase READ ONLY: exportar no se ofrece.
    await expect(page.getByTestId('sap-outbound-disabled')).toBeVisible()
    await expect(page.getByRole('button', { name: /Exportar a SAP|Export to SAP/ })).toHaveCount(0)

    const respuesta = page.waitForResponse(
      (r) => r.url().includes('/sap/inbound/sync') && r.request().method() === 'POST', { timeout: 60_000 })
    await page.getByTestId('sap-inbound-sync').click()
    const sync = await respuesta
    expect(sync.status()).toBe(200)
    const jobs = (await sync.json()).jobs as any[]
    expect(jobs).toHaveLength(14)
    expect(jobs.filter((j) => j.status !== 'completed'), 'todos los objetos completan').toEqual([])

    // La pantalla refleja el job y los registros.
    const fila = page.getByTestId('sap-inbound-object-purchase_order')
    await expect(fila).toContainText(/completado|completed/, { timeout: 20_000 })
    await page.getByRole('button', { name: /^Registros$|^Records$/ }).click()
    await expect(page.getByText(`100|${OC}`, { exact: true })).toBeVisible({ timeout: 15_000 })

    // El centro sin mapear queda retenido y visible, no promovido.
    await page.getByRole('button', { name: /Errores de sincronización|Synchronization errors/ }).click()
    await expect(page.getByText('100|1200', { exact: true }).first()).toBeVisible({ timeout: 15_000 })
  })

  test('las referencias sincronizadas quedan disponibles con su cantidad', async ({ request }) => {
    const r = await request.get(`${API}/sap/references?ref_type=purchase_order&limit=200`,
      { headers: analista.cabecera })
    expect(r.status()).toBe(200)
    const oc = (await r.json()).references.find((x: any) => x.sap_code === OC)
    expect(oc, 'la OC sincronizada debe figurar entre las referencias').toBeTruthy()
    expect(oc.quantity).toBe(ORDENADO)
    expect(oc.extra_data.source).toBe('SAP_HANA_CLOUD')
    expect(oc.extra_data.items).toHaveLength(2)

    // Sincronizar otra vez no duplica nada: mismo hash, no-op.
    const otra = await request.post(`${BASE}/sync/purchase_order`, { headers: analista.cabecera, data: {} })
    expect(otra.status()).toBe(200)
    for (const job of (await otra.json()).jobs) {
      expect(job.status).toBe('completed')
      expect(job.rows_raw, `${job.object_type} no debe crear versiones nuevas`).toBe(0)
    }
    const despues = await (await request.get(`${API}/sap/references?ref_type=purchase_order&limit=200`,
      { headers: analista.cabecera })).json()
    expect(despues.references.filter((x: any) => x.sap_code === OC)).toHaveLength(1)
  })

  test('recepción: el flujo ofrece la OC sincronizada; parcial, hasta el límite y BR-18', async ({ page, request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, 'HANA5', 'broiler')

    // El formulario de recepción recibe la OC sincronizada en su selector de documento SAP.
    const clave = process.env.GA_TEST_ADMIN_PASSWORD as string
    await entrar(page, 'test_admin', clave)
    const ordenes = page.waitForResponse(
      (r) => r.url().includes('/sap/references') && r.url().includes('purchase_order'), { timeout: 30_000 })
    await page.goto('/operations/new?type=bird_reception')
    const lista = (await (await ordenes).json()).references as any[]
    expect(lista.map((x) => x.sap_code)).toContain(OC)

    const base = {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_date: hoy(), event_type: 'bird_reception', sap_document_ref: OC,
    }
    const parcial = await registrar(request, cab, { ...base, bird_movements: [{ sex: 'mixed', quantity: 300 }] })
    expect(parcial.status(), await parcial.text()).toBe(201)
    expect((await parcial.json()).sap_document_ref).toBe(OC)

    const hastaElLimite = await registrar(request, cab,
      { ...base, bird_movements: [{ sex: 'mixed', quantity: ORDENADO - 300 }] })
    expect(hastaElLimite.status(), await hastaElLimite.text()).toBe(201)

    const exceso = await registrar(request, cab, { ...base, bird_movements: [{ sex: 'mixed', quantity: 1 }] })
    expect(exceso.status()).toBe(400)
    expect((await exceso.json()).rule).toBe('BR-18')
  })

  test('traslados: la STO sincronizada queda disponible para el flujo que la consume', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    // El destino de la STO es el centro 1200: hasta mapearlo, la orden queda retenida entera.
    const antes = await (await request.get(`${API}/sap/references?ref_type=transfer_order&limit=200`,
      { headers: analista.cabecera })).json()
    expect(antes.references.map((x: any) => x.sap_code)).not.toContain(STO)

    await mapear(request, cab, { entity_type: 'PLANT', sap_key: '1200', parent_sap_key: '1000' })
    const sync = await request.post(`${BASE}/sync/transfer_order`, { headers: analista.cabecera, data: {} })
    expect(sync.status()).toBe(200)
    expect((await sync.json()).jobs[0].status).toBe('completed')

    const despues = await (await request.get(`${API}/sap/references?ref_type=transfer_order&limit=200`,
      { headers: analista.cabecera })).json()
    const sto = despues.references.find((x: any) => x.sap_code === STO)
    expect(sto, 'la STO debe figurar como referencia de traslado').toBeTruthy()
    expect(sto.quantity).toBe(5000)
    expect(sto.unit).toBe('KG')
    expect(sto.extra_data.source_plant).toBe('1100')
    expect(sto.extra_data.destination_plant).toBe('1200')
  })

  test('fase READ ONLY: exportar y reintentar responden 409 y no existe SQL por HTTP', async ({ request }) => {
    for (const ruta of ['export', 'retry']) {
      const r = await request.post(`${API}/sap/${ruta}`, { headers: analista.cabecera, data: {} })
      expect(r.status(), ruta).toBe(409)
      expect((await r.json()).detail.code).toBe('SAP_OUTBOUND_DISABLED_READ_ONLY_PHASE')
    }
    const sql = await request.post(`${BASE}/sync`, {
      headers: analista.cabecera, data: { sql: 'SELECT * FROM MATDOC' },
    })
    expect(sql.status()).toBe(422)
    const libre = await request.post(`${BASE}/sync/MATDOC`, { headers: analista.cabecera, data: {} })
    expect([404, 422]).toContain(libre.status())
  })
})
