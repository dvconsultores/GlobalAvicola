#!/usr/bin/env node
/**
 * AUDITORÍA CLAUDE · recorrido runtime autenticado (PROGENITORAS) en https://avicola.globaldv.net
 * Cuentas: las del fixture GA-UAT-09 (~/ga_uat09_credentials.txt · empresa 1 · unidad grandparent ON).
 * Cubre lo que el retry C2f no cubrió: registros diarios por UI, distribución/salida/recolección sobre el
 * lote autocreado (sin galpón), transición de fase, devolución/rechazo/reenvío por UI, EN y móvil.
 * Evidencia: scratchpad/evidence-runtime/. Sin mutación del producto. Ledger de datos al final.
 */
import { chromium } from '/home/maria/Proyectos/GlobalAvicola/node_modules/playwright/index.mjs'
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'

const SCRATCH = path.dirname(new URL(import.meta.url).pathname)
const OUT = path.join(SCRATCH, 'evidence-runtime'); fs.mkdirSync(OUT, { recursive: true })
const BASE = 'https://avicola.globaldv.net'
const API = BASE + '/api/v1'
const HOY = new Date().toISOString().slice(0, 10)
const d = (days) => new Date(Date.now() + days * 864e5).toISOString().slice(0, 10)
const PO = 'PO-C001-GPR-0001'
const raw = fs.readFileSync(path.join(os.homedir(), 'ga_uat09_credentials.txt'), 'utf8')
const OP_USER = /Operador de abuelas:\s*(\S+)/.exec(raw)?.[1], AP_USER = /Aprobador:\s*(\S+)/.exec(raw)?.[1], PASS = /Contraseña \(ambos\):\s*(\S+)/.exec(raw)?.[1]
if (!OP_USER || !AP_USER || !PASS) throw new Error('credenciales ilegibles')

const J = { fecha: HOY, base: BASE, pasos: [], posts: [], pageerror: [], consoleError: [], httpErrores: [], asserts: [], ids: {}, ledger: [] }
const paso = (n, s, dd) => { J.pasos.push({ step: n, status: s, detail: dd ?? null }); console.log(`${(typeof s === 'number' && s < 400) || s === 'OK' ? 'OK ' : '!! '}${n}: ${s}${dd !== undefined ? ' :: ' + JSON.stringify(dd).slice(0, 240) : ''}`) }
const assert = (n, ok, dd) => { J.asserts.push({ name: n, ok, detail: dd ?? null }); console.log(`${ok ? 'PASS' : 'FAIL'} ${n}${dd !== undefined ? ' :: ' + JSON.stringify(dd).slice(0, 220) : ''}`); return ok }
const record = (n, dd) => { J.asserts.push({ name: n, ok: null, detail: dd ?? null }); console.log(`NOTE ${n} :: ${JSON.stringify(dd).slice(0, 280)}`) }
async function api(method, p, token, body) { const r = await fetch(API + p, { method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: body ? JSON.stringify(body) : undefined }); let data = null; try { data = await r.json() } catch { }; return { status: r.status, data } }
async function loginApi(u) { const { status, data } = await api('POST', '/login', null, { username: u, password: PASS }); if (status !== 200) throw new Error(`login ${u} ${status}`); return data.access_token }
function wire(page, tag) {
  page.on('pageerror', e => J.pageerror.push({ tag, msg: String(e.message || e).slice(0, 300) }))
  page.on('console', m => { if (m.type() === 'error') { const t = m.text(); if (!t.includes('Failed to load resource')) J.consoleError.push({ tag, msg: t.slice(0, 300) }) } })
  page.on('response', r => { const u = r.url(); if (u.includes('/api/v1/') && r.status() >= 400) J.httpErrores.push({ tag, status: r.status(), method: r.request().method(), url: u.replace(BASE, '') }) })
}
const shot = async (p, n) => { await p.screenshot({ path: path.join(OUT, n), fullPage: true }).catch(() => { }) }
async function loginUi(page, user) { await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' }); await page.locator('input[autocomplete="username"], #login-username').first().fill(user); await page.locator('#login-password, input[type="password"]').first().fill(PASS); await Promise.all([page.waitForURL(u => !String(u).includes('/login'), { timeout: 30000 }), page.locator('button[type="submit"]').first().click()]); await page.waitForTimeout(600) }
async function pickSearch(page, placeholder, optionText) { await page.getByRole('button').filter({ hasText: placeholder }).first().click(); await page.waitForTimeout(150); if (optionText) { await page.keyboard.type(optionText.slice(0, 12), { delay: 10 }); await page.waitForTimeout(250) }; const opt = optionText ? page.locator('div.z-50 button').filter({ hasText: optionText }).first() : page.locator('div.z-50 button').first(); const t = await opt.innerText().catch(() => ''); await opt.click(); return t.trim() }
const fill = (page, name, v) => page.locator(`[name="${name}"]`).first().fill(String(v))
const selOpt = (page, name, v) => page.locator(`select[name="${name}"]`).first().selectOption(v)
const visible = (loc, t = 4000) => loc.waitFor({ state: 'visible', timeout: t }).then(() => true).catch(() => false)
async function save(page, label) {
  const before = J.pageerror.length
  const respP = page.waitForResponse(r => r.url().includes('/api/v1/operations') && r.request().method() === 'POST', { timeout: 8000 }).catch(() => null)
  await page.locator('#operation-form button[type="submit"]').click()
  const resp = await respP; let req = null, body = null
  if (resp) { try { req = JSON.parse(resp.request().postData() || 'null') } catch { } try { body = await resp.json() } catch { } }
  await page.waitForTimeout(900)
  const banner = await page.locator('div.bg-red-50, div.bg-green-50').first().innerText().catch(() => '')
  const zod = await page.locator('p.text-red-500, p.text-red-600').allInnerTexts().catch(() => [])
  const out = { label, status: resp ? resp.status() : 'NO_REQUEST', req, resp: body ? (body.id ? { id: body.id, status: body.status } : body) : null, banner: banner.slice(0, 200), zod, formVisible: await page.locator('#operation-form').isVisible().catch(() => false), pageerrorDelta: J.pageerror.length - before }
  J.posts.push(out); paso(label, out.status, { id: body?.id, detail: body?.detail || body?.rule, banner: out.banner.slice(0, 100), zod })
  if (body?.id) J.ledger.push({ id: body.id, type: req?.event_type, lot: req?.lot_id })
  return out
}
async function viaHub(page, card, sub, ev) { await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' }); await page.locator('aside a[href="/menu/poultry"]').first().click(); await page.waitForURL('**/menu/poultry', { timeout: 15000 }); await page.getByRole('button', { name: new RegExp(card, 'i') }).first().click(); if (sub) await page.getByRole('button', { name: new RegExp(sub, 'i') }).first().click(); await page.waitForURL('**/poultry/**', { timeout: 15000 }); const tile = page.locator(`a[href*="type=${ev}"]`).first(); if (!await visible(tile, 6000)) throw new Error(`tile ${ev}`); await tile.click(); await page.locator('#operation-form').waitFor({ timeout: 30000 }); await page.waitForTimeout(1200) }
async function viaLotDetail(page, lotId, ev) { await page.goto(`${BASE}/lots/${lotId}`, { waitUntil: 'domcontentloaded' }); const link = page.locator(`a[href="/operations/new?type=${ev}&lot_id=${lotId}"]`).first(); if (await visible(link, 8000)) await link.click(); else { record(`lotdetail-sin-accion-${ev}`, lotId); await page.goto(`${BASE}/operations/new?type=${ev}&lot_id=${lotId}`, { waitUntil: 'domcontentloaded' }) }; await page.locator('#operation-form').waitFor({ timeout: 30000 }); await page.waitForTimeout(1200) }
async function submitUi(op, id) { await op.goto(`${BASE}/operations/${id}`, { waitUntil: 'domcontentloaded' }); const btn = op.getByRole('button', { name: /Enviar a revisi|Reenviar a revisi/ }).first(); if (!await visible(btn, 6000)) return 'NO_CTA'; const [r] = await Promise.all([op.waitForResponse(r => r.url().includes(`/operations/${id}/submit`), { timeout: 20000 }), btn.click()]); await op.waitForTimeout(700); return r.status() }
async function reviewUi(ap, id, mode = 'approve', obs = 'Observación de auditoría independiente (Claude)') {
  const out = {}; await ap.goto(`${BASE}/review/${id}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(1200)
  const start = ap.getByRole('button', { name: /Iniciar Revisi/i }).first()
  if (await visible(start, 5000)) { const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes(`/review/start/${id}`), { timeout: 20000 }), start.click()]); out.start = r.status(); await ap.goto(`${BASE}/review/${id}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(1200) }
  if (mode === 'return') { await ap.locator('input[type="text"]').first().fill(obs); const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes('/review/return'), { timeout: 20000 }), ap.getByRole('button', { name: /Devolver/ }).first().click()]); out.return = r.status() }
  else if (mode === 'reject') { await ap.locator('input[type="text"]').last().fill(obs); const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes('/approvals/reject'), { timeout: 20000 }), ap.getByRole('button', { name: /Rechazar/ }).first().click()]); out.reject = r.status() }
  else {
    // Nivel multiple: «Completar revisión» deja el evento en `corrected` (pendiente de aprobador) y la misma pantalla ofrece «Aprobar»
    let done = false
    for (let i = 0; i < 3 && !done; i++) {
      if (i > 0) { await ap.goto(`${BASE}/review/${id}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(1200) }
      const complete = ap.getByRole('button', { name: /Completar Revisi/i }).first(); const approve = ap.getByRole('button', { name: /Aprobar/ }).first()
      if (await visible(complete, 4000)) { const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes('/review/complete'), { timeout: 20000 }), complete.click()]); out.complete = r.status(); let dd = null; try { dd = await r.json() } catch { }; out.status = dd?.status; if (['approved', 'reversed'].includes(dd?.status)) done = true; continue }
      if (await visible(approve, 4000)) { const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes('/approvals/approve'), { timeout: 20000 }), approve.click()]); out.approve = r.status(); let dd = null; try { dd = await r.json() } catch { }; out.status = dd?.status ?? out.status; done = true; break }
      break
    }
    if (!done && out.approve === undefined) out.approve = 'NO_BUTTON'
  }
  return out
}

const browser = await chromium.launch({ headless: true })
const ctxOp = await browser.newContext({ viewport: { width: 1440, height: 900 } }); const op = await ctxOp.newPage(); wire(op, 'op')
const ctxAp = await browser.newContext({ viewport: { width: 1440, height: 900 } }); const ap = await ctxAp.newPage(); wire(ap, 'ap')
try {
  const html = await (await fetch(BASE + '/')).text(); J.ids.bundle = /index-[A-Za-z0-9_.-]+\.js/.exec(html)?.[0]; paso('generacion-frontend', 200, J.ids.bundle)
  const tokOp = await loginApi(OP_USER), tokAp = await loginApi(AP_USER)
  const me = (await api('GET', '/me', tokOp)).data; paso('me-op', 200, { company: me?.company_id, keys: Object.keys(me || {}).slice(0, 20) })
  // marcadores backend (C2d) sin mutación
  const pFeed = await api('POST', '/operations', tokOp, { event_type: 'grandparent_import', event_date: HOY, sap_document_ref: PO, feed_movements: [{}] }); assert('backend-C2d-feed-vacio-422', pFeed.status === 422, pFeed.status)
  const h100 = await api('GET', '/operations/100', tokOp); assert('backend-C2d-lectura-tolerante', h100.status !== 500, h100.status)
  const lots0 = (await api('GET', '/lots?search=L-GP&limit=100', tokOp)).data; const base0 = (Array.isArray(lots0) ? lots0 : lots0?.items || []).map(l => l.lot_code); paso('lotes-gp-antes', 200, base0)

  await loginUi(op, OP_USER); await loginUi(ap, AP_USER); paso('login-ui', 200)
  // 1 · importación por navegación normal (hub)
  const REUSE = process.env.GA_REUSE_IMPORT ? Number(process.env.GA_REUSE_IMPORT) : null
  let impId
  if (REUSE) { impId = REUSE; J.ids.import = impId; J.ids.reused = true; paso('R-01-import-ui', 'REUSED', { id: REUSE, nota: 'importacion creada por UI en la corrida 2 (201, evidencia run2-partial); reutilizada para no crear un segundo lote' }) }
  else {
  await viaHub(op, 'Progenitoras', 'Cría', 'grandparent_import'); paso('nav-hub-import', 'OK', op.url())
  await pickSearch(op, 'Seleccionar documento SAP...', 'PO-C001'); await pickSearch(op, 'Seleccionar proveedor...', 'Cobb'); await pickSearch(op, 'Seleccionar transporte...', 'ABC-123'); await pickSearch(op, 'Seleccionar granja...', null)
  await fill(op, 'extra_data.import_plan.origin_country', 'Francia'); await fill(op, 'extra_data.import_plan.purchased_total', 55); await fill(op, 'extra_data.import_plan.shipped_total', 52); await fill(op, 'extra_data.import_plan.received_total', 50); await fill(op, 'extra_data.import_plan.transit_mortality', 2)
  await fill(op, 'extra_data.import_plan.departure_date', d(-7)); await fill(op, 'extra_data.import_plan.arrival_date', HOY); await fill(op, 'extra_data.import_plan.quarantine_days', 21); await fill(op, 'extra_data.import_plan.quarantine_end_date', d(21))
  await fill(op, 'bird_movements.0.quantity', 20); await fill(op, 'bird_movements.0.avg_weight', 3800); await fill(op, 'bird_movements.1.quantity', 30); await fill(op, 'bird_movements.1.avg_weight', 3600)
  await shot(op, 'R01-import-form.png')
  const imp = await save(op, 'R-01-import-ui'); assert('R-01-import-201', imp.status === 201, imp.resp?.detail); impId = imp.resp?.id; J.ids.import = impId
  }
  if (impId) {
    const st0 = (await api('GET', `/operations/${impId}`, tokOp)).data?.status
    if (st0 === 'registered') paso('R-02-submit-ui', await submitUi(op, impId)); else paso('R-02-submit-ui', 'SKIP', { status: st0 })
    const rv = await reviewUi(ap, impId, 'approve'); paso('R-03-review-ui', rv.complete ?? rv.approve, rv)
    const det = (await api('GET', `/operations/${impId}`, tokOp)).data; const lotId = det?.lot_id; J.ids.lot = lotId
    assert('R-03-aprobado-lote', det?.status === 'approved' && !!lotId, { status: det?.status, lotId })
    const lot = (await api('GET', `/lots/${lotId}`, tokOp)).data; J.ids.lotCode = lot?.lot_code; J.ledger.push({ lot: lotId, code: lot?.lot_code }); paso('lote-auto', 200, { code: lot?.lot_code, house: lot?.house_id, farm: lot?.farm_id })
    await op.goto(`${BASE}/lots/${lotId}`, { waitUntil: 'domcontentloaded' }); await op.waitForTimeout(1500); await shot(op, 'R02-lot-detail.png')
    record('lotdetail-poblacion-visible', /Poblaci[oó]n|Saldo/i.test(await op.locator('body').innerText()))
    // 2 · recepción por UI → devolver → reenviar → aprobar (P-07 por UI)
    await viaLotDetail(op, lotId, 'bird_reception'); await pickSearch(op, 'Seleccionar documento SAP...', 'PO-C001'); await pickSearch(op, 'Seleccionar proveedor...', 'Cobb')
    await pickSearch(op, 'Seleccionar galpón...', null); await selOpt(op, 'bird_movements.0.sex', 'male'); await fill(op, 'bird_movements.0.quantity', 20); await fill(op, 'bird_movements.0.avg_weight', 3800)
    await pickSearch(op, 'Seleccionar galpón...', null); await selOpt(op, 'bird_movements.1.sex', 'female'); await fill(op, 'bird_movements.1.quantity', 30); await fill(op, 'bird_movements.1.avg_weight', 3600)
    const rec = await save(op, 'R-04-reception-ui'); assert('R-04-recepcion-201', rec.status === 201, rec.resp?.detail); const recId = rec.resp?.id; J.ids.reception = recId
    if (recId) {
      paso('R-05-submit', await submitUi(op, recId)); const r1 = await reviewUi(ap, recId, 'return'); paso('R-05-return-ui', r1.return, r1)
      let e = (await api('GET', `/operations/${recId}`, tokOp)).data; assert('R-05-devuelto', e?.status === 'returned', e?.status)
      const unread = (await api('GET', '/notifications/unread-count', tokOp)).data; record('R-05-notificacion-operador', unread)
      paso('R-06-resubmit-ui', await submitUi(op, recId)); e = (await api('GET', `/operations/${recId}`, tokOp)).data; assert('R-06-reenviado', e?.status === 'pending_review', e?.status)
      const r2 = await reviewUi(ap, recId, 'approve'); e = (await api('GET', `/operations/${recId}`, tokOp)).data; assert('R-06-aprobado', e?.status === 'approved', { ...r2, status: e?.status })
      const b = await api('POST', '/operations', tokOp, { event_type: 'mortality_recording', event_date: HOY, lot_id: lotId, bird_movements: [{ sex: 'female', quantity: 51 }] }); assert('R-07-poblacion-50', b.status === 400 && /50/.test(String(b.data?.detail)), b.data?.detail)
    }
    // 3 · registros diarios por UI sobre el lote autocreado
    const daily = [
      ['mortality_recording', async () => { await pickSearch(op, 'Seleccionar causa...', null); await fill(op, 'bird_movements.0.week_number', 1); await fill(op, 'bird_movements.1.quantity', 1) }],
      ['feed_registration', async () => { await op.locator('select[name="feed_movements.0.feed_type_id"]').selectOption({ index: 1 }); await fill(op, 'feed_movements.0.week_number', 1); await fill(op, 'feed_movements.0.quantity_kg', 25) }],
      ['weight_recording', async () => { await fill(op, 'bird_movements.0.week_number', 1); await fill(op, 'sample_size', 10); await fill(op, 'bird_movements.0.quantity', 5); await fill(op, 'bird_movements.0.avg_weight', 3900); await fill(op, 'bird_movements.1.quantity', 5); await fill(op, 'bird_movements.1.avg_weight', 3700) }],
      ['vaccination', async () => { await pickSearch(op, 'Seleccionar vacuna...', null); await selOpt(op, 'vaccination_route', 'water'); await fill(op, 'dosage_per_bird', 0.5); await fill(op, 'bird_movements.0.quantity', 20); await fill(op, 'bird_movements.1.quantity', 30) }],
      ['farm_inspection', async () => { await pickSearch(op, 'Seleccionar galpón...', null); await fill(op, 'house_inspections.0.temperature', 28); await fill(op, 'house_inspections.0.humidity', 60); await selOpt(op, 'house_inspections.0.litter_condition', 'seca') }],
      ['bird_distribution', async () => { await pickSearch(op, 'Seleccionar galpón...', null); await selOpt(op, 'bird_movements.0.sex', 'mixed'); await fill(op, 'bird_movements.0.quantity', 10) }],
      ['bird_exit', async () => { await fill(op, 'bird_movements.0.quantity', 2); await fill(op, 'bird_movements.0.avg_weight', 4000); await fill(op, 'bird_movements.1.quantity', 2); await fill(op, 'bird_movements.1.avg_weight', 3800) }],
    ]
    for (const [ev, fn] of daily) { try { await viaLotDetail(op, lotId, ev); await fn(); const r = await save(op, `R-08-${ev}`); record(`R-08-${ev}-resultado`, { status: r.status, detail: r.resp?.detail, house_id: r.req?.house_id, farm_id: r.req?.farm_id }) } catch (e2) { paso(`R-08-${ev}-EXC`, 'error', String(e2).slice(0, 200)) } }
    // 4 · transición a producción (LotDetail) y recolección
    await op.goto(`${BASE}/lots/${lotId}`, { waitUntil: 'domcontentloaded' }); await op.waitForTimeout(1200)
    const tr = op.getByRole('button', { name: /Iniciar Producci/ }).first()
    if (await visible(tr, 5000)) { await tr.click(); await op.waitForTimeout(500); const [r] = await Promise.all([op.waitForResponse(r => r.url().includes('/phases') && r.request().method() === 'POST', { timeout: 20000 }).catch(() => null), op.getByRole('button', { name: /^Confirmar$/ }).first().click()]); await op.waitForTimeout(800); record('R-09-transicion-ui', { status: r ? r.status() : 'NO_REQUEST', req: r ? JSON.parse(r.request().postData() || 'null') : null, detail: r ? (await r.json().catch(() => null))?.detail : null, toasts: await op.locator('.fixed.top-4 span').allInnerTexts().catch(() => []) }); await shot(op, 'R03-transition.png') } else record('R-09-boton-transicion', 'no visible')
    await viaLotDetail(op, lotId, 'egg_collection'); await fill(op, 'egg_movements.0.quantity', 10); await fill(op, 'egg_movements.0.avg_weight', 60)
    const eg = await save(op, 'R-10-egg_collection'); record('R-10-recoleccion', { status: eg.status, detail: eg.resp?.detail, house_id: eg.req?.house_id })
    // 5 · rechazo → reenvío por UI (OD-17) sobre el alimento
    const feedId = J.ledger.find(x => x.type === 'feed_registration')?.id
    if (feedId) { paso('R-11-submit', await submitUi(op, feedId)); const rj = await reviewUi(ap, feedId, 'reject'); let e = (await api('GET', `/operations/${feedId}`, tokOp)).data; assert('R-11-rechazado', e?.status === 'rejected', { ...rj, status: e?.status }); paso('R-11-resubmit', await submitUi(op, feedId)); e = (await api('GET', `/operations/${feedId}`, tokOp)).data; assert('R-11-rechazado-reenviado', e?.status === 'pending_review', e?.status); const r3 = await reviewUi(ap, feedId, 'approve'); e = (await api('GET', `/operations/${feedId}`, tokOp)).data; assert('R-11-aprobado', e?.status === 'approved', { ...r3, status: e?.status }) }
    // 6 · centro de revisión: pestañas (evento in_review)
    const wt = J.ledger.find(x => x.type === 'weight_recording')?.id
    if (wt) { await api('POST', `/operations/${wt}/submit`, tokOp); await api('POST', `/review/start/${wt}`, tokAp); const tabs = {}; for (const st of ['pending_review', 'in_review']) { await ap.goto(`${BASE}/review?status=${st}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(1500); tabs[st] = (await ap.locator('body').innerText()).includes(`#${wt}`) }; record('R-12-review-tabs-in_review', tabs); await shot(ap, 'R04-review-tabs.png'); const r4 = await reviewUi(ap, wt, 'approve'); paso('R-12-approve-in_review', r4.complete ?? r4.approve) }
    // 7 · UX de error real + EN + móvil
    await viaLotDetail(op, lotId, 'mortality_recording'); await pickSearch(op, 'Seleccionar causa...', null); await fill(op, 'bird_movements.0.week_number', 1); await fill(op, 'bird_movements.0.quantity', 99999)
    const bad = await save(op, 'R-13-mortality-exceso'); assert('R-13-4xx-seguro', bad.status === 400 && bad.formVisible && bad.pageerrorDelta === 0 && bad.banner.length > 0, { status: bad.status, banner: bad.banner }); await shot(op, 'R05-error-ux.png')
    await op.evaluate(() => window.__i18n.changeLanguage('en')); await op.waitForTimeout(1000); await shot(op, 'R06-en-form.png')
    const en = await op.locator('body').innerText(); record('R-14-EN', { spanish: (en.match(/Seleccionar|Galpón|Cantidad|Guardar|Semana|Causa/g) || []).length, rawKeys: (en.match(/\b(operations|common|nav|lots)\.[a-zA-Z]+/g) || []).slice(0, 8), sample: en.slice(0, 160).replace(/\n/g, ' | ') })
    await op.goto(`${BASE}/menu/poultry`, { waitUntil: 'domcontentloaded' }); await op.waitForTimeout(800); await shot(op, 'R07-en-hub.png'); record('R-14-EN-hub', (await op.locator('body').innerText()).slice(0, 200).replace(/\n/g, ' | '))
    await op.evaluate(() => window.__i18n.changeLanguage('es')); await op.waitForTimeout(500)
    const m = await ctxOp.newPage(); wire(m, 'movil'); await m.setViewportSize({ width: 390, height: 844 })
    await m.goto(`${BASE}/lots/${lotId}`, { waitUntil: 'domcontentloaded' }); await m.waitForTimeout(1500); record('R-15-movil-overflow-lote', await m.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)); await shot(m, 'R08-mobile-lot.png')
    await m.goto(`${BASE}/operations/new?type=mortality_recording&lot_id=${lotId}`, { waitUntil: 'domcontentloaded' }); await m.waitForTimeout(1500); record('R-15-movil-overflow-form', await m.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)); await shot(m, 'R09-mobile-form.png')
    await m.close()
    // 8 · limpieza de lo cancelable (registrados) — los aprobados quedan en el ledger
    for (const x of J.ledger.filter(x => x.id)) { const e = (await api('GET', `/operations/${x.id}`, tokOp)).data; if (e && ['registered', 'returned', 'rejected'].includes(e.status)) { const c = await api('POST', `/operations/${x.id}/cancel`, tokOp); x.cleanup = `cancel ${c.status}` } else x.cleanup = `retenido (${e?.status})` }
    const lots1 = (await api('GET', '/lots?search=L-GP&limit=100', tokOp)).data; assert('AC06-un-solo-lote-nuevo', (Array.isArray(lots1) ? lots1 : lots1?.items || []).length === base0.length + 1)
  }
} catch (e) { paso('ERROR-GLOBAL', 'excepcion', String(e).slice(0, 400)) }
finally {
  J.fatal_react = J.pageerror.filter(p => /React|#31/.test(p.msg)).length; J.http5xx = J.httpErrores.filter(h => h.status >= 500)
  fs.writeFileSync(path.join(OUT, 'runtime-gp-e2e.json'), JSON.stringify(J, null, 2))
  const fails = J.asserts.filter(a => a.ok === false)
  console.log(`\n== resumen runtime == PASS ${J.asserts.filter(a => a.ok === true).length} · FAIL ${fails.length} · notas ${J.asserts.filter(a => a.ok === null).length} · pageerror ${J.pageerror.length} (React ${J.fatal_react}) · 5xx ${J.http5xx.length} · 4xx ${J.httpErrores.length}`)
  for (const f of fails) console.log('FALLO:', f.name, JSON.stringify(f.detail).slice(0, 200))
  await browser.close()
}
