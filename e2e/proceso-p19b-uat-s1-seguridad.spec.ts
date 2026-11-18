import { test, expect } from '@playwright/test'
import * as fs from 'node:fs'
import { API, cabeceraAdmin, cabeceraAdminEnOtraEmpresa, crearEscenario, hoy, sufijo } from '../test-support/e2e-api'
import { crearRol, crearUsuario } from '../test-support/admin-rbac'
test.describe.configure({ mode: 'serial' })
let admin: any, adminOtra: any, evB = 0, evR = 0, tokA = '', tokB = ''
const ev: Record<string, any> = {}
const habil: string[] = []
const login = async (request: any, u: string, c: string) => {
  const r = await request.post(`${API}/login`, { data: { username: u, password: c } })
  return `Bearer ${(await r.json()).access_token}`
}
test.beforeAll(async ({ request }) => {
  admin = await cabeceraAdmin(request)
  const otra = await cabeceraAdminEnOtraEmpresa(request)
  adminOtra = otra.cabecera
  const ur = await request.get(`${API}/business-units`, { headers: admin })
  const raw: any = await ur.json()
  const unidades: any[] = Array.isArray(raw) ? raw : (raw.items ?? raw.data ?? [])
  for (const code of ['breeder', 'broiler']) {
    const u = unidades.find((x: any) => x.code === code)
    if (u && u.is_enabled === false) {
      await request.patch(`${API}/business-units/${code}/enable`, { headers: admin })
      habil.push(code)
    }
  }
  const b = await crearEscenario(request, admin, 'S1P19B', 'breeder')
  const r = await crearEscenario(request, admin, 'S1P19B', 'broiler')
  const op = (data: any) => request.post(`${API}/operations`, { headers: admin, data })
  await op({
    event_type: 'bird_reception', lot_id: b.lotId, farm_id: b.farmId, house_id: b.houseId,
    event_date: hoy(), received_total: 1000, dead_on_arrival: 15, rejected_on_arrival: 5,
    bird_movements: [
      { sex: 'male', quantity: 100, avg_weight: 2.0 },
      { sex: 'female', quantity: 880, avg_weight: 1.8 },
    ],
  })
  await op({
    event_type: 'bird_reception', lot_id: r.lotId, farm_id: r.farmId, house_id: r.houseId,
    event_date: hoy(), bird_movements: [{ sex: 'mixed', quantity: 100 }],
  })
  const mB = await op({
    event_type: 'mortality_recording', lot_id: b.lotId, event_date: hoy(),
    bird_movements: [{ sex: 'male', quantity: 3 }],
  })
  const mR = await op({
    event_type: 'mortality_recording', lot_id: r.lotId, event_date: hoy(),
    bird_movements: [{ sex: 'mixed', quantity: 3 }],
  })
  evB = (await mB.json()).id
  evR = (await mR.json()).id
  const s = sufijo()
  const clave = `Aa1!${sufijo()}${sufijo()}`
  const rolA = await crearRol(request, admin, `S1P19B-A-${s}`, [
    { module: 'lots', action: 'read' },
    { module: 'operations', action: 'read' },
    { module: 'corrections', action: 'read' },
  ])
  const rolB = await crearRol(request, admin, `S1P19B-B-${s}`, [
    { module: 'lots', action: 'read' },
    { module: 'operations', action: 'read' },
  ])
  const uA = await crearUsuario(request, admin, { username: `s1p19b-a-${s}`, clave, role_id: rolA })
  const uB = await crearUsuario(request, admin, { username: `s1p19b-b-${s}`, clave, role_id: rolB })
  for (const uid of [uA, uB]) {
    await request.post(`${API}/users/${uid}/business-units`, { headers: admin, data: { code: 'breeder' } })
  }
  tokA = await login(request, `s1p19b-a-${s}`, clave)
  tokB = await login(request, `s1p19b-b-${s}`, clave)
})
test.afterAll(async ({ request }) => {
  for (const code of habil) {
    await request.patch(`${API}/business-units/${code}/disable`, { headers: admin })
  }
  const dir = 'audit/ga-uat-breeder-cria-s1-2026-11-10/evidence'
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(`${dir}/e2e_p19b_seguridad.json`, JSON.stringify(ev, null, 2))
})
test('P19-3a: correctable-fields exige autenticación y permiso corrections', async ({ request }) => {
  const u = (id: number) => `${API}/corrections/events/${id}/correctable-fields`
  const sinAuth = await request.get(u(evB))
  ev['3a_sin_auth'] = sinAuth.status()
  expect(sinAuth.status()).toBe(401)

  const sinPermiso = await request.get(u(evB), { headers: { Authorization: tokB } })
  ev['3a_usuario_sin_corrections'] = sinPermiso.status()
  expect(sinPermiso.status()).toBe(403)

  const ok = await request.get(u(evB), { headers: { Authorization: tokA } })
  ev['3a_autorizado'] = ok.status()
  expect(ok.status()).toBe(200)
  const lista: any[] = await ok.json()
  expect(Array.isArray(lista)).toBeTruthy()
  expect(lista.length).toBeGreaterThan(0)
  for (const item of lista) expect(item.field_name).toBeTruthy()

  const otroEvento = await request.get(u(evR), { headers: { Authorization: tokA } })
  ev['3a_evento_fuera_de_alcance'] = otroEvento.status()
  expect(otroEvento.status()).toBe(404)

  const inexistente = await request.get(u(999999999), { headers: admin })
  ev['3a_evento_inexistente'] = inexistente.status()
  expect(inexistente.status()).toBe(404)
})
test('P19-3b: correctable-fields no filtra entre empresas', async ({ request }) => {
  const u = (id: number) => `${API}/corrections/events/${id}/correctable-fields`
  const ajeno = await request.get(u(evB), { headers: adminOtra })
  ev['3b_admin_otra_empresa'] = ajeno.status()
  expect(ajeno.status()).toBe(404)

  const propio = await request.get(u(evB), { headers: admin })
  ev['3b_admin_misma_empresa'] = propio.status()
  expect(propio.status()).toBe(200)
})

