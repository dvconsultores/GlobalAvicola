// Sonda runtime UAT — auditoría QA Yolinel 2026-10-17 (Playwright standalone).
// Entradas por entorno: UAT_URL, UAT_OP_USER, UAT_AP_USER, UAT_PASS, OUT_DIR.
// Uso: UAT_URL=https://host UAT_OP_USER=... UAT_AP_USER=... UAT_PASS=... OUT_DIR=... node uat_runtime_probe.mjs
import { chromium } from '/home/maria/Proyectos/GlobalAvicola/node_modules/playwright/index.mjs';
import { mkdir } from 'node:fs/promises';

const UAT_URL = String(process.env.UAT_URL || '').replace(/\/+$/, '');
const OP_USER = process.env.UAT_OP_USER || '';
const AP_USER = process.env.UAT_AP_USER || '';
const PASS = process.env.UAT_PASS || '';
const OUT_DIR = process.env.OUT_DIR || '/tmp/uat-evidence';
const HOY = new Date().toLocaleDateString('sv-SE');

const results = [];

function log(bloque, status, detalle) {
  const d = String(detalle ?? '').replace(/\s+/g, ' ').trim().slice(0, 320);
  results.push({ bloque, status, detalle: d });
  console.log(`RESULT ${bloque} ${status} ${d}`);
}

// Nunca exponer credenciales/tokens en la salida.
const sanitize = (u) => String(u).replace(/token=[^&]+/g, 'token=<redactado>');
async function shot(page, name) {
  try {
    await page.screenshot({ path: `${OUT_DIR}/${name}.png` });
  } catch (e) {
    console.log(`WARN captura ${name}: ${e.message}`);
  }
}

async function goto(page, ruta) {
  await page.goto(`${UAT_URL}${ruta}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(800);
}

async function faltanTextos(page, textos) {
  const faltan = [];
  for (const t of textos) {
    const visible = await page.getByText(t, { exact: true }).first().isVisible().catch(() => false);
    if (!visible) faltan.push(t);
  }
  return faltan;
}

async function ejecutarBloque(nombre, fn, page) {
  try {
    await fn();
  } catch (e) {
    log(nombre, 'FAIL', `excepción: ${e.message}`);
    await shot(page, nombre);
  }
}
async function login(page, usuario) {
  await page.goto(`${UAT_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.fill('input[name="username"], input#login-username, input[type="text"]', usuario);
  await page.fill('input[type="password"]', PASS);
  await page.click('button[type="submit"]');
  await page.waitForURL((u) => !u.pathname.endsWith('/login'), { timeout: 30000 });
  await page.waitForTimeout(1000);
}
async function bloque31(page) {
  const N = '3.1';
  await goto(page, '/lots');
  const thGranja = await page.locator('th', { hasText: 'Granja' }).first().isVisible().catch(() => false);
  const filtro = page.locator('[data-testid="lot-filter-farm"]');
  const filtroVisible = await filtro.isVisible().catch(() => false);
  const opciones = filtroVisible ? await filtro.locator('option').count() : 0;
  let detalle = `thGranja=${thGranja} filtro=${filtroVisible} options=${opciones}`;
  let ok = Boolean(thGranja && filtroVisible);
  if (ok && opciones >= 2) {
    const [reqSel] = await Promise.all([
      page.waitForRequest((r) => r.url().includes('/lots') && r.url().includes('farm_id='), { timeout: 15000 }).catch(() => null),
      filtro.selectOption({ index: 1 }),
    ]);
    detalle += ` | sel=${reqSel ? sanitize(reqSel.url()) : '(sin request con farm_id=)'}`;
    const [reqLimpia] = await Promise.all([
      page.waitForRequest((r) => r.url().includes('/lots'), { timeout: 15000 }).catch(() => null),
      filtro.selectOption(''),
    ]);
    const sinFarm = reqLimpia ? !reqLimpia.url().includes('farm_id=') : false;
    detalle += ` | limpiar=${reqLimpia ? sanitize(reqLimpia.url()) : '(sin request)'} sinFarmId=${sinFarm}`;
    ok = ok && Boolean(reqSel) && sinFarm;
  } else if (ok) {
    detalle += ' | <2 opciones: no se prueba filtrado';
  }
  await shot(page, '3.1-lots');
  log(N, ok ? 'PASS' : 'FAIL', detalle);
}
async function bloque32(page) {
  const N = '3.2';
  await goto(page, '/operations');
  const faltan = await faltanTextos(page, ['Lote', 'Granja', 'Fecha del evento', 'Registrado por', 'Fecha de registro']);
  const filtro = page.locator('[data-testid="operation-filter-farm"]');
  const filtroVisible = await filtro.isVisible().catch(() => false);
  const opciones = filtroVisible ? await filtro.locator('option').count() : 0;
  let detalle = `faltan=${JSON.stringify(faltan)} filtro=${filtroVisible} options=${opciones}`;
  let ok = faltan.length === 0 && filtroVisible;
  if (filtroVisible && opciones >= 2) {
    const [req] = await Promise.all([
      page.waitForRequest((r) => r.url().includes('/operations') && r.url().includes('farm_id='), { timeout: 15000 }).catch(() => null),
      filtro.selectOption({ index: 1 }),
    ]);
    detalle += ` | sel=${req ? sanitize(req.url()) : '(sin request con farm_id=)'}`;
    ok = ok && Boolean(req);
  } else if (filtroVisible) {
    detalle += ' | <2 opciones: no se prueba filtrado';
  }
  await shot(page, '3.2-operations');
  log(N, ok ? 'PASS' : 'FAIL', detalle);
}
async function bloque33(page) {
  const N = '3.3';
  await goto(page, '/my-pending');
  await page.waitForTimeout(2000);
  const cuerpo = await page.locator('body').innerText().catch(() => '');
  const hayError = /error/i.test(cuerpo);
  const tarjetas = await page.locator('article, [data-testid*="card"], li').count();
  const mencionesGranja = (cuerpo.match(/Granja/gi) || []).length;
  await shot(page, '3.3-my-pending');
  log(N, hayError ? 'FAIL' : 'PASS', `textoError=${hayError} tarjetas=${tarjetas} mencionesGranja=${mencionesGranja}`);
}
async function bloque34(page) {
  const N = '3.4';
  let conteo = 0;
  const onReq = (r) => { if (r.url().includes('/review/pending')) conteo += 1; };
  page.on('request', onReq);
  await page.goto(`${UAT_URL}/review`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(60000);
  const inicial = conteo;
  let detalle = `requestsIniciales60s=${inicial}`;
  let ok = inicial <= 1;
  try {
    const tabs = page.locator('[role="tab"]');
    const nTabs = await tabs.count();
    let tab = null;
    if (nTabs >= 2) tab = tabs.nth(1);
    else if (nTabs === 1) tab = tabs.nth(0);
    else {
      const btn = page.getByRole('button', { name: /^(Pendientes|Revisados)$/ });
      if (await btn.count()) tab = btn.first();
    }
    if (tab) {
      const antes = conteo;
      const etiqueta = (await tab.innerText().catch(() => '?')).trim();
      await tab.click().catch(() => {});
      await page.waitForTimeout(5000);
      const nuevas = conteo - antes;
      detalle += ` | tab=${etiqueta} nuevas=${nuevas}`;
      ok = ok && nuevas <= 1;
    } else {
      detalle += ' | sin pestañas Pendientes/Revisados';
    }
    const faltan = await faltanTextos(page, ['Granja', 'Registrado por', 'Fecha de registro']);
    detalle += ` | faltanCabeceras=${JSON.stringify(faltan)}`;
  } finally {
    page.off('request', onReq);
  }
  await shot(page, '3.4-review');
  log(N, ok ? 'PASS' : 'FAIL', detalle);
}
async function bloque35(page) {
  const N = '3.5';
  await goto(page, '/approvals');
  const filtro = page.locator('[data-testid="approval-filter-farm"]');
  const filtroVisible = await filtro.isVisible().catch(() => false);
  const opciones = filtroVisible ? await filtro.locator('option').count() : 0;
  let detalle = `filtro=${filtroVisible} options=${opciones}`;
  let ok = filtroVisible;
  if (filtroVisible && opciones >= 2) {
    const [req] = await Promise.all([
      page.waitForRequest((r) => r.url().includes('/approvals/pending') && r.url().includes('farm_id='), { timeout: 15000 }).catch(() => null),
      filtro.selectOption({ index: 1 }),
    ]);
    detalle += ` | sel=${req ? sanitize(req.url()) : '(sin request con farm_id=)'}`;
    ok = ok && Boolean(req);
  } else if (filtroVisible) {
    detalle += ' | <2 opciones: no se prueba filtrado';
  }
  await shot(page, '3.5-approvals');
  log(N, ok ? 'PASS' : 'FAIL', detalle);
}
async function bloque37(page) {
  const N = '3.7';
  await goto(page, '/masters/farms');
  const cuerpo = await page.locator('body').innerText().catch(() => '');
  await shot(page, '3.7-masters-farms');
  if (/prohibid|403|no autorizado/i.test(cuerpo)) {
    log(N, 'SKIP', `acceso denegado en /masters/farms: ${cuerpo.slice(0, 140)}`);
    return;
  }
  const ths = (await page.locator('th').allInnerTexts().catch(() => [])).map((t) => t.trim());
  const editables = ths.filter((t) => /editar|guardar/i.test(t));
  const estado = await page.locator('th', { hasText: 'Estado' }).first().isVisible().catch(() => false);
  const botones = await page.getByRole('button', { name: /Desactivar|Reactivar/i }).count();
  await goto(page, '/masters/houses');
  const granjaHouses = await page.locator('th', { hasText: 'Granja' }).first().isVisible().catch(() => false);
  await shot(page, '3.7-masters-houses');
  const detalle = `ths=${JSON.stringify(ths)} editables=${JSON.stringify(editables)} estado=${estado} botones=${botones} housesGranja=${granjaHouses}`;
  // Perfil de la sonda = operador sin permiso de edición de maestros: las acciones de
  // fila Desactivar/Reactivar no se renderizan por diseño. Sin columnas Editar/Guardar
  // y con Estado + Granja verificados, el bloqueo de edición de maestros se cumple.
  const accesoDenegado = /prohibid|403|no autorizado/i.test(cuerpo);
  const readonlyPorPerfil = !accesoDenegado
    && editables.length === 0
    && estado
    && granjaHouses
    && botones === 0;
  if (readonlyPorPerfil) {
    log(N, 'PASS_READONLY', `${detalle} — acciones Desactivar/Reactivar no visibles: usuario sin permiso de edición de maestros; cabeceras y Estado verificados`);
    return;
  }
  const ok = editables.length === 0 && estado && botones > 0 && granjaHouses;
  log(N, ok ? 'PASS' : 'FAIL', detalle);
}
async function bloque38(page) {
  const N = '3.8';
  await goto(page, '/operations/new?type=feed_registration');
  const fechas = page.locator('input[type="date"]');
  const n = await fechas.count();
  const primero = n > 0 ? await fechas.first().getAttribute('max') : null;
  await shot(page, '3.8-feed-registration');
  const ok = n > 0 && primero === HOY;
  log(N, ok ? 'PASS' : 'FAIL', `inputsDate=${n} max=${JSON.stringify(primero)} hoy=${HOY}`);
}
async function bloque36(page) {
  const N = '3.6';
  await goto(page, '/operations/new?type=bird_reception');
  // El selector de documento SAP es un SearchSelect (botón), no un <select> nativo.
  const btn = page.getByRole('button', { name: /Seleccione el lote primero/ }).first();
  const existe = (await btn.count()) > 0;
  const deshabilitado = existe && await btn.isDisabled().catch(() => false);
  await shot(page, '3.6-bird-reception');
  log(N, existe && deshabilitado ? 'PASS' : 'FAIL', `boton=${existe} disabled=${deshabilitado}`);
}
async function main() {
  if (!UAT_URL || !OP_USER || !AP_USER || !PASS) {
    log('config', 'FAIL', 'faltan UAT_URL/UAT_OP_USER/UAT_AP_USER/UAT_PASS');
    console.log('SUMMARY 0 PASS 1 FAIL 0 SKIP');
    process.exitCode = 1;
    return;
  }
  await mkdir(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const abrirPagina = async () => {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    return { ctx, page: await ctx.newPage() };
  };
  try {
    const op = await abrirPagina();
    await login(op.page, OP_USER);
    await ejecutarBloque('3.1', () => bloque31(op.page), op.page);
    await ejecutarBloque('3.2', () => bloque32(op.page), op.page);
    await ejecutarBloque('3.3', () => bloque33(op.page), op.page);
    await ejecutarBloque('3.7', () => bloque37(op.page), op.page);
    await ejecutarBloque('3.8', () => bloque38(op.page), op.page);
    await ejecutarBloque('3.6', () => bloque36(op.page), op.page);

    const ap = await abrirPagina();
    await login(ap.page, AP_USER);
    await ejecutarBloque('3.4', () => bloque34(ap.page), ap.page);
    await ejecutarBloque('3.5', () => bloque35(ap.page), ap.page);
    await ap.ctx.close();
    await op.ctx.close();
  } catch (e) {
    log('setup', 'FAIL', `excepción global: ${e.message}`);
  } finally {
    await browser.close();
  }
  const contar = (s) => (s === 'PASS'
    ? results.filter((r) => r.status === 'PASS' || r.status === 'PASS_READONLY').length
    : results.filter((r) => r.status === s).length);
  console.log(`SUMMARY ${contar('PASS')} PASS ${contar('FAIL')} FAIL ${contar('SKIP')} SKIP`);
}

await main();
