/**
 * `GA-UAT-BREEDER-CRIA-S1-2026-11-10` · spec `015` §3 y §5 — E2E P18A.
 *
 * Escenario A — corrección obligatoria de un dato real: el peso promedio de una fila de
 * `bird_movements` de una recepción de reproductoras en revisión. El formulario ofrece los
 * campos reales del evento (no «Observaciones» fijo), el original es de solo lectura, el dato
 * cambia, la corrección queda auditada y sobrevive a la aprobación.
 *
 * Escenario B — trazabilidad de la inspección de granja sin lote: una granja de una sola
 * cadena deriva su unidad de negocio y aparece en el historial; una de dos cadenas nace
 * pendiente de clasificar, fuera del historial y con su bandeja visible.
 */
import { test, expect, type APIRequestContext } from '@playwright/test'
import * as fs from 'node:fs'
import {
  API, hoy, sufijo, empresaActiva, cabeceraAdmin, cabeceraAprobador, cabeceraOtraEmpresa,
  crearEscenario, registrar, tipoDeCorreccion,
} from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

const PREFIJO = 'S1P18A'
const DIR = 'audit/ga-uat-breeder-cria-s1-2026-11-10/evidence'
const CAPTURAS = `${DIR}/screenshots`

/** Evidencia sanitizada: ids, estados, valores, motivos y códigos; nunca credenciales. */
const evidencia: Record<string, any> = {
  spec: '015-breeder-cria-uat-s1',
  generado: new Date().toISOString(),
  escenarioA: {},
  escenarioB: {},
}

async function como(request: APIRequestContext, quien: 'admin' | 'operator' | 'approver') {
  const claves = {
    admin: ['test_admin', process.env.GA_TEST_ADMIN_PASSWORD!],
    operator: ['test_operator', process.env.GA_TEST_OPERATOR_PASSWORD!],
    approver: ['test_approver', process.env.GA_TEST_APPROVER_PASSWORD!],
  } as const
  const [usuario, clave] = claves[quien]
  const r = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
  expect(r.status(), `login de ${usuario}: ${await r.text()}`).toBe(200)
  return { Authorization: `Bearer ${(await r.json()).access_token}` }
}

/** POST que debe crear: el 201 forma parte de la precondición del escenario. */
async function crearFila(request: APIRequestContext, cabecera: any, ruta: string, data: any) {
  const r = await request.post(`${API}${ruta}`, { headers: cabecera, data })
  expect(r.status(), `${ruta}: ${await r.text()}`).toBe(201)
  return await r.json()
}

test.describe('P18A · corrección por submovimiento e inspección sin lote (spec 015)', () => {
  test('A · el peso promedio de una recepción breeder se corrige, se audita y sobrevive a la aprobación', async ({
    request,
    page,
  }) => {
    const admin = await cabeceraAdmin(request)
    const operador = await como(request, 'operator')
    const esc = await crearEscenario(request, admin, PREFIJO)

    // RECEPCIÓN — registrada por el operador (`BR-20`: 980 alojadas + 15 + 5 = 1000).
    const creacion = await registrar(request, operador, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'bird_reception', event_date: hoy(),
      received_total: 1000, dead_on_arrival: 15, rejected_on_arrival: 5,
      bird_movements: [
        { sex: 'male', quantity: 100, avg_weight: 2.0 },
        { sex: 'female', quantity: 880, avg_weight: 1.8 },
      ],
    })
    expect(creacion.status(), `recepción de reproductoras: ${await creacion.text()}`).toBe(201)
    const idEvento = (await creacion.json()).id

    const enviado = await request.post(`${API}/operations/${idEvento}/submit`, { headers: operador })
    expect(enviado.status(), await enviado.text()).toBe(200)
    expect((await enviado.json()).status, 'el registrante la envía a revisión').toBe('pending_review')

    const revision = await request.post(`${API}/review/start/${idEvento}`, { headers: admin })
    expect(revision.status(), await revision.text()).toBe(200)
    expect((await revision.json()).status, 'otra identidad inicia la revisión (BR-14)').toBe('in_review')

    // El endpoint nuevo ofrece los campos REALES del evento (`S1-CORR-01`). El detalle no
    // publica el id de cada fila: el identificador viaja en el propio `field_name`.
    const camposResp = await request.get(`${API}/corrections/events/${idEvento}/correctable-fields`, {
      headers: admin,
    })
    expect(camposResp.status(), await camposResp.text()).toBe(200)
    const campos = await camposResp.json()
    const pesos = campos.filter((c: any) => String(c.field_name).endsWith('.avg_weight'))
    expect(pesos.length, 'las dos filas ofrecen su peso promedio').toBeGreaterThanOrEqual(2)
    expect(
      campos.some((c: any) => /\.quantity$/.test(String(c.field_name))),
      'la cantidad de la recepción breeder no se ofrece',
    ).toBe(false)

    const filaMacho = pesos.find((c: any) => c.row_label === 'male')
    const filaHembra = pesos.find((c: any) => c.row_label === 'female')
    expect(filaMacho && filaHembra, 'cada fila se distingue por su sexo').toBeTruthy()
    const campoMacho = String(filaMacho.field_name)
    expect(campoMacho, 'el campo lleva el id de la fila').toMatch(
      /^bird_movements\[\d+\]\.avg_weight$/,
    )

    // `RR-27` (`OD-S2-01`): toda corrección nueva declara su tipo.
    const tipoCorreccion = await tipoDeCorreccion(request, admin)
    // NEGATIVO (i) — la cantidad de una recepción breeder no se corrige aislada (`BR-20`).
    const cantidad = await request.post(`${API}/corrections`, {
      headers: admin,
      data: {
        event_id: idEvento,
        correction_type_id: tipoCorreccion,
        field_name: `bird_movements[${filaMacho.row_id}].quantity`,
        corrected_value: '120',
        reason: 'Intento de corregir la cantidad de la recepción aislada',
      },
    })
    const cuerpoCantidad = await cantidad.json()
    expect(cantidad.status(), 'la cantidad breeder no se corrige (BR-20)').toBe(400)
    expect(String(cuerpoCantidad.detail), 'mensaje en español').toMatch(/no se corrige/i)
    expect(String(cuerpoCantidad.detail), 'sin códigos internos').not.toMatch(/BR-\d/)

    // UI — el formulario de corrección, como lo usa un supervisor.
    await entrar(page, 'admin')
    let postsCorrecciones = 0
    page.on('request', req => {
      const url = new URL(req.url())
      if (req.method() === 'POST' && url.pathname.endsWith('/corrections')) postsCorrecciones++
    })

    await page.goto(`/review/${idEvento}/correct`)
    const selector = page.locator('form select').first()
    await expect(selector, 'el formulario ofrece el selector de campo').toBeVisible({ timeout: 20_000 })

    const opciones = await selector.locator('option').allTextContents()
    const pesosOfrecidos = opciones.filter(o => /Peso promedio/i.test(o))
    expect(
      pesosOfrecidos.length,
      `el selector no puede limitarse a Observaciones: ${opciones.join(' | ')}`,
    ).toBeGreaterThanOrEqual(2)
    expect(
      opciones.some(o => /^Cantidad\b/.test(o)),
      'la cantidad de la recepción breeder no se ofrece en el selector',
    ).toBe(false)
    expect(pesosOfrecidos.some(o => /Macho/i.test(o)), 'la fila de machos se distingue').toBe(true)

    await selector.selectOption(campoMacho)
    const original = page.getByTestId('correction-original')
    await expect(original, 'el valor original se muestra').toBeVisible()
    expect(await original.getAttribute('readonly'), 'el original es de solo lectura').not.toBeNull()
    await expect(original, 'el original es el peso que registró el operador').toHaveValue(/^2\.0+$/)

    const corregido = page.getByTestId('correction-corrected')
    await corregido.fill('2.5')
    const motivo = page.locator('form textarea').first()

    await page.getByTestId('correction-type').selectOption(String(tipoCorreccion))
    // NEGATIVO (ii) — motivo de 3 caracteres: mensaje inline y NINGUNA llamada al backend.
    await motivo.fill('abc')
    const guardar = page.locator('form button[type="submit"]').first()
    await expect(guardar, 'el formulario ofrece Guardar').toBeVisible()
    await guardar.click()
    const errorInline = page.getByTestId('correction-error')
    await expect(errorInline, 'motivo corto: mensaje inline (sin alerta nativa)').toBeVisible()
    await expect(errorInline, 'mensaje en español').toContainText(/al menos 5/i)
    expect(postsCorrecciones, 'la validación de cliente no llama al backend').toBe(0)

    fs.mkdirSync(CAPTURAS, { recursive: true })
    await motivo.fill('Báscula mal calibrada en recepción')
    await page.screenshot({ path: `${CAPTURAS}/p18a_correccion_before.png`, fullPage: true })
    await guardar.click()
    await expect(page, 'tras guardar se vuelve al detalle de revisión').toHaveURL(
      new RegExp(`/review/${idEvento}$`),
      { timeout: 20_000 },
    )
    await page.screenshot({ path: `${CAPTURAS}/p18a_correccion_after.png`, fullPage: true })
    expect(postsCorrecciones, 'guardar sí llama al backend, una sola vez').toBe(1)

    // El DATO cambió y la otra fila quedó intacta (`RR-01`).
    const detalleCorregido = await (
      await request.get(`${API}/operations/${idEvento}`, { headers: admin })
    ).json()
    const machoCorregido = detalleCorregido.bird_movements.find((bm: any) => bm.sex === 'male')
    const hembraIntacta = detalleCorregido.bird_movements.find((bm: any) => bm.sex === 'female')
    expect(machoCorregido.avg_weight, 'el peso corregido se escribe en la fila').toBe(2.5)
    expect(hembraIntacta.avg_weight, 'la fila de hembras queda intacta').toBe(1.8)
    expect(detalleCorregido.status, 'corregir no es aprobar').toBe('corrected')

    // El registro de corrección conserva original, corregido, motivo y autor.
    const correccionesResp = await request.get(`${API}/corrections/event/${idEvento}`, { headers: admin })
    expect(correccionesResp.status(), await correccionesResp.text()).toBe(200)
    const correcciones = await correccionesResp.json()
    expect(correcciones.length, 'queda un único registro de corrección').toBe(1)
    const log = correcciones[0]
    expect(log.field_name, 'el campo se identifica con el id de su fila').toBe(campoMacho)
    expect(log.original_value, 'el original lo lee el servidor del dato').toBe('2.0')
    expect(log.corrected_value).toBe('2.5')
    expect(log.reason).toContain('Báscula')
    expect(log.corrected_by_id, 'quién corrigió queda registrado').toBeTruthy()

    // Auditoría: la corrección deja rastro con sus valores.
    const auditoriaResp = await request.get(
      `${API}/audit?entity_type=operational_event&entity_id=${idEvento}&limit=100`,
      { headers: admin },
    )
    expect(auditoriaResp.status(), await auditoriaResp.text()).toBe(200)
    const logs = (await auditoriaResp.json()).logs ?? []
    const rastro = logs.find((l: any) => l.action === 'corrected')
    expect(
      rastro,
      `la auditoría debe registrar la corrección (acciones: ${logs.map((l: any) => l.action).join(',')})`,
    ).toBeTruthy()
    expect(JSON.stringify(rastro), 'la auditoría conserva el valor corregido').toContain('2.5')

    // UI del detalle: etiqueta traducida, original→corregido y motivo.
    await page.goto(`/review/${idEvento}`)
    const cuerpo = page.locator('body')
    await expect(cuerpo, 'el historial usa la etiqueta traducida').toContainText('Peso promedio', {
      timeout: 20_000,
    })
    await expect(cuerpo, 'el historial nunca muestra el nombre crudo del campo').not.toContainText(
      'bird_movements[',
    )
    await expect(cuerpo, 'el original del historial').toContainText('2.0')
    await expect(cuerpo, 'el corregido del historial').toContainText('2.5')
    await expect(cuerpo, 'el motivo del historial').toContainText('Báscula mal calibrada en recepción')

    // APROBACIÓN con una identidad distinta de la que registró (`BR-14`).
    const aprobador = await cabeceraAprobador(request)
    const aprobado = await request.post(`${API}/approvals/approve`, {
      headers: aprobador,
      data: { event_id: idEvento, observations: 'Verificado en UAT' },
    })
    expect(aprobado.status(), await aprobado.text()).toBe(200)

    const final = await (await request.get(`${API}/operations/${idEvento}`, { headers: admin })).json()
    expect(final.status).toBe('approved')
    const machoFinal = final.bird_movements.find((bm: any) => bm.sex === 'male')
    const hembraFinal = final.bird_movements.find((bm: any) => bm.sex === 'female')
    expect(machoFinal.avg_weight, 'el detalle final conserva 2.5').toBe(2.5)
    expect(hembraFinal.avg_weight, 'la fila de hembras sigue en 1.8 tras aprobar').toBe(1.8)
    const correccionesFinal = await (
      await request.get(`${API}/corrections/event/${idEvento}`, { headers: admin })
    ).json()
    expect(correccionesFinal.length, 'la corrección sigue en el historial').toBe(1)

    // NEGATIVO (iii) — tras aprobar, corregir es 400 con el estado en español.
    const tarde = await request.post(`${API}/corrections`, {
      headers: admin,
      data: {
        event_id: idEvento,
        correction_type_id: tipoCorreccion,
        field_name: campoMacho,
        corrected_value: '2.6',
        reason: 'Corrección posterior a la aprobación',
      },
    })
    const cuerpoTarde = await tarde.json()
    expect(tarde.status(), 'un evento aprobado no admite correcciones').toBe(400)
    expect(String(cuerpoTarde.detail), 'el estado viaja en español').toMatch(/Aprobado/)
    expect(String(cuerpoTarde.detail), 'sin el valor crudo del enum').not.toMatch(/approved/i)

    evidencia.escenarioA = {
      lote_id: esc.lotId,
      granja_id: esc.farmId,
      galpon_id: esc.houseId,
      evento_id: idEvento,
      fila_macho_id: filaMacho.row_id,
      campo_corregido: campoMacho,
      correccion: {
        original: log.original_value,
        corregido: log.corrected_value,
        motivo: log.reason,
        corrected_by_id: log.corrected_by_id,
      },
      estado_tras_corregir: detalleCorregido.status,
      estado_final: final.status,
      valores_finales: final.bird_movements.map((bm: any) => ({
        sexo: bm.sex,
        cantidad: bm.quantity,
        peso_promedio: bm.avg_weight,
      })),
      http: {
        recepcion: creacion.status(),
        cantidad_breeder: cantidad.status(),
        motivo_corto_ui: 'validación de cliente: 0 POST /corrections',
        correccion_tras_aprobar: tarde.status(),
      },
      auditoria_acciones: logs.map((l: any) => l.action),
      capturas: [
        `${CAPTURAS}/p18a_correccion_before.png`,
        `${CAPTURAS}/p18a_correccion_after.png`,
      ],
    }
  })

  test('B1 · la inspección de una granja de una sola cadena deriva su unidad y entra en trazabilidad', async ({
    request,
    page,
  }) => {
    const admin = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, admin, PREFIJO)

    // INSPECCIÓN SIN LOTE en una granja de una sola cadena (`D1`).
    const creacion = await registrar(request, admin, {
      event_type: 'farm_inspection',
      event_date: hoy(),
      farm_id: esc.farmId,
      house_id: esc.houseId,
      inspection_details: [{ house_id: esc.houseId, parameter: 'temperature', value: '24' }],
    })
    expect(creacion.status(), `inspección con unidad derivada: ${await creacion.text()}`).toBe(201)
    const idEvento = (await creacion.json()).id

    const detalleResp = await request.get(`${API}/operations/${idEvento}`, { headers: admin })
    expect(detalleResp.status(), 'el autor ve su inspección').toBe(200)
    const detalle = await detalleResp.json()
    expect(detalle.farm_name, 'AC-S1-I01: el detalle trae el nombre de la granja').toBeTruthy()
    expect(detalle.house_name, 'AC-S1-I01: el detalle trae el nombre del galpón').toBeTruthy()

    const listado = await (
      await request.get(`${API}/operations?farm_id=${esc.farmId}&limit=100`, { headers: admin })
    ).json()
    expect(
      listado.some((e: any) => e.id === idEvento),
      'con unidad derivada aparece en el historial normal',
    ).toBe(true)

    const pendientes = await (
      await request.get(`${API}/operations/pending-classification?limit=100`, { headers: admin })
    ).json()
    expect(
      pendientes.some((e: any) => e.id === idEvento),
      'con unidad derivada NO está en la bandeja de pendientes',
    ).toBe(false)

    // Cola de revisión (`ReviewCenter` consume `/review/pending`).
    const enviado = await request.post(`${API}/operations/${idEvento}/submit`, { headers: admin })
    expect(enviado.status(), await enviado.text()).toBe(200)
    const cola = await (
      await request.get(`${API}/review/pending?status=pending_review&limit=100`, { headers: admin })
    ).json()
    expect(
      (cola.events ?? []).some((e: any) => e.id === idEvento),
      'la inspección enviada a revisión aparece en la cola del revisor',
    ).toBe(true)

    const auditoriaResp = await request.get(
      `${API}/audit?entity_type=operational_event&entity_id=${idEvento}&limit=100`,
      { headers: admin },
    )
    expect(auditoriaResp.status(), await auditoriaResp.text()).toBe(200)
    const logs = (await auditoriaResp.json()).logs ?? []
    expect(
      logs.some((l: any) => l.action === 'created'),
      `la auditoría tiene el alta (acciones: ${logs.map((l: any) => l.action).join(',')})`,
    ).toBe(true)

    // UI — el detalle muestra nombres, no identificadores numéricos.
    await entrar(page, 'admin')
    await page.goto(`/operations/${idEvento}`)
    const cuerpo = page.locator('body')
    await expect(cuerpo, 'el detalle muestra el nombre de la granja').toContainText(
      String(detalle.farm_name),
      { timeout: 20_000 },
    )
    await expect(cuerpo, 'el detalle muestra el nombre del galpón').toContainText(
      String(detalle.house_name),
    )
    await expect(cuerpo, 'el detalle no cae al identificador numérico').not.toContainText(
      `#${esc.farmId}`,
    )

    evidencia.escenarioB.derivada = {
      granja_id: esc.farmId,
      galpon_id: esc.houseId,
      evento_id: idEvento,
      farm_name: detalle.farm_name,
      house_name: detalle.house_name,
      en_historial: true,
      en_pendientes: false,
      en_cola_revision: true,
      auditoria_acciones: logs.map((l: any) => l.action),
      http: { alta: creacion.status(), detalle: detalleResp.status(), envio_revision: enviado.status() },
    }
  })

  test('B2 · la inspección en una granja multicadena nace pendiente, va a la bandeja y no al historial', async ({
    request,
    page,
  }) => {
    const admin = await cabeceraAdmin(request)
    const companyId = empresaActiva(admin)
    const s = sufijo()

    // Granja con dos cadenas vivas: la unidad NO es inequívoca (`D1`).
    const granja = await crearFila(request, admin, '/masters/farms', {
      company_id: companyId, name: `${PREFIJO}-mixta-${s}`, code: `${PREFIJO}-MX-${s}`,
      location: 'Escenario multicadena', farm_type: 'breeding',
    })
    const galpon = await crearFila(request, admin, '/masters/houses', {
      farm_id: granja.id, name: `${PREFIJO}-mixta-galpon-${s}`, capacity: 50_000,
    })
    const galponB = await crearFila(request, admin, '/masters/houses', {
      farm_id: granja.id, name: `${PREFIJO}-mixta-galponB-${s}`, capacity: 50_000,
    })
    const loteBreeder = await crearFila(request, admin, '/lots', {
      company_id: companyId, farm_id: granja.id, house_id: galpon.id,
      lot_code: `${PREFIJO}-MX-BR-${s}`, bird_type: 'breeder', sex: 'mixed',
    })
    const loteBroiler = await crearFila(request, admin, '/lots', {
      company_id: companyId, farm_id: granja.id, house_id: galponB.id,
      lot_code: `${PREFIJO}-MX-BO-${s}`, bird_type: 'broiler', sex: 'mixed',
    })

    const creacion = await registrar(request, admin, {
      event_type: 'farm_inspection',
      event_date: hoy(),
      farm_id: granja.id,
      house_id: galpon.id,
      inspection_details: [{ house_id: galpon.id, parameter: 'temperature', value: '24' }],
    })
    expect(creacion.status(), `inspección multicadena: ${await creacion.text()}`).toBe(201)
    const idEvento = (await creacion.json()).id

    const listado = await (
      await request.get(`${API}/operations?farm_id=${granja.id}&limit=100`, { headers: admin })
    ).json()
    expect(
      listado.some((e: any) => e.id === idEvento),
      'un pendiente de clasificar no entra en el historial normal',
    ).toBe(false)

    const pendientes = await (
      await request.get(`${API}/operations/pending-classification?limit=100`, { headers: admin })
    ).json()
    const fila = pendientes.find((e: any) => e.id === idEvento)
    expect(fila, 'aparece en la bandeja de pendientes').toBeTruthy()
    expect(fila.farm_name, 'la bandeja trae el nombre de la granja').toBeTruthy()
    expect(fila.house_name, 'la bandeja trae el nombre del galpón').toBeTruthy()

    // Otro usuario no alcanza el registro pendiente.
    const otraEmpresa = await cabeceraOtraEmpresa(request)
    const ajeno = await request.get(`${API}/operations/${idEvento}`, { headers: otraEmpresa })
    expect(ajeno.status(), 'otro usuario no alcanza el pendiente por identificador').toBe(404)

    // NEGATIVO — inspección con granja y SIN galpón: `BR-08` en español y sin códigos.
    const sinGalpon = await registrar(request, admin, {
      event_type: 'farm_inspection',
      event_date: hoy(),
      farm_id: granja.id,
      inspection_details: [{ parameter: 'temperature', value: '24' }],
    })
    const cuerpoSinGalpon = await sinGalpon.json()
    expect(sinGalpon.status(), 'la inspección exige galpón (BR-08)').toBe(400)
    expect(String(cuerpoSinGalpon.detail), 'mensaje en español').toMatch(/galp[oó]n/i)
    expect(String(cuerpoSinGalpon.detail), 'sin códigos internos en el texto').not.toMatch(/BR-\d/)
    expect(cuerpoSinGalpon.rule, 'la regla viaja aparte, para la interfaz').toBe('BR-08')

    // UI — bandeja de pendientes con nombres legibles y acceso desde el historial.
    await entrar(page, 'admin')
    await page.goto('/operations/pending-classification')
    const filas = page.locator('[data-testid="pending-row"]')
    await expect(filas.first(), 'la bandeja lista registros pendientes').toBeVisible({
      timeout: 20_000,
    })
    const miFila = filas.filter({ hasText: String(fila.farm_name) }).first()
    await expect(miFila, 'la fila de la inspección se ve en la bandeja').toBeVisible({
      timeout: 20_000,
    })
    await expect(miFila, 'la fila muestra el nombre del galpón').toContainText(String(fila.house_name))

    await page.goto('/operations')
    const enlace = page.getByTestId('pending-classification-link')
    await expect(enlace, 'el historial ofrece el acceso a la bandeja').toBeVisible({
      timeout: 20_000,
    })
    await enlace.click()
    await expect(page, 'el enlace navega a la bandeja').toHaveURL(/\/operations\/pending-classification/)
    await expect(page.getByTestId('pending-classification-page'), 'la bandeja se abre').toBeVisible()

    evidencia.escenarioB.pendiente = {
      granja_id: granja.id,
      granja_nombre: fila.farm_name,
      galpon_id: galpon.id,
      galpon_nombre: fila.house_name,
      lote_breeder_id: loteBreeder.id,
      lote_broiler_id: loteBroiler.id,
      evento_id: idEvento,
      en_historial: false,
      en_pendientes: true,
      detalle_otro_usuario: ajeno.status(),
      sin_galpon: { http: sinGalpon.status(), detail: cuerpoSinGalpon.detail, rule: cuerpoSinGalpon.rule },
      http: { alta: creacion.status() },
    }
  })

  test.afterAll(() => {
    fs.mkdirSync(DIR, { recursive: true })
    fs.writeFileSync(
      `${DIR}/e2e_p18a_correccion_inspeccion.json`,
      JSON.stringify(evidencia, null, 2),
    )
  })
})
