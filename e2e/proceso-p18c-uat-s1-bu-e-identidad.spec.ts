import { test, expect } from '@playwright/test';
import * as fs from 'node:fs';
import { API, cabeceraAdmin, crearEscenario, hoy, sufijo } from '../test-support/e2e-api';
import { crearRol, crearUsuario, entrarComo } from '../test-support/admin-rbac';
import { entrar } from '../test-support/auth';

test.describe.configure({ mode: 'serial' });

const EVIDENCIA = 'audit/ga-uat-breeder-cria-s1-2026-11-10/evidence';
const SHOTS = `${EVIDENCIA}/screenshots`;

let admin: Record<string, string>;
let breeder: { companyId: string; farmId: string; houseId: string; lotId: string; codigo: string };
let broiler: { companyId: string; farmId: string; houseId: string; lotId: string; codigo: string };
let eventoBreeder = '';
let eventoBroiler = '';
let rolId = '';
let userIdBreeder = '';
let userIdSinBu = '';
let usuarioBreeder = '';
let usuarioSinBu = '';
let clave = '';
let tokenBreeder = '';
let tokenSinBu = '';
let granjaNombre = '';
let galponNombre = '';
const http: Record<string, unknown> = {};

test.beforeAll(async ({ request }) => {
  admin = await cabeceraAdmin(request);
  await request.patch(`${API}/business-units/breeder/enable`, { headers: admin });
  await request.patch(`${API}/business-units/broiler/enable`, { headers: admin });

  breeder = await crearEscenario(request, admin, 'S1P18C', 'breeder');
  broiler = await crearEscenario(request, admin, 'S1P18C', 'broiler');
  http['escenario.breeder'] = breeder;
  http['escenario.broiler'] = broiler;

  const rBreeder = await request.post(`${API}/operations`, {
    headers: admin,
    data: {
      event_type: 'bird_reception',
      lot_id: breeder.lotId,
      farm_id: breeder.farmId,
      house_id: breeder.houseId,
      event_date: hoy(),
      received_total: 1000,
      dead_on_arrival: 15,
      rejected_on_arrival: 5,
      bird_movements: [
        { sex: 'male', quantity: 100, avg_weight: 2.0 },
        { sex: 'female', quantity: 880, avg_weight: 1.8 },
      ],
    },
  });
  http['POST /operations recepcion breeder'] = rBreeder.status();
  const bodyRBreeder = await rBreeder.json();
  eventoBreeder = String(bodyRBreeder.id ?? bodyRBreeder.event_id ?? '');

  const mBreeder = await request.post(`${API}/operations`, {
    headers: admin,
    data: {
      event_type: 'mortality_recording',
      lot_id: breeder.lotId,
      event_date: hoy(),
      bird_movements: [{ sex: 'male', quantity: 3 }],
    },
  });
  http['POST /operations mortalidad breeder'] = mBreeder.status();

  const rBroiler = await request.post(`${API}/operations`, {
    headers: admin,
    data: {
      event_type: 'bird_reception',
      lot_id: broiler.lotId,
      farm_id: broiler.farmId,
      house_id: broiler.houseId,
      event_date: hoy(),
      bird_movements: [{ sex: 'mixed', quantity: 100 }],
    },
  });
  http['POST /operations recepcion broiler'] = rBroiler.status();
  const bodyRBroiler = await rBroiler.json();
  eventoBroiler = String(bodyRBroiler.id ?? bodyRBroiler.event_id ?? '');

  const mBroiler = await request.post(`${API}/operations`, {
    headers: admin,
    data: {
      event_type: 'mortality_recording',
      lot_id: broiler.lotId,
      event_date: hoy(),
      bird_movements: [{ sex: 'mixed', quantity: 3 }],
    },
  });
  http['POST /operations mortalidad broiler'] = mBroiler.status();

  rolId = await crearRol(request, admin, `s1p18c-rol-${sufijo()}`, [
    { module: 'lots', action: 'read' },
    { module: 'operations', action: 'read' },
    { module: 'operations', action: 'create' },
    { module: 'reports', action: 'read' },
    { module: 'review', action: 'read' },
    { module: 'corrections', action: 'read' },
  ]);
  http['rolId'] = rolId;

  const s = sufijo();
  clave = `Aa1!${s}${sufijo()}`;
  usuarioBreeder = `s1p18c-breeder-${s}`;
  usuarioSinBu = `s1p18c-sinbu-${s}`;

  userIdBreeder = await crearUsuario(request, admin, { username: usuarioBreeder, clave, role_id: rolId });
  userIdSinBu = await crearUsuario(request, admin, { username: usuarioSinBu, clave, role_id: rolId });
  http['userIdBreeder'] = userIdBreeder;
  http['userIdSinBu'] = userIdSinBu;

  const grant = await request.post(`${API}/users/${userIdBreeder}/business-units`, {
    headers: admin,
    data: { code: 'breeder' },
  });
  http['POST /users/{id}/business-units breeder'] = grant.status();

  const loginBreeder = await request.post(`${API}/login`, { data: { username: usuarioBreeder, password: clave } });
  http['POST /login breeder'] = loginBreeder.status();
  tokenBreeder = (await loginBreeder.json()).access_token;

  const loginSinBu = await request.post(`${API}/login`, { data: { username: usuarioSinBu, password: clave } });
  http['POST /login sinbu'] = loginSinBu.status();
  tokenSinBu = (await loginSinBu.json()).access_token;
});

function cab(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}`, Accept: 'application/json' };
}

test('P1 API: identidad BU breeder aísla datos del broiler', async ({ request }) => {
  const cabB = cab(tokenBreeder);

  const rLots = await request.get(`${API}/lots?limit=100`, { headers: cabB });
  expect(rLots.status()).toBe(200);
  const lots = (await rLots.json()) as Array<{ id: string }>;
  const ids = lots.map((l) => String(l.id));
  expect(ids).toContain(String(breeder.lotId));
  expect(ids).not.toContain(String(broiler.lotId));
  http['GET /lots (token breeder)'] = rLots.status();

  const rBroilerType = await request.get(`${API}/lots?bird_type=broiler&limit=100`, { headers: cabB });
  expect(rBroilerType.status()).toBe(200);
  expect(await rBroilerType.json()).toEqual([]);

  const rBreederType = await request.get(`${API}/lots?bird_type=breeder&limit=100`, { headers: cabB });
  expect(rBreederType.status()).toBe(200);
  const breederLots = (await rBreederType.json()) as Array<{ id: string }>;
  expect(breederLots.map((l) => String(l.id))).toContain(String(breeder.lotId));

  const rZzz = await request.get(`${API}/lots?bird_type=zzz&limit=100`, { headers: cabB });
  expect(rZzz.status()).toBe(400);
  http['GET /lots?bird_type=zzz'] = rZzz.status();

  const rLotBroiler = await request.get(`${API}/lots/${broiler.lotId}`, { headers: cabB });
  expect(rLotBroiler.status()).toBe(404);
  http['GET /lots/{broiler}'] = rLotBroiler.status();

  const rOp = await request.get(`${API}/operations/${eventoBroiler}`, { headers: cabB });
  expect(rOp.status()).toBe(404);
  http['GET /operations/{eventoBroiler}'] = rOp.status();

  const codeLower = broiler.codigo.toLowerCase();
  const rOpsByCode = await request.get(`${API}/operations?lot_code=${encodeURIComponent(codeLower)}`, {
    headers: cabB,
  });
  expect(rOpsByCode.status()).toBe(200);
  expect(await rOpsByCode.json()).toEqual([]);
  expect(rOpsByCode.headers()['x-total-count']).toBe('0');
  http['GET /operations?lot_code=<broiler>'] = rOpsByCode.status();

  const rRepLot = await request.get(`${API}/reports/lot/${broiler.lotId}`, { headers: cabB });
  expect(rRepLot.status()).toBe(404);
  http['GET /reports/lot/{broiler}'] = rRepLot.status();

  const rKpis = await request.get(`${API}/reports/kpis?lot_id=${broiler.lotId}`, { headers: cabB });
  expect(rKpis.status()).toBe(404);
  http['GET /reports/kpis?lot_id=<broiler>'] = rKpis.status();

  const rPost = await request.post(`${API}/operations`, {
    headers: cabB,
    data: {
      event_type: 'mortality_recording',
      lot_id: broiler.lotId,
      event_date: hoy(),
      bird_movements: [{ sex: 'mixed', quantity: 1 }],
    },
  });
  const rPostBody = await rPost.text();
  http['POST /operations mortality lote broiler'] = { status: rPost.status(), body: rPostBody };
  // El lote ajeno debe ser invisible: `404`/`403`, o el `400` de `BR-07`
  // (anti-enumeración) que esta superficie usa para «lote no encontrado».
  expect([400, 403, 404]).toContain(rPost.status());
  if (rPost.status() === 400) {
    expect(rPostBody.toLowerCase()).toContain('no encontrado');
  }

  const cabS = cab(tokenSinBu);
  const rSinBu = await request.get(`${API}/lots`, { headers: cabS });
  expect(rSinBu.status()).toBe(200);
  expect(await rSinBu.json()).toEqual([]);
  expect(rSinBu.headers()['x-total-count']).toBe('0');
  http['GET /lots (token sin BU)'] = rSinBu.status();

  const rAdmin = await request.get(`${API}/lots?limit=100`, { headers: admin });
  expect(rAdmin.status()).toBe(200);
  const adminIds = ((await rAdmin.json()) as Array<{ id: string }>).map((l) => String(l.id));
  expect(adminIds).toContain(String(breeder.lotId));
  expect(adminIds).toContain(String(broiler.lotId));
  http['GET /lots (token admin)'] = rAdmin.status();

  const rLotBreeder = await request.get(`${API}/lots/${breeder.lotId}`, { headers: admin });
  expect(rLotBreeder.status()).toBe(200);
  const detalle = (await rLotBreeder.json()) as Record<string, unknown>;
  granjaNombre = String(detalle.farm_name ?? '');
  galponNombre = String(detalle.house_name ?? '');
  expect(granjaNombre.length).toBeGreaterThan(0);
  expect(galponNombre.length).toBeGreaterThan(0);
});

test('P2 UI: usuario breeder solo ve sus lotes', async ({ page }) => {
  await entrarComo(page, usuarioBreeder, clave);
  await page.goto('/lots');
  await expect(page.getByTestId('lot-filter-all')).toBeVisible();
  await expect(page.getByTestId('lot-filter-breeder')).toBeVisible();

  await expect(page.getByTestId('lot-filter-broiler')).toHaveCount(0);
  await expect(page.getByTestId('lot-filter-grandparent')).toHaveCount(0);
  await expect(page.getByTestId('lot-filter-hatchery')).toHaveCount(0);

  const body = page.locator('body');
  await expect(body).toContainText(breeder.codigo);
  await expect(body).not.toContainText(broiler.codigo);

  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: `${SHOTS}/p18c_lotes_solo_breeder.png`, fullPage: true });

  await page.goto(`/lots/${broiler.lotId}`);
  await page.waitForLoadState('networkidle');
  await expect(page.locator('body')).not.toContainText(broiler.codigo);

  await page.goto(`/reports/lot/${broiler.lotId}`);
  await page.waitForLoadState('networkidle');
  await expect(page.locator('body')).not.toContainText(broiler.codigo);
  http['UI /reports/lot/{broiler} sin codigo'] = 'ok';
});

test('P2b UI: usuario sin unidades no consulta lotes', async ({ page }) => {
  const peticiones: string[] = [];
  page.on('request', (req) => {
    if (req.url().includes('/api/v1/lots?')) peticiones.push(req.url());
  });

  await entrarComo(page, usuarioSinBu, clave);
  await page.goto('/lots');

  const aviso = page.getByTestId('lots-no-units');
  await expect(aviso).toBeVisible();
  await expect(aviso).toContainText('Sin unidades de negocio asignadas');
  expect(peticiones, `peticiones inesperadas: ${peticiones.join(', ')}`).toEqual([]);

  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: `${SHOTS}/p18c_lotes_sin_unidades.png`, fullPage: true });
  http['UI /lots sin unidades'] = { aviso: true, peticiones: peticiones.length };
});

test('P3 UI admin: ficha de lote, evento y filtro por codigo de lote', async ({ page }) => {
  await entrar(page, 'admin');

  await page.goto(`/lots/${breeder.lotId}`);
  const bodyLote = page.locator('body');
  await expect(bodyLote).toContainText(granjaNombre);
  await expect(bodyLote).toContainText(galponNombre);
  await expect(bodyLote).toContainText('Activo');

  await page.goto(`/operations/${eventoBreeder}`);
  const bodyEvento = page.locator('body');
  await expect(bodyEvento).toContainText(breeder.codigo);
  await expect(bodyEvento).toContainText(granjaNombre);

  const urlsOps: string[] = [];
  page.on('request', (req) => {
    if (req.url().includes('/api/v1/operations')) urlsOps.push(req.url());
  });

  await page.goto('/operations');
  const filtro = page.getByTestId('operation-filter-lot-code');
  await expect(filtro).toBeVisible();
  const trozo = breeder.codigo.slice(0, Math.min(6, breeder.codigo.length)).toLowerCase();
  await filtro.pressSequentially(trozo, { delay: 30 });
  await page.waitForTimeout(800);

  const conLotCode = urlsOps.filter((u) => u.includes('lot_code='));
  const conLotId = urlsOps.filter((u) => u.includes('lot_id='));
  expect(conLotCode).toHaveLength(1);
  expect(conLotId).toHaveLength(0);

  await expect(page.locator('body')).toContainText(breeder.codigo);
  http['UI /operations filtro lot_code'] = { conLotCode: conLotCode.length, conLotId: conLotId.length };
});

// <!--CHUNK-->

test.afterAll(async () => {
  fs.mkdirSync(EVIDENCIA, { recursive: true });
  const payload = {
    escenario: 'S1 P18C BU identidad',
    breeder,
    broiler,
    eventoBreeder,
    eventoBroiler,
    rolId,
    usuarioBreeder,
    usuarioSinBu,
    granjaNombre,
    galponNombre,
    http,
  };
  fs.writeFileSync(`${EVIDENCIA}/e2e_p18c_bu_identidad.json`, JSON.stringify(payload, null, 2));
});
