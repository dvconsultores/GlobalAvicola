/**
 * `GA-UAT-BREEDER-CRIA-S2-O23-NULL-TO-MASTER` · spec `020` §7 — E2E de `NULL → maestro` (`O-23`).
 *
 * Una recepción de reproductoras nace sin proveedor. Desde Revisión → «Corregir» el operador
 * elige «Proveedor», lee «Sin valor» como valor original, ve solo proveedores activos con su
 * etiqueta funcional (`código — nombre`), completa el dato con tipo y motivo, y el evento se
 * aprueba. El historial dice «Sin valor → "nombre"» y lo sigue diciendo tras recargar y tras
 * volver a iniciar sesión. Por API, un proveedor de otra empresa o uno dado de baja no completan
 * nada (`AC-O23-03` D, `AC-O23-05`): el servidor no depende de la pantalla.
 */
import { test, expect, type APIRequestContext } from '@playwright/test'
import {
  API, hoy, sufijo, cabeceraAdmin, cabeceraAdminEnOtraEmpresa, crearEscenario, registrar, tipoDeCorreccion,
} from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

/** Día desplazado desde `hoy()`, en el mismo formato local: nunca fechas literales. */
function dia(dias: number): string {
  const d = new Date(`${hoy()}T12:00:00`)
  d.setDate(d.getDate() + dias)
  return d.toLocaleDateString('sv-SE')
}

const DIAS_DEL_LOTE = 30
const MOTIVO = 'Completar proveedor omitido en el registro'

async function como(request: APIRequestContext, quien: 'operator' | 'approver') {
  const claves = {
    operator: ['test_operator', process.env.GA_TEST_OPERATOR_PASSWORD!],
    approver: ['test_approver', process.env.GA_TEST_APPROVER_PASSWORD!],
  } as const
  const [usuario, clave] = claves[quien]
  const r = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
  expect(r.status(), `login de ${usuario}: ${await r.text()}`).toBe(200)
  return { Authorization: `Bearer ${(await r.json()).access_token}` }
}

async function crear(request: APIRequestContext, cabecera: any, ruta: string, data: any) {
  const r = await request.post(`${API}${ruta}`, { headers: cabecera, data })
  expect(r.status(), `${ruta}: ${await r.text()}`).toBe(201)
  return await r.json()
}

async function detalle(request: APIRequestContext, cabecera: any, id: number) {
  const r = await request.get(`${API}/operations/${id}`, { headers: cabecera })
  expect(r.status(), await r.text()).toBe(200)
  return await r.json()
}

async function darDeBaja(request: APIRequestContext, cabecera: any, ruta: string) {
  const r = await request.delete(`${API}${ruta}`, { headers: cabecera })
  expect(r.status(), `baja ${ruta}: ${await r.text()}`).toBe(204)
}

/** Recepción de reproductoras SIN proveedor, enviada y puesta en revisión, en un lote propio. */
async function recepcionEnRevision(request: APIRequestContext) {
  const admin = await cabeceraAdmin(request)
  const operador = await como(request, 'operator')
  const esc = await crearEscenario(request, admin, 'O23', 'breeder')
  const lote = await crear(request, admin, '/lots', {
    company_id: esc.companyId, farm_id: esc.farmId, house_id: esc.houseId,
    lot_code: `O23-NULL-${sufijo()}`, bird_type: 'breeder', sex: 'mixed', start_date: dia(-DIAS_DEL_LOTE),
  })
  const alta = await registrar(request, operador, {
    lot_id: lote.id, farm_id: esc.farmId, house_id: esc.houseId, event_type: 'bird_reception',
    event_date: dia(-DIAS_DEL_LOTE), received_total: 300, dead_on_arrival: 0, rejected_on_arrival: 0,
    bird_movements: [{ sex: 'mixed', quantity: 300 }],
  })
  expect(alta.status(), `recepción: ${await alta.text()}`).toBe(201)
  const id = (await alta.json()).id as number
  const enviado = await request.post(`${API}/operations/${id}/submit`, { headers: operador })
  expect(enviado.status(), await enviado.text()).toBe(200)
  const revision = await request.post(`${API}/review/start/${id}`, { headers: admin })
  expect(revision.status(), await revision.text()).toBe(200)
  const evento = await detalle(request, admin, id)
  expect(evento.supplier_id, 'la recepción nace sin proveedor').toBeNull()
  return { admin, id }
}

test.describe('SPEC 020 §7 · O-23 · completar un maestro vacío por corrección', () => {
  test('E2E-O23-01 · Completar el proveedor vacío desde Corregir y aprobar', async ({ request, page }) => {
    const { admin, id } = await recepcionEnRevision(request)
    const s = sufijo()
    const nombre = `O23 Proveedor ${s}`
    const activo = await crear(request, admin, '/masters/suppliers', { name: nombre, sap_code: `O23-${s}` })
    const retirado = await crear(request, admin, '/masters/suppliers', { name: `O23 Retirado ${s}` })
    await darDeBaja(request, admin, `/masters/suppliers/${retirado.id}`)
    const tipoId = await tipoDeCorreccion(request, admin)

    // UI — «Proveedor» se ofrece aunque esté vacío; el original se lee «Sin valor»
    await entrar(page, 'admin')
    await page.goto(`/review/${id}`)
    await page.getByRole('link', { name: /corregir/i }).first().click()
    await expect(page.getByTestId('correction-original')).toBeVisible({ timeout: 20_000 })
    await page.locator('form select').first().selectOption('supplier_id')
    await expect(page.getByTestId('correction-original'), 'original vacío ⇒ «Sin valor»').toHaveValue('Sin valor')
    const selector = page.getByTestId('correction-corrected-master')
    await expect(selector, 'maestro ⇒ selector, nunca texto libre').toBeVisible()
    await expect(page.getByTestId('correction-corrected')).toHaveCount(0)
    await expect(selector.locator(`option[value="${activo.id}"]`), 'etiqueta funcional código — nombre')
      .toHaveText(`O23-${s} — ${nombre}`, { timeout: 20_000 })
    await expect(selector.locator(`option[value="${retirado.id}"]`), 'el proveedor dado de baja no se ofrece').toHaveCount(0)

    await selector.selectOption(String(activo.id))
    await page.getByTestId('correction-type').selectOption(String(tipoId))
    await page.getByPlaceholder(/Explica por qué/).fill(MOTIVO)
    await page.getByRole('button', { name: /Guardar Corrección/ }).click()
    await expect(page).toHaveURL(new RegExp(`/review/${id}$`), { timeout: 20_000 })

    // Historial funcional: «Sin valor → "nombre"», nunca ids
    const linea = page.locator('p', { has: page.getByTestId('correction-no-value') })
    await expect(page.getByTestId('correction-no-value')).toHaveText('Sin valor', { timeout: 20_000 })
    await expect(linea).toContainText(`"${nombre}"`)
    await expect(linea).not.toContainText(`"${activo.id}"`)

    // Valor efectivo y auditoría por API
    const corregido = await detalle(request, admin, id)
    expect(corregido.status).toBe('corrected')
    expect(corregido.supplier_id, 'valor efectivo = proveedor elegido').toBe(activo.id)
    const hist = await request.get(`${API}/corrections/event/${id}`, { headers: admin })
    expect(hist.status(), await hist.text()).toBe(200)
    const fila = (await hist.json()).filter((c: any) => c.field_name === 'supplier_id').pop()
    expect(fila, 'la corrección queda en el historial').toBeTruthy()
    expect(fila.original_value, 'original = NULL').toBeNull()
    expect(fila.corrected_value).toBe(String(activo.id))
    expect(fila.corrected_display).toBe(nombre)
    expect(fila.correction_type_id).toBe(tipoId)
    expect(fila.reason).toBe(MOTIVO)

    // Aprobación (otra identidad, `BR-14`)
    const aprobador = await como(request, 'approver')
    const aprobado = await request.post(`${API}/approvals/approve`, {
      headers: aprobador, data: { event_id: id, observations: 'Verificado' },
    })
    expect(aprobado.status(), await aprobado.text()).toBe(200)
    const final = await detalle(request, admin, id)
    expect(final.status).toBe('approved')
    expect(final.supplier_id).toBe(activo.id)

    // Refresco
    await page.reload()
    await expect(page.getByTestId('correction-no-value')).toHaveText('Sin valor', { timeout: 20_000 })
    await expect(linea).toContainText(`"${nombre}"`)

    // Re-login
    await page.context().clearCookies()
    await page.evaluate(() => { localStorage.clear(); sessionStorage.clear() })
    await entrar(page, 'admin')
    await page.goto(`/review/${id}`)
    await expect(page.getByTestId('correction-no-value')).toHaveText('Sin valor', { timeout: 20_000 })
    await expect(page.locator('p', { has: page.getByTestId('correction-no-value') })).toContainText(`"${nombre}"`)
  })

  test('E2E-O23-02 · La API rechaza un maestro de otra empresa y uno inactivo (NULL → maestro)', async ({ request }) => {
    const { admin, id } = await recepcionEnRevision(request)
    const s = sufijo()
    const tipoId = await tipoDeCorreccion(request, admin)
    const corregir = (valor: number) => request.post(`${API}/corrections`, { headers: admin, data: {
      event_id: id, field_name: 'supplier_id', corrected_value: String(valor),
      reason: 'Manipulación de payload', correction_type_id: tipoId,
    } })

    const { cabecera: ajena } = await cabeceraAdminEnOtraEmpresa(request)
    const nombreAjeno = `O23 Ajeno ${s}`
    const ajeno = await crear(request, ajena, '/masters/suppliers', { name: nombreAjeno })
    const cruzada = await corregir(ajeno.id)
    expect(cruzada.status(), 'maestro de otra empresa ⇒ DENY').toBe(400)
    expect(await cruzada.text(), 'el ajeno no se nombra').not.toContain(nombreAjeno)

    const retirado = await crear(request, admin, '/masters/suppliers', { name: `O23 Baja ${s}` })
    await darDeBaja(request, admin, `/masters/suppliers/${retirado.id}`)
    const inactiva = await corregir(retirado.id)
    expect(inactiva.status(), 'maestro inactivo ⇒ DENY').toBe(400)
    expect((await inactiva.json()).rule).toBe('OD-21')

    const evento = await detalle(request, admin, id)
    expect(evento.supplier_id, 'el evento queda intacto').toBeNull()
    expect(evento.status).toBe('in_review')
  })
})
