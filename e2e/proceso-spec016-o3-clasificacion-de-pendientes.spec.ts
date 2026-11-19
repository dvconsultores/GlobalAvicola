import { test, expect, type Page } from '@playwright/test'
import * as fs from 'node:fs'
import {
  API,
  cabeceraAdmin,
  cabeceraAdminEnOtraEmpresa,
  empresaActiva,
  hoy,
  sufijo,
} from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

test.describe.configure({ mode: 'serial' })

const DIR_EV = 'audit/ga-o3-classification-build-provenance/evidence/e2e_spec016'
const DIR_PNG = `${DIR_EV}/screenshots`
const ev: Record<string, any> = {}
const habilitadas: string[] = []
let admin: any
let adminOtra: any

const lista = (raw: any): any[] => (Array.isArray(raw) ? raw : (raw?.items ?? raw?.data ?? []))
const s = () => sufijo()

const pedir = async (request: any, url: string, headers: any) => {
  const r = await request.get(url, { headers })
  expect(r.ok()).toBeTruthy()
  return lista(await r.json())
}

const pendientes = (request: any, headers: any, extra = '') =>
  pedir(request, `${API}/operations/pending-classification?limit=100${extra}`, headers)

const historial = (request: any, headers: any, extra = '') =>
  pedir(request, `${API}/operations?limit=100${extra}`, headers)

/** Crea granja + galpón + los lotes indicados (['breeder'] o ['breeder','broiler']) y devuelve ids. */
const crearGranjaConLotes = async (
  request: any,
  prefijo: string,
  companyId: number,
  birdTypes: string[],
) => {
  const suf = s()
  const nombre = `${prefijo}-g-${suf}`
  const fr = await request.post(`${API}/masters/farms`, {
    headers: admin,
    data: {
      company_id: companyId,
      name: nombre,
      code: `${prefijo}-G-${suf}`,
      location: 'QA',
      farm_type: 'breeding',
    },
  })
  expect(fr.ok()).toBeTruthy()
  const farm: any = await fr.json()
  const hs = await request.post(`${API}/masters/houses`, {
    headers: admin,
    data: { farm_id: farm.id, name: `${prefijo}-h-${suf}`, capacity: 50000 },
  })
  expect(hs.ok()).toBeTruthy()
  const house: any = await hs.json()
  const houseNombre = house.name as string
  const lotes: any[] = []
  for (const birdType of birdTypes) {
    const lr = await request.post(`${API}/lots`, {
      headers: admin,
      data: {
        company_id: companyId,
        farm_id: farm.id,
        house_id: house.id,
        lot_code: `${prefijo}-${birdType.slice(0, 3).toUpperCase()}-${suf}`,
        bird_type: birdType,
        sex: 'mixed',
      },
    })
    expect(lr.ok(), `lote ${birdType}: ${lr.status()} ${await lr.text()}`).toBeTruthy()
    lotes.push(await lr.json())
  }
  return {
    farmId: farm.id as number,
    houseId: house.id as number,
    nombre,
    houseNombre,
    suf,
    lotes,
  }
}

/** Inspección de granja (evento O-3) por API. */
const crearInspeccion = async (
  request: any,
  farmId: number,
  houseId: number,
  headers: any = admin,
) => {
  const r = await request.post(`${API}/operations`, {
    headers,
    data: {
      event_type: 'farm_inspection',
      event_date: hoy(),
      farm_id: farmId,
      house_id: houseId,
      inspection_details: [{ house_id: houseId, parameter: 'temperature', value: '24' }],
    },
  })
  expect(r.status()).toBe(201)
  return await r.json()
}

/** Credenciales de usuario sembrado, por rol, tomadas del entorno del arnés. */
const credencialesDe = (rol: 'operator' | 'approver') => {
  const mapa = {
    operator: { usuario: 'test_operator', variable: 'GA_TEST_OPERATOR_PASSWORD' },
    approver: { usuario: 'test_approver', variable: 'GA_TEST_APPROVER_PASSWORD' },
  }[rol]
  const clave = process.env[mapa.variable]
  if (!clave) throw new Error(`${mapa.variable} no definida: use bash scripts_e2e.sh`)
  return { usuario: mapa.usuario, clave }
}

/** Cabecera de API del rol sembrado, sin pasar por la interfaz. */
const cabeceraDe = async (request: any, rol: 'operator' | 'approver' = 'operator') => {
  const { usuario, clave } = credencialesDe(rol)
  const r = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
  expect(r.status(), `login de ${usuario}`).toBe(200)
  return { Authorization: `Bearer ${(await r.json()).access_token}` }
}

const postClasificar = (request: any, eventId: number, data: any, headers: any = admin) =>
  request.post(`${API}/operations/${eventId}/classify`, { headers, data })

const getCandidatos = (request: any, eventId: number, headers: any = admin) =>
  request.get(`${API}/operations/${eventId}/classification-candidates`, { headers })

const sigueEnBandeja = async (request: any, eventId: number, headers: any = admin) =>
  (await pendientes(request, headers)).some((x: any) => x.id === eventId)

/** Rastro de `P-09` del evento, en orden cronológico. */
const timelineDe = async (request: any, eventId: number, headers: any = admin) => {
  const r = await request.get(`${API}/audit/timeline/operational_event/${eventId}`, {
    headers,
  })
  expect(r.status(), `timeline de ${eventId}: ${await r.text()}`).toBe(200)
  return ((await r.json()).timeline ?? []) as any[]
}

/** Las entradas que registran la **clasificación** —`pending` → código de unidad—. */
const clasificacionesDe = (linea: any[]) =>
  linea.filter((l: any) => l.action === 'updated' && l.previous_state === 'pending')

const prepararEvidencia = () => {
  fs.mkdirSync(DIR_PNG, { recursive: true })
}

/**
 * Abre el Historial con el filtro de granja ya aplicado.
 *
 * No se usa el selector `operation-filter-farm`: solo trae 100 granjas
 * (`/masters/farms?limit=100`, tope del backend) y la BD de E2E acumula granjas
 * dentro de una corrida, así que la opción puede no existir. `OperationListPage`
 * restaura el filtro desde `sessionStorage` y lo envía como `farm_id` al servidor.
 */
async function abrirHistorialDeGranja(page: Page, farmId: number) {
  await page.goto('/operations')
  await page.evaluate(
    (id) => sessionStorage.setItem('ga.filters.operations.farmId', id),
    String(farmId),
  )
  await page.goto('/operations')
}

test.beforeAll(async ({ request }) => {
  admin = await cabeceraAdmin(request)
  const otra = await cabeceraAdminEnOtraEmpresa(request)
  adminOtra = otra.cabecera
  const unidades = await pedir(request, `${API}/business-units`, admin)
  ev.business_units_inicial = unidades.map((bu: any) => ({ code: bu.code, is_enabled: bu.is_enabled }))
  for (const code of ['breeder', 'broiler']) {
    const u = unidades.find((x: any) => x.code === code)
    if (u && u.is_enabled === false) {
      const r = await request.patch(`${API}/business-units/${code}/enable`, { headers: admin })
      expect(r.ok()).toBeTruthy()
      habilitadas.push(code)
    }
  }
})

test.afterAll(async ({ request }) => {
  for (const code of habilitadas) {
    await request.patch(`${API}/business-units/${code}/disable`, { headers: admin })
  }
  fs.mkdirSync(DIR_PNG, { recursive: true })
  fs.writeFileSync(`${DIR_EV}/e2e_spec016_clasificacion_pendientes.json`, JSON.stringify(ev, null, 2))
})

test('O3-E2E-01 derivación automática: granja con lotes de UNA sola cadena', async ({
  page,
  request,
}) => {
  // `D1` (`spec 015 §5`): la granja cuyos lotes vivos pertenecen todos a una cadena no
  // necesita que nadie decida nada. El registro nace atribuido y nunca pisa la bandeja.
  const companyId = empresaActiva(admin)
  const g = await crearGranjaConLotes(request, 'P20A01', companyId, ['breeder'])
  const op = await crearInspeccion(request, g.farmId, g.houseId)

  const claves = Object.keys(op).sort()
  const unidadEnRespuesta =
    op.business_unit_code ?? op.business_unit ?? op.chain ?? op.cadena ?? null
  const enBandeja = await sigueEnBandeja(request, op.id)
  const historialApi = await historial(request, admin, `&farm_id=${g.farmId}`)
  const enHistorial = historialApi.some((x: any) => x.id === op.id)
  ev['01'] = {
    eventId: op.id,
    granja: g.nombre,
    granjaId: g.farmId,
    lote: g.lotes.map((l: any) => l.lot_code),
    enBandeja,
    enHistorial,
    unidad_en_respuesta: unidadEnRespuesta,
    claves_respuesta: claves,
  }

  expect(enBandeja, 'una inspección de granja de una sola cadena no es un pendiente').toBe(
    false,
  )
  expect(enHistorial, 'debe verse en el historial sin pasar por la bandeja').toBe(true)
  if (unidadEnRespuesta !== null) {
    expect(String(unidadEnRespuesta)).toBe('breeder')
  }

  // Interfaz: el Historial la muestra y la bandeja no la reclama.
  prepararEvidencia()
  await entrar(page, 'admin')
  await abrirHistorialDeGranja(page, g.farmId)
  await expect(page.getByTestId(`operation-row-${op.id}`)).toBeVisible()
  ev['01'].historial_ui = true
  await page.screenshot({ path: `${DIR_PNG}/o3_01_historial.png`, fullPage: true })

  await page.goto('/operations/pending-classification')
  await expect(page.getByTestId('pending-classification-page')).toBeVisible()
  await expect(page.locator('body')).not.toContainText(g.nombre)
  ev['01'].bandeja_ui_sin_derivada = true
})

test('O3-E2E-02 ambigua: clasificación completa por la interfaz', async ({
  page,
  request,
}) => {
  // Dos cadenas en la misma granja: el dato no es inequívoco y el registro nace pendiente.
  const companyId = empresaActiva(admin)
  const g = await crearGranjaConLotes(request, 'P20A02', companyId, ['breeder', 'broiler'])
  const op = await crearInspeccion(request, g.farmId, g.houseId)
  const motivo = `Clasificación E2E O3-02 ${sufijo()}`

  expect(await sigueEnBandeja(request, op.id), 'nace pendiente').toBe(true)
  const historialAntes = await historial(request, admin, `&farm_id=${g.farmId}`)
  expect(
    historialAntes.some((x: any) => x.id === op.id),
    'lo pendiente queda fuera del historial',
  ).toBe(false)

  const cand = await getCandidatos(request, op.id)
  expect(cand.status()).toBe(200)
  const candidatos: any[] = await cand.json()
  const codigos = candidatos.map((c: any) => c.code)
  expect(codigos).toContain('breeder')
  expect(codigos).toContain('broiler')
  expect(candidatos.every((c: any) => Object.keys(c).sort().join(',') === 'code,name_key')).toBe(
    true,
  )

  prepararEvidencia()
  await entrar(page, 'admin')
  await page.goto('/operations/pending-classification')
  await expect(page.getByTestId('pending-classification-page')).toBeVisible()
  const fila = page.getByTestId('pending-row').filter({ hasText: g.nombre })
  await expect(fila).toHaveCount(1)
  await expect(fila).toContainText(g.houseNombre)
  const boton = fila.getByTestId('classify-btn')
  await expect(boton).toBeVisible()
  await expect(boton).toHaveText(/Clasificar/i)
  await boton.click()

  const dialogo = page.getByTestId('classify-dialog')
  await expect(dialogo).toBeVisible()
  await expect(dialogo).toContainText(g.nombre)
  await expect(dialogo).toContainText(g.houseNombre)

  const select = page.getByTestId('classify-unit')
  await expect(select.locator('option', { hasText: 'breeder' })).toHaveCount(1, {
    timeout: 20_000,
  })
  for (const code of codigos) {
    const opcion = select.locator(`option[value="${code}"]`)
    await expect(opcion).toHaveCount(1)
    await expect(opcion).toContainText(`${code} —`)
  }
  await select.selectOption('breeder')

  const motivoInput = page.getByTestId('classify-reason')
  await motivoInput.fill(motivo)
  const enviar = page.getByTestId('classify-submit')
  await expect(enviar).toBeEnabled()
  await page.screenshot({ path: `${DIR_PNG}/o3_02_dialogo.png`, fullPage: true })
  await enviar.click()

  await expect(dialogo).toBeHidden()
  await expect(page.getByTestId('pending-row').filter({ hasText: g.nombre })).toHaveCount(0)
  await page.screenshot({ path: `${DIR_PNG}/o3_02_despues.png`, fullPage: true })

  expect(await sigueEnBandeja(request, op.id), 'deja de estar pendiente').toBe(false)

  const detalle = await request.get(`${API}/operations/${op.id}`, { headers: admin })
  expect(detalle.status()).toBe(200)
  const det: any = await detalle.json()
  const unidadDetalle =
    det.business_unit_code ?? det.business_unit ?? det.chain ?? det.cadena ?? null
  if (unidadDetalle !== null) expect(String(unidadDetalle)).toBe('breeder')

  const linea = await timelineDe(request, op.id)
  const clasificaciones = clasificacionesDe(linea)
  expect(clasificaciones.length).toBe(1)
  expect(clasificaciones[0].change_reason).toBe(motivo)
  expect(clasificaciones[0].new_state).toBe('breeder')

  const historialApi = await historial(request, admin, `&farm_id=${g.farmId}`)
  expect(historialApi.some((x: any) => x.id === op.id), 'aparece en el historial').toBe(true)

  await abrirHistorialDeGranja(page, g.farmId)
  await expect(page.getByTestId(`operation-row-${op.id}`)).toBeVisible()
  await page.screenshot({ path: `${DIR_PNG}/o3_02_historial.png`, fullPage: true })

  // Recarga: la decisión está persistida, no en memoria de la pantalla.
  await page.reload()
  await expect(page.getByTestId(`operation-row-${op.id}`)).toBeVisible()
  await page.goto('/operations/pending-classification')
  await expect(page.getByTestId('pending-classification-page')).toBeVisible()
  await expect(page.getByTestId('pending-row').filter({ hasText: g.nombre })).toHaveCount(0)

  // Sesión nueva: se sale de verdad y se vuelve a entrar.
  await page.evaluate(() => window.localStorage.clear()).catch(() => undefined)
  await page.context().clearCookies()
  await entrar(page, 'admin')
  await page.goto('/operations/pending-classification')
  await expect(page.getByTestId('pending-classification-page')).toBeVisible()
  await expect(page.getByTestId('pending-row').filter({ hasText: g.nombre })).toHaveCount(0)
  await abrirHistorialDeGranja(page, g.farmId)
  await expect(page.getByTestId(`operation-row-${op.id}`)).toBeVisible()

  ev['02'] = {
    eventId: op.id,
    granja: g.nombre,
    granjaId: g.farmId,
    galpon: g.houseNombre,
    motivo,
    candidatos: codigos,
    unidad_detalle: unidadDetalle,
    claves_detalle: Object.keys(det).sort(),
    auditoria: clasificaciones.length,
    persiste_tras_recarga_y_login: true,
  }
})

test('O3-E2E-03 granja sin lotes: bandeja, clasificación y auditoría', async ({
  page,
  request,
}) => {
  // Sin ningún lote no hay cadena que derivar: es el caso extremo de «no se adivina».
  const companyId = empresaActiva(admin)
  const g = await crearGranjaConLotes(request, 'P20A03', companyId, [])
  expect(g.lotes.length).toBe(0)
  const op = await crearInspeccion(request, g.farmId, g.houseId)
  const motivo = `Granja sin lotes O3-03 ${sufijo()}`

  expect(await sigueEnBandeja(request, op.id)).toBe(true)

  prepararEvidencia()
  await entrar(page, 'admin')
  await page.goto('/operations/pending-classification')
  const fila = page.getByTestId('pending-row').filter({ hasText: g.nombre })
  await expect(fila).toHaveCount(1)
  await fila.getByTestId('classify-btn').click()
  const dialogo = page.getByTestId('classify-dialog')
  await expect(dialogo).toBeVisible()
  const select = page.getByTestId('classify-unit')
  await expect(select.locator('option[value="breeder"]')).toHaveCount(1, { timeout: 20_000 })
  await select.selectOption('breeder')
  await page.getByTestId('classify-reason').fill(motivo)
  await page.getByTestId('classify-submit').click()
  await expect(dialogo).toBeHidden()
  await expect(page.getByTestId('pending-row').filter({ hasText: g.nombre })).toHaveCount(0)
  await page.screenshot({ path: `${DIR_PNG}/o3_03_clasificada.png`, fullPage: true })

  expect(await sigueEnBandeja(request, op.id)).toBe(false)
  const clasificaciones = clasificacionesDe(await timelineDe(request, op.id))
  expect(clasificaciones.length).toBe(1)
  expect(clasificaciones[0].change_reason).toBe(motivo)
  expect(clasificaciones[0].previous_state).toBe('pending')
  expect(clasificaciones[0].new_state).toBe('breeder')

  ev['03'] = { eventId: op.id, granja: g.nombre, motivo, auditoria: clasificaciones.length }
})

test('O3-E2E-04 sin permiso: el operador ve el pendiente y no puede clasificarlo', async ({
  page,
  request,
}) => {
  const companyId = empresaActiva(admin)
  const operador = await cabeceraDe(request, 'operator')
  const g = await crearGranjaConLotes(request, 'P20A04', companyId, ['breeder', 'broiler'])
  // El operador registra el evento: es el autor, así que **ve** su pendiente.
  const op = await crearInspeccion(request, g.farmId, g.houseId, operador)

  const pendientesOperador = await pendientes(request, operador)
  expect(
    pendientesOperador.some((x: any) => x.id === op.id),
    'el autor ve su propio pendiente',
  ).toBe(true)

  prepararEvidencia()
  await entrar(page, 'operator')
  await page.goto('/operations/pending-classification')
  await expect(page.getByTestId('pending-classification-page')).toBeVisible()
  const fila = page.getByTestId('pending-row').filter({ hasText: g.nombre })
  await expect(fila).toHaveCount(1)
  await expect(fila.getByTestId('classify-btn')).toHaveCount(0)
  await expect(page.getByTestId('classify-btn')).toHaveCount(0)
  await page.screenshot({ path: `${DIR_PNG}/o3_04_operador_sin_boton.png`, fullPage: true })

  const intento = await postClasificar(request, op.id, {
    business_unit_code: 'breeder',
    reason: `Intento sin permiso ${sufijo()}`,
  }, operador)
  expect(intento.status()).toBe(403)
  const candidatos = await getCandidatos(request, op.id, operador)
  expect(candidatos.status()).toBe(403)

  expect(await sigueEnBandeja(request, op.id), 'el registro sigue pendiente').toBe(true)
  ev['04'] = {
    eventId: op.id,
    granja: g.nombre,
    operator_ve: true,
    classify_btn: 0,
    post_status: intento.status(),
    candidates_status: candidatos.status(),
  }
})

test('O3-E2E-05 unidad no habilitada: ni el diálogo ni la API la aceptan', async ({
  page,
  request,
}) => {
  const companyId = empresaActiva(admin)
  const g = await crearGranjaConLotes(request, 'P20A05', companyId, ['breeder', 'broiler'])
  const op = await crearInspeccion(request, g.farmId, g.houseId)
  expect(await sigueEnBandeja(request, op.id)).toBe(true)

  const antes = await getCandidatos(request, op.id)
  expect(antes.status()).toBe(200)
  const codigosAntes = ((await antes.json()) as any[]).map((c: any) => c.code)
  expect(codigosAntes).toContain('broiler')

  let rehabilitar = false
  try {
    const apagar = await request.patch(`${API}/business-units/broiler/disable`, {
      headers: admin,
    })
    expect(apagar.ok()).toBeTruthy()
    rehabilitar = true

    const despues = await getCandidatos(request, op.id)
    expect(despues.status()).toBe(200)
    const codigosDespues = ((await despues.json()) as any[]).map((c: any) => c.code)
    expect(codigosDespues).not.toContain('broiler')
    expect(codigosDespues).toContain('breeder')

    const unidades = await pedir(request, `${API}/business-units`, admin)
    const habilitadas = unidades.filter((u: any) => u.is_enabled).map((u: any) => u.code)

    prepararEvidencia()
    await entrar(page, 'admin')
    await page.goto('/operations/pending-classification')
    const fila = page.getByTestId('pending-row').filter({ hasText: g.nombre })
    await expect(fila).toHaveCount(1)
    await fila.getByTestId('classify-btn').click()
    const select = page.getByTestId('classify-unit')
    await expect(select.locator('option[value="breeder"]')).toHaveCount(1, { timeout: 20_000 })
    await expect(select.locator('option[value="broiler"]')).toHaveCount(0)
    const valores = await select
      .locator('option')
      .evaluateAll((opciones) => opciones.map((o: any) => o.value).filter(Boolean))
    expect(valores.sort()).toEqual([...codigosDespues].sort())
    await page.screenshot({ path: `${DIR_PNG}/o3_05_dialogo_sin_unidad_apagada.png`, fullPage: true })

    const meAntes: any = await (await request.get(`${API}/me`, { headers: admin })).json()
    const porCodigoAjeno = await postClasificar(request, op.id, {
      business_unit_code: 'broiler',
      reason: `Unidad apagada ${sufijo()}`,
    })
    expect(porCodigoAjeno.status(), await porCodigoAjeno.text()).toBe(400)
    expect((await porCodigoAjeno.json()).detail).toBe(
      'la unidad no existe o no esta habilitada para la empresa',
    )
    const inexistente = await postClasificar(request, op.id, {
      business_unit_code: 'zzz',
      reason: `Unidad inexistente ${sufijo()}`,
    })
    expect(inexistente.status(), await inexistente.text()).toBe(400)
    const meDespues: any = await (await request.get(`${API}/me`, { headers: admin })).json()

    expect([...(meAntes.effective_business_units ?? [])].sort()).toEqual(
      [...(meDespues.effective_business_units ?? [])].sort(),
    )
    expect(await sigueEnBandeja(request, op.id), 'sigue pendiente').toBe(true)

    ev['05'] = {
      eventId: op.id,
      granja: g.nombre,
      candidatos_antes: codigosAntes,
      candidatos_con_broiler_apagado: codigosDespues,
      habilitadas_empresa: habilitadas,
      opciones_dialogo: valores.sort(),
      status_broiler: porCodigoAjeno.status(),
      status_zzz: inexistente.status(),
      effective_business_units: meDespues.effective_business_units ?? [],
    }
  } finally {
    if (rehabilitar) {
      const encender = await request.patch(`${API}/business-units/broiler/enable`, {
        headers: admin,
      })
      expect(encender.ok()).toBeTruthy()
    }
  }
})

test('O3-E2E-06 empresa ajena: ni candidatos ni clasificación sobre el evento de A', async ({
  request,
}) => {
  const companyId = empresaActiva(admin)
  const g = await crearGranjaConLotes(request, 'P20A06', companyId, ['breeder', 'broiler'])
  const op = await crearInspeccion(request, g.farmId, g.houseId)
  expect(await sigueEnBandeja(request, op.id)).toBe(true)

  const candidatos = await getCandidatos(request, op.id, adminOtra)
  expect(candidatos.status(), await candidatos.text()).toBe(404)
  const intento = await postClasificar(request, op.id, {
    business_unit_code: 'breeder',
    reason: `Clasificación desde otra empresa ${sufijo()}`,
  }, adminOtra)
  expect(intento.status(), await intento.text()).toBe(404)

  expect(await sigueEnBandeja(request, op.id), 'el registro sigue pendiente').toBe(true)
  const clasificaciones = clasificacionesDe(await timelineDe(request, op.id))
  expect(clasificaciones.length).toBe(0)

  ev['06'] = {
    eventId: op.id,
    granja: g.nombre,
    candidates_status: candidatos.status(),
    classify_status: intento.status(),
    auditoria: clasificaciones.length,
  }
})

test('O3-E2E-07 motivo vacío o corto: no se envía y la API responde 422', async ({
  page,
  request,
}) => {
  const companyId = empresaActiva(admin)
  const g = await crearGranjaConLotes(request, 'P20A07', companyId, ['breeder', 'broiler'])
  const op = await crearInspeccion(request, g.farmId, g.houseId)

  prepararEvidencia()
  await entrar(page, 'admin')
  await page.goto('/operations/pending-classification')
  const fila = page.getByTestId('pending-row').filter({ hasText: g.nombre })
  await expect(fila).toHaveCount(1)
  await fila.getByTestId('classify-btn').click()
  const select = page.getByTestId('classify-unit')
  await expect(select.locator('option[value="breeder"]')).toHaveCount(1, { timeout: 20_000 })
  const enviar = page.getByTestId('classify-submit')
  const motivoInput = page.getByTestId('classify-reason')

  let intentos = 0
  page.on('request', (r) => {
    if (r.method() === 'POST' && /\/operations\/\d+\/classify/.test(r.url())) intentos += 1
  })

  // Sin unidad y sin motivo: deshabilitado.
  await expect(enviar).toBeDisabled()
  await select.selectOption('breeder')
  const estados: Record<string, boolean> = {}
  for (const [caso, texto] of [
    ['vacio', ''],
    ['dos_caracteres', 'ab'],
    ['solo_espacios', '   '],
  ] as Array<[string, string]>) {
    await motivoInput.fill(texto)
    estados[caso] = await enviar.isEnabled()
    expect(estados[caso], `con «${texto}» el botón no debe habilitarse`).toBe(false)
    await enviar.click({ force: true }).catch(() => undefined)
  }
  await page.screenshot({ path: `${DIR_PNG}/o3_07_motivo_invalido.png`, fullPage: true })
  expect(intentos, 'la interfaz no debe enviar el POST').toBe(0)

  const variantes = ['', '   ', null, 'ab']
  const status: any[] = []
  for (const reason of variantes) {
    const r = await postClasificar(request, op.id, { business_unit_code: 'breeder', reason })
    status.push({ reason, status: r.status() })
    expect(r.status(), `reason=${JSON.stringify(reason)}`).toBe(422)
  }
  expect(await sigueEnBandeja(request, op.id), 'sigue pendiente').toBe(true)
  expect(clasificacionesDe(await timelineDe(request, op.id)).length).toBe(0)

  ev['07'] = { eventId: op.id, granja: g.nombre, estados_boton: estados,
    intentos_ui: intentos, api: status }
})

test('O3-E2E-08 doble clasificación: el segundo intento es 404 y no reescribe nada', async ({
  request,
}) => {
  const companyId = empresaActiva(admin)
  const g = await crearGranjaConLotes(request, 'P20A08', companyId, ['breeder', 'broiler'])
  const op = await crearInspeccion(request, g.farmId, g.houseId)
  const motivo = `Clasificación única O3-08 ${sufijo()}`

  const primera = await postClasificar(request, op.id, {
    business_unit_code: 'breeder',
    reason: motivo,
  })
  expect(primera.status(), await primera.text()).toBe(200)
  expect((await primera.json()).id).toBe(op.id)

  const mismaUnidad = await postClasificar(request, op.id, {
    business_unit_code: 'breeder',
    reason: `Repetición ${sufijo()}`,
  })
  expect(mismaUnidad.status(), await mismaUnidad.text()).toBe(404)
  const otraUnidad = await postClasificar(request, op.id, {
    business_unit_code: 'broiler',
    reason: `Cambio de unidad ${sufijo()}`,
  })
  expect(otraUnidad.status(), await otraUnidad.text()).toBe(404)

  const clasificaciones = clasificacionesDe(await timelineDe(request, op.id))
  expect(clasificaciones.length, 'el acto es único y su rastro también').toBe(1)
  expect(clasificaciones[0].change_reason).toBe(motivo)
  expect(clasificaciones[0].new_state).toBe('breeder')

  const detalle: any = await (await request.get(`${API}/operations/${op.id}`, {
    headers: admin,
  })).json()
  const unidadDetalle =
    detalle.business_unit_code ?? detalle.business_unit ?? detalle.chain ?? detalle.cadena ?? null
  if (unidadDetalle !== null) expect(String(unidadDetalle)).toBe('breeder')
  expect(await sigueEnBandeja(request, op.id)).toBe(false)

  ev['08'] = {
    eventId: op.id,
    granja: g.nombre,
    motivo,
    primera: primera.status(),
    segunda_misma_unidad: mismaUnidad.status(),
    segunda_otra_unidad: otraUnidad.status(),
    auditoria: clasificaciones.length,
    unidad_detalle: unidadDetalle,
  }
})

// <!--CHUNK-->
