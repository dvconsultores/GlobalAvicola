#!/usr/bin/env node
/**
 * AUDITORÍA CLAUDE · E2E de UI por unidad de negocio contra el stack LOCAL (código HEAD)
 * Stack: local_stack.sh (backend 8099 · frontend 5199 · PostgreSQL de pruebas aislado).
 * Actores: test_admin (web, todas las unidades) · test_approver (web) · test_operator (mobile).
 * Cada paso captura la petición POST /operations real, su estado y la UX resultante.
 * Sin mutación del producto. Evidencia: scratchpad/evidence-local/.
 */
import { chromium } from '/home/maria/Proyectos/GlobalAvicola/node_modules/playwright/index.mjs'
import fs from 'node:fs'
import path from 'node:path'

const SCRATCH = path.dirname(new URL(import.meta.url).pathname)
const OUT = path.join(SCRATCH, 'evidence-local'); fs.mkdirSync(OUT, { recursive: true })
const BASE = 'http://127.0.0.1:5199'
const API = 'http://127.0.0.1:8099/api/v1'
const HOY = new Date().toLocaleDateString('sv-SE')
const env = Object.fromEntries(fs.readFileSync(path.join(SCRATCH, 'local_creds.env'), 'utf8').trim().split('\n').map(l => l.split('=')))
const CRED = { admin: ['test_admin', env.GA_TEST_ADMIN_PASSWORD], approver: ['test_approver', env.GA_TEST_APPROVER_PASSWORD], operator: ['test_operator', env.GA_TEST_OPERATOR_PASSWORD] }

// ── journal ────────────────────────────────────────────────────────────────
const J = { fecha: HOY, base: BASE, pasos: [], posts: [], pageerror: [], consoleError: [], httpErrores: [], asserts: [], ids: {} }
const paso = (n, s, d) => { J.pasos.push({ step: n, status: s, detail: d ?? null }); console.log(`${(typeof s === 'number' && s < 400) || s === 'OK' ? 'OK ' : '!! '}${n}: ${s}${d !== undefined ? ' :: ' + JSON.stringify(d).slice(0, 260) : ''}`) }
const assert = (n, ok, d) => { J.asserts.push({ name: n, ok, detail: d ?? null }); console.log(`${ok ? 'PASS' : 'FAIL'} ${n}${d !== undefined ? ' :: ' + JSON.stringify(d).slice(0, 240) : ''}`); return ok }
const record = (n, d) => { J.asserts.push({ name: n, ok: null, detail: d ?? null }); console.log(`NOTE ${n} :: ${JSON.stringify(d).slice(0, 300)}`) }

// ── API ────────────────────────────────────────────────────────────────────
async function api(method, p, token, body) {
  const r = await fetch(API + p, { method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: body ? JSON.stringify(body) : undefined })
  let data = null; try { data = await r.json() } catch { }
  return { status: r.status, data }
}
async function loginApi(who) { const { status, data } = await api('POST', '/login', null, { username: CRED[who][0], password: CRED[who][1] }); if (status !== 200) throw new Error(`login ${who} ${status}`); return data.access_token }

// ── browser helpers ────────────────────────────────────────────────────────
function wire(page, tag) {
  page.on('pageerror', e => J.pageerror.push({ tag, msg: String(e.message || e).slice(0, 300) }))
  page.on('console', m => { if (m.type() === 'error') { const t = m.text(); if (!t.includes('Failed to load resource')) J.consoleError.push({ tag, msg: t.slice(0, 300) }) } })
  page.on('response', r => { const u = r.url(); if (u.includes('/api/v1/') && r.status() >= 400) J.httpErrores.push({ tag, status: r.status(), method: r.request().method(), url: u.replace(BASE, '') }) })
}
const shot = async (page, name) => { await page.screenshot({ path: path.join(OUT, name), fullPage: true }).catch(() => { }) }
async function loginUi(page, who) {
  await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' })
  await page.locator('input[autocomplete="username"], #login-username, input[name="username"]').first().fill(CRED[who][0])
  await page.locator('#login-password, input[type="password"]').first().fill(CRED[who][1])
  await Promise.all([page.waitForURL(u => !String(u).includes('/login'), { timeout: 30000 }), page.locator('button[type="submit"]').first().click()])
  await page.waitForTimeout(600)
}
async function pickSearch(page, placeholder, optionText) {
  const btn = page.getByRole('button').filter({ hasText: placeholder }).first()
  await btn.click()
  await page.waitForTimeout(150)
  if (optionText) { await page.keyboard.type(optionText.slice(0, 12), { delay: 10 }); await page.waitForTimeout(200) }
  const opt = optionText ? page.locator('div.z-50 button').filter({ hasText: optionText }).first() : page.locator('div.z-50 button').first()
  const txt = await opt.innerText().catch(() => '')
  await opt.click()
  return txt.trim()
}
const fill = (page, name, v) => page.locator(`[name="${name}"]`).first().fill(String(v))
const selOpt = (page, name, v) => page.locator(`select[name="${name}"]`).first().selectOption(v)
const visible = (loc, t = 4000) => loc.waitFor({ state: 'visible', timeout: t }).then(() => true).catch(() => false)

/** Guarda el formulario y captura el POST real (o su ausencia = bloqueo silencioso). */
async function save(page, label) {
  const before = J.pageerror.length
  const respP = page.waitForResponse(r => r.url().includes('/api/v1/operations') && r.request().method() === 'POST', { timeout: 7000 }).catch(() => null)
  await page.locator('#operation-form button[type="submit"]').click()
  const resp = await respP
  let req = null, body = null
  if (resp) { try { req = JSON.parse(resp.request().postData() || 'null') } catch { } try { body = await resp.json() } catch { } }
  await page.waitForTimeout(900)
  const msg = await page.locator('#operation-form').locator('xpath=preceding-sibling::div[contains(@class,"rounded-lg")]').last().innerText().catch(() => '')
  const banner = await page.locator('div.bg-red-50, div.bg-green-50').first().innerText().catch(() => '')
  const zodErrors = await page.locator('p.text-red-500, p.text-red-600').allInnerTexts().catch(() => [])
  const out = { label, status: resp ? resp.status() : 'NO_REQUEST', req, resp: body ? (body.id ? { id: body.id, status: body.status } : body) : null, banner: (banner || msg).slice(0, 200), zodErrors, formVisible: await page.locator('#operation-form').isVisible().catch(() => false), pageerrorDelta: J.pageerror.length - before }
  J.posts.push(out)
  paso(label, out.status, { id: body?.id, detail: body?.detail || body?.rule, banner: out.banner.slice(0, 120), zod: zodErrors })
  return out
}

/** Navegación NORMAL: sidebar → hub Gestión Avícola → tarjeta → (subtarjeta) → etapa → tile. */
async function viaHub(page, cardTitle, subCard, eventType) {
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' })
  await page.locator('aside a[href="/menu/poultry"]').first().click()
  await page.waitForURL('**/menu/poultry', { timeout: 15000 })
  await page.getByRole('button', { name: new RegExp(cardTitle, 'i') }).first().click()
  if (subCard) await page.getByRole('button', { name: new RegExp(subCard, 'i') }).first().click()
  await page.waitForURL('**/poultry/**', { timeout: 15000 })
  const tile = page.locator(`a[href*="type=${eventType}"]`).first()
  const ok = await visible(tile, 6000)
  if (!ok) throw new Error(`tile ${eventType} no visible en la etapa`)
  await tile.click()
  await page.locator('#operation-form').waitFor({ timeout: 20000 })
  await page.waitForTimeout(900)
}
async function viaLotDetail(page, lotId, eventType) {
  await page.goto(`${BASE}/lots/${lotId}`, { waitUntil: 'domcontentloaded' })
  const link = page.locator(`a[href="/operations/new?type=${eventType}&lot_id=${lotId}"]`).first()
  if (await visible(link, 6000)) await link.click()
  else { record(`lotdetail-sin-accion-${eventType}`, { lotId }); await page.goto(`${BASE}/operations/new?type=${eventType}&lot_id=${lotId}`, { waitUntil: 'domcontentloaded' }) }
  await page.locator('#operation-form').waitFor({ timeout: 20000 })
  await page.waitForTimeout(900)
}
/** Si el formulario no trae lote prefijado, lo elige por código. */
async function ensureLot(page, lotCode) {
  const ph = page.getByRole('button').filter({ hasText: 'Seleccionar lote...' })
  if (await ph.count()) await pickSearch(page, 'Seleccionar lote...', lotCode)
}

/** P-07 por UI: envío (detalle) → revisión (aprobador) → aprobado. */
async function submitUi(op, eventId) {
  await op.goto(`${BASE}/operations/${eventId}`, { waitUntil: 'domcontentloaded' })
  const btn = op.getByRole('button', { name: /Enviar a revisi|Reenviar a revisi/ }).first()
  if (!await visible(btn, 5000)) return 'NO_CTA'
  const [r] = await Promise.all([op.waitForResponse(r => r.url().includes(`/operations/${eventId}/submit`), { timeout: 15000 }), btn.click()])
  await op.waitForTimeout(700)
  return r.status()
}
async function reviewUi(ap, eventId, mode = 'approve', obs = 'Observación de auditoría con más de diez caracteres') {
  // mode: approve | return | reject
  const out = {}
  await ap.goto(`${BASE}/review/${eventId}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(900)
  const start = ap.getByRole('button', { name: /Iniciar Revisi/i }).first()
  if (await visible(start, 4000)) { const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes(`/review/start/${eventId}`), { timeout: 15000 }), start.click()]); out.start = r.status(); await ap.goto(`${BASE}/review/${eventId}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(900) }
  if (mode === 'return') {
    await ap.locator('input[placeholder]').filter({ hasNot: ap.locator('[type=checkbox]') }).first().fill(obs)
    const btn = ap.getByRole('button', { name: /Devolver/ }).first()
    const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes('/review/return'), { timeout: 15000 }), btn.click()]); out.return = r.status()
  } else if (mode === 'reject') {
    const inputs = ap.locator('input[type="text"]'); await inputs.last().fill(obs)
    const btn = ap.getByRole('button', { name: /Rechazar/ }).first()
    const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes('/approvals/reject'), { timeout: 15000 }), btn.click()]); out.reject = r.status()
  } else {
    // Nivel multiple: «Completar revisión» deja el evento en `corrected` y la misma pantalla ofrece «Aprobar»
    let done = false
    for (let i = 0; i < 3 && !done; i++) {
      if (i > 0) { await ap.goto(`${BASE}/review/${eventId}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(900) }
      const complete = ap.getByRole('button', { name: /Completar Revisi/i }).first(); const approve = ap.getByRole('button', { name: /Aprobar/ }).first()
      if (await visible(complete, 3000)) { const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes('/review/complete'), { timeout: 15000 }), complete.click()]); out.complete = r.status(); let d = null; try { d = await r.json() } catch { }; out.status = d?.status; if (['approved', 'reversed'].includes(d?.status)) done = true; continue }
      if (await visible(approve, 3000)) { const [r] = await Promise.all([ap.waitForResponse(r => r.url().includes('/approvals/approve'), { timeout: 15000 }), approve.click()]); out.approve = r.status(); let d = null; try { d = await r.json() } catch { }; out.status = d?.status ?? out.status; done = true; break }
      break
    }
    if (!done && out.approve === undefined) out.approve = 'NO_BUTTON'
  }
  return out
}

// ── main ───────────────────────────────────────────────────────────────────
const browser = await chromium.launch({ headless: true })
const ctxAdmin = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const ctxAp = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const ad = await ctxAdmin.newPage(); wire(ad, 'admin')
const ap = await ctxAp.newPage(); wire(ap, 'approver')

try {
  const tokA = await loginApi('admin'); const tokP = await loginApi('approver'); const tokO = await loginApi('operator')
  const me = (await api('GET', '/me', tokA)).data; const companyId = me.company_id; J.ids.company = companyId
  paso('me-admin', 200, { company_id: companyId, permisos: Array.isArray(me.permissions) ? me.permissions.length : typeof me.permissions, bu: me.business_units ?? me.effective_business_units ?? 'n/a' })

  // ── fixture mínima por API (maestros que el asistente necesita) ──────────
  const farms = (await api('GET', '/masters/farms?limit=100', tokA)).data; const farm = farms.find(f => f.code === 'TEST-GRANJA-01') || farms[0]
  const houses = (await api('GET', '/masters/houses?limit=100', tokA)).data; const house1 = houses.find(h => h.name === 'TEST-GALPON-01'); const house2 = houses.find(h => h.name === 'TEST Galpon 02')
  const hat = (await api('POST', '/masters/hatcheries', tokA, { company_id: companyId, name: 'AUD Planta Incubación', code: 'AUD-H1' })); paso('fixture-hatchery', hat.status, hat.data?.id)
  const inc = (await api('POST', '/masters/incubators', tokA, { hatchery_id: hat.data?.id, name: 'AUD Incubadora 1', capacity: 50000 })); paso('fixture-incubator', inc.status, inc.data?.id)
  const hch = (await api('POST', '/masters/hatchers', tokA, { hatchery_id: hat.data?.id, name: 'AUD Nacedora 1', capacity: 20000 })); paso('fixture-hatcher', hch.status, hch.data?.id)
  const gl = (await api('POST', '/masters/genetic-lines', tokA, { company_id: companyId, name: 'AUD Ross', code: 'AUD-ROSS' })); paso('fixture-genetic-line', gl.status, gl.data?.id)
  const br = (await api('POST', '/masters/breeds', tokA, { genetic_line_id: gl.data?.id, name: 'AUD Ross 308' })); paso('fixture-breed', br.status, br.data?.id)
  const sup = (await api('POST', '/masters/suppliers', tokA, { company_id: companyId, name: 'AUD Cobb Internacional', country: 'Francia', supplier_type: 'international' })); paso('fixture-supplier', sup.status, sup.data?.id)
  const refs = await api('POST', '/sap/references/import', tokA, { references: [
    { ref_type: 'purchase_order', sap_code: 'AUD-PO-GP', quantity: 200, extra_data: { vendor_name: 'Cobb' } },
    { ref_type: 'purchase_order', sap_code: 'AUD-PO-BR', quantity: 5000 },
    { ref_type: 'purchase_order', sap_code: 'AUD-PO-BO', quantity: 6000 },
    { ref_type: 'transfer_order', sap_code: 'AUD-STO-EGG', quantity: 2000 },
    { ref_type: 'transfer_order', sap_code: 'AUD-STO-CHK', quantity: 2000 },
  ] }); paso('fixture-sap-refs', refs.status, refs.data?.imported ?? refs.data)
  const lots0 = (await api('GET', '/lots?limit=100', tokA)).data; const broiler = lots0.find(l => l.lot_code === 'TEST-LOTE-BROILER-01'); J.ids.broilerLot = broiler?.id

  await loginUi(ad, 'admin'); paso('login-ui-admin', 200)
  await loginUi(ap, 'approver'); paso('login-ui-approver', 200)
  await shot(ad, 'A00-home-admin.png')


  const dd = n => new Date(Date.now() + n * 864e5).toLocaleDateString('sv-SE')
  // ═══════════════════════ A2 · PROGENITORAS (pasa 2): contrato de fecha opcional vacía + cadena completa local ═══════════════════════
  let gpLot = null, gpLotCode = null
  try {
    await viaHub(ad, 'Progenitoras', 'Cría', 'grandparent_import'); paso('GP2-nav-hub-import', 'OK', ad.url())
    await pickSearch(ad, 'Seleccionar documento SAP...', 'AUD-PO-GP'); await pickSearch(ad, 'Seleccionar granja...', 'TEST Granja'); await pickSearch(ad, 'Seleccionar proveedor...', 'AUD Cobb'); await pickSearch(ad, 'Seleccionar transporte...', 'TST-000')
    await fill(ad, 'extra_data.import_plan.origin_country', 'Francia'); await fill(ad, 'extra_data.import_plan.purchased_total', 110); await fill(ad, 'extra_data.import_plan.shipped_total', 105); await fill(ad, 'extra_data.import_plan.received_total', 100); await fill(ad, 'extra_data.import_plan.transit_mortality', 5)
    await fill(ad, 'extra_data.import_plan.departure_date', dd(-7)); await fill(ad, 'extra_data.import_plan.arrival_date', HOY)
    await fill(ad, 'bird_movements.0.quantity', 40); await fill(ad, 'bird_movements.0.avg_weight', 3800); await fill(ad, 'bird_movements.1.quantity', 60); await fill(ad, 'bird_movements.1.avg_weight', 3600)
    // 1) cuarentena (opcional en el plan) dejada en blanco por el usuario
    const imp0 = await save(ad, 'GP2-01a-import-cuarentena-vacia')
    record('GP2-01a-contrato-fecha-vacia', { status: imp0.status, detail: imp0.resp?.detail, quarantine_end_date_enviado: JSON.stringify(imp0.req?.extra_data?.import_plan?.quarantine_end_date), quarantine_days_enviado: JSON.stringify(imp0.req?.extra_data?.import_plan?.quarantine_days) })
    assert('GP2-01a-opcional-vacio-aceptado', imp0.status === 201, { status: imp0.status, detail: imp0.resp?.detail })
    await shot(ad, 'P2-A00-gp-import-cuarentena-vacia.png')
    let imp = imp0
    if (imp0.status !== 201) {
      await fill(ad, 'extra_data.import_plan.quarantine_days', 21); await fill(ad, 'extra_data.import_plan.quarantine_end_date', dd(21))
      imp = await save(ad, 'GP2-01-grandparent_import')
    }
    assert('GP2-01-import-201', imp.status === 201, imp.resp?.detail)
    assert('GP2-01-payload-canonico', imp.req && JSON.stringify(imp.req.egg_storage_records) === '[]' && JSON.stringify(imp.req.feed_movements) === '[]' && JSON.stringify(imp.req.hatchery_params) === '[]' && imp.req.sap_document_ref === 'AUD-PO-GP' && imp.req.lot_id == null, { storage: imp.req?.egg_storage_records, ref: imp.req?.sap_document_ref })
    const impId = imp.resp?.id; J.ids.gpImport = impId

    if (impId) {
      const s = await submitUi(ad, impId); paso('GP2-02-submit-ui', s)
      const rv = await reviewUi(ap, impId, 'approve'); paso('GP2-03-review-approve-ui', rv.complete ?? rv.approve, rv)
      const det = (await api('GET', `/operations/${impId}`, tokA)).data
      assert('GP2-03-aprobado-y-lote', det?.status === 'approved' && !!det?.lot_id, { status: det?.status, lot_id: det?.lot_id })
      gpLot = det?.lot_id
      const lot = (await api('GET', `/lots/${gpLot}`, tokA)).data; gpLotCode = lot?.lot_code; J.ids.gpLot = gpLot; J.ids.gpLotCode = gpLotCode
      assert('GP2-04-lote-auto-codigo', /^L-GP-\d{4}-\d{2}$/.test(gpLotCode || ''), { code: gpLotCode, house: lot?.house_id, farm: lot?.farm_id })
      await ad.goto(`${BASE}/operations/${impId}`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(800)
      assert('GP2-04b-enlace-lote-en-detalle', await visible(ad.locator(`a[href="/lots/${gpLot}"]`), 4000))
      await ad.goto(`${BASE}/lots/${gpLot}`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1200); await shot(ad, 'P2-A02-gp-lot-detail.png')
      const bodyTxt = await ad.locator('body').innerText()
      record('GP2-lotdetail-poblacion-visible', { muestraSaldo: /Poblaci[oó]n|Saldo|aves vivas/i.test(bodyTxt), granjaComoId: /Granja\s*\n?\s*\d+/.test(bodyTxt) })

      // recepción (F-01e): lote sin galpón ⇒ galpón por fila
      await viaLotDetail(ad, gpLot, 'bird_reception')
      await pickSearch(ad, 'Seleccionar documento SAP...', 'AUD-PO-GP')
      await pickSearch(ad, 'Seleccionar proveedor...', 'AUD Cobb')
      await pickSearch(ad, 'Seleccionar línea...', 'AUD Ross 308')
      await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01')
      await selOpt(ad, 'bird_movements.0.sex', 'male'); await fill(ad, 'bird_movements.0.quantity', 40); await fill(ad, 'bird_movements.0.avg_weight', 3800)
      await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01')
      await selOpt(ad, 'bird_movements.1.sex', 'female'); await fill(ad, 'bird_movements.1.quantity', 60); await fill(ad, 'bird_movements.1.avg_weight', 3600)
      const rec = await save(ad, 'GP2-05-bird_reception')
      assert('GP2-05-recepcion-201', rec.status === 201, rec.resp?.detail)
      assert('GP2-05-house-id-derivado', rec.req?.house_id === house1?.id, { house_id: rec.req?.house_id })
      J.ids.gpReception = rec.resp?.id
      if (rec.resp?.id) { const s2 = await submitUi(ad, rec.resp.id); const rv2 = await reviewUi(ap, rec.resp.id, 'approve'); paso('GP2-06-recepcion-aprobada', rv2.complete ?? rv2.approve, { submit: s2, ...rv2 }) }
      const pop1 = await api('POST', '/operations', tokA, { event_type: 'mortality_recording', event_date: HOY, lot_id: gpLot, bird_movements: [{ sex: 'female', quantity: 101 }] })
      assert('GP2-06b-poblacion-100-bracket', pop1.status === 400 && /100/.test(String(pop1.data?.detail)), pop1.data?.detail)

      // registros diarios por UI (lote autocreado sin galpón)
      await viaLotDetail(ad, gpLot, 'mortality_recording'); await pickSearch(ad, 'Seleccionar causa...', null); await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'bird_movements.0.quantity', 1); await fill(ad, 'bird_movements.1.quantity', 1)
      const mort = await save(ad, 'GP2-07-mortality_recording'); assert('GP2-07-mortalidad-201', mort.status === 201, mort.resp?.detail)
      await viaLotDetail(ad, gpLot, 'feed_registration'); await ad.locator('select[name="feed_movements.0.feed_type_id"]').selectOption({ index: 1 }); await fill(ad, 'feed_movements.0.week_number', 1); await fill(ad, 'feed_movements.0.quantity_kg', 50); await fill(ad, 'feed_movements.0.sacks_count', 1)
      const feed = await save(ad, 'GP2-08-feed_registration'); assert('GP2-08-alimento-201', feed.status === 201, feed.resp?.detail); assert('GP2-08-sin-fila-vacia', feed.req?.feed_movements?.length === 1, feed.req?.feed_movements)
      await viaLotDetail(ad, gpLot, 'weight_recording'); await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'sample_size', 20); await fill(ad, 'bird_movements.0.quantity', 10); await fill(ad, 'bird_movements.0.avg_weight', 3900); await fill(ad, 'bird_movements.1.quantity', 10); await fill(ad, 'bird_movements.1.avg_weight', 3700)
      const wt = await save(ad, 'GP2-09-weight_recording'); assert('GP2-09-pesaje-201', wt.status === 201, wt.resp?.detail)
      await viaLotDetail(ad, gpLot, 'vaccination'); await pickSearch(ad, 'Seleccionar vacuna...', null); await selOpt(ad, 'vaccination_route', 'water'); await fill(ad, 'vaccine_lot_number', 'VAC-AUD-1'); await fill(ad, 'dosage_per_bird', 0.5); await fill(ad, 'bird_movements.0.quantity', 40); await fill(ad, 'bird_movements.1.quantity', 60)
      const vac = await save(ad, 'GP2-10-vaccination'); assert('GP2-10-vacunacion-201', vac.status === 201, vac.resp?.detail)
      await viaLotDetail(ad, gpLot, 'medication'); await pickSearch(ad, 'Seleccionar medicamento...', null); await fill(ad, 'dosage_per_bird', 0.1); await fill(ad, 'treatment_days', 3); await fill(ad, 'bird_movements.0.quantity', 40); await fill(ad, 'bird_movements.1.quantity', 60)
      const med = await save(ad, 'GP2-11-medication'); assert('GP2-11-medicacion-201', med.status === 201, med.resp?.detail)
      await viaLotDetail(ad, gpLot, 'farm_inspection'); await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01'); await fill(ad, 'house_inspections.0.temperature', 28); await fill(ad, 'house_inspections.0.humidity', 60); await selOpt(ad, 'house_inspections.0.litter_condition', 'seca')
      const insp = await save(ad, 'GP2-12-farm_inspection'); assert('GP2-12-inspeccion-201', insp.status === 201, insp.resp?.detail)
      await viaLotDetail(ad, gpLot, 'cull_recording'); await pickSearch(ad, 'Seleccionar causa...', null); await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'bird_movements.0.quantity', 1)
      const cull = await save(ad, 'GP2-13-cull_recording'); assert('GP2-13-descarte-201', cull.status === 201, cull.resp?.detail)
      // distribución y salida sobre lote SIN galpón (OD-25): ¿BR-08?
      await viaLotDetail(ad, gpLot, 'bird_distribution'); await pickSearch(ad, 'Seleccionar galpón...', 'TEST Galpon 02'); await selOpt(ad, 'bird_movements.0.sex', 'mixed'); await fill(ad, 'bird_movements.0.quantity', 50)
      const dist = await save(ad, 'GP2-14-bird_distribution'); record('GP2-14-distribucion-lote-sin-galpon', { status: dist.status, detail: dist.resp?.detail, house_id_enviado: dist.req?.house_id })
      await viaLotDetail(ad, gpLot, 'bird_exit'); await fill(ad, 'bird_movements.0.quantity', 5); await fill(ad, 'bird_movements.0.avg_weight', 4000); await fill(ad, 'bird_movements.1.quantity', 5); await fill(ad, 'bird_movements.1.avg_weight', 3800)
      const exit = await save(ad, 'GP2-15-bird_exit'); record('GP2-15-salida-lote-sin-galpon', { status: exit.status, detail: exit.resp?.detail, house_id_enviado: exit.req?.house_id })
      // transición a producción por UI y recolección de huevo
      await ad.goto(`${BASE}/lots/${gpLot}`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1000)
      const tr = ad.getByRole('button', { name: /Iniciar Producci/ }).first()
      if (await visible(tr, 4000)) {
        await tr.click(); await ad.waitForTimeout(500)
        const confirmBtn = ad.getByRole('button', { name: /^Confirmar$/ }).first()
        const [r] = await Promise.all([ad.waitForResponse(r => r.url().includes('/phases') && r.request().method() === 'POST', { timeout: 15000 }).catch(() => null), confirmBtn.click()])
        paso('GP2-16-transicion-produccion-ui', r ? r.status() : 'NO_REQUEST'); await ad.waitForTimeout(800)
        const phases = (await api('GET', `/lots/${gpLot}/phases`, tokA)).data
        record('GP2-16-fases', Array.isArray(phases) ? phases.map(p => ({ code: p.phase?.code ?? p.phase_code, active: p.is_active })) : phases)
      } else record('GP2-16-boton-transicion', 'no visible')
      await viaLotDetail(ad, gpLot, 'egg_collection'); await fill(ad, 'egg_movements.0.quantity', 30); await fill(ad, 'egg_movements.1.quantity', 2); await fill(ad, 'egg_movements.0.avg_weight', 62)
      const egg = await save(ad, 'GP2-17-egg_collection'); record('GP2-17-recoleccion-lote-sin-galpon', { status: egg.status, detail: egg.resp?.detail, house_id_enviado: egg.req?.house_id })
      // UX de error real (BR-01 saldo)
      await viaLotDetail(ad, gpLot, 'mortality_recording'); await pickSearch(ad, 'Seleccionar causa...', null); await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'bird_movements.0.quantity', 99999)
      const bad = await save(ad, 'GP2-18-mortality-exceso'); assert('GP2-18-4xx-seguro', bad.status === 400 && bad.formVisible && bad.pageerrorDelta === 0 && bad.banner.length > 0, { status: bad.status, banner: bad.banner })
      await shot(ad, 'P2-A03-gp-error-ux.png')
    }
  } catch (e) { paso('GP2-EXCEPCION', 'error', String(e).slice(0, 300)); await shot(ad, 'P2-A99-gp-exception.png') }

  // ═══════════════════════ B2 · REPRODUCTORAS: cuadre B01 (BR-20) por navegación ?type= vs asistente por URL ═══════════════════════
  let brLot = null
  try {

    await ad.goto(BASE + '/lots', { waitUntil: 'domcontentloaded' }); await ad.getByRole('link', { name: /Nuevo Lote/ }).first().click()
    await ad.waitForURL('**/lots/new'); await ad.waitForTimeout(1000)
    await fill(ad, 'lot_code', 'AUD-BR-01'); await selOpt(ad, 'bird_type', 'breeder'); await fill(ad, 'start_date', HOY)
    await ad.locator('select[name="farm_id"]').selectOption({ label: 'TEST Granja' }); await ad.waitForTimeout(300)
    await ad.locator('select[name="house_id"]').selectOption({ label: 'TEST-GALPON-01' })
    await ad.locator('select[name="genetic_line_id"]').selectOption({ index: 1 }).catch(() => { }); await ad.locator('select[name="breed_id"]').selectOption({ index: 1 }).catch(() => { })
    const [rl] = await Promise.all([ad.waitForResponse(r => r.url().endsWith('/api/v1/lots') && r.request().method() === 'POST', { timeout: 15000 }), ad.getByRole('button', { name: /Crear Lote/ }).click()])
    const lotBody = await rl.json().catch(() => null); brLot = lotBody?.id; J.ids.brLot = brLot; paso('BR2-00-lote-ui', rl.status(), { id: brLot, curvaAviso: await ad.locator('text=/curva/i').count() })
    assert('BR2-00-lote-201', rl.status() === 201)

    // ¿existe una entrada del producto al asistente sin ?type= (paso 1, el único que fija `stage`)?
    await ad.goto(BASE + '/operations', { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(900)
    record('BR2-entrada-asistente-sin-type', { enlaces_operations_new: await ad.locator('a[href="/operations/new"]').count(), botones_nueva: await ad.getByRole('link', { name: /Nueva operaci|Registrar operaci/i }).count() + await ad.getByRole('button', { name: /Nueva operaci|Registrar operaci/i }).count() })
    // 1) por el hub (type=bird_reception): el bloque de cuadre no se renderiza ⇒ el servidor exige BR-20
    await viaHub(ad, 'Reproductoras', 'Cría', 'bird_reception'); await ensureLot(ad, 'AUD-BR-01')
    record('BR2-hub-campo-cuadre-visible', await ad.locator('[name="received_total"]').count())
    await pickSearch(ad, 'Seleccionar documento SAP...', 'AUD-PO-BR'); await pickSearch(ad, 'Seleccionar proveedor...', 'AUD Cobb'); await pickSearch(ad, 'Seleccionar línea...', 'AUD Ross 308')
    await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01'); await selOpt(ad, 'bird_movements.0.sex', 'male'); await fill(ad, 'bird_movements.0.quantity', 200); await fill(ad, 'bird_movements.0.avg_weight', 42)
    await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01'); await selOpt(ad, 'bird_movements.1.sex', 'female'); await fill(ad, 'bird_movements.1.quantity', 800); await fill(ad, 'bird_movements.1.avg_weight', 40)
    await shot(ad, 'P2-B01-br-reception-por-hub.png')
    const brecHub = await save(ad, 'BR2-01-bird_reception-por-hub')
    record('BR2-01-hub-resultado', { status: brecHub.status, detail: brecHub.resp?.detail, rule: brecHub.resp?.rule, received_total_enviado: JSON.stringify(brecHub.req?.received_total) })
    assert('BR2-01-recepcion-por-hub-201', brecHub.status === 201, { status: brecHub.status, detail: brecHub.resp?.detail })
    // 2) por el asistente (URL directa /operations/new, paso 1 → paso 2 → formulario)
    await ad.goto(BASE + '/operations/new', { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(900)
    await ad.getByRole('button', { name: /Reproductoras\s*[—-]\s*Cría/ }).first().click(); await ad.waitForTimeout(500)
    await ad.getByRole('button', { name: /Recepci[oó]n de Aves/i }).first().click(); await ad.locator('#operation-form').waitFor({ timeout: 15000 }); await ad.waitForTimeout(800)
    await ensureLot(ad, 'AUD-BR-01')
    record('BR2-asistente-campo-cuadre-visible', await ad.locator('[name="received_total"]').count())
    await pickSearch(ad, 'Seleccionar documento SAP...', 'AUD-PO-BR'); await pickSearch(ad, 'Seleccionar proveedor...', 'AUD Cobb'); await pickSearch(ad, 'Seleccionar línea...', 'AUD Ross 308')
    await fill(ad, 'received_total', 1010); await fill(ad, 'dead_on_arrival', 6); await fill(ad, 'rejected_on_arrival', 4); await fill(ad, 'sample_size', 50)
    await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01'); await selOpt(ad, 'bird_movements.0.sex', 'male'); await fill(ad, 'bird_movements.0.quantity', 200); await fill(ad, 'bird_movements.0.avg_weight', 42)
    await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01'); await selOpt(ad, 'bird_movements.1.sex', 'female'); await fill(ad, 'bird_movements.1.quantity', 800); await fill(ad, 'bird_movements.1.avg_weight', 40)
    await shot(ad, 'P2-B02-br-reception-asistente.png')
    const brec = await save(ad, 'BR2-02-bird_reception-B01-asistente'); assert('BR2-02-recepcion-201', brec.status === 201, brec.resp?.detail); J.ids.brReception = brec.resp?.id

    for (const [ev, fn] of [
      ['bird_distribution', async () => { await pickSearch(ad, 'Seleccionar galpón...', 'TEST Galpon 02'); await selOpt(ad, 'bird_movements.0.sex', 'mixed'); await fill(ad, 'bird_movements.0.quantity', 300) }],
      ['feed_registration', async () => { await ad.locator('select[name="feed_movements.0.feed_type_id"]').selectOption({ index: 1 }); await fill(ad, 'feed_movements.0.week_number', 1); await fill(ad, 'feed_movements.0.quantity_kg', 120) }],
      ['water_consumption', async () => { await fill(ad, 'water_liters', 250.5) }],
      ['weight_recording', async () => { await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'sample_size', 30); await fill(ad, 'bird_movements.0.quantity', 15); await fill(ad, 'bird_movements.0.avg_weight', 45); await fill(ad, 'bird_movements.1.quantity', 15); await fill(ad, 'bird_movements.1.avg_weight', 43) }],
      ['mortality_recording', async () => { await pickSearch(ad, 'Seleccionar causa...', null); await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'bird_movements.0.quantity', 2); await fill(ad, 'bird_movements.1.quantity', 3) }],
      ['cull_recording', async () => { await pickSearch(ad, 'Seleccionar causa...', null); await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'bird_movements.1.quantity', 1) }],
      ['vaccination', async () => { await pickSearch(ad, 'Seleccionar vacuna...', null); await selOpt(ad, 'vaccination_route', 'spray'); await fill(ad, 'dosage_per_bird', 0.3); await fill(ad, 'bird_movements.0.quantity', 200); await fill(ad, 'bird_movements.1.quantity', 800) }],
      ['medication', async () => { await pickSearch(ad, 'Seleccionar medicamento...', null); await fill(ad, 'dosage_per_bird', 0.2); await fill(ad, 'treatment_days', 5); await fill(ad, 'bird_movements.0.quantity', 200); await fill(ad, 'bird_movements.1.quantity', 800) }],
      ['bird_exit', async () => { await fill(ad, 'bird_movements.0.quantity', 10); await fill(ad, 'bird_movements.0.avg_weight', 3000); await fill(ad, 'bird_movements.1.quantity', 10); await fill(ad, 'bird_movements.1.avg_weight', 2800) }],
    ]) {
      try { await viaLotDetail(ad, brLot, ev); await fn(); const r = await save(ad, `BR-${ev}`); assert(`BR-${ev}-201`, r.status === 201, r.resp?.detail ?? r.zodErrors) } catch (e) { paso(`BR-${ev}-EXC`, 'error', String(e).slice(0, 200)) }
    }
    // transición a producción + huevo
    await ad.goto(`${BASE}/lots/${brLot}`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1000)
    const tr = ad.getByRole('button', { name: /Iniciar Producci/ }).first()
    if (await visible(tr, 4000)) { await tr.click(); await ad.waitForTimeout(400); const [r] = await Promise.all([ad.waitForResponse(r => r.url().includes('/phases') && r.request().method() === 'POST', { timeout: 15000 }).catch(() => null), ad.getByRole('button', { name: /^Confirmar$/ }).first().click()]); paso('BR2-transicion-ui', r ? r.status() : 'NO_REQUEST') }
    await viaLotDetail(ad, brLot, 'egg_collection'); await fill(ad, 'egg_movements.0.quantity', 500); await fill(ad, 'egg_movements.1.quantity', 10); await fill(ad, 'egg_movements.2.quantity', 5); await fill(ad, 'egg_movements.0.avg_weight', 60)
    const ec = await save(ad, 'BR2-egg_collection'); assert('BR2-egg_collection-201', ec.status === 201, ec.resp?.detail); J.ids.brEggCollection = ec.resp?.id
    await viaLotDetail(ad, brLot, 'egg_dispatch'); await pickSearch(ad, 'Seleccionar documento SAP...', 'AUD-STO-EGG'); await pickSearch(ad, 'Seleccionar incubadora...', 'AUD Incubadora'); await pickSearch(ad, 'Seleccionar transporte...', 'TST-000'); await fill(ad, 'egg_movements.0.quantity', 400)
    const ed = await save(ad, 'BR2-egg_dispatch'); assert('BR2-egg_dispatch-201', ed.status === 201, ed.resp?.detail ?? ed.zodErrors); record('BR2-egg_dispatch-payload', { hp: ed.req?.hatchery_params, ref: ed.req?.sap_document_ref, transport: ed.req?.transport_id, extra: ed.req?.extra_data })
    await viaLotDetail(ad, brLot, 'egg_dispatch'); await fill(ad, 'egg_movements.0.quantity', 5000)
    const ed2 = await save(ad, 'BR2-egg_dispatch-exceso'); assert('BR2-BR02-4xx-seguro', ed2.status === 400 && ed2.formVisible && ed2.pageerrorDelta === 0, { status: ed2.status, banner: ed2.banner })
    // ── P-07 por UI: devolver → reenviar → corregir → aprobar; rechazar → reenviar ──
    if (J.ids.brEggCollection) {
      const id = J.ids.brEggCollection
      paso('BR2-P07-submit', await submitUi(ad, id))
      const r1 = await reviewUi(ap, id, 'return'); paso('BR2-P07-return-ui', r1.return, r1)
      let d = (await api('GET', `/operations/${id}`, tokA)).data; assert('BR2-P07-devuelto', d?.status === 'returned', d?.status)
      paso('BR2-P07-resubmit-ui', await submitUi(ad, id))
      d = (await api('GET', `/operations/${id}`, tokA)).data; assert('BR2-P07-reenviado', d?.status === 'pending_review', d?.status)
      // corrección por UI (admin tiene corrections:correct)
      await ap.goto(`${BASE}/review/${id}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(800)
      const st = ap.getByRole('button', { name: /Iniciar Revisi/i }).first(); if (await visible(st, 3000)) { await Promise.all([ap.waitForResponse(r => r.url().includes('/review/start/'), { timeout: 15000 }), st.click()]) }
      await ad.goto(`${BASE}/review/${id}/correct`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(900)
      const fieldOpts = await ad.locator('select').first().locator('option').allInnerTexts().catch(() => [])
      record('BR2-P07-campos-corregibles-ui', fieldOpts)
      await ad.locator('input[type="text"]').nth(1).fill('Recolección corregida por auditoría')
      await ad.locator('textarea').first().fill('Motivo de corrección con longitud suficiente')
      const [rc] = await Promise.all([ad.waitForResponse(r => r.url().endsWith('/corrections') && r.request().method() === 'POST', { timeout: 15000 }).catch(() => null), ad.getByRole('button', { name: /Guardar/ }).first().click()])
      paso('BR2-P07-correccion-ui', rc ? rc.status() : 'NO_REQUEST', rc ? await rc.json().catch(() => null) : null)
      d = (await api('GET', `/operations/${id}`, tokA)).data; record('BR2-P07-tras-correccion', { status: d?.status, observations: d?.observations })
      const r2 = await reviewUi(ap, id, 'approve'); paso('BR2-P07-approve-ui', r2.complete ?? r2.approve, r2)
      d = (await api('GET', `/operations/${id}`, tokA)).data; assert('BR2-P07-aprobado-final', d?.status === 'approved', d?.status)
      // rechazo → reenvío (OD-17)
      const id2 = J.ids.brReception
      if (id2) {
        paso('BR2-P07b-submit', await submitUi(ad, id2))
        const rj = await reviewUi(ap, id2, 'reject'); paso('BR2-P07b-reject-ui', rj.reject, rj)
        let e2 = (await api('GET', `/operations/${id2}`, tokA)).data; assert('BR2-P07b-rechazado', e2?.status === 'rejected', e2?.status)
        paso('BR2-P07b-resubmit-ui', await submitUi(ad, id2))
        e2 = (await api('GET', `/operations/${id2}`, tokA)).data; assert('BR2-P07b-rechazado-reenviado', e2?.status === 'pending_review', e2?.status)
        const r3 = await reviewUi(ap, id2, 'approve'); e2 = (await api('GET', `/operations/${id2}`, tokA)).data; assert('BR2-P07b-aprobado', e2?.status === 'approved', { ...r3, status: e2?.status })
      }
      // bandeja de aprobaciones + notificaciones del operador
      await ap.goto(`${BASE}/approvals`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(1000); await shot(ap, 'P2-B02-approvals.png')
      const unread = (await api('GET', '/notifications/unread-count', tokA)).data; record('BR2-P14-notificaciones-admin', unread)
    }
  } catch (e) { paso('BR2-EXCEPCION', 'error', String(e).slice(0, 300)); await shot(ad, 'P2-B99-br-exception.png') }
  // ═══════════════════════ C · INCUBADORA (P-05) · pasa 2 (selector de planta corregido) ═══════════════════════
  let hLot = null
  try {
    await ad.goto(BASE + '/lots/new', { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1000)
    await fill(ad, 'lot_code', 'AUD-HAT-01'); await selOpt(ad, 'bird_type', 'hatchery'); await fill(ad, 'start_date', HOY)
    await ad.locator('select[name="farm_id"]').selectOption({ label: 'TEST Granja' }); await ad.waitForTimeout(300); await ad.locator('select[name="house_id"]').selectOption({ label: 'TEST Galpon 02' })
    const [rl] = await Promise.all([ad.waitForResponse(r => r.url().endsWith('/api/v1/lots') && r.request().method() === 'POST', { timeout: 15000 }), ad.getByRole('button', { name: /Crear Lote/ }).click()])
    hLot = (await rl.json().catch(() => null))?.id; J.ids.hatLot = hLot; paso('HAT2-00-lote-ui', rl.status(), hLot)
    await viaHub(ad, 'Incubadora', null, 'hatchery_inspection'); paso('HAT2-nav-hub', 'OK', ad.url())
    await pickSearch(ad, 'Seleccionar incubadora...', 'AUD Planta').catch(() => { }); await pickSearch(ad, 'Seleccionar incubadora...', 'AUD Incubadora'); await fill(ad, 'hatchery_params.0.temperature', 37.6); await fill(ad, 'hatchery_params.0.humidity', 56); await fill(ad, 'hatchery_params.0.co2', 0.4)
    const hi = await save(ad, 'HAT2-01-hatchery_inspection'); assert('HAT2-01-inspeccion-201', hi.status === 201, hi.resp?.detail ?? hi.zodErrors)
    // recepción de huevos por UI
    await viaLotDetail(ad, hLot, 'egg_reception_hatchery')
    await pickSearch(ad, 'Seleccionar documento SAP...', 'AUD-STO-EGG').catch(() => { }); await pickSearch(ad, 'Seleccionar granja...', 'TEST Granja'); await pickSearch(ad, 'Seleccionar...', 'TST-000').catch(() => { })
    await fill(ad, 'extra_data.dispatch_order', 'D-AUD-1'); await fill(ad, 'egg_storage_records.0.eggs_received', 1000); await fill(ad, 'egg_storage_records.0.transport_temp_c', 15); await fill(ad, 'egg_storage_records.0.storage_temp_c', 15)
    await shot(ad, 'P2-C01-hat-egg-reception-form.png')
    const er = await save(ad, 'HAT2-02-egg_reception_hatchery'); record('HAT2-02-recepcion-huevos-ui', { status: er.status, detail: er.resp?.detail || er.resp, farm_id: er.req?.farm_id, house_id: er.req?.house_id, egg_movements: er.req?.egg_movements, storage: er.req?.egg_storage_records })
    assert('HAT2-02-recepcion-201', er.status === 201, er.resp?.detail || er.resp)
    // variante sin datos de almacenamiento
    await viaLotDetail(ad, hLot, 'egg_reception_hatchery'); await pickSearch(ad, 'Seleccionar granja...', 'TEST Granja'); await fill(ad, 'extra_data.dispatch_order', 'D-AUD-2')
    const er2 = await save(ad, 'HAT2-02b-egg_reception-sin-almacen'); record('HAT2-02b', { status: er2.status, detail: er2.resp?.detail || er2.resp, farm_id: er2.req?.farm_id, house_id: er2.req?.house_id, egg_movements: er2.req?.egg_movements })
    // sondas API para aislar causas (mismo cuerpo de la UI + granja/galpón)
    if (er.req) {
      const p1 = await api('POST', '/operations', tokA, { ...er.req, farm_id: farm.id, house_id: house2?.id }); record('HAT2-02-sonda-con-granja', { status: p1.status, detail: p1.data?.detail })
      const p2 = await api('POST', '/operations', tokA, { ...er.req, farm_id: farm.id, house_id: house2?.id, egg_storage_records: [] }); record('HAT2-02-sonda-sin-storage', { status: p2.status, detail: p2.data?.detail, id: p2.data?.id })
      const bal = await api('POST', '/operations', tokA, { event_type: 'incubation_load', event_date: HOY, lot_id: hLot, hatchery_params: [{ quantity_loaded: 1, temperature: 37.5 }] }); record('HAT2-02-saldo-tras-recepcion-ui', { status: bal.status, detail: bal.data?.detail })
    }
    await viaLotDetail(ad, hLot, 'egg_reception_classification'); await fill(ad, 'egg_movements.0.quantity', 950); await fill(ad, 'egg_movements.1.quantity', 10)
    const ecl = await save(ad, 'HAT2-03-egg_reception_classification'); record('HAT2-03', { status: ecl.status, detail: ecl.resp?.detail })
    await viaLotDetail(ad, hLot, 'incubation_load'); await pickSearch(ad, 'Seleccionar incubadora...', 'AUD Planta').catch(() => { }); await pickSearch(ad, 'Seleccionar incubadora...', 'AUD Incubadora'); await fill(ad, 'hatchery_params.0.quantity_loaded', 800); await fill(ad, 'hatchery_params.0.temperature', 37.5); await fill(ad, 'hatchery_params.0.humidity', 55)
    const il = await save(ad, 'HAT2-04-incubation_load'); record('HAT2-04-carga-ui', { status: il.status, detail: il.resp?.detail, hp: il.req?.hatchery_params }); assert('HAT2-04-carga-201', il.status === 201, il.resp?.detail)
    await viaLotDetail(ad, hLot, 'ovoscopy'); await fill(ad, 'bird_movements.0.week_number', 10); await fill(ad, 'egg_movements.1.quantity', 40); await fill(ad, 'egg_movements.2.quantity', 5)
    const ov = await save(ad, 'HAT2-05-ovoscopy'); record('HAT2-05', { status: ov.status, detail: ov.resp?.detail, bm: ov.req?.bird_movements, em: ov.req?.egg_movements })
    await viaLotDetail(ad, hLot, 'transfer_to_hatcher'); await pickSearch(ad, 'Seleccionar nacedora...', 'AUD Nacedora'); await fill(ad, 'extra_data.incubation_day', 18); await fill(ad, 'hatchery_params.0.quantity_transferred', 750); await fill(ad, 'hatchery_params.0.temperature', 37); await fill(ad, 'hatchery_params.0.humidity', 68)
    const th = await save(ad, 'HAT2-06-transfer_to_hatcher'); record('HAT2-06', { status: th.status, detail: th.resp?.detail })
    // nacimiento: dosis vacía (defecto candidato) y con dosis
    await viaLotDetail(ad, hLot, 'birth_registration'); await fill(ad, 'bird_movements.0.quantity', 300); await fill(ad, 'bird_movements.1.quantity', 350); await fill(ad, 'chicks_healthy', 600); await fill(ad, 'chicks_weak', 50)
    await shot(ad, 'P2-C02-hat-birth-form.png')
    const b1 = await save(ad, 'HAT2-07-birth_registration-dosis-vacia'); record('HAT2-07-nacimiento-sin-dosis', { status: b1.status, detail: b1.resp?.detail, zod: b1.zodErrors, banner: b1.banner })
    await viaLotDetail(ad, hLot, 'birth_registration'); await fill(ad, 'bird_movements.0.quantity', 300); await fill(ad, 'bird_movements.1.quantity', 350); await fill(ad, 'chicks_healthy', 600); await fill(ad, 'chicks_weak', 50); await fill(ad, 'dosage_per_bird', 0.2)
    const b2 = await save(ad, 'HAT2-07b-birth_registration-con-dosis'); record('HAT2-07b-nacimiento-con-dosis', { status: b2.status, detail: b2.resp?.detail, zod: b2.zodErrors })
    assert('HAT2-07-nacimiento-201', b1.status === 201 || b2.status === 201, { sinDosis: b1.status, conDosis: b2.status })
    // sonda API del mismo nacimiento (contrato backend OK?)
    const bp = await api('POST', '/operations', tokA, { event_type: 'birth_registration', event_date: HOY, lot_id: hLot, farm_id: farm.id, house_id: house2?.id, chicks_healthy: 600, chicks_weak: 50, bird_movements: [{ sex: 'male', quantity: 300 }, { sex: 'female', quantity: 350 }] }); record('HAT2-07-sonda-api-nacimiento', { status: bp.status, detail: bp.data?.detail, id: bp.data?.id })
    await viaLotDetail(ad, hLot, 'chick_dispatch'); await pickSearch(ad, 'Seleccionar documento SAP...', 'AUD-PO').catch(() => { }); await pickSearch(ad, 'Seleccionar granja...', 'TEST Granja destino'); await pickSearch(ad, 'Seleccionar transporte...', 'TST-000'); await fill(ad, 'bird_movements.0.quantity', 100); await fill(ad, 'bird_movements.1.quantity', 100)
    const cd = await save(ad, 'HAT2-08-chick_dispatch'); record('HAT2-08-despacho-pollitos-ui', { status: cd.status, detail: cd.resp?.detail, farm_id: cd.req?.farm_id, house_id: cd.req?.house_id, dest: cd.req?.destination_farm_id })
    await shot(ad, 'P2-C03-hat-chick-dispatch.png')
  } catch (e) { paso('HAT2-EXCEPCION', 'error', String(e).slice(0, 300)); await shot(ad, 'P2-C99-hat-exception.png') }

  // ═══════════════════════ D · ENGORDE (P-06) · pasa 2 (aprobación por UI con detalle + respaldo API) ═══════════════════════
  try {
    const boLot = J.ids.broilerLot
    await viaHub(ad, 'Pollo de Engorde', null, 'farm_inspection'); paso('BO2-nav-hub', 'OK', ad.url())
    await pickSearch(ad, 'Seleccionar granja...', 'TEST Granja'); await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01'); await fill(ad, 'house_inspections.0.temperature', 30); await fill(ad, 'house_inspections.0.humidity', 60); await selOpt(ad, 'house_inspections.0.litter_condition', 'seca')
    const bi = await save(ad, 'BO2-01-farm_inspection'); assert('BO2-01-201', bi.status === 201, bi.resp?.detail)
    const ids = []
    await viaLotDetail(ad, boLot, 'bird_reception'); await pickSearch(ad, 'Seleccionar documento SAP...', 'AUD-PO-BO'); await pickSearch(ad, 'Seleccionar proveedor...', 'AUD Cobb'); await pickSearch(ad, 'Seleccionar galpón...', 'TEST-GALPON-01'); await selOpt(ad, 'bird_movements.0.sex', 'mixed'); await fill(ad, 'bird_movements.0.quantity', 5000); await fill(ad, 'bird_movements.0.avg_weight', 42)
    const rec = await save(ad, 'BO2-02-bird_reception'); assert('BO2-02-recepcion-201', rec.status === 201, rec.resp?.detail); if (rec.resp?.id) ids.push(rec.resp.id)
    for (const [ev, fn] of [
      ['bird_distribution', async () => { await pickSearch(ad, 'Seleccionar galpón...', 'TEST Galpon 02'); await selOpt(ad, 'bird_movements.0.sex', 'mixed'); await fill(ad, 'bird_movements.0.quantity', 2000) }],
      ['feed_registration', async () => { await ad.locator('select[name="feed_movements.0.feed_type_id"]').selectOption({ index: 1 }); await fill(ad, 'feed_movements.0.week_number', 1); await fill(ad, 'feed_movements.0.quantity_kg', 850.5) }],
      ['water_consumption', async () => { await fill(ad, 'water_liters', 1200) }],
      ['weight_recording', async () => { await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'sample_size', 100); await fill(ad, 'bird_movements.0.quantity', 50); await fill(ad, 'bird_movements.0.avg_weight', 2400); await fill(ad, 'bird_movements.1.quantity', 50); await fill(ad, 'bird_movements.1.avg_weight', 2200) }],
      ['mortality_recording', async () => { await pickSearch(ad, 'Seleccionar causa...', null); await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'bird_movements.0.quantity', 20); await fill(ad, 'bird_movements.1.quantity', 20) }],
      ['cull_recording', async () => { await pickSearch(ad, 'Seleccionar causa...', null); await fill(ad, 'bird_movements.0.week_number', 1); await fill(ad, 'bird_movements.0.quantity', 15) }],
      ['vaccination', async () => { await pickSearch(ad, 'Seleccionar vacuna...', null); await selOpt(ad, 'vaccination_route', 'water'); await fill(ad, 'dosage_per_bird', 0.5); await fill(ad, 'bird_movements.0.quantity', 2500); await fill(ad, 'bird_movements.1.quantity', 2500) }],
      ['medication', async () => { await pickSearch(ad, 'Seleccionar medicamento...', null); await fill(ad, 'dosage_per_bird', 0.1); await fill(ad, 'treatment_days', 5); await fill(ad, 'bird_movements.0.quantity', 2500); await fill(ad, 'bird_movements.1.quantity', 2500) }],
      ['bird_exit', async () => { await pickSearch(ad, 'Seleccionar tipo...', null); await pickSearch(ad, 'Seleccionar transporte...', 'TST-000'); await selOpt(ad, 'extra_data.transport_cage_condition', 'good'); await fill(ad, 'bird_movements.0.quantity', 100); await fill(ad, 'bird_movements.0.avg_weight', 2500); await fill(ad, 'bird_movements.1.quantity', 100); await fill(ad, 'bird_movements.1.avg_weight', 2300) }],
    ]) {
      try { await viaLotDetail(ad, boLot, ev); await fn(); const r = await save(ad, `BO2-${ev}`); assert(`BO2-${ev}-201`, r.status === 201, r.resp?.detail ?? r.zodErrors); if (r.resp?.id) ids.push(r.resp.id) } catch (e) { paso(`BO2-${ev}-EXC`, 'error', String(e).slice(0, 200)) }
    }
    // cierre con registros sin aprobar (R7) — ¿feedback en UI?
    await ad.goto(`${BASE}/lots/${boLot}`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1200)
    const closeBtn = ad.getByRole('button', { name: /Cerrar Lote/ }).first()
    if (await visible(closeBtn, 4000)) {
      await closeBtn.click(); await ad.waitForTimeout(400)
      const [r] = await Promise.all([ad.waitForResponse(r => r.url().includes('/close') && r.request().method() === 'POST', { timeout: 15000 }).catch(() => null), ad.getByRole('button', { name: /Cerrar Lote/ }).last().click()])
      await ad.waitForTimeout(1000)
      const toasts = await ad.locator('.fixed.top-4 span').allInnerTexts().catch(() => [])
      const bodyT = await ad.locator('body').innerText()
      record('BO2-close-sin-aprobar', { status: r ? r.status() : 'NO_REQUEST', detail: r ? (await r.json().catch(() => null))?.detail : null, toasts, bannerError: /error|no se pudo|R7|aprob/i.test(bodyT.slice(0, 4000)) })
      await shot(ad, 'P2-D01-bo-close-unapproved.png')
    } else record('BO2-close-boton', 'no visible')
    // aprobar todo por UI (aprobador) y cerrar
    let aprobados = 0
    const detalles = []
    if (ids[0]) { await ap.goto(`${BASE}/review/${ids[0]}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(1200); await shot(ap, 'P2-D00-review-page-approver.png'); record('BO2-review-page-approver', { url: ap.url(), botones: await ap.getByRole('button').allInnerTexts().catch(() => []) }) }
    for (const id of ids) { const s = await submitUi(ad, id); const rv = await reviewUi(ap, id, 'approve'); const ok = (rv.status === 'approved') || rv.approve === 200; if (!ok) { const a1 = await api('POST', `/review/start/${id}`, tokP); const a2 = await api('POST', '/review/complete', tokP, { event_id: id }); rv.apiFallback = { start: a1.status, complete: a2.status, status: a2.data?.status, detail: a2.data?.detail }; if (a2.data?.status === 'approved') aprobados++ } else aprobados++; detalles.push({ id, submit: s, ...rv }) }
    record('BO2-aprobaciones-detalle', detalles)
    paso('BO2-aprobaciones-ui', 'OK', { aprobados, total: ids.length })
    await ad.goto(`${BASE}/lots/${boLot}`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1200)
    if (await visible(ad.getByRole('button', { name: /Cerrar Lote/ }).first(), 4000)) {
      await ad.getByRole('button', { name: /Cerrar Lote/ }).first().click(); await ad.waitForTimeout(400)
      const [r] = await Promise.all([ad.waitForResponse(r => r.url().includes('/close') && r.request().method() === 'POST', { timeout: 15000 }).catch(() => null), ad.getByRole('button', { name: /Cerrar Lote/ }).last().click()])
      await ad.waitForTimeout(1200); const body = r ? await r.json().catch(() => null) : null
      paso('BO2-close-aprobado', r ? r.status() : 'NO_REQUEST', body?.detail || { mort: body?.total_mortality, feed: body?.total_feed_kg })
      const lot = (await api('GET', `/lots/${boLot}`, tokA)).data; assert('BO2-lote-cerrado', lot?.status === 'closed', lot?.status)
      await shot(ad, 'P2-D02-bo-closed.png')
      const rep = (await api('GET', `/reports/lot/${boLot}`, tokA)); record('BO2-reporte-lote', { status: rep.status, keys: rep.data && Object.keys(rep.data).slice(0, 15) })
      const ipe = (await api('GET', `/reports/kpi/ipe/${boLot}`, tokA)); record('BO2-ipe', { status: ipe.status, ipe: ipe.data?.ipe, fcr: ipe.data?.fcr, viab: ipe.data?.viabilidad_pct })
    }
  } catch (e) { paso('BO2-EXCEPCION', 'error', String(e).slice(0, 300)); await shot(ad, 'P2-D99-bo-exception.png') }

  // ═══════════════════════ E · MAESTROS / ADMIN / OD-23 · pasa 2 (etiquetas Desactivar/Activar) ═══════════════════════
  try {
    await ad.goto(`${BASE}/masters/hatcheries`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1000); await shot(ad, 'P2-E01-masters-hatcheries.png')
    await ad.getByRole('button', { name: /Nuevo/ }).first().click(); await ad.waitForTimeout(500)
    const inputs = ad.locator('form input, [role=dialog] input'); const n = await inputs.count(); record('MAS2-form-inputs', n)
    const names = []; for (let i = 0; i < n; i++) names.push(await inputs.nth(i).getAttribute('name') || await inputs.nth(i).getAttribute('placeholder'))
    record('MAS2-form-fields', names)
    for (let i = 0; i < n; i++) { const nm = names[i] || ''; if (/name/i.test(nm)) await inputs.nth(i).fill('AUD Planta UI'); else if (/code/i.test(nm)) await inputs.nth(i).fill('AUD-UI'); }
    const [rm] = await Promise.all([ad.waitForResponse(r => r.url().includes('/masters/hatcheries') && r.request().method() === 'POST', { timeout: 10000 }).catch(() => null), ad.getByRole('button', { name: /Guardar|Crear|Save/ }).first().click()])
    paso('MAS2-hatchery-create-ui', rm ? rm.status() : 'NO_REQUEST', rm ? { req: JSON.parse(rm.request().postData() || 'null'), detail: (await rm.json().catch(() => null))?.detail } : null)
    // usuarios / roles / auditoría / reportes / dashboard
    for (const [p, tag] of [['/users', 'users'], ['/roles', 'roles'], ['/audit', 'audit'], ['/reports', 'reports'], ['/', 'dashboard'], ['/sap', 'sap'], ['/profile', 'profile'], ['/reports/sap', 'sap-comparison']]) {
      await ad.goto(BASE + p, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1200)
      const txt = await ad.locator('main, body').first().innerText().catch(() => ''); await shot(ad, `P2-E02-${tag}.png`)
      record(`PAGE2-${tag}`, { chars: txt.length, rawKeys: (txt.match(/\b(nav|operations|lots|review|common|admin|masters|sap|audit|reports|kpi)\.[a-zA-Z]+/g) || []).slice(0, 8), cargando: /Cargando/.test(txt) })
    }
    // OD-23 por UI: apagar Incubadora → concesión termina → reencender no revive → conceder de nuevo
    await ad.goto(`${BASE}/admin/unit-access`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1200); await shot(ad, 'P2-E03-unit-access.png')
    const opId = (await api('GET', '/me', tokO)).data?.id
    const gr0 = (await api('GET', `/users/${opId}/business-units`, tokA)).data; record('OD23b-grants-antes', gr0)
    const hatCard = ad.locator('li').filter({ hasText: /Incubadora/ }).first()
    await hatCard.getByRole('button', { name: /Desactivar|Deshabilitar|Apagar/ }).click(); await ad.waitForTimeout(400)
    const [rd] = await Promise.all([ad.waitForResponse(r => r.url().includes('/business-units/hatchery/disable'), { timeout: 15000 }).catch(() => null), ad.getByRole('button', { name: /Desactivar|Deshabilitar|Apagar|Confirmar/ }).last().click()])
    paso('OD23b-disable-ui', rd ? rd.status() : 'NO_REQUEST'); await ad.waitForTimeout(1000)
    const gr1 = (await api('GET', `/users/${opId}/business-units`, tokA)).data; record('OD23b-grants-tras-apagar', gr1)
    const me1 = (await api('GET', '/me', tokO)).data; record('OD23b-operador-me-tras-apagar', { eff: me1?.effective_business_units ?? me1?.business_units })
    // navegación del admin sin Incubadora
    await ad.goto(`${BASE}/menu/poultry`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(900)
    assert('OD16b-hub-sin-incubadora-tras-OFF', (await ad.getByRole('button', { name: /Incubadora/ }).count()) === 0)
    const denied = await api('POST', '/operations', tokA, { event_type: 'hatchery_inspection', event_date: HOY, hatchery_params: [{ temperature: 37 }] }); record('OD16b-global-actor-bu-off-api', { status: denied.status, detail: denied.data?.detail })
    await ad.goto(`${BASE}/admin/unit-access`, { waitUntil: 'domcontentloaded' }); await ad.waitForTimeout(1000)
    await ad.locator('li').filter({ hasText: /Incubadora/ }).first().getByRole('button', { name: /^Activar|Habilitar|Encender/ }).click(); await ad.waitForTimeout(400)
    const [re] = await Promise.all([ad.waitForResponse(r => r.url().includes('/business-units/hatchery/enable'), { timeout: 15000 }).catch(() => null), ad.getByRole('button', { name: /^Activar|Habilitar|Encender|Confirmar/ }).last().click()])
    paso('OD23b-enable-ui', re ? re.status() : 'NO_REQUEST'); await ad.waitForTimeout(800)
    const gr2 = (await api('GET', `/users/${opId}/business-units`, tokA)).data; record('OD23b-grants-tras-reencender', gr2)
    const vivas = Array.isArray(gr2) ? gr2.filter(g => (g.business_unit_code || g.code) === 'hatchery' && !g.revoked_at) : []
    assert('OD23b-reencender-no-revive', vivas.length === 0, vivas)
    await ad.locator('#ga-fe02-unit').selectOption('hatchery'); await ad.waitForTimeout(1200)
    const row = ad.locator('li').filter({ hasText: 'test_operator' }).first()
    const [rg] = await Promise.all([ad.waitForResponse(r => r.url().includes(`/users/${opId}/business-units`) && r.request().method() === 'POST', { timeout: 15000 }).catch(() => null), row.getByRole('button', { name: /Conceder/ }).click()])
    paso('OD23b-regrant-ui', rg ? rg.status() : 'NO_REQUEST'); await ad.waitForTimeout(800)
    const gr3 = (await api('GET', `/users/${opId}/business-units`, tokA)).data; assert('OD23b-regrant-restaura', Array.isArray(gr3) && gr3.some(g => (g.business_unit_code || g.code) === 'hatchery' && !g.revoked_at), gr3)
    await shot(ad, 'P2-E04-unit-access-after.png')
    // self-grant negativo por API (OD-15)
    const selfG = await api('POST', `/users/${me.id}/business-units`, tokA, { business_unit_code: 'hatchery' }); record('OD15b-self-grant-api', { status: selfG.status, detail: selfG.data?.detail })
  } catch (e) { paso('ADM-EXCEPCION', 'error', String(e).slice(0, 300)); await shot(ad, 'P2-E99-adm-exception.png') }


  // ═══════════════════════ H8b · E-02 con lotes gemelos: control (cierra) vs reverso efectivo (¿cierra?) ═══════════════════════
  try {
    const aprobar = async (id) => { const s = await api('POST', `/operations/${id}/submit`, tokA); const st = await api('POST', `/review/start/${id}`, tokP); const cp = await api('POST', '/review/complete', tokP, { event_id: id }); return { submit: s.status, start: st.status, complete: cp.status, status: cp.data?.status, detail: cp.data?.detail } }
    const gemelo = async (code) => {
      const nl = await api('POST', '/lots', tokA, { lot_code: code, bird_type: 'broiler', farm_id: farm?.id, house_id: house2?.id, sex: 'mixed', start_date: HOY })
      const lotId = nl.data?.id; const out = { lote: { status: nl.status, id: lotId, detail: nl.status >= 400 ? nl.data?.detail : undefined } }
      const rec = (await api('POST', '/operations', tokA, { event_type: 'bird_reception', event_date: HOY, lot_id: lotId, farm_id: farm?.id, house_id: house2?.id, bird_movements: [{ sex: 'male', quantity: 50, avg_weight: 40, house_id: house2?.id }, { sex: 'female', quantity: 50, avg_weight: 40, house_id: house2?.id }] })).data
      out.recepcion = { id: rec?.id, detail: rec?.detail, aprob: rec?.id ? await aprobar(rec.id) : null }
      const wt = (await api('POST', '/operations', tokA, { event_type: 'weight_recording', event_date: HOY, lot_id: lotId, farm_id: farm?.id, house_id: house2?.id, sample_size: 10, bird_movements: [{ sex: 'male', quantity: 5, avg_weight: 45 }, { sex: 'female', quantity: 5, avg_weight: 43 }] })).data
      out.pesaje = { id: wt?.id, detail: wt?.detail, aprob: wt?.id ? await aprobar(wt.id) : null }
      const fe = (await api('POST', '/operations', tokA, { event_type: 'feed_registration', event_date: HOY, lot_id: lotId, feed_movements: [{ quantity_kg: 7 }] })).data
      out.feed = { id: fe?.id, detail: fe?.detail, aprob: fe?.id ? await aprobar(fe.id) : null }
      return { lotId, feedId: fe?.id, out }
    }
    const ctrl = await gemelo('AUD-REV-CTRL'); record('H8b-control-fixture', ctrl.out)
    const clc = await api('POST', `/lots/${ctrl.lotId}/close`, tokA); record('H8b-control-cierre', { status: clc.status, detail: clc.data?.detail, resumen: clc.status === 200 ? { status: clc.data?.status, end_date: clc.data?.end_date } : undefined })
    assert('H8b-control-cierra-200', clc.status === 200, { status: clc.status, detail: clc.data?.detail })
    const rev = await gemelo('AUD-REV-REV'); record('H8b-reverso-fixture', rev.out)
    const rv = await api('POST', '/reversals', tokA, { event_id: rev.feedId, reason: 'Reverso de auditoría E-02 (Claude, sin producto)' })
    record('H8b-reverso-solicitado', { status: rv.status, counterpart: rv.data?.reversal_event_id, detail: rv.status >= 400 ? rv.data?.detail : undefined })
    const cId = rv.data?.reversal_event_id
    if (cId) {
      const c0 = (await api('GET', `/operations/${cId}`, tokA)).data
      const ap2 = await aprobar(cId)
      const o = (await api('GET', `/operations/${rev.feedId}`, tokA)).data; const c = (await api('GET', `/operations/${cId}`, tokA)).data
      record('H8b-reverso-efectuado', { contraparteNace: c0?.status, aprobContraparte: ap2, original: o?.status, contraparte: c?.status })
      const cl = await api('POST', `/lots/${rev.lotId}/close`, tokA); record('H8b-cierre-con-reverso', { status: cl.status, detail: cl.data?.detail })
      assert('H8b-E02-cierre-bloqueado-por-reversed', cl.status === 400 && /aprob|pendiente|reversed/i.test(String(cl.data?.detail)), { status: cl.status, detail: cl.data?.detail })
      const cn = await api('POST', `/operations/${rev.feedId}/cancel`, tokA); record('H8b-reversed-no-cancelable', { status: cn.status, detail: cn.data?.detail })
      const tl = await api('GET', `/audit/timeline/operational_event/${rev.feedId}`, tokA); record('H8b-timeline-original', { status: tl.status, acciones: (tl.data?.timeline || []).map(a => `${a.action}:${a.new_state || ''}`) })
      const tlc = await api('GET', `/audit/timeline/operational_event/${cId}`, tokA); record('H8b-timeline-contraparte', { status: tlc.status, acciones: (tlc.data?.timeline || []).map(a => `${a.action}:${a.new_state || ''}`) })
    }
  } catch (e) { record('H8b-excepcion', String(e).slice(0, 200)) }

} catch (e) {
  paso('ERROR-GLOBAL', 'excepcion', String(e).slice(0, 400))
} finally {
  J.fatal_react = J.pageerror.filter(p => /React|#31/.test(p.msg)).length
  J.http5xx = J.httpErrores.filter(h => h.status >= 500)
  fs.writeFileSync(path.join(OUT, 'ui-e2e-local-pass2.json'), JSON.stringify(J, null, 2))
  const fails = J.asserts.filter(a => a.ok === false)
  console.log(`\n== resumen == asserts PASS ${J.asserts.filter(a => a.ok === true).length} · FAIL ${fails.length} · notas ${J.asserts.filter(a => a.ok === null).length} · pageerror ${J.pageerror.length} (React: ${J.fatal_react}) · 5xx ${J.http5xx.length}`)
  for (const f of fails) console.log('FALLO:', f.name, JSON.stringify(f.detail).slice(0, 200))
  await browser.close()
}
