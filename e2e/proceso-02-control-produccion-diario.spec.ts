/**
 * PROCESO 02 — CONTROL DE PRODUCCIÓN DIARIO
 *
 * Segundo del orden de `GA-REM-016`: mortalidad, alimento y pesaje. Concentraba el
 * bloqueador `P0-1` y es el de mayor frecuencia operativa.
 *
 * Depende de `GA-REM-005`, ya `CERTIFIED`. Aquí no se reabre su implementación: se
 * demuestra el proceso de extremo a extremo.
 */
import { test, expect, type APIRequestContext } from '@playwright/test'

const API = 'http://127.0.0.1:8099/api/v1'

function hoy(): string {
  return new Date().toISOString().slice(0, 10)
}

async function token(request: APIRequestContext, usuario: string, clave: string) {
  const r = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
  expect(r.status(), `login de ${usuario}`).toBe(200)
  return (await r.json()).access_token as string
}

async function admin(request: APIRequestContext) {
  const clave = process.env.GA_TEST_ADMIN_PASSWORD!
  return { Authorization: `Bearer ${await token(request, 'test_admin', clave)}` }
}

/** Deja el lote con saldo conocido y devuelve el saldo resultante. */
async function saldoDeAves(request: APIRequestContext, cabecera: any, lotId: number) {
  const lista = await request.get(`${API}/operations?lot_id=${lotId}&limit=100`, { headers: cabecera })
  expect(lista.status()).toBe(200)
  const entradas = new Set(['bird_reception', 'birth_registration'])
  const salidas = new Set(['mortality_recording', 'cull_recording', 'bird_exit', 'chick_dispatch'])
  let total = 0
  for (const evento of await lista.json()) {
    if (evento.status === 'cancelled') continue
    const detalle = await request.get(`${API}/operations/${evento.id}`, { headers: cabecera })
    const cantidad = ((await detalle.json()).bird_movements ?? [])
      .reduce((a: number, m: any) => a + m.quantity, 0)
    if (entradas.has(evento.event_type)) total += cantidad
    else if (salidas.has(evento.event_type)) total -= cantidad
  }
  return total
}

test.describe('Proceso 02 · Control de producción diario', () => {
  test('HAPPY PATH · mortalidad con causa, y el saldo baja', async ({ request }) => {
    const cabecera = await admin(request)

    await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 2, farm_id: 1, house_id: 1, event_type: 'bird_reception',
        event_date: hoy(), bird_movements: [{ sex: 'mixed', quantity: 1000 }],
      },
    })
    const antes = await saldoDeAves(request, cabecera, 2)

    const causas = await request.get(`${API}/masters/mortality-causes`, { headers: cabecera })
    expect(causas.status()).toBe(200)
    const causaId = (await causas.json())[0]?.id

    const r = await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 2, event_type: 'mortality_recording', event_date: hoy(),
        cause_id: causaId,
        bird_movements: [{ sex: 'mixed', quantity: 10 }],
      },
    })
    expect(r.status(), await r.text()).toBe(201)
    const evento = await r.json()
    expect(evento.cause_id, 'la causa es exigencia del cliente y debe conservarse').toBe(causaId)

    expect(await saldoDeAves(request, cabecera, 2), 'el saldo debe reflejar la baja')
      .toBe(antes - 10)
  })

  test('REGLA · BR-01 rechaza mortalidad superior al saldo', async ({ request }) => {
    const cabecera = await admin(request)
    const saldo = await saldoDeAves(request, cabecera, 2)

    const r = await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 2, event_type: 'mortality_recording', event_date: hoy(),
        bird_movements: [{ sex: 'mixed', quantity: saldo + 1 }],
      },
    })
    expect(r.status()).toBe(400)
    const cuerpo = await r.json()
    expect(cuerpo.rule).toBe('BR-01')
    expect(cuerpo.detail).toContain(String(saldo))
    expect(await saldoDeAves(request, cabecera, 2), 'nada debe persistirse').toBe(saldo)
  })

  test('REGLA · una mortalidad de cero no es un registro', async ({ request }) => {
    const cabecera = await admin(request)
    const r = await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 2, event_type: 'mortality_recording', event_date: hoy(),
        bird_movements: [{ sex: 'mixed', quantity: 0 }],
      },
    })
    expect([400, 422]).toContain(r.status())
  })

  test('ALERTA · el umbral configurado dispara la alerta', async ({ request }) => {
    const cabecera = await admin(request)

    await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 1, farm_id: 1, house_id: 1, event_type: 'bird_reception',
        event_date: hoy(), bird_movements: [{ sex: 'mixed', quantity: 10000 }],
      },
    })
    const saldo = await saldoDeAves(request, cabecera, 1)
    const cantidad = Math.ceil(saldo * 0.10) // 10 %: por encima del umbral crítico (8 %)

    const r = await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 1, event_type: 'mortality_recording', event_date: hoy(),
        bird_movements: [{ sex: 'mixed', quantity: cantidad }],
      },
    })
    expect(r.status(), await r.text()).toBe(201)
    const eventoId = (await r.json()).id

    const alertas = await request.get(`${API}/operations/alerts?lot_id=1`, { headers: cabecera })
    expect(alertas.status(), 'el endpoint de alertas debe ser alcanzable').toBe(200)
    const suyas = (await alertas.json()).filter((a: any) => a.event_id === eventoId)
    expect(suyas.length, 'una mortalidad del 10 % debe alertar').toBeGreaterThan(0)
    expect(suyas[0].severity).toBe('critical')
  })

  test('ALIMENTO · el consumo se registra con su tipo', async ({ request }) => {
    const cabecera = await admin(request)
    const tipos = await request.get(`${API}/masters/feed-types`, { headers: cabecera })
    expect(tipos.status()).toBe(200)
    const tipoId = (await tipos.json())[0]?.id

    const r = await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 2, event_type: 'feed_registration', event_date: hoy(),
        feed_movements: [{ feed_type_id: tipoId, quantity_kg: 250.5, sacks_count: 5 }],
      },
    })
    expect(r.status(), await r.text()).toBe(201)

    const detalle = await request.get(`${API}/operations/${(await r.json()).id}`, { headers: cabecera })
    const movimientos = (await detalle.json()).feed_movements
    expect(movimientos[0].quantity_kg).toBe(250.5)
    expect(movimientos[0].feed_type_id).toBe(tipoId)
  })

  test('PESAJE · el peso promedio se conserva', async ({ request }) => {
    const cabecera = await admin(request)
    const r = await request.post(`${API}/operations`, {
      headers: cabecera,
      data: {
        lot_id: 2, event_type: 'weight_recording', event_date: hoy(), sample_size: 30,
        bird_movements: [{ sex: 'mixed', quantity: 30, avg_weight: 1850.5 }],
      },
    })
    expect(r.status(), await r.text()).toBe(201)
    expect((await r.json()).sample_size, 'la muestra tomada es exigencia del cliente').toBe(30)

    const detalle = await request.get(`${API}/operations/${(await r.json()).id}`, { headers: cabecera })
    expect((await detalle.json()).bird_movements[0].avg_weight).toBe(1850.5)
  })

  test('AISLAMIENTO · no se registra mortalidad en un lote ajeno', async ({ request }) => {
    const claveOp = process.env.GA_TEST_OPERATOR_PASSWORD!
    const jwtOp = await token(request, 'test_operator', claveOp)
    const cabecera = await admin(request)

    const cambio = await request.post(`${API}/switch-company`, {
      headers: cabecera, data: { company_id: 2 },
    })
    const jwtB = (await cambio.json()).access_token
    const granja = await request.post(`${API}/masters/farms`, {
      headers: { Authorization: `Bearer ${jwtB}` },
      data: { name: 'P2 B', code: `P2-B-${Date.now()}`, company_id: 2 },
    })
    const lote = await request.post(`${API}/lots`, {
      headers: { Authorization: `Bearer ${jwtB}` },
      data: { lot_code: `P2-LOT-${Date.now()}`, farm_id: (await granja.json()).id,
              bird_type: 'broiler', sex: 'mixed' },
    })

    const r = await request.post(`${API}/operations`, {
      headers: { Authorization: `Bearer ${jwtOp}` },
      data: {
        lot_id: (await lote.json()).id, event_type: 'mortality_recording',
        event_date: hoy(), bird_movements: [{ sex: 'mixed', quantity: 1 }],
      },
    })
    expect(r.status()).toBeGreaterThanOrEqual(400)
  })
})
