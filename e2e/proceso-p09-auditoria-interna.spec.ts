/**
 * P-09 — AUDITORÍA INTERNA   (`spec.md §4.11`, `docs/02 §3.11`)
 *
 * «Cada acción en el sistema genera un registro de auditoría inmutable», con usuario,
 * acción, fecha, módulo y entidad; y una vista filtrable por usuario, lote, fecha, tipo de
 * operación, módulo, estado y documento SAP.
 *
 * No confundir con `P-10`: aquélla relaciona lotes entre generaciones; ésta relaciona
 * **acciones con quien las hizo**.
 *
 * `GA-REM-032` cerró dos huecos:
 *   R-81  seis de los once módulos declarados no producían ni un registro
 *   R-82  la vista aparentaba filtrar y no filtraba
 */
import { test, expect } from '@playwright/test'
import { API, cabeceraAdmin, crearEscenario, hoy, sufijo } from '../test-support/e2e-api'

async function auditar(request: any, cab: any, params: Record<string, string> = {}) {
  const q = new URLSearchParams({ limit: '200', ...params }).toString()
  const r = await request.get(`${API}/audit?${q}`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  return (await r.json()).logs as any[]
}

test.describe('P-09 · cadena de auditoría interna', () => {
  test('el acceso al sistema deja rastro, con actor y módulo', async ({ request }) => {
    const cab = await cabeceraAdmin(request)   // el propio login es la acción auditada

    const accesos = await auditar(request, cab, { action: 'login', module: 'auth' })
    expect(accesos.length, 'el inicio de sesión no dejó rastro').toBeGreaterThan(0)

    const ultimo = accesos[0]
    expect(ultimo.user_id, 'el registro no identifica al actor').toBeTruthy()
    expect(ultimo.module).toBe('auth')
    expect(ultimo.created_at).toBeTruthy()
  })

  test('el alta de un maestro deja rastro con su entidad', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P09${sufijo()}`, 'breeder')

    const altas = await auditar(request, cab, { action: 'created', module: 'masters' })
    const dela = altas.filter(l => l.entity_type === 'farm' && l.entity_id === String(esc.farmId))
    expect(dela, 'el alta de la granja no dejó rastro').toHaveLength(1)
    expect(dela[0].user_id).toBeTruthy()

    // Y el lote va a su propio módulo, no al de maestros.
    const lotes = await auditar(request, cab, { action: 'created', module: 'lots' })
    expect(lotes.map(l => l.entity_id)).toContain(String(esc.lotId))
  })

  test('el cambio de permisos deja rastro', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const s = sufijo()
    const rol = await request.post(`${API}/roles`, {
      headers: cab,
      data: { name: `P09-rol-${s}`, description: 'Auditoría', permissions: [{ module: 'lots', action: 'read' }] },
    })
    expect(rol.status(), await rol.text()).toBe(201)
    const rolId = String((await rol.json()).id)

    const cambios = await auditar(request, cab, { action: 'permission_change', module: 'users' })
    const suyo = cambios.filter(l => l.entity_id === rolId)
    expect(suyo, 'el alta del rol no dejó rastro de permisos').toHaveLength(1)
  })

  test('los filtros acotan de verdad y se pueden componer', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P09F${sufijo()}`, 'breeder')

    // Filtro por módulo: solo maestros, ningún registro de otro módulo se cuela.
    const maestros = await auditar(request, cab, { module: 'masters' })
    expect(maestros.length).toBeGreaterThan(0)
    expect(maestros.every(l => l.module === 'masters'), 'el filtro de módulo dejó pasar otros').toBe(true)

    // Filtro por acción: idéntico razonamiento.
    const altas = await auditar(request, cab, { action: 'created' })
    expect(altas.every(l => l.action === 'created')).toBe(true)

    // Compuesto: el resultado debe cumplir las dos condiciones a la vez.
    const ambos = await auditar(request, cab, { action: 'created', module: 'lots' })
    expect(ambos.length).toBeGreaterThan(0)
    expect(ambos.every(l => l.action === 'created' && l.module === 'lots')).toBe(true)
    expect(ambos.map(l => l.entity_id)).toContain(String(esc.lotId))
  })

  test('el filtro de fecha responde en vez de romperse', async ({ request }) => {
    // `R-84`. Comparaba la cadena contra una columna `timestamptz` y devolvía 500. Es el
    // único filtro que la interfaz enviaba, de modo que estrenarlo rompía la pantalla.
    const cab = await cabeceraAdmin(request)
    const r = await request.get(`${API}/audit?limit=50&date_from=${hoy()}`, { headers: cab })
    expect(r.status(), await r.text()).toBe(200)
    const registros = (await r.json()).logs as any[]
    expect(registros.every(l => String(l.created_at).slice(0, 10) >= hoy())).toBe(true)
  })

  test('sin permiso de auditoría no se consulta', async ({ request }) => {
    const clave = process.env.GA_TEST_OPERATOR_PASSWORD
    const entrada = await request.post(`${API}/login`, {
      data: { username: 'test_operator', password: clave },
    })
    expect(entrada.status()).toBe(200)
    const operador = { Authorization: `Bearer ${(await entrada.json()).access_token}` }

    const r = await request.get(`${API}/audit`, { headers: operador })
    expect(r.status(), 'un operador sin `audit:read` consultó la auditoría').toBe(403)
  })
})
