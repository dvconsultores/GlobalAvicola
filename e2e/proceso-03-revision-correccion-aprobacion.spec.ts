/**
 * PROCESO 03 — REVISIÓN → CORRECCIÓN → APROBACIÓN
 *
 * Tercero del orden de `GA-REM-016` y, según la spec, «el diferenciador declarado del
 * producto». Depende de `GA-REM-006` y `GA-REM-007`, ambas `CERTIFIED`.
 *
 * Regla vigente `RR-01` (Wave 1.5): la corrección escribe el valor en el acto, conserva el
 * original y deja el registro **pendiente de aprobación**. `RC-01` no se reabre.
 *
 * Regla vigente `RR-03`: `BR-14` es configurable por paso, con segregación por defecto.
 * `RC-03` no se reabre.
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

async function como(request: APIRequestContext, quien: 'admin' | 'operator' | 'approver') {
  const claves = {
    admin: ['test_admin', process.env.GA_TEST_ADMIN_PASSWORD!],
    operator: ['test_operator', process.env.GA_TEST_OPERATOR_PASSWORD!],
    approver: ['test_approver', process.env.GA_TEST_APPROVER_PASSWORD!],
  } as const
  const [usuario, clave] = claves[quien]
  return { Authorization: `Bearer ${await token(request, usuario, clave)}` }
}

/** Registra un evento como operador y lo deja en revisión. */
async function eventoEnRevision(request: APIRequestContext) {
  const operador = await como(request, 'operator')
  const creado = await request.post(`${API}/operations`, {
    headers: operador,
    data: {
      lot_id: 2, event_type: 'feed_registration', event_date: hoy(),
      observations: 'valor original del operador',
      feed_movements: [{ quantity_kg: 300.0 }],
    },
  })
  expect(creado.status(), await creado.text()).toBe(201)
  const id = (await creado.json()).id

  const enviado = await request.post(`${API}/operations/${id}/submit`, { headers: operador })
  expect(enviado.status(), await enviado.text()).toBe(200)
  expect((await enviado.json()).status).toBe('pending_review')

  const admin = await como(request, 'admin')
  const revision = await request.post(`${API}/review/start/${id}`, { headers: admin })
  expect(revision.status(), await revision.text()).toBe(200)
  expect((await revision.json()).status).toBe('in_review')
  return id
}

test.describe('Proceso 03 · Revisión → Corrección → Aprobación', () => {
  test('HAPPY PATH · el ciclo completo cambia el dato y termina aprobado', async ({ request }) => {
    const id = await eventoEnRevision(request)
    const admin = await como(request, 'admin')

    // CORRECCIÓN — `RR-01`: el valor se escribe en el acto
    const correccion = await request.post(`${API}/corrections`, {
      headers: admin,
      data: {
        event_id: id, field_name: 'observations',
        corrected_value: 'valor corregido por el supervisor',
        reason: 'Error de digitación detectado en revisión',
      },
    })
    expect(correccion.status(), await correccion.text()).toBe(201)
    const registro = await correccion.json()

    // El original lo lee el servidor del dato, no del payload: la auditoría es evidencia
    expect(registro.original_value).toBe('valor original del operador')
    expect(registro.corrected_value).toBe('valor corregido por el supervisor')

    // El DATO cambió — esto era `P0-2`
    const leido = await request.get(`${API}/operations/${id}`, { headers: admin })
    const evento = await leido.json()
    expect(evento.observations, 'la corrección debe escribir el valor').toBe(
      'valor corregido por el supervisor')
    expect(evento.status, 'corregir no es aprobar (RR-01)').toBe('corrected')
    expect(evento.approved_by_id).toBeNull()
    expect(evento.version, 'una corrección produce versión nueva').toBeGreaterThan(1)

    // APROBACIÓN — con una identidad distinta de la que registró (`BR-14`)
    const aprobador = await como(request, 'approver')
    const aprobado = await request.post(`${API}/approvals/approve`, {
      headers: aprobador, data: { event_id: id, observations: 'Verificado' },
    })
    expect(aprobado.status(), await aprobado.text()).toBe(200)

    const final = await request.get(`${API}/operations/${id}`, { headers: admin })
    const cuerpo = await final.json()
    expect(cuerpo.status).toBe('approved')
    expect(cuerpo.approved_by_id, 'un evento aprobado debe tener aprobador').not.toBeNull()
  })

  test('BR-14 · quien registra no aprueba su propia carga', async ({ request }) => {
    const id = await eventoEnRevision(request)
    const operador = await como(request, 'operator')

    const r = await request.post(`${API}/approvals/approve`, {
      headers: operador, data: { event_id: id },
    })
    expect(r.status(), 'segregación de funciones (RR-03)').toBe(403)

    const admin = await como(request, 'admin')
    const leido = await request.get(`${API}/operations/${id}`, { headers: admin })
    expect((await leido.json()).status, 'el evento no puede haber cambiado').toBe('in_review')
  })

  test('RECHAZO · exige motivo y deja el evento rechazado', async ({ request }) => {
    const id = await eventoEnRevision(request)
    const aprobador = await como(request, 'approver')

    const r = await request.post(`${API}/approvals/reject`, {
      headers: aprobador,
      data: { event_id: id, observations: 'Datos no verificables contra la guía' },
    })
    expect(r.status(), await r.text()).toBe(200)

    const admin = await como(request, 'admin')
    const leido = await request.get(`${API}/operations/${id}`, { headers: admin })
    expect((await leido.json()).status).toBe('rejected')
  })

  test('LISTA BLANCA · una corrección no puede tocar el flujo', async ({ request }) => {
    const id = await eventoEnRevision(request)
    const admin = await como(request, 'admin')

    for (const campo of ['status', 'approved_by_id', 'company_id']) {
      const r = await request.post(`${API}/corrections`, {
        headers: admin,
        data: { event_id: id, field_name: campo, corrected_value: '1',
                reason: 'intento de escalada de privilegios' },
      })
      expect(r.status(), `'${campo}' no es corregible`).toBe(400)
    }

    const leido = await request.get(`${API}/operations/${id}`, { headers: admin })
    expect((await leido.json()).status).toBe('in_review')
  })

  test('R-32 · el estado no se fija con un PUT', async ({ request }) => {
    const id = await eventoEnRevision(request)
    const admin = await como(request, 'admin')

    const r = await request.put(`${API}/operations/${id}`, {
      headers: admin, data: { status: 'approved' },
    })
    expect(r.status(), 'el estado solo cambia por el flujo').toBe(422)

    const leido = await request.get(`${API}/operations/${id}`, { headers: admin })
    const cuerpo = await leido.json()
    expect(cuerpo.status).toBe('in_review')
    expect(cuerpo.approved_by_id).toBeNull()
  })

  test('AUTORIZACIÓN · un operador no aprueba ni rechaza', async ({ request }) => {
    const operador = await como(request, 'operator')
    for (const ruta of ['approve', 'reject']) {
      const r = await request.post(`${API}/approvals/${ruta}`, {
        headers: operador, data: { event_id: 1, observations: 'x' },
      })
      expect(r.status(), `el operador no puede ${ruta}`).toBe(403)
    }
  })

  test('AUDITORÍA · el ciclo deja rastro de cada transición', async ({ request }) => {
    const id = await eventoEnRevision(request)
    const admin = await como(request, 'admin')

    await request.post(`${API}/corrections`, {
      headers: admin,
      data: { event_id: id, field_name: 'observations', corrected_value: 'x',
              reason: 'prueba de auditoría del ciclo' },
    })

    const auditoria = await request.get(`${API}/audit?limit=200`, { headers: admin })
    expect(auditoria.status()).toBe(200)
    const suyos = ((await auditoria.json()).logs ?? [])
      .filter((l: any) => String(l.entity_id) === String(id))
    expect(suyos.length, 'debe haber rastro del ciclo').toBeGreaterThan(1)

    const acciones = new Set(suyos.map((l: any) => l.action))
    expect(acciones.size, 'más de un tipo de acción registrada').toBeGreaterThan(1)
    expect(JSON.stringify(suyos), 'la auditoría no guarda secretos').not.toContain('password')
  })
})
