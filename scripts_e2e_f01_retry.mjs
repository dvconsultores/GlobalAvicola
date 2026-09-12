#!/usr/bin/env node
/**
 * GA-F01 · REINTENTO DEL RECORRIDO UAT-09 / CERTIFICACIÓN RUNTIME (post-C2d)
 *
 * Modos:
 *   node scripts_e2e_f01_retry.mjs calibrate   → sin mutaciones (intercepta y ABORTA los POST) — valida selectores
 *   node scripts_e2e_f01_retry.mjs live        → recorrido real (crea fixture sintético empresa 1)
 *
 * Expectativa de recepción:  F01_RECEPTION=gap   → se espera el bloqueo BR-08 (evidencia RED)
 *                            F01_RECEPTION=success (por defecto) → se espera 201 y flujo completo
 *
 * Credenciales: ~/ga_uat09_credentials.txt (600, fuera del repo; nunca se imprimen ni persisten).
 * Evidencia: audit/ga-f01/evidence/runtime-c2d/ (live) · /tmp/f01-calib (calibrate).
 */
import { chromium } from 'playwright'
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'

const MODE = process.argv[2] === 'live' ? 'live' : 'calibrate'
const EXPECT = process.env.F01_RECEPTION === 'gap' ? 'gap' : 'success'
const BASE = 'https://avicola.globaldv.net'
const API = BASE + '/api/v1'
const HOY = new Date().toISOString().slice(0, 10)
const d = (days) => new Date(Date.now() + days * 864e5).toISOString().slice(0, 10)
const PO = 'PO-C001-GPR-0001'

const OUT = MODE === 'live' ? path.resolve(process.env.F01_OUT || 'audit/ga-f01/evidence/runtime-c2d') : '/tmp/f01-calib'
fs.mkdirSync(OUT, { recursive: true })

// ── credenciales (nunca se imprimen) ──────────────────────────────────────
const raw = fs.readFileSync(path.join(os.homedir(), 'ga_uat09_credentials.txt'), 'utf8')
const OP_USER = /Operador de abuelas:\s*(\S+)/.exec(raw)?.[1]
const AP_USER = /Aprobador:\s*(\S+)/.exec(raw)?.[1]
const PASS = /Contraseña \(ambos\):\s*(\S+)/.exec(raw)?.[1]
if (!OP_USER || !AP_USER || !PASS) throw new Error('~/ga_uat09_credentials.txt ilegible')

// ── journal ───────────────────────────────────────────────────────────────
const J = { mode: MODE, expectativa_recepcion: EXPECT, fecha: HOY, base: BASE,
  pasos: [], posts: [], pageerror: [], consoleError: [], httpErrores: [], archivos: [], asserts: [], ids: {} }
const paso = (n, s, detalle) => { J.pasos.push({ step: n, status: s, detail: detalle ?? null })
  const m = (typeof s === 'number' && s < 400) ? 'OK ' : '!! '
  console.log(`${m}${n}: ${s}${detalle !== undefined ? ' :: ' + JSON.stringify(detalle).slice(0, 240) : ''}`) }
const assert = (n, ok, detalle) => { J.asserts.push({ name: n, ok, detail: detalle ?? null })
  console.log(`${ok ? 'PASS' : 'FAIL'} ${n}${detalle !== undefined ? ' :: ' + JSON.stringify(detalle).slice(0, 220) : ''}`)
  return ok }

// ── API (tokens vía /login; sin secretos en logs) ─────────────────────────
async function api(method, p, token, body) {
  const r = await fetch(API + p, { method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) },
    body: body ? JSON.stringify(body) : undefined })
  let data = null; try { data = await r.json() } catch { /* sin cuerpo */ }
  return { status: r.status, data }
}
async function loginApi(user) {
  const { status, data } = await api('POST', '/login', null, { username: user, password: PASS })
  if (status !== 200 || !data?.access_token) throw new Error(`login API ${user} ⇒ ${status}`)
  return data.access_token
}

// ── navegador ─────────────────────────────────────────────────────────────
function wire(page, tag) {
  page.on('pageerror', (e) => J.pageerror.push({ tag, msg: String(e.message || e).slice(0, 300) }))
  page.on('console', (m) => { if (m.type() === 'error') {
    const t = m.text(); if (!t.includes('Failed to load resource')) J.consoleError.push({ tag, msg: t.slice(0, 300) }) } })
  page.on('response', (r) => { const u = r.url()
    if (u.includes('/api/v1/') && r.status() >= 400) J.httpErrores.push({ tag, status: r.status(), method: r.request().method(), url: u.replace(BASE, '') }) })
}
async function shot(page, name) { const f = path.join(OUT, name); await page.screenshot({ path: f, fullPage: true }); J.archivos.push(name) }
async function pickSearch(page, placeholder, searchText, optionText) {
  await page.getByRole('button').filter({ hasText: placeholder }).first().click()
  await page.waitForTimeout(200)
  if (searchText) await page.keyboard.type(searchText, { delay: 15 })
  await page.waitForTimeout(250)
  await page.locator('div.z-50 button').filter({ hasText: optionText }).first().click()
}
async function pickFirst(page, placeholder) {
  await page.getByRole('button').filter({ hasText: placeholder }).first().click()
  const first = page.locator('div.z-50 button').first()
  const txt = await first.innerText().catch(() => '')
  await first.click()
  return txt.trim()
}
async function loginUi(page, user) {
  await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' })
  await page.locator('input[autocomplete="username"], #login-username').first().fill(user)
  await page.locator('#login-password, input[type="password"]').first().fill(PASS)
  await Promise.all([
    page.waitForURL((u) => !String(u).includes('/login'), { timeout: 30000 }),
    page.locator('button[type="submit"]').first().click(),
  ])
}
const waitPost = (page, frag) => page.waitForResponse(
  (r) => r.url().includes(frag) && r.request().method() === 'POST', { timeout: 45000 })
const visible = (loc) => loc.waitFor({ state: 'visible', timeout: 6000 }).then(() => true).catch(() => false)

// ── recorrido ─────────────────────────────────────────────────────────────
const browser = await chromium.launch({ headless: true })
const ctxOp = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const ctxAp = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const op = await ctxOp.newPage(); wire(op, 'op')
const ap = await ctxAp.newPage(); wire(ap, 'ap')

let abortPost = null
if (MODE === 'calibrate') {
  abortPost = async (route) => {
    const req = route.request()
    if (req.method() === 'POST') {
      let body = null; try { body = JSON.parse(req.postData() || 'null') } catch {}
      J.posts.push({ abortado: true, url: req.url().replace(BASE, ''), body })
      await route.abort()
    } else await route.continue()
  }
  await op.route('**/api/v1/operations**', abortPost)
  await ap.route('**/api/v1/operations**', abortPost)
}

try {
  // 0 · generación desplegada + tokens API
  const html = await (await fetch(BASE + '/')).text()
  const bundle = /index-[A-Za-z0-9_.-]+\.js/.exec(html)?.[0] || 'desconocido'
  paso('generacion-desplegada', 200, { bundle })
  J.ids.bundle = bundle
  const tokOp = await loginApi(OP_USER); paso('login-api-op', 200)
  const tokAp = await loginApi(AP_USER); paso('login-api-ap', 200)
  const { data: me } = await api('GET', '/me', tokOp)
  paso('me-op', 200, { company_id: me?.company_id, username: me?.username })
  assert('op-empresa-1', me?.company_id === 1, me?.company_id)

  // base de lotes L-GP antes
  const { data: lots0 } = await api('GET', '/lots?search=L-GP&limit=100', tokOp)
  const list0 = Array.isArray(lots0) ? lots0 : (lots0?.items || [])
  const baseGp = list0.map((l) => l.lot_code)
  paso('lotes-gp-antes', 200, baseGp)
  J.ids.base_gp = baseGp

  // pruebas de generación backend C2d (sin mutación): escritura estricta + lectura tolerante
  const pFeed = await api('POST', '/operations', tokOp, { event_type: 'grandparent_import', event_date: HOY, sap_document_ref: PO, feed_movements: [{}] })
  paso('probe-backend-feed-vacio', pFeed.status, Array.isArray(pFeed.data?.detail) ? pFeed.data.detail[0]?.loc : pFeed.data?.detail)
  assert('C2d-backend-escritura-estricta-422', pFeed.status === 422, pFeed.status)
  for (const id of [100, 112, 115, 116, 117]) {
    let r = await api('GET', `/operations/${id}`, tokOp)
    let via = 'op'
    if (r.status >= 400) { r = await api('GET', `/operations/${id}`, tokAp); via = 'ap' }
    J.ids[`historico_${id}`] = { status: r.status, via }
    paso(`historico-${id}`, r.status, { via })
  }
  assert('C2d-lectura-tolerante-historico-sin-500', [100, 112, 115, 116, 117].every((i) => J.ids[`historico_${i}`]?.status !== 500))

  // 1 · UI importación (UAT-01 / E2E-01)
  await loginUi(op, OP_USER); paso('login-ui-op', 200)
  await op.goto(BASE + '/operations/new?type=grandparent_import', { waitUntil: 'domcontentloaded' })
  await op.locator('#operation-form').waitFor({ timeout: 30000 })
  await op.waitForTimeout(1200)
  const notaVisible = await op.getByText('se creará automáticamente al aprobar la importación', { exact: false }).first().isVisible().catch(() => false)
  assert('NOTA-lote-automatico-visible', notaVisible)
  await shot(op, 'C01-formulario-importacion.png')

  await pickSearch(op, 'Seleccionar documento SAP...', 'PO-C001', PO)
  await pickSearch(op, 'Seleccionar proveedor...', 'Cobb', 'Cobb-Vantress')
  await pickSearch(op, 'Seleccionar transporte...', 'ABC-123', 'ABC-123')
  let granja = null
  try { granja = await pickFirst(op, 'Seleccionar granja...') } catch { }
  J.ids.granja_texto = granja
  const fill = async (name, value) => op.locator(`input[name="${name}"]`).fill(String(value))
  await fill('extra_data.import_plan.origin_country', 'Francia')
  await fill('extra_data.import_plan.purchased_total', 110)
  await fill('extra_data.import_plan.shipped_total', 105)
  await fill('extra_data.import_plan.received_total', 100)
  await fill('extra_data.import_plan.transit_mortality', 5)
  await fill('extra_data.import_plan.departure_date', d(-7))
  await fill('extra_data.import_plan.arrival_date', HOY)
  await fill('extra_data.import_plan.reception_condition', 'buena')
  await fill('extra_data.import_plan.quarantine_days', 21)
  await fill('extra_data.import_plan.quarantine_end_date', d(21))
  await fill('extra_data.import_plan.initial_health_inspection', 'sin hallazgos')
  await fill('bird_movements.0.quantity', 40)
  await fill('bird_movements.0.avg_weight', 3800)
  await fill('bird_movements.1.quantity', 60)
  await fill('bird_movements.1.avg_weight', 3600)
  await shot(op, 'C01b-formulario-llenado.png')

  let respImp = null; let reqImp = null; let bodyImp = null
  if (MODE === 'calibrate') {
    await op.locator('#operation-form button[type="submit"]').click().catch(() => { })
    await op.waitForTimeout(2500)
    await shot(op, 'calib-import-llenado.png')
    paso('calib-import-abortado', 200, { capturado: (J.posts.at(-1)?.body ? 'payload' : 'sin-payload') })
  } else {
    ;[respImp] = await Promise.all([waitPost(op, '/api/v1/operations'), op.locator('#operation-form button[type="submit"]').click()])
    try { reqImp = JSON.parse(respImp.request().postData() || 'null') } catch {}
    try { bodyImp = await respImp.json() } catch {}
    J.posts.push({ url: '/api/v1/operations', status: respImp.status(), body: reqImp, respuesta: { id: bodyImp?.id, status: bodyImp?.status } })
    paso('E2E-01-import-post', respImp.status(), { id: bodyImp?.id })
    await op.screenshot({ path: path.join(OUT, 'C02s-banner-exito.png'), fullPage: false }).catch(() => { })
    J.archivos.push('C02s-banner-exito.png')
    assert('E2E-01-import-201', respImp.status() === 201)
  }
  const eventId = bodyImp?.id; J.ids.import = eventId
  if (reqImp) {
    assert('E2E-03-almacenamiento-canonico', JSON.stringify(reqImp.egg_storage_records) === '[]', reqImp.egg_storage_records)
    assert('E2E-03b-alimento-canonico', JSON.stringify(reqImp.feed_movements) === '[]', reqImp.feed_movements)
    assert('E2E-03c-incubadora-canonico', JSON.stringify(reqImp.hatchery_params) === '[]', reqImp.hatchery_params)
    assert('E2E-02-oc-en-campo-tipado', reqImp.sap_document_ref === PO, reqImp.sap_document_ref)
    assert('E2E-02b-oc-ref-ui', reqImp.extra_data?.sap_order_ref === PO, reqImp.extra_data?.sap_order_ref)
    assert('UAT-01-sin-lote-en-payload', reqImp.lot_id == null, reqImp.lot_id)
    assert('E2E-01b-aves-40-60', (reqImp.bird_movements || []).length === 2)
  }

  if (MODE === 'calibrate') {
    // recepción (solo forma y payload, abortado) contra un lote existente
    const l62 = list0.find((l) => l.lot_code === 'L-GP-2026-09') || list0[0]
    await op.goto(`${BASE}/operations/new?type=bird_reception&lot_id=${l62.id}`, { waitUntil: 'domcontentloaded' })
    await op.locator('#operation-form').waitFor({ timeout: 30000 }); await op.waitForTimeout(2000)
    const lotePref = await op.getByRole('button').filter({ hasText: 'Seleccionar lote...' }).count()
    paso('calib-recepcion-lote-prefill', 200, { placeholderVisible: lotePref })
    try { await pickSearch(op, 'Seleccionar documento SAP...', 'PO-C001', PO) } catch { }
    try {
      await pickFirst(op, 'Seleccionar galpón...')
      await op.locator('select[name="bird_movements.0.sex"]').selectOption('female')
      await op.locator('input[name="bird_movements.0.quantity"]').fill('60')
      await op.locator('input[name="bird_movements.0.avg_weight"]').fill('3600')
    } catch (e) { paso('calib-recepcion-fila1', 'warn', String(e).slice(0, 160)) }
    await shot(op, 'calib-recepcion.png')
    await op.locator('#operation-form button[type="submit"]').click().catch(() => { })
    await op.waitForTimeout(2000)
    paso('calib-recepcion-post', 200, { posts: J.posts.length })
    paso('calibracion-completa', 200)
  } else {
    // 2 · detalle pre-aprobación (UAT-02)
    await op.goto(`${BASE}/operations/${eventId}`, { waitUntil: 'domcontentloaded' })
    await op.waitForTimeout(1500)
    const pend = await op.getByText('Se creará al aprobar').first().isVisible().catch(() => false)
    assert('UAT-02-lote-pendiente-visible', pend)
    await shot(op, 'C02-pre-aprobacion.png')
    const { data: det0 } = await api('GET', `/operations/${eventId}`, tokOp)
    assert('UAT-02b-detalle-sin-lote', det0?.lot_id == null, det0?.lot_id)

    // 3 · enviar a revisión + aprobación (UAT-03)
    let viaSubmit = 'ui'
    try {
      const [respSub] = await Promise.all([waitPost(op, `/operations/${eventId}/submit`), op.getByRole('button', { name: /Enviar a revisión/ }).first().click()])
      paso('submit-a-revision', respSub.status())
    } catch { viaSubmit = 'api'; const r = await api('POST', `/operations/${eventId}/submit`, tokOp); paso('submit-a-revision-api', r.status) }
    J.ids.via_submit = viaSubmit

    await loginUi(ap, AP_USER); paso('login-ui-ap', 200)
    let done = false
    for (const intento of [1, 2, 3, 4]) {
      await ap.goto(`${BASE}/review/${eventId}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(1500)
      const start = ap.getByRole('button', { name: /Iniciar Revisi/i }).first()
      const complete = ap.getByRole('button', { name: /Completar Revisi/i }).first()
      const approve = ap.getByRole('button', { name: /Aprobar/ }).first()
      if (await visible(start)) {
        const [r] = await Promise.all([waitPost(ap, `/review/start/${eventId}`), start.click()]); paso('review-start', r.status())
        continue
      }
      if (await visible(complete)) {
        const [r] = await Promise.all([waitPost(ap, '/review/complete'), complete.click()])
        let d2 = null; try { d2 = await r.json() } catch {}
        paso('review-complete', r.status(), { status: d2?.status })
        if (d2?.status === 'approved') { done = true; break }
        continue
      }
      if (await visible(approve)) {
        const [r] = await Promise.all([waitPost(ap, '/approvals/approve'), approve.click()])
        paso('approve', r.status()); done = true; break
      }
      paso('review-paso', 'espera', `intento ${intento}`); await ap.waitForTimeout(1200)
    }
    if (!done) { const r = await api('POST', '/approvals/approve', tokAp, { event_id: eventId }); paso('approve-api', r.status); done = r.status === 200 }
    const { data: det1 } = await api('GET', `/operations/${eventId}`, tokOp)
    assert('UAT-03-aprobado', det1?.status === 'approved', det1?.status)
    const lotId = det1?.lot_id; J.ids.lote = lotId
    assert('UAT-03b-lote-enlazado', Number.isInteger(lotId) && lotId > 0, lotId)

    // 4 · detalle con enlace + datos del lote (UAT-04)
    await op.goto(`${BASE}/operations/${eventId}`, { waitUntil: 'domcontentloaded' }); await op.waitForTimeout(1500)
    const enlace = await op.locator(`a[href="/lots/${lotId}"]`).first().isVisible().catch(() => false)
    assert('UAT-03c-enlace-lote-visible', enlace)
    await shot(op, 'C03-detalle-aprobado-lote.png')

    const { data: lot } = await api('GET', `/lots/${lotId}`, tokOp)
    J.ids.lote_codigo = lot?.lot_code
    assert('UAT-04-codigo-canonico', /^L-GP-2026-\d{2}$/.test(lot?.lot_code || ''), lot?.lot_code)
    assert('UAT-04b-dominio-gp', String(lot?.bird_type).toLowerCase() === 'grandparent', lot?.bird_type)
    assert('UAT-04c-sexo-plan', String(lot?.sex).toLowerCase() === 'mixed', lot?.sex)
    assert('UAT-04d-fecha-llegada', String(lot?.start_date).slice(0, 10) === HOY, lot?.start_date)
    assert('UAT-04e-misma-empresa', lot?.company_id === 1, lot?.company_id)
    const { data: lots1 } = await api('GET', '/lots?search=L-GP&limit=100', tokOp)
    const list1 = Array.isArray(lots1) ? lots1 : (lots1?.items || [])
    assert('AC06-exactamente-un-lote-nuevo', list1.length === list0.length + 1, { antes: list0.length, despues: list1.length })
    J.ids.house_id_lote = lot?.house_id; J.ids.farm_id_lote = lot?.farm_id
    paso('lote-creado', 200, { codigo: lot?.lot_code, house_id: lot?.house_id, farm_id: lot?.farm_id })

    await op.goto(`${BASE}/lots/${lotId}`, { waitUntil: 'domcontentloaded' }); await op.waitForTimeout(2000)
    await shot(op, 'C04-lote-datos.png')

    // 5 · UAT-05 sin aves + bracket BR-01 antes de recepción
    const { data: evs } = await api('GET', `/operations?lot_id=${lotId}&limit=50`, tokOp)
    const evList = Array.isArray(evs) ? evs : (evs?.items || [])
    const recepciones = evList.filter((e) => e.event_type === 'bird_reception')
    assert('UAT-05-sin-recepciones-antes', recepciones.length === 0, evList.map((e) => e.event_type))
    await shot(op, 'C05-lote-sin-aves.png')
    const probe1 = await api('POST', '/operations', tokOp, { event_type: 'mortality_recording', event_date: HOY, lot_id: lotId, bird_movements: [{ sex: 'female', quantity: 1 }] })
    paso('bracket-pre-recepcion-mortalidad-1', probe1.status, probe1.data?.detail)
    assert('AC16-aprobacion-no-puebla', probe1.status === 400, probe1.data?.detail)

    // 6 · recepción por UI (UAT-06)
    await op.goto(`${BASE}/operations/new?type=bird_reception&lot_id=${lotId}`, { waitUntil: 'domcontentloaded' })
    await op.locator('#operation-form').waitFor({ timeout: 30000 }); await op.waitForTimeout(2000)
    const lotePlaceholder = await op.getByRole('button').filter({ hasText: 'Seleccionar lote...' }).count()
    paso('recepcion-lote-prefill', 200, { placeholderVisible: lotePlaceholder })
    if (lotePlaceholder > 0) { try { await pickSearch(op, 'Seleccionar lote...', J.ids.lote_codigo, J.ids.lote_codigo) } catch { } }
    try { await pickSearch(op, 'Seleccionar documento SAP...', 'PO-C001', PO) } catch { }
    try {
      await pickFirst(op, 'Seleccionar galpón...')
      await op.locator('select[name="bird_movements.0.sex"]').selectOption('male')
      await op.locator('input[name="bird_movements.0.quantity"]').fill('40')
      await op.locator('input[name="bird_movements.0.avg_weight"]').fill('3800')
      await pickFirst(op, 'Seleccionar galpón...')
      await op.locator('select[name="bird_movements.1.sex"]').selectOption('female')
      await op.locator('input[name="bird_movements.1.quantity"]').fill('60')
      await op.locator('input[name="bird_movements.1.avg_weight"]').fill('3600')
    } catch (e) { paso('recepcion-llenado', 'warn', String(e).slice(0, 200)) }
    await shot(op, 'C06a-recepcion-formulario.png')

    const [respRec] = await Promise.all([waitPost(op, '/api/v1/operations'), op.locator('#operation-form button[type="submit"]').click()])
    let reqRec = null; try { reqRec = JSON.parse(respRec.request().postData() || 'null') } catch {}
    let bodyRec = null; try { bodyRec = await respRec.json() } catch {}
    J.posts.push({ url: '/api/v1/operations', status: respRec.status(), body: reqRec, respuesta: { id: bodyRec?.id } })
    paso('UAT-06-recepcion-post', respRec.status(), bodyRec?.detail || bodyRec?.id)

    if (respRec.status() === 201) {
      const recId = bodyRec?.id; J.ids.recepcion = recId
      if (reqRec) {
        assert('E2E-recepcion-almacenamiento-canonico', JSON.stringify(reqRec.egg_storage_records) === '[]', reqRec.egg_storage_records)
        assert('E2E-recepcion-alimento-incubadora-canonico', JSON.stringify(reqRec.feed_movements) === '[]' && JSON.stringify(reqRec.hatchery_params) === '[]')
        assert('E2E-recepcion-lote-correcto', reqRec.lot_id === lotId)
      }
      let viaR = 'ui'
      try { await op.goto(`${BASE}/operations/${recId}`, { waitUntil: 'domcontentloaded' }); await op.waitForTimeout(1200)
        const [rs] = await Promise.all([waitPost(op, `/operations/${recId}/submit`), op.getByRole('button', { name: /Enviar a revisión/ }).first().click()]); paso('recep-submit', rs.status())
      } catch { viaR = 'api'; const r = await api('POST', `/operations/${recId}/submit`, tokOp); paso('recep-submit-api', r.status) }
      J.ids.via_recep_submit = viaR
      let doneR = false
      for (const intento of [1, 2, 3, 4]) {
        await ap.goto(`${BASE}/review/${recId}`, { waitUntil: 'domcontentloaded' }); await ap.waitForTimeout(1200)
        const start = ap.getByRole('button', { name: /Iniciar Revisi/i }).first()
        const complete = ap.getByRole('button', { name: /Completar Revisi/i }).first()
        const approve = ap.getByRole('button', { name: /Aprobar/ }).first()
        if (await visible(start)) { const [r] = await Promise.all([waitPost(ap, `/review/start/${recId}`), start.click()]); paso('recep-review-start', r.status()); continue }
        if (await visible(complete)) { const [r] = await Promise.all([waitPost(ap, '/review/complete'), complete.click()]); let dd = null; try { dd = await r.json() } catch {}; paso('recep-review-complete', r.status(), { status: dd?.status }); if (dd?.status === 'approved') { doneR = true; break } continue }
        if (await visible(approve)) { const [r] = await Promise.all([waitPost(ap, '/approvals/approve'), approve.click()]); paso('recep-approve', r.status()); doneR = true; break }
        await ap.waitForTimeout(1000)
      }
      if (!doneR) { const r = await api('POST', '/approvals/approve', tokAp, { event_id: recId }); paso('recep-approve-api', r.status); doneR = r.status === 200 }
      const { data: detR } = await api('GET', `/operations/${recId}`, tokOp)
      assert('UAT-06-recepcion-aprobada', detR?.status === 'approved', detR?.status)

      const { data: evs2 } = await api('GET', `/operations?lot_id=${lotId}&limit=50`, tokOp)
      const evList2 = Array.isArray(evs2) ? evs2 : (evs2?.items || [])
      const recs2 = evList2.filter((e) => e.event_type === 'bird_reception')
      assert('UAT-06b-recepcion-una-vez', recs2.length === 1, recs2.length)
      await op.goto(`${BASE}/lots/${lotId}`, { waitUntil: 'domcontentloaded' }); await op.waitForTimeout(2000)
      await shot(op, 'C06-lote-con-recepcion.png')

      const p100 = await api('POST', '/operations', tokOp, { event_type: 'mortality_recording', event_date: HOY, lot_id: lotId, bird_movements: [{ sex: 'female', quantity: 100 }] })
      paso('bracket-post-100', p100.status, p100.data?.detail || p100.data?.id)
      if (p100.status === 201 && p100.data?.id) { const c = await api('POST', `/operations/${p100.data.id}/cancel`, tokOp); paso('bracket-100-cancelado', c.status) }
      const p101 = await api('POST', '/operations', tokOp, { event_type: 'mortality_recording', event_date: HOY, lot_id: lotId, bird_movements: [{ sex: 'female', quantity: 101 }] })
      paso('bracket-post-101', p101.status, p101.data?.detail)
      assert('AC21-poblacion-exacta-100', p100.status === 201 && p101.status === 400, { p100: p100.status, p101: p101.status })
    } else if (EXPECT === 'gap') {
      paso('GAP-UAT-06-bloqueo-recepcion', respRec.status(), bodyRec?.detail)
      assert('RED-BR-08-recepcion-bloqueada', respRec.status() === 400 && /galpón asignado/.test(JSON.stringify(bodyRec || {})), bodyRec?.detail)
      const formVivo = await op.locator('#operation-form').isVisible().catch(() => false)
      assert('F03-formulario-permanece', formVivo)
      await shot(op, 'F03-recepcion-bloqueada.png')
    } else {
      assert('UAT-06-recepcion-201', false, { status: respRec.status(), detalle: bodyRec?.detail })
    }

    // 7 · UX de error con 4xx real gobernado (sin OC ⇒ BR-22)
    await op.goto(BASE + '/operations/new?type=grandparent_import', { waitUntil: 'domcontentloaded' })
    await op.locator('#operation-form').waitFor({ timeout: 30000 }); await op.waitForTimeout(800)
    const errAntes = J.pageerror.length + J.consoleError.length
    await op.locator('input[name="extra_data.import_plan.origin_country"]').fill('Francia')
    await op.locator('input[name="bird_movements.0.quantity"]').fill('1')
    let statusUX = null; let detalleUX = null
    try {
      const [respUX] = await Promise.all([waitPost(op, '/api/v1/operations'), op.locator('#operation-form button[type="submit"]').click()])
      statusUX = respUX.status(); try { detalleUX = await respUX.json() } catch {}
    } catch (e) { paso('ux-error', 'sin-peticion', String(e).slice(0, 160)) }
    paso('E2E-04-4xx-gobernado', statusUX, detalleUX?.detail || detalleUX?.rule)
    const formVivo2 = await op.locator('#operation-form').isVisible().catch(() => false)
    const errDespues = J.pageerror.length + J.consoleError.length
    assert('E2E-04b-formulario-permanece', formVivo2)
    assert('E2E-04c-sin-error-fatal-nuevo', errDespues === errAntes, { antes: errAntes, despues: errDespues })
    await shot(op, 'F02-error-ux.png')

    // 8 · vía manual visible (UAT-07)
    await op.goto(BASE + '/lots', { waitUntil: 'domcontentloaded' }); await op.waitForTimeout(1500)
    const nuevoLote = await op.getByText('Nuevo Lote', { exact: false }).first().isVisible().catch(() => false)
    assert('UAT-07-via-manual-visible', nuevoLote)
    await shot(op, 'C07-via-manual.png')

    // 9 · idempotencia: reaprobar no duplica lote
    const rp = await api('POST', '/approvals/approve', tokAp, { event_id: eventId })
    paso('reaprobacion', rp.status, rp.data?.detail)
    const { data: lots2 } = await api('GET', '/lots?search=L-GP&limit=100', tokOp)
    const list2 = Array.isArray(lots2) ? lots2 : (lots2?.items || [])
    assert('AC23-sin-segundo-lote', list2.length === list0.length + 1, { total: list2.length })

    // 10 · móvil
    const m = await ctxOp.newPage(); wire(m, 'movil'); await m.setViewportSize({ width: 390, height: 844 })
    await m.goto(BASE + '/operations/new?type=grandparent_import', { waitUntil: 'domcontentloaded' })
    await m.waitForTimeout(1500)
    await m.screenshot({ path: path.join(OUT, 'C08m-movil.png'), fullPage: true }).catch(() => { })
    J.archivos.push('C08m-movil.png')
    paso('movil-390x844', 200)
  }
} catch (e) {
  paso('ERROR-DE-RECORRIDO', 'excepcion', String(e).slice(0, 400))
} finally {
  J.fatal_react = J.pageerror.filter((p) => /React|#31/.test(p.msg)).length
  J.http5xx = J.httpErrores.filter((h) => h.status >= 500)
  fs.writeFileSync(path.join(OUT, MODE === 'live' ? 'retry-walkthrough.json' : 'calib-walkthrough.json'), JSON.stringify(J, null, 2))
  const fails = J.asserts.filter((a) => !a.ok)
  console.log(`\n== resumen ${MODE} == asserts: ${J.asserts.length - fails.length}/${J.asserts.length} · pageerror: ${J.pageerror.length} (React: ${J.fatal_react}) · 5xx: ${J.http5xx.length}`)
  for (const f of fails) console.log('FALLO:', f.name, JSON.stringify(f.detail))
  await browser.close()
  process.exit(fails.length ? 1 : 0)
}
