import { test, expect } from '@playwright/test'
import * as fs from 'node:fs'
import { API, cabeceraAdmin, crearEscenario, hoy, sufijo } from '../test-support/e2e-api'
import { crearRol, crearUsuario } from '../test-support/admin-rbac'
import { entrar } from '../test-support/auth'
test.describe.configure({ mode: 'serial' })
const ev: Record<string, any> = {}
const habil: string[] = []
let admin: any
test.beforeAll(async ({ request }) => {
  admin = await cabeceraAdmin(request)
  const res = await request.get(`${API}/business-units`, { headers: admin })
  const raw: any = await res.json()
  const lista: any[] = Array.isArray(raw) ? raw : (raw.items ?? [])
  ev.business_units = lista.map((bu: any) => ({ code: bu.code, is_enabled: bu.is_enabled }))
  for (const bu of lista) {
    if (!bu.is_enabled && (bu.code === 'breeder' || bu.code === 'broiler')) {
      const r = await request.patch(`${API}/business-units/${bu.code}/enable`, { headers: admin })
      expect(r.ok()).toBeTruthy()
      habil.push(bu.code)
    }
  }
})
test.afterAll(async ({ request }) => {
  for (const code of habil) {
    await request.patch(`${API}/business-units/${code}/disable`, { headers: admin })
  }
  const dir = 'audit/ga-uat-breeder-cria-s1-2026-11-10/evidence'
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(`${dir}/e2e_p19c_autoridad_pendientes.json`, JSON.stringify(ev, null, 2))
})
test('P19-4 autoridad tras PR #1', async ({ request }) => {
  const creds: Array<[string, string | undefined]> = [
    ['test_admin', process.env.GA_TEST_ADMIN_PASSWORD],
    ['test_operator', process.env.GA_TEST_OPERATOR_PASSWORD],
    ['test_approver', process.env.GA_TEST_APPROVER_PASSWORD],
  ]
  ev.me = {}
  const tokens: Record<string, string> = {}
  for (const [usuario, clave] of creds) {
    const r = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
    expect(r.ok()).toBeTruthy()
    const body: any = await r.json()
    tokens[usuario] = body.access_token
    const me = await request.get(`${API}/me`, {
      headers: { Authorization: `Bearer ${body.access_token}` },
    })
    const yo: any = await me.json()
    ev.me[usuario] = { is_super_admin: yo.is_super_admin }
  }
  expect(ev.me.test_admin.is_super_admin).toBe(true)
  expect(ev.me.test_operator.is_super_admin).toBe(false)
  expect(ev.me.test_approver.is_super_admin).toBe(false)
  const rolesOp = await request.get(`${API}/roles`, {
    headers: { Authorization: `Bearer ${tokens.test_operator}` },
  })
  ev.roles_operador_status = rolesOp.status()
  expect(rolesOp.status()).toBe(403)
  const s = sufijo()
  const roleId = await crearRol(request, admin, `S1P19C-R-${s}`, [{ module: 'lots', action: 'read' }])
  const username = `s1p19c-${s}`
  const claveUsuario = `Aa1!${sufijo()}${sufijo()}`
  await crearUsuario(request, admin, { username, clave: claveUsuario, role_id: roleId })
  const login2 = await request.post(`${API}/login`, {
    data: { username, password: claveUsuario },
  })
  expect(login2.ok()).toBeTruthy()
  const tk2: any = await login2.json()
  const me2 = await request.get(`${API}/me`, {
    headers: { Authorization: `Bearer ${tk2.access_token}` },
  })
  const yo2: any = await me2.json()
  ev.me[username] = { is_super_admin: yo2.is_super_admin }
  expect(yo2.is_super_admin).toBe(false)
  const oa = await request.get('http://127.0.0.1:8099/openapi.json')
  ev.openapi = oa.status()
  if (oa.status() === 200) {
    const texto = await oa.text()
    expect(texto.toLowerCase()).not.toContain('bootstrap')
  }
})
test('P19-5a O-3 pendiente nace y no se ve en el historial', async ({ request }) => {
  const s = sufijo()
  const e = await crearEscenario(request, admin, 'S1P19C', 'breeder')
  ev.escenario = { companyId: e.companyId, lotId: e.lotId, codigo: e.codigo }
  ev.granjaNombre = `S1P19C-g-${s}`
  const fr = await request.post(`${API}/masters/farms`, {
    headers: admin,
    data: {
      company_id: e.companyId,
      name: ev.granjaNombre,
      code: `S1P19C-G-${s}`,
      location: 'QA',
      farm_type: 'breeding',
    },
  })
  expect(fr.ok()).toBeTruthy()
  const farm: any = await fr.json()
  const hs = await request.post(`${API}/masters/houses`, {
    headers: admin,
    data: { farm_id: farm.id, name: `S1P19C-h-${s}`, capacity: 50000 },
  })
  expect(hs.ok()).toBeTruthy()
  const house: any = await hs.json()
  const crearLote = (lotCode: string, birdType: string) =>
    request.post(`${API}/lots`, {
      headers: admin,
      data: {
        company_id: e.companyId,
        farm_id: farm.id,
        house_id: house.id,
        lot_code: lotCode,
        bird_type: birdType,
        sex: 'mixed',
      },
    })
  const l1 = await crearLote(`S1P19C-B-${s}`, 'breeder')
  expect(l1.ok()).toBeTruthy()
  const l2 = await crearLote(`S1P19C-R-${s}`, 'broiler')
  expect(l2.ok()).toBeTruthy()
  const insp = await request.post(`${API}/operations`, {
    headers: admin,
    data: {
      event_type: 'farm_inspection',
      event_date: hoy(),
      farm_id: farm.id,
      house_id: house.id,
      inspection_details: [{ house_id: house.id, parameter: 'temperature', value: '24' }],
    },
  })
  expect(insp.status()).toBe(201)
  const op: any = await insp.json()
  ev.pendiente_id = op.id
  const pend = await request.get(`${API}/operations/pending-classification?limit=100`, {
    headers: admin,
  })
  expect(pend.ok()).toBeTruthy()
  const rawPend: any = await pend.json()
  const pendientes: any[] = Array.isArray(rawPend) ? rawPend : (rawPend.items ?? [])
  expect(pendientes.some((x: any) => x.id === ev.pendiente_id)).toBe(true)
  const hist = await request.get(`${API}/operations?farm_id=${farm.id}&limit=100`, {
    headers: admin,
  })
  expect(hist.ok()).toBeTruthy()
  const rawHist: any = await hist.json()
  const historial: any[] = Array.isArray(rawHist) ? rawHist : (rawHist.items ?? [])
  expect(historial.some((x: any) => x.id === ev.pendiente_id)).toBe(false)
})
test('P19-5b O-3 UI y cadena de resolución', async ({ page, request }) => {
  await entrar(page, 'admin')
  await page.goto('/operations/pending-classification')
  await expect(page.locator('[data-testid="pending-row"]').first()).toBeVisible()
  expect(await page.locator('[data-testid="pending-row"]').count()).toBeGreaterThanOrEqual(1)
  await expect(page.locator('body')).toContainText(ev.granjaNombre)
  await page.goto('/operations')
  await expect(page.locator('[data-testid="pending-classification-link"]').first()).toBeVisible()
  await page.goto('/operations/pending-classification')
  const pantalla = page.getByTestId('pending-classification-page')
  await expect(pantalla).toBeVisible()
  ev.texto = (await pantalla.innerText()).slice(0, 400)
  ev.acciones_clasificar = await page
    .locator(
      '[data-testid="pending-classification-page"] button:not([data-testid="back-navigation"]), ' +
        '[data-testid="pending-classification-page"] select',
    )
    .count()
  const dirPng = 'audit/ga-uat-breeder-cria-s1-2026-11-10/evidence/screenshots'
  fs.mkdirSync(dirPng, { recursive: true })
  await page.screenshot({ path: `${dirPng}/p19_pendientes.png`, fullPage: true })
  const bu = await request.get(`${API}/business-units`, { headers: admin })
  const rawBu: any = await bu.json()
  const listaBu: any[] = Array.isArray(rawBu) ? rawBu : (rawBu.items ?? [])
  ev.claves_habilitacion = listaBu.length > 0 ? Object.keys(listaBu[0]) : []
})
