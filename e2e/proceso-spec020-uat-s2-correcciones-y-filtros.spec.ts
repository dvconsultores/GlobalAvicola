/**
 * `GA-UAT-BREEDER-CRIA-S2-2026-11-24` · spec `020` §3 — E2E de la Sesión 2.
 *
 * Escenario 01 — el circuito completo de un dato real: una recepción de reproductoras se
 * envía a revisión, el revisor corrige el **proveedor** con un selector de catálogo (el
 * original se lee por nombre, no por id), el historial muestra «A → B» y la aprobación
 * —filtrada por el código del lote, tecleado en minúsculas— deja el evento aprobado con el
 * proveedor corregido.
 *
 * Escenario 02 — un campo numérico hereda el contrato del campo: la muestra negativa y la
 * muestra mayor que las aves recibidas se rechazan con un mensaje en español que nombra el
 * dato («Tamaño de muestra») y nunca la columna (`sample_size`), sin escribir nada.
 *
 * Escenario 03 — los filtros de Revisión: código de lote parcial en minúsculas, rango de
 * fechas válido de un solo día, rango invertido con un único aviso (sin toast de error) y
 * rango abierto por el inicio.
 *
 * Escenario 04 — la lista de Operaciones: un evento de nivel granja sin lote se rotula
 * «Sin lote (nivel granja)», no «Se creará al aprobar».
 */
import { test, expect, type APIRequestContext } from '@playwright/test'
import {
  API, hoy, sufijo, empresaActiva, cabeceraAdmin, crearEscenario, registrar, tipoDeCorreccion,
} from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

/** Día desplazado desde `hoy()`, en el mismo formato local: nunca fechas literales. */
function dia(dias: number): string {
  const d = new Date(`${hoy()}T12:00:00`)
  d.setDate(d.getDate() + dias)
  return d.toLocaleDateString('sv-SE')
}

async function como(request: APIRequestContext, quien: 'operator') {
  const claves = { operator: ['test_operator', process.env.GA_TEST_OPERATOR_PASSWORD!] } as const
  const [usuario, clave] = claves[quien]
  const r = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
  expect(r.status(), `login de ${usuario}: ${await r.text()}`).toBe(200)
  return { Authorization: `Bearer ${(await r.json()).access_token}` }
}

/** POST que debe crear: el 201 forma parte de la precondición del escenario. */
async function crear(request: APIRequestContext, cabecera: any, ruta: string, data: any) {
  const r = await request.post(`${API}${ruta}`, { headers: cabecera, data })
  expect(r.status(), `${ruta}: ${await r.text()}`).toBe(201)
  return await r.json()
}

/** Recepción de aves cuadrada (`BR-20`): recibidas = alojadas + muertas + rechazadas. */
async function recepcion(
  request: APIRequestContext, operador: any, esc: any, extra: Record<string, any> = {},
): Promise<number> {
  const r = await registrar(request, operador, {
    lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
    event_type: 'bird_reception', event_date: hoy(),
    received_total: 100, dead_on_arrival: 0, rejected_on_arrival: 0,
    bird_movements: [{ sex: 'female', quantity: 100, avg_weight: 1.8 }],
    ...extra,
  })
  expect(r.status(), `recepción de aves: ${await r.text()}`).toBe(201)
  return (await r.json()).id as number
}

/**
 * Camino de un supervisor: entra a Revisión, abre la pestaña del estado, filtra por una
 * parte del código del lote en minúsculas, abre el evento y pulsa «Corregir».
 */
async function abrirCorreccion(
  page: any, id: number, codigo: string, pestana: 'Pendientes' | 'En revisión',
) {
  await page.goto('/review')
  await page.getByRole('button', { name: new RegExp(`^${pestana}$`, 'i') }).click()
  await page.getByTestId('review-filter-lot').fill(codigo.slice(-6).toLowerCase())
  const fila = page.getByRole('row').filter({ hasText: new RegExp(`#${id}(?!\\d)`) })
  await expect(fila, 'el evento está en la bandeja de Revisión').toBeVisible({ timeout: 20_000 })
  await fila.getByRole('link').first().click()
  await expect(page).toHaveURL(new RegExp(`/review/${id}$`), { timeout: 20_000 })
  await page.getByRole('link', { name: /corregir/i }).first().click()
  await expect(
    page.getByTestId('correction-original'), 'el formulario de corrección se abre',
  ).toBeVisible({ timeout: 20_000 })
  // `RR-27` (`OD-S2-01`): se elige el tipo de corrección (el selector solo ofrece activos).
  const tipo = page.getByTestId('correction-type')
  await expect(tipo.locator('option').nth(1), 'hay al menos un tipo de corrección activo').toBeAttached()
  await tipo.selectOption({ index: 1 })
}

test.describe('SPEC 020 · UAT Sesión 2 (reproductoras/cría)', () => {
  test.beforeAll(async ({ request }) => {
    await tipoDeCorreccion(request, await cabeceraAdmin(request))
  })
  test('E2E-S2-01 · Recepción → Revisión → Corrección de maestro → Aprobación', async ({
    request, page,
  }) => {
    const admin = await cabeceraAdmin(request)
    const operador = await como(request, 'operator')
    const companyId = empresaActiva(admin)
    const s = sufijo()
    const esc = await crearEscenario(request, admin, 'S2P20A', 'breeder')

    const nombreA = `S2P20A-PROV-A-${s}`
    const nombreB = `S2P20A-PROV-B-${s}`
    const proveedor = async (name: string) => (await crear(request, admin, '/masters/suppliers', {
      company_id: companyId, name, country: 'Francia', supplier_type: 'international',
    })).id as number
    const idA = await proveedor(nombreA)
    const idB = await proveedor(nombreB)

    const idEvento = await recepcion(request, operador, esc, { supplier_id: idA })
    const enviado = await request.post(`${API}/operations/${idEvento}/submit`, { headers: operador })
    expect(enviado.status(), await enviado.text()).toBe(200)
    expect((await enviado.json()).status, 'el registrante la envía a revisión').toBe('pending_review')
    const revision = await request.post(`${API}/review/start/${idEvento}`, { headers: admin })
    expect(revision.status(), await revision.text()).toBe(200)

    // UI — el revisor corrige el maestro por el selector, no escribiendo un id.
    await entrar(page, 'admin')
    await abrirCorreccion(page, idEvento, esc.codigo, 'En revisión')
    const selector = page.locator('form select').first()
    const opciones = await selector.locator('option').allTextContents()
    expect(opciones.join(' | '), 'el maestro se ofrece con su nombre funcional')
      .toContain('Proveedor')
    await selector.selectOption('supplier_id')

    const original = page.getByTestId('correction-original')
    await expect(original, 'el original es el NOMBRE del proveedor, no su id')
      .toHaveValue(nombreA)
    const maestro = page.getByTestId('correction-corrected-master')
    await expect(maestro, 'un campo de maestro se corrige con un selector').toBeVisible()
    const nombres = await maestro.locator('option').allTextContents()
    expect(nombres, 'el selector ofrece el otro proveedor').toContain(nombreB)
    expect(nombres, 'el proveedor actual no se ofrece como corrección').not.toContain(nombreA)

    await maestro.selectOption(String(idB))
    await page.locator('form textarea').first().fill('Proveedor equivocado en la recepción')
    await page.locator('form button[type="submit"]').first().click()
    await expect(page, 'tras guardar se vuelve al detalle de revisión').toHaveURL(
      new RegExp(`/review/${idEvento}$`), { timeout: 20_000 },
    )
    await expect(
      page.getByText(`"${nombreA}" → "${nombreB}"`).first(),
      'el historial de correcciones muestra los nombres',
    ).toBeVisible()

    // `BR-14`: quien corrigió un registro no puede aprobarlo (el servidor lo rechaza con 403, y es un
    // control vigente). La aprobación la hace otro usuario: el aprobador de pruebas.
    await page.evaluate(() => window.localStorage.clear()).catch(() => undefined)
    await page.evaluate(() => window.sessionStorage.clear()).catch(() => undefined)
    await page.context().clearCookies()
    await entrar(page, 'approver')
    // Aprobaciones — el filtro es de CÓDIGO de lote, tecleado parcial y en minúsculas.
    await page.goto('/approvals')
    await page.getByTestId('approval-filter-lot').fill(esc.codigo.slice(-6).toLowerCase())
    const fila = page.getByRole('row').filter({ hasText: new RegExp(`#${idEvento}(?!\\d)`) })
    await expect(fila, 'el evento corregido aparece en Aprobaciones').toBeVisible({ timeout: 20_000 })
    await fila.getByRole('button', { name: /aprobar/i }).click()
    const dialogo = page.getByRole('dialog')
    await expect(dialogo, 'la aprobación pide confirmación').toBeVisible()
    await dialogo.getByRole('button', { name: /^aprobar$/i }).click()
    await expect.poll(async () => (await (await request.get(`${API}/operations/${idEvento}`, {
      headers: admin,
    })).json()).status, { timeout: 20_000, message: 'la aprobación se completa' }).toBe('approved')

    const detalle = await (await request.get(`${API}/operations/${idEvento}`, { headers: admin })).json()
    expect(detalle.status, 'el evento queda aprobado').toBe('approved')
    expect(detalle.supplier_id, 'el proveedor aprobado es el corregido (B)').toBe(idB)
    expect(detalle.approved_by_id, 'aprueba un usuario distinto de quien registró').not.toBe(detalle.registered_by_id)
    expect(detalle.approved_by_id, 'y distinto de quien revisó y corrigió').not.toBe(detalle.reviewed_by_id)
    const correcciones = await (await request.get(`${API}/corrections/event/${idEvento}`, {
      headers: admin,
    })).json()
    expect(correcciones.length, 'la corrección queda auditada').toBe(1)
    expect(correcciones[0].original_display, 'la auditoría nombra el original').toBe(nombreA)
    expect(correcciones[0].corrected_display, 'la auditoría nombra el corregido').toBe(nombreB)
  })

  test('E2E-S2-02 · campo numérico: muestra negativa y muestra mayor que lo recibido', async ({
    request, page,
  }) => {
    const admin = await cabeceraAdmin(request)
    const operador = await como(request, 'operator')
    const esc = await crearEscenario(request, admin, 'S2P20B', 'breeder')
    const idEvento = await recepcion(request, operador, esc, { sample_size: 50 })

    const detalle = async () =>
      await (await request.get(`${API}/operations/${idEvento}`, { headers: admin })).json()
    const correcciones = async () =>
      await (await request.get(`${API}/corrections/event/${idEvento}`, { headers: admin })).json()
    expect((await detalle()).sample_size, 'la muestra inicial es la registrada').toBe(50)

    await entrar(page, 'admin')
    await abrirCorreccion(page, idEvento, esc.codigo, 'Pendientes')
    const selector = page.locator('form select').first()
    expect(
      (await selector.locator('option').allTextContents()).join(' | '),
      'el campo se ofrece con su nombre funcional',
    ).toContain('Tamaño de muestra')
    await selector.selectOption('sample_size')

    const valor = page.getByTestId('correction-corrected')
    const motivo = page.locator('form textarea').first()
    const guardar = page.locator('form button[type="submit"]').first()
    const toasts = page.getByTestId('toast-container')

    await valor.fill('-1')
    await motivo.fill('Muestra mal digitada en la recepción')
    await guardar.click()
    await expect(toasts, 'muestra negativa: error en español que nombra el dato')
      .toContainText(/tamaño de muestra/i)
    expect(await toasts.innerText(), 'sin el nombre técnico de la columna')
      .not.toContain('sample_size')

    await valor.fill('150')
    await guardar.click()
    await expect(toasts, 'muestra mayor que lo recibido: aviso con la población')
      .toContainText('La muestra tomada no puede superar las aves recibidas (100)')

    expect((await detalle()).sample_size, 'un rechazo no escribe nada').toBe(50)
    expect((await correcciones()).length, 'un rechazo no deja corrección auditada').toBe(0)

    await valor.fill('40')
    await guardar.click()
    await expect(page, 'el valor válido se guarda y vuelve al detalle').toHaveURL(
      new RegExp(`/review/${idEvento}$`), { timeout: 20_000 },
    )
    expect((await detalle()).sample_size, 'la muestra válida queda aplicada').toBe(40)
  })

  test('E2E-S2-03 · filtros de Revisión: código de lote y rango de fechas', async ({
    request, page,
  }) => {
    const admin = await cabeceraAdmin(request)
    const operador = await como(request, 'operator')
    // Ambas recepciones se cuadran (`BR-20`): exige que los DOS lotes sean de reproductoras.
    const escA = await crearEscenario(request, admin, 'S2P20CA', 'breeder')
    const escB = await crearEscenario(request, admin, 'S2P20CB', 'breeder')
    const idA = await recepcion(request, operador, escA)
    await recepcion(request, operador, escB)

    await entrar(page, 'admin')
    await page.goto('/review')

    const filaA = page.getByRole('row').filter({ hasText: new RegExp(`#${idA}(?!\\d)`) })
    const alerta = page.locator('[role="alert"]')
    const lotFilter = page.getByTestId('review-filter-lot')

    // Código parcial en minúsculas: el filtro es de código, no de id.
    await lotFilter.fill(escA.codigo.slice(-6).toLowerCase())
    await expect(filaA, 'el filtro por código encuentra el lote').toBeVisible({ timeout: 20_000 })
    await expect(page.getByRole('row').filter({ hasText: escB.codigo }),
      'el otro lote queda fuera de la tabla').toHaveCount(0)

    // El filtro por el código de B trae B y deja fuera A; luego se vuelve al de A.
    await lotFilter.fill(escB.codigo.slice(-6).toLowerCase())
    await expect(page.getByRole('row').filter({ hasText: escB.codigo }),
      'el filtro por el código de B muestra B').toBeVisible({ timeout: 20_000 })
    await expect(page.getByRole('row').filter({ hasText: escA.codigo }),
      'y ya no A').toHaveCount(0)
    await lotFilter.fill(escA.codigo.slice(-6).toLowerCase())

    const desde = page.getByTestId('review-filter-date-from')
    const hasta = page.getByTestId('review-filter-date-to')

    // Rango válido de un solo día: filtra y no avisa.
    await desde.fill(hoy())
    await hasta.fill(hoy())
    await expect(filaA, 'el rango válido muestra el evento').toBeVisible({ timeout: 20_000 })
    await expect(alerta, 'un rango válido no avisa').toHaveCount(0)

    // Rango invertido: un único aviso en español y ningún toast de error.
    await desde.fill(dia(1))
    await expect(alerta, 'un único aviso para el rango invertido').toHaveCount(1)
    await expect(alerta).toContainText('La fecha inicial no puede ser posterior a la fecha final')
    await expect(page.getByTestId('toast-container'), 'el aviso no es un toast de error')
      .toHaveText(/^\s*$/)

    // Un solo extremo: válido (el evento de hoy debe quedar dentro del rango).
    await hasta.fill('')
    await desde.fill(hoy())
    await expect(alerta, 'solo el inicio: rango válido').toHaveCount(0)
    await expect(filaA, 'solo el inicio: el evento de hoy sigue visible')
      .toBeVisible({ timeout: 20_000 })

    await desde.fill('')
    await hasta.fill(hoy())
    await expect(alerta, 'solo el fin: rango válido').toHaveCount(0)
    await expect(filaA, 'solo el fin: el evento de hoy sigue visible')
      .toBeVisible({ timeout: 20_000 })
  })

  test('E2E-S2-04 · la lista de Operaciones rotula el evento de nivel granja', async ({
    request, page,
  }) => {
    const admin = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, admin, 'S2P20D', 'breeder')
    const idEvento = (await crear(request, admin, '/operations', {
      farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'farm_inspection', event_date: hoy(),
      observations: 'Inspección de granja sin novedades',
    })).id as number

    await entrar(page, 'admin')
    await page.goto('/operations')
    const fila = page.getByTestId(`operation-row-${idEvento}`)
    await expect(fila, 'la inspección está en la lista de Operaciones').toBeVisible({
      timeout: 20_000,
    })
    await expect(fila, 'sin lote de granja no se promete un lote')
      .toContainText('Sin lote (nivel granja)')
    await expect(fila, 'solo la importación de abuelos crea lote al aprobar')
      .not.toContainText('Se creará al aprobar')
  })
})
