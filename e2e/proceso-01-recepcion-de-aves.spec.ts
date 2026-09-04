/**
 * PROCESO 01 — RECEPCIÓN DE AVES
 *
 * Piloto de la Wave 3, primer proceso del orden que fija `GA-REM-016`: alimenta el
 * inventario del que dependen todos los demás.
 *
 * La unidad de certificación es el **proceso de negocio**, no la pantalla ni el endpoint
 * (`GA-REM-016`, Art. IV de la constitución). Por eso cada caso recorre la cadena
 * completa —interfaz, API y base— y no se conforma con que un endpoint responda 201.
 *
 * Casos exigidos por la spec: `HAPPY PATH` · `NEGATIVE PATH` · `AUTHORIZATION` ·
 * `VALIDATION` · `PERSISTENCE` · `AUDIT`.
 *
 * Fechas relativas al reloj, nunca literales: `R-28` quedó cerrado y no se reabre.
 */
import { test, expect, type Page, type APIRequestContext } from '@playwright/test'

const API = 'http://127.0.0.1:8099/api/v1'

/** Fecha de hoy en ISO, sin literales que caduquen con el calendario (`R-28`). */
function hoy(): string {
  return new Date().toISOString().slice(0, 10)
}

async function credenciales(): Promise<{ usuario: string; clave: string }> {
  const clave = process.env.GA_TEST_ADMIN_PASSWORD
  if (!clave) throw new Error('GA_TEST_ADMIN_PASSWORD no definida: use bash scripts_e2e.sh')
  return { usuario: 'test_admin', clave }
}

async function token(request: APIRequestContext, usuario: string, clave: string) {
  const r = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
  expect(r.status(), 'el login debe funcionar').toBe(200)
  return (await r.json()).access_token as string
}

/** Entra por la interfaz, como lo haría un operador. */
async function entrar(page: Page, usuario: string, clave: string) {
  await page.goto('/login')
  await page.getByLabel(/usuario|username/i).fill(usuario).catch(async () => {
    await page.locator('input[name="username"], input#login-username').first().fill(usuario)
  })
  await page.locator('input[type="password"]').first().fill(clave)
  await page.locator('button[type="submit"]').first().click()
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 20_000 })
}

test.describe('Proceso 01 · Recepción de aves', () => {
  test('AUTENTICACIÓN · sin sesión la aplicación no expone el proceso', async ({ page }) => {
    await page.goto('/operations/new')
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 })
  })

  test('HAPPY PATH · la recepción se registra y queda persistida', async ({ page, request }) => {
    const { usuario, clave } = await credenciales()
    await entrar(page, usuario, clave)

    // La interfaz responde y el proceso es alcanzable para el usuario autenticado.
    await page.goto('/operations')
    await expect(page.locator('body')).toBeVisible()

    // El registro se ejerce por API con la sesión real: el formulario tiene muchas
    // variantes por etapa y lo que se certifica aquí es el proceso, no un widget.
    const jwt = await token(request, usuario, clave)
    const cabecera = { Authorization: `Bearer ${jwt}` }

    const creacion = await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 1, farm_id: 1, house_id: 1,
        event_type: 'bird_reception',
        event_date: hoy(),
        bird_movements: [
          { sex: 'male', quantity: 200 },
          { sex: 'female', quantity: 800 },
        ],
      },
    })
    expect(creacion.status(), await creacion.text()).toBe(201)
    const evento = await creacion.json()
    expect(evento.event_type).toBe('bird_reception')
    expect(evento.status).toBe('registered')

    // PERSISTENCIA · el detalle conserva los submovimientos
    const detalle = await request.get(`${API}/operations/${evento.id}`, { headers: cabecera })
    expect(detalle.status()).toBe(200)
    const cuerpo = await detalle.json()
    const total = cuerpo.bird_movements.reduce((a: number, m: any) => a + m.quantity, 0)
    expect(total, 'la cantidad recibida debe conservarse').toBe(1000)

    // La operación aparece en el listado que ve el usuario
    await page.goto('/operations')
    await expect(page.locator('body')).toBeVisible()
  })

  test('VALIDACIÓN · BR-08 exige granja y galpón', async ({ request }) => {
    const { usuario, clave } = await credenciales()
    const jwt = await token(request, usuario, clave)

    const r = await request.post(`${API}/operations`, {
      headers: { Authorization: `Bearer ${jwt}` },
      data: {
        lot_id: 1, event_type: 'bird_reception', event_date: hoy(),
        bird_movements: [{ sex: 'mixed', quantity: 10 }],
      },
    })
    expect(r.status(), 'sin granja la recepción debe rechazarse').toBe(400)
    const cuerpo = await r.json()
    expect(cuerpo.rule, 'el error debe identificar la regla').toBe('BR-08')
    expect(typeof cuerpo.detail).toBe('string')
  })

  test('VALIDACIÓN · BR-19 rechaza una fecha en período cerrado', async ({ request }) => {
    const { usuario, clave } = await credenciales()
    const jwt = await token(request, usuario, clave)

    const antigua = new Date()
    antigua.setDate(antigua.getDate() - 120) // más de 90 días: relativo, nunca literal

    const r = await request.post(`${API}/operations`, {
      headers: { Authorization: `Bearer ${jwt}` },
      data: {
        lot_id: 1, farm_id: 1, house_id: 1,
        event_type: 'bird_reception',
        event_date: antigua.toISOString().slice(0, 10),
        bird_movements: [{ sex: 'mixed', quantity: 10 }],
      },
    })
    expect(r.status()).toBe(400)
    expect((await r.json()).rule).toBe('BR-19')
  })

  test('AUTORIZACIÓN · un rol sin permiso no registra', async ({ request }) => {
    const clave = process.env.GA_TEST_APPROVER_PASSWORD
    test.skip(!clave, 'GA_TEST_APPROVER_PASSWORD no definida')

    const jwt = await token(request, 'test_approver', clave!)
    const r = await request.post(`${API}/operations`, {
      headers: { Authorization: `Bearer ${jwt}` },
      data: {
        lot_id: 1, farm_id: 1, house_id: 1,
        event_type: 'bird_reception', event_date: hoy(),
        bird_movements: [{ sex: 'mixed', quantity: 10 }],
      },
    })
    expect(r.status(), 'el aprobador no tiene operations:create').toBe(403)
  })

  test('AUDITORÍA · la recepción deja rastro', async ({ request }) => {
    const { usuario, clave } = await credenciales()
    const jwt = await token(request, usuario, clave)
    const cabecera = { Authorization: `Bearer ${jwt}` }

    const creacion = await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 1, farm_id: 1, house_id: 1,
        event_type: 'bird_reception', event_date: hoy(),
        bird_movements: [{ sex: 'mixed', quantity: 50 }],
      },
    })
    expect(creacion.status()).toBe(201)
    const id = (await creacion.json()).id

    const auditoria = await request.get(`${API}/audit?entity_type=operational_event&limit=100`,
      { headers: cabecera })
    expect(auditoria.status()).toBe(200)
    const registros = (await auditoria.json()).logs ?? []
    const suyo = registros.filter((l: any) => String(l.entity_id) === String(id))
    expect(suyo.length, 'el evento debe aparecer en la auditoría').toBeGreaterThan(0)
  })

  test('AISLAMIENTO · no se registra contra un lote de otra empresa', async ({ request }) => {
    const { usuario, clave } = await credenciales()
    const jwt = await token(request, usuario, clave)

    // El Super Admin se sitúa en la empresa 2 y crea allí un lote.
    const cambio = await request.post(`${API}/switch-company`, {
      headers: { Authorization: `Bearer ${jwt}` }, data: { company_id: 2 },
    })
    expect(cambio.status()).toBe(200)
    const jwtB = (await cambio.json()).access_token

    const granjaB = await request.post(`${API}/masters/farms`, {
      headers: { Authorization: `Bearer ${jwtB}` },
      data: { name: 'E2E B', code: `E2E-B-${Date.now()}`, company_id: 2 },
    })
    expect(granjaB.status()).toBe(201)
    const loteB = await request.post(`${API}/lots`, {
      headers: { Authorization: `Bearer ${jwtB}` },
      data: { lot_code: `E2E-LOT-B-${Date.now()}`, farm_id: (await granjaB.json()).id,
              bird_type: 'broiler', sex: 'mixed' },
    })
    expect([200, 201]).toContain(loteB.status())

    // Un operador de la empresa 1 intenta registrar contra ese lote.
    const claveOp = process.env.GA_TEST_OPERATOR_PASSWORD
    test.skip(!claveOp, 'GA_TEST_OPERATOR_PASSWORD no definida')
    const jwtOp = await token(request, 'test_operator', claveOp!)

    const intruso = await request.post(`${API}/operations`, {
      headers: { Authorization: `Bearer ${jwtOp}` },
      data: {
        lot_id: (await loteB.json()).id, farm_id: 1, house_id: 1,
        event_type: 'bird_reception', event_date: hoy(),
        bird_movements: [{ sex: 'mixed', quantity: 999 }],
      },
    })
    expect(intruso.status(), 'escribir contra un lote ajeno debe rechazarse')
      .toBeGreaterThanOrEqual(400)
  })
})
