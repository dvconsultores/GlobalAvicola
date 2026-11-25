/**
 * `GA-UAT-BREEDER-CRIA-S2-OWNER-DECISIONS` · spec `020` §6 — E2E del cierre de las decisiones Owner.
 *
 * Recorrido de Reproductoras/Cría con el contrato ratificado el 25-11-2026: inspección con contenido
 * (`RR-28`), distribución con aves (`RR-29`), semana derivada de la edad del lote (`RR-30`), lote de
 * vacuna (`RR-31`), causa de mortalidad y descarte (`RR-32`), tipo de alimento (`RR-33`), fase derivada
 * (`RR-34`) y tipo de corrección obligatorio (`RR-27`). El DENY lo da el servidor (es la autoridad); la
 * pantalla se mide en lo que no puede editarse (semana y fase de solo lectura) y en el aviso inline del
 * formulario de corrección.
 */
import { test, expect, type APIRequestContext } from '@playwright/test'
import {
  API, hoy, sufijo, empresaActiva, cabeceraAdmin, crearEscenario, registrar,
} from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

/** Día desplazado desde `hoy()`, en el mismo formato local: nunca fechas literales. */
function dia(dias: number): string {
  const d = new Date(`${hoy()}T12:00:00`)
  d.setDate(d.getDate() + dias)
  return d.toLocaleDateString('sv-SE')
}

const DIAS_DEL_LOTE = 30
/** Fecha del día `n` de vida del lote (día 0 = inicio). */
const fechaDeVida = (n: number) => dia(n - DIAS_DEL_LOTE)

async function como(request: APIRequestContext, quien: 'operator') {
  const claves = { operator: ['test_operator', process.env.GA_TEST_OPERATOR_PASSWORD!] } as const
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

async function listar(request: APIRequestContext, cabecera: any, ruta: string): Promise<any[]> {
  const r = await request.get(`${API}${ruta}`, { headers: cabecera })
  expect(r.status(), `${ruta}: ${await r.text()}`).toBe(200)
  return await r.json()
}

/** Causa compartida «Desconocida» sembrada por la migración: es un valor explícito, no `NULL`. */
async function desconocida(request: APIRequestContext, cabecera: any, recurso: string): Promise<number> {
  const filas = await listar(request, cabecera, `/masters/${recurso}?search=Desconocida&limit=100`)
  const fila = filas.find((f) => f.name === 'Desconocida')
  expect(fila, `«Desconocida» debe existir en ${recurso}`).toBeTruthy()
  return fila.id as number
}

interface Mundo {
  admin: any
  operador: any
  esc: any
  loteId: number
  fase: number
  alimento: number
}

/** Lote reproductor con inicio hace 30 días, aves recibidas ese día y una fase vigente. */
async function montar(request: APIRequestContext): Promise<Mundo> {
  const admin = await cabeceraAdmin(request)
  const operador = await como(request, 'operator')
  const esc = await crearEscenario(request, admin, 'S2D', 'breeder')
  const s = sufijo()
  const lote = await crear(request, admin, '/lots', {
    company_id: esc.companyId, farm_id: esc.farmId, house_id: esc.houseId,
    lot_code: `S2D-OWNER-${s}`, bird_type: 'breeder', sex: 'mixed', start_date: fechaDeVida(0),
  })
  const rec = await registrar(request, operador, {
    lot_id: lote.id, farm_id: esc.farmId, house_id: esc.houseId, event_type: 'bird_reception',
    event_date: fechaDeVida(0), received_total: 300, dead_on_arrival: 0, rejected_on_arrival: 0,
    bird_movements: [{ sex: 'mixed', quantity: 300 }],
  })
  expect(rec.status(), `recepción: ${await rec.text()}`).toBe(201)
  const fases = await listar(request, admin, '/masters/productive-phases?limit=100')
  const fase = fases.length
    ? fases[0].id
    : (await crear(request, admin, '/masters/productive-phases', { name: `Cría ${s}`, code: `CR${s}`, order: 1 })).id
  await crear(request, admin, `/lots/${lote.id}/phases`, {
    lot_id: lote.id, phase_id: fase, start_date: fechaDeVida(0),
  })
  const alimento = (await crear(request, admin, '/masters/feed-types', {
    company_id: esc.companyId, name: `S2D-ALIM-${s}`,
  })).id
  return { admin, operador, esc, loteId: lote.id, fase, alimento }
}

async function detalle(request: APIRequestContext, cabecera: any, id: number) {
  const r = await request.get(`${API}/operations/${id}`, { headers: cabecera })
  expect(r.status(), await r.text()).toBe(200)
  return await r.json()
}

test.describe('SPEC 020 §6 · decisiones Owner de la Sesión 2 (reproductoras/cría)', () => {
  test('E2E-S2D-01 · Inspección: vacía se rechaza; con contenido y sin lote se acepta', async ({ request }) => {
    const m = await montar(request)
    const base = {
      farm_id: m.esc.farmId, house_id: m.esc.houseId, event_type: 'farm_inspection', event_date: dia(-1),
    }
    const vacia = await registrar(request, m.operador, { ...base, lot_id: m.loteId })
    expect(vacia.status(), '1 · inspección vacía ⇒ DENY').toBe(400)
    expect((await vacia.json()).rule).toBe('RR-28')

    const sinLote = await registrar(request, m.operador, {
      ...base, inspection_details: [{ parameter: 'temperature', value_numeric: 26.5 }],
    })
    expect(sinLote.status(), `2 · inspección de granja sin lote con contenido ⇒ ALLOW: ${await sinLote.text()}`).toBe(201)
    expect((await sinLote.json()).lot_id).toBeNull()
  })

  test('E2E-S2D-02 · Distribución: cero aves se rechaza; positiva se acepta', async ({ request }) => {
    const m = await montar(request)
    const base = {
      lot_id: m.loteId, farm_id: m.esc.farmId, house_id: m.esc.houseId, event_type: 'bird_distribution',
      event_date: dia(-1),
    }
    const cero = await registrar(request, m.operador, { ...base, bird_movements: [{ sex: 'male', quantity: 0 }] })
    expect(cero.status(), '3 · distribución de cero aves ⇒ DENY').toBe(400)
    expect((await cero.json()).rule).toBe('RR-29')
    const ok = await registrar(request, m.operador, { ...base, bird_movements: [{ sex: 'male', quantity: 40 }] })
    expect(ok.status(), `4 · distribución válida ⇒ ALLOW: ${await ok.text()}`).toBe(201)
  })

  test('E2E-S2D-03 · Alimento: sin tipo se rechaza; con tipo deriva fase y semana', async ({ request }) => {
    const m = await montar(request)
    const base = { lot_id: m.loteId, event_type: 'feed_registration', event_date: fechaDeVida(15) }
    const sinTipo = await registrar(request, m.operador, { ...base, feed_movements: [{ quantity_kg: 5 }] })
    expect(sinTipo.status(), '5 · alimento sin tipo ⇒ DENY').toBe(400)
    expect((await sinTipo.json()).rule).toBe('RR-33')

    const ok = await registrar(request, m.operador, {
      ...base, feed_movements: [{ feed_type_id: m.alimento, quantity_kg: 5, phase_id: 999999, week_number: 99 }],
    })
    expect(ok.status(), `6 · alimento válido ⇒ ALLOW: ${await ok.text()}`).toBe(201)
    const fila = (await detalle(request, m.admin, (await ok.json()).id)).feed_movements[0]
    expect(fila.phase_id, 'la fase es la vigente del lote, no la que manda el cliente').toBe(m.fase)
    expect(fila.week_number, 'día 15 de vida ⇒ semana 3, no el 99 enviado').toBe(3)
  })

  test('E2E-S2D-04 · Pesaje: la semana se deriva y la pantalla no la deja editar', async ({ request, page }) => {
    const m = await montar(request)
    const r = await registrar(request, m.operador, {
      lot_id: m.loteId, event_type: 'weight_recording', event_date: fechaDeVida(7),
      bird_movements: [{ sex: 'mixed', quantity: 0, avg_weight: 1500 }],
    })
    expect(r.status(), await r.text()).toBe(201)
    expect((await detalle(request, m.admin, (await r.json()).id)).bird_movements[0].week_number, '7 · día 7 ⇒ semana 2').toBe(2)

    await entrar(page, 'operator')
    await page.goto('/operations/new?type=weight_recording')
    await expect(page.getByTestId('derived-week'), 'la semana es un texto de solo lectura').toBeVisible({ timeout: 20_000 })
    await expect(page.locator('input[name$="week_number"]'), 'no hay campo de semana editable en el pesaje').toHaveCount(0)

    await page.goto('/operations/new?type=feed_registration')
    await expect(page.getByTestId('derived-phase'), 'la fase del alimento es de solo lectura').toBeVisible({ timeout: 20_000 })
    await expect(page.locator('select[name="extra_data.feed_phase"]'), 'ya no se pide la fase al operador').toHaveCount(0)
  })

  test('E2E-S2D-05 · Mortalidad y descarte: sin causa se rechaza; «Desconocida» se acepta', async ({ request }) => {
    const m = await montar(request)
    const mov = [{ sex: 'mixed', quantity: 2 }]
    const base = { lot_id: m.loteId, event_date: fechaDeVida(10), bird_movements: mov }

    const sinCausaM = await registrar(request, m.operador, { ...base, event_type: 'mortality_recording' })
    expect(sinCausaM.status(), '8 · mortalidad sin causa ⇒ DENY').toBe(400)
    expect((await sinCausaM.json()).rule).toBe('RR-32')
    const okM = await registrar(request, m.operador, {
      ...base, event_type: 'mortality_recording', cause_id: await desconocida(request, m.admin, 'mortality-causes'),
    })
    expect(okM.status(), `9 · mortalidad con causa «Desconocida» ⇒ ALLOW: ${await okM.text()}`).toBe(201)

    const sinCausaC = await registrar(request, m.operador, { ...base, event_type: 'cull_recording' })
    expect(sinCausaC.status(), '10 · descarte sin causa ⇒ DENY').toBe(400)
    expect((await sinCausaC.json()).rule).toBe('RR-32')
    const okC = await registrar(request, m.operador, {
      ...base, event_type: 'cull_recording', cull_cause_id: await desconocida(request, m.admin, 'cull-causes'),
    })
    expect(okC.status(), `11 · descarte válido ⇒ ALLOW: ${await okC.text()}`).toBe(201)
  })

  test('E2E-S2D-06 · Vacunación: sin lote de vacuna se rechaza; con lote se acepta', async ({ request }) => {
    const m = await montar(request)
    const vacuna = (await crear(request, m.admin, '/masters/vaccines', {
      company_id: m.esc.companyId, name: `S2D-VAC-${sufijo()}`,
    })).id
    const base = {
      lot_id: m.loteId, event_type: 'vaccination', event_date: fechaDeVida(10), vaccine_id: vacuna,
      vaccination_route: 'water',
    }
    const sin = await registrar(request, m.operador, base)
    expect(sin.status(), '12 · vacunación sin lote de vacuna ⇒ DENY').toBe(400)
    expect((await sin.json()).rule).toBe('RR-31')
    const blanco = await registrar(request, m.operador, { ...base, vaccine_lot_number: '   ' })
    expect(blanco.status(), 'el lote de solo espacios tampoco es texto').toBe(400)
    const ok = await registrar(request, m.operador, { ...base, vaccine_lot_number: `LOT-${sufijo()}` })
    expect(ok.status(), `13 · vacunación con lote ⇒ ALLOW: ${await ok.text()}`).toBe(201)
  })

  test('E2E-S2D-07 · Corrección: sin tipo se bloquea en pantalla; con tipo se guarda y la fecha recalcula la semana', async ({
    request, page,
  }) => {
    const m = await montar(request)
    let tipos = await listar(request, m.admin, '/masters/correction-types?limit=100')
    if (!tipos.length) {
      await crear(request, m.admin, '/masters/correction-types', { company_id: m.esc.companyId, name: `Error de digitación ${sufijo()}` })
      tipos = await listar(request, m.admin, '/masters/correction-types?limit=100')
    }

    // evento a corregir: un pesaje que se envía a revisión y se pone en revisión
    const alta = await registrar(request, m.operador, {
      lot_id: m.loteId, event_type: 'weight_recording', event_date: fechaDeVida(6),
      bird_movements: [{ sex: 'mixed', quantity: 0, avg_weight: 1500 }],
    })
    expect(alta.status(), await alta.text()).toBe(201)
    const id = (await alta.json()).id as number
    const enviado = await request.post(`${API}/operations/${id}/submit`, { headers: m.operador })
    expect(enviado.status(), await enviado.text()).toBe(200)
    const revision = await request.post(`${API}/review/start/${id}`, { headers: m.admin })
    expect(revision.status(), await revision.text()).toBe(200)

    // API — el servidor también exige el tipo (RR-27) y la semana sigue a la fecha corregida (RR-30)
    const sinTipo = await request.post(`${API}/corrections`, { headers: m.admin, data: {
      event_id: id, field_name: 'event_date', corrected_value: fechaDeVida(14), reason: 'Fecha mal digitada',
    } })
    expect(sinTipo.status(), '14 · corrección sin tipo ⇒ DENY').toBe(400)
    expect((await sinTipo.json()).rule).toBe('RR-27')

    // UI — el formulario avisa en línea y no envía hasta que se elige el tipo
    await entrar(page, 'admin')
    await page.goto('/review')
    await page.getByRole('button', { name: /^En revisión$/i }).click()
    await page.getByTestId('review-filter-lot').fill(m.esc.codigo.slice(-6).toLowerCase())
    await page.goto(`/review/${id}`)
    await page.getByRole('link', { name: /corregir/i }).first().click()
    await expect(page.getByTestId('correction-original')).toBeVisible({ timeout: 20_000 })
    await page.locator('form select').first().selectOption('observations')
    await page.getByTestId('correction-corrected').fill('Observación corregida desde pantalla')
    await page.getByPlaceholder(/Explica por qué/).fill('Corrección de prueba E2E')
    let posts = 0
    page.on('request', (q) => { if (q.method() === 'POST' && q.url().includes('/corrections')) posts += 1 })
    await page.getByRole('button', { name: /Guardar Corrección/ }).click()
    await expect(page.getByText('Seleccione el tipo de corrección'), 'aviso inline en español').toBeVisible()
    expect(posts, 'sin tipo no se envía nada').toBe(0)
    await page.getByTestId('correction-type').selectOption({ index: 1 })
    await page.getByRole('button', { name: /Guardar Corrección/ }).click()
    await expect(page).toHaveURL(new RegExp(`/review/${id}$`), { timeout: 20_000 })

    // API — con tipo, corregir la fecha recalcula la semana
    const conTipo = await request.post(`${API}/corrections`, { headers: m.admin, data: {
      event_id: id, field_name: 'event_date', corrected_value: fechaDeVida(14), reason: 'Fecha mal digitada',
      correction_type_id: tipos[0].id,
    } })
    expect(conTipo.status(), `15 · corrección de fecha con tipo ⇒ ALLOW: ${await conTipo.text()}`).toBe(201)
    expect((await detalle(request, m.admin, id)).bird_movements[0].week_number, 'día 14 ⇒ semana 3').toBe(3)
  })

  test('E2E-S2D-08 · Históricos: los eventos anteriores siguen legibles en lista y detalle', async ({ request, page }) => {
    const m = await montar(request)
    const lista = await request.get(`${API}/operations?limit=100`, { headers: m.admin })
    expect(lista.status(), '16 · la lista sigue respondiendo con registros antiguos y nuevos').toBe(200)
    const eventos = await lista.json()
    expect(Array.isArray(eventos) && eventos.length > 0).toBeTruthy()
    for (const e of eventos.slice(0, 5)) {
      const d = await request.get(`${API}/operations/${e.id}`, { headers: m.admin })
      expect(d.status(), `detalle de #${e.id}`).toBe(200)
    }
    await entrar(page, 'admin')
    await page.goto('/operations')
    await expect(page.getByRole('row').nth(1), 'la lista de operaciones se pinta').toBeVisible({ timeout: 20_000 })
  })
})
