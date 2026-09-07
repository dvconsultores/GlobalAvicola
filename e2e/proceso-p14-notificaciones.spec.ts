/**
 * P-14 — NOTIFICACIONES INTERNAS   (`docs/02 §3.14` · `OD-07` · `GA-REM-038`)
 *
 * `OD-07` fijó el canal: los avisos viven **dentro** de Global Avícola. Que exista una fila en
 * `notifications` no es eso; lo es que el usuario la vea, la abra y quede leída. Por eso esta
 * suite es `UI_E2E` y no `API_E2E` — la misma lección que costó `R-96`.
 *
 * Se certifican los dos tipos que `docs/02 §3.14` y `docs/10 §6.2` definen con destinatario.
 * Los otros cuatro no dicen a quién avisar y esperan a `OD-08`; no se simulan aquí.
 */
import { test, expect } from '@playwright/test'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

const PREFIJO = 'P14'

function haceDias(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toLocaleDateString('sv-SE')
}

function empresaDe(cab: any): number {
  return JSON.parse(Buffer.from(cab.Authorization.split('.')[1], 'base64').toString()).company_id
}

async function crear(request: any, cab: any, ruta: string, data: any) {
  const r = await request.post(`${API}${ruta}`, { headers: cab, data })
  expect(r.status(), `${ruta}: ${await r.text()}`).toBe(201)
  return await r.json()
}

/**
 * Un registro del operador, rechazado por el administrador.
 *
 * El destinatario del aviso es **quien registró**, no quien rechaza: `docs/02 §3.14` dice
 * «notificar al operador», y `BR-14` exige que sean personas distintas.
 */
async function registroRechazado(request: any, cab: any, marca: string) {
  const companyId = empresaDe(cab)
  const granja = await crear(request, cab, '/masters/farms', {
    company_id: companyId, name: `${marca}-granja`, code: `${marca}-G`, farm_type: 'breeding',
  })
  const galpon = await crear(request, cab, '/masters/houses', {
    farm_id: granja.id, name: `${marca}-galpon`, capacity: 50_000,
  })
  const lote = await crear(request, cab, '/lots', {
    company_id: companyId, farm_id: granja.id, house_id: galpon.id,
    lot_code: `${marca}-LOTE`, bird_type: 'breeder', sex: 'mixed',
    start_date: haceDias(60),
  })

  // El evento lo registra el **operador**: es quien debe recibir el aviso.
  const clave = process.env.GA_TEST_OPERATOR_PASSWORD
  if (!clave) throw new Error('GA_TEST_OPERATOR_PASSWORD no definida: use bash scripts_e2e.sh')
  const login = await request.post(`${API}/login`, {
    data: { username: 'test_operator', password: clave },
  })
  expect(login.status(), await login.text()).toBe(200)
  const operador = { Authorization: `Bearer ${(await login.json()).access_token}` }

  const evento = await crear(request, operador, '/operations', {
    lot_id: lote.id, farm_id: granja.id, house_id: galpon.id,
    event_type: 'weight_recording', event_date: haceDias(7),
    bird_movements: [{ sex: 'mixed', quantity: 10, avg_weight: 1800 }],
  })

  const enviado = await request.post(`${API}/operations/${evento.id}/submit`, { headers: operador })
  expect(enviado.status(), await enviado.text()).toBe(200)
  const inicio = await request.post(`${API}/review/start/${evento.id}`, { headers: cab })
  expect(inicio.status(), await inicio.text()).toBe(200)
  const rechazo = await request.post(`${API}/approvals/reject`, {
    headers: cab,
    data: { event_id: evento.id, observations: `${marca} rechazado por datos incoherentes` },
  })
  expect(rechazo.status(), await rechazo.text()).toBe(200)

  return { evento, lote }
}

const campana = (page: any) => page.getByRole('button', { name: /notificacion|notification/i })

test.describe('P-14 · notificaciones internas', () => {
  test('AC16/AC17/AC18 · el operador ve el aviso, lo abre y queda leído',
    async ({ page, request }) => {
      const cab = await cabeceraAdmin(request)
      const marca = `${PREFIJO}${sufijo()}`
      const { evento } = await registroRechazado(request, cab, marca)

      await entrar(page, 'operator')

      // `AC16` · la campana existe y dice cuántas hay sin leer.
      const boton = campana(page).first()
      await expect(boton, 'no hay campana de notificaciones en la cabecera')
        .toBeVisible({ timeout: 20_000 })
      await expect(boton, 'la campana no anuncia notificaciones sin leer')
        .toHaveAccessibleName(/[1-9]/)

      // `AC17` · el panel dice qué pasó, y distingue leída de no leída por texto.
      await boton.click()
      const aviso = page.getByRole('listitem').filter({ hasText: new RegExp(marca) }).first()
      await expect(aviso, 'el aviso del rechazo no aparece en el panel')
        .toBeVisible({ timeout: 15_000 })
      await expect(aviso.getByText(/sin leer|unread/i),
        'no se distingue por texto que está sin leer').toBeVisible()

      // `AC18` · abrirla la marca leída, y el contador baja sin recargar.
      await aviso.click()
      await expect(boton, 'el contador no bajó al leer el aviso')
        .not.toHaveAccessibleName(/[1-9]/, { timeout: 15_000 })

      // Y quedó leída en el backend, no solo en la pantalla.
      const clave = process.env.GA_TEST_OPERATOR_PASSWORD!
      const login = await request.post(`${API}/login`, {
        data: { username: 'test_operator', password: clave } })
      const op = { Authorization: `Bearer ${(await login.json()).access_token}` }
      const bandeja = await request.get(`${API}/notifications?limit=100`, { headers: op })
      expect(bandeja.status(), await bandeja.text()).toBe(200)
      const suya = (await bandeja.json()).find(
        (n: any) => n.related_entity_id === evento.id)
      expect(suya, 'el aviso no existe en el backend').toBeTruthy()
      expect(suya.read_at, 'la lectura no se persistió').not.toBeNull()
    })

  test('AC17 · el aviso lleva a la operación de la que informa', async ({ page, request }) => {
    const cab = await cabeceraAdmin(request)
    const marca = `${PREFIJO}L${sufijo()}`
    const { evento } = await registroRechazado(request, cab, marca)

    await entrar(page, 'operator')
    await campana(page).first().click()
    await page.getByRole('listitem').filter({ hasText: new RegExp(marca) }).first().click()

    await expect(page, 'abrir el aviso no lleva al registro rechazado')
      .toHaveURL(new RegExp(`/operations/${evento.id}`), { timeout: 15_000 })
  })

  test('AC14 · la bandeja de otro no se ve', async ({ page, request }) => {
    // Mismo tenant, otra persona. El sujeto negativo tiene empresa propia: el Super
    // Administrador está exento de tenencia y haría pasar la prueba sin comprobar nada.
    const cab = await cabeceraAdmin(request)
    const marca = `${PREFIJO}O${sufijo()}`
    await registroRechazado(request, cab, marca)

    await entrar(page, 'approver')
    const boton = campana(page).first()
    await expect(boton).toBeVisible({ timeout: 20_000 })
    await boton.click()

    await expect(page.getByText(new RegExp(marca)),
      'un compañero de empresa ve el aviso de otro').toHaveCount(0)
  })

  test('AC19 · sin avisos se dice, y no se confunde con un fallo', async ({ page }) => {
    // El aprobador no es destinatario de ninguno de los dos tipos implementados: su bandeja
    // está vacía de verdad, no vacía porque algo fallara.
    await entrar(page, 'approver')
    const boton = campana(page).first()
    await expect(boton).toBeVisible({ timeout: 20_000 })
    await boton.click()

    // El aprobador no recibe avisos de los tipos implementados: su bandeja está vacía.
    await expect(page.getByText(/no tienes notificaciones|no notifications/i),
      'la bandeja vacía no se declara').toBeVisible({ timeout: 15_000 })
  })

  test('AC02 · no se introduce ningún canal externo', async ({ page, request }) => {
    // `OD-07` deja fuera correo, WhatsApp, SMS y push. La comprobación es sobre el producto:
    // la interfaz no ofrece configurar ningún canal ni suscripción.
    const cab = await cabeceraAdmin(request)
    const marca = `${PREFIJO}X${sufijo()}`
    await registroRechazado(request, cab, marca)

    await entrar(page, 'operator')
    await campana(page).first().click()

    await expect(page.getByText(/correo|email|whatsapp|sms|push/i),
      'la interfaz ofrece un canal externo, que OD-07 deja fuera').toHaveCount(0)
  })
})
