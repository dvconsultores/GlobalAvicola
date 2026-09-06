/**
 * P-06 — POLLO DE ENGORDE   (`spec.md §4.8`, `audit/06 §P-06`)
 *
 * La cadena es la de `P-03` más el paso terminal `lot_closure`:
 *
 *     farm_inspection → bird_reception → bird_distribution
 *       → ciclo: feed_registration · weight_recording · mortality_recording
 *                cull_recording · vaccination · medication
 *       → bird_exit → lot_closure
 *
 * El cierre era inalcanzable: `POST /lots/{id}/close` respondía 500 siempre (`R-73`), y es
 * el único punto del backend que pone un lote en `closed`. `GA-REM-029` lo corrigió junto
 * con `R-74` —`BR-05` vigilaba el evento `lot_closure`, que no cierra nada— y `R-75` —la
 * fecha de cierre se guardaba a medianoche local y se releía como la del día anterior—.
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * Estado de los bloqueantes históricos de este proceso:
 *
 *   GA-TD-014  cerrado: `OD-04` autorizó las entregas parciales y `GA-REM-035` implantó el
 *              límite acumulado. La recepción lleva la OC al campo tipado.
 *   R-76       cerrado: `GA-REM-036` implantó `docs/12 R7`, la aprobación previa al cierre.
 *   GA-REQ-037 **no aplica a `P-06`**: `§4.8` no exige alertas por desviación; las exige
 *              `§4.5`, que es `P-03`.
 *
 * ══════════════════════════════════════════════════════════════════════════════
 */
import { test, expect } from '@playwright/test'
import {
  API, cabeceraAdmin, cabeceraAprobador, crearEscenario, crearMaestros, hoy, registrar,
} from '../test-support/e2e-api'

const RECIBIDAS = 5_000
const MORTALIDAD = 40
const DESCARTES = 15
const ALIMENTO_KG = 850.5

/** Lleva un evento por el ciclo real de `P-07` hasta quedar aprobado.
 *
 * `BR-14` impide que lo apruebe quien lo registró, así que interviene el aprobador. No se
 * toca la base: `docs/12 R7` es una regla de aprobación y comprobarla saltándose la
 * aprobación no probaría el proceso.
 */
async function aprobar(request: any, cab: any, aprobador: any, eventId: number) {
  const enviado = await request.post(`${API}/operations/${eventId}/submit`, { headers: cab })
  expect(enviado.status(), await enviado.text()).toBeLessThan(300)
  const revision = await request.post(`${API}/review/start/${eventId}`, { headers: aprobador })
  expect(revision.status(), await revision.text()).toBeLessThan(300)
  const aprobado = await request.post(`${API}/approvals/approve`, {
    headers: aprobador, data: { event_id: eventId },
  })
  expect(aprobado.status(), await aprobado.text()).toBe(200)
}

/** Recorre la cadena hasta dejar el lote listo para cerrar. Devuelve lo registrado. */
async function cadenaDeEngorde(request: any, cab: any, aprobarTodo = true) {
  const esc = await crearEscenario(request, cab, 'P06', 'broiler')
  const m = await crearMaestros(request, cab, 'P06')
  const base = { lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId, event_date: hoy() }

  const pasos: [string, any][] = [
    ['farm_inspection', { inspection_details: [{ parameter: 'Bioseguridad', value: 'ok', status: 'ok' }] }],
    ['bird_reception', { bird_movements: [{ sex: 'mixed', quantity: RECIBIDAS }] }],
    ['bird_distribution', { bird_movements: [{ sex: 'mixed', quantity: RECIBIDAS }] }],
    ['feed_registration', { feed_movements: [{ quantity_kg: ALIMENTO_KG, feed_type_id: m.alimentoId }] }],
    ['weight_recording', { bird_movements: [{ sex: 'mixed', quantity: 100, avg_weight: 2400 }] }],
    ['mortality_recording', { bird_movements: [{ sex: 'mixed', quantity: MORTALIDAD, mortality_cause_id: m.causaMortalidadId }] }],
    ['cull_recording', { bird_movements: [{ sex: 'mixed', quantity: DESCARTES, cull_cause_id: m.causaDescarteId }] }],
    ['vaccination', { vaccine_id: m.vacunaId }],
    ['medication', { medication_id: m.medicamentoId }],
  ]

  const ids: number[] = []
  for (const [tipo, extra] of pasos) {
    const r = await registrar(request, cab, { ...base, event_type: tipo, ...extra })
    expect(r.status(), `${tipo}: ${await r.text()}`).toBe(201)
    ids.push((await r.json()).id)
  }

  // `R-76` / `docs/12 R7`: el lote no puede cerrarse con registros sin aprobar. El happy
  // path los aprueba por el camino normativo, no manipulando la base.
  if (aprobarTodo) {
    const aprobador = await cabeceraAprobador(request)
    for (const id of ids) await aprobar(request, cab, aprobador, id)
  }
  return { ...esc, eventos: ids }
}

test.describe('P-06 · cadena de engorde hasta el cierre', () => {
  test('la cadena completa se recorre y el lote cierra con su resumen', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await cadenaDeEngorde(request, cab)

    const cierre = await request.post(`${API}/lots/${esc.lotId}/close`, { headers: cab })
    expect(cierre.status(), await cierre.text()).toBe(200)
    const resumen = await cierre.json()

    // El resumen refleja lo registrado, no ceros ni cuentas intercambiadas.
    expect(resumen.total_mortality).toBe(MORTALIDAD)
    expect(resumen.total_feed_kg).toBeCloseTo(ALIMENTO_KG, 1)
    expect(resumen.total_events).toBe(9)
    expect(resumen.status).toBe('closed')
    expect(resumen.lot_id).toBe(esc.lotId)
  })

  test('el cierre se persiste con la fecha del día, no con la del día anterior', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await cadenaDeEngorde(request, cab)

    const cierre = await request.post(`${API}/lots/${esc.lotId}/close`, { headers: cab })
    expect(cierre.status()).toBe(200)

    // `R-75`. Se relee: lo que importa es lo guardado, no lo que devolvió la llamada.
    const leido = await request.get(`${API}/lots/${esc.lotId}`, { headers: cab })
    expect(leido.status()).toBe(200)
    const lote = await leido.json()
    expect(lote.status).toBe('closed')
    expect(String(lote.end_date).slice(0, 10)).toBe(hoy())
  })

  test('R7 · un registro sin aprobar impide cerrar el lote', async ({ request }) => {
    // `R-76`. Evidencia negativa permanente del proceso: la cadena entera registrada, `BR-05`
    // satisfecho, y un solo registro sin aprobar basta para impedir el cierre.
    const cab = await cabeceraAdmin(request)
    const esc = await cadenaDeEngorde(request, cab, false)   // nada aprobado

    const cierre = await request.post(`${API}/lots/${esc.lotId}/close`, { headers: cab })
    expect(cierre.status(), await cierre.text()).toBe(400)
    expect((await cierre.json()).rule).toBe('R7')

    // El lote sigue operativo: una negativa no deja el cierre a medias.
    const leido = await request.get(`${API}/lots/${esc.lotId}`, { headers: cab })
    expect((await leido.json()).status).toBe('active')
  })

  test('BR-05 impide cerrar sin pesaje ni alimento', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, 'P06BR', 'broiler')

    // Un lote con recepción pero sin pesaje ni alimento: no hay base para el FCR.
    const recepcion = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId, event_date: hoy(),
      event_type: 'bird_reception', bird_movements: [{ sex: 'mixed', quantity: RECIBIDAS }],
    })
    expect(recepcion.status()).toBe(201)

    const cierre = await request.post(`${API}/lots/${esc.lotId}/close`, { headers: cab })
    expect(cierre.status(), await cierre.text()).toBe(400)
    expect((await cierre.json()).rule).toBe('BR-05')

    // Y el lote sigue operativo: un rechazo no deja el cierre a medias.
    const leido = await request.get(`${API}/lots/${esc.lotId}`, { headers: cab })
    expect((await leido.json()).status).toBe('active')
  })

  test('un lote cerrado no se cierra otra vez', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await cadenaDeEngorde(request, cab)

    const primero = await request.post(`${API}/lots/${esc.lotId}/close`, { headers: cab })
    expect(primero.status()).toBe(200)
    const fecha = (await primero.json()).end_date

    const segundo = await request.post(`${API}/lots/${esc.lotId}/close`, { headers: cab })
    expect(segundo.status()).toBe(400)

    const leido = await request.get(`${API}/lots/${esc.lotId}`, { headers: cab })
    expect(String((await leido.json()).end_date).slice(0, 10)).toBe(String(fecha).slice(0, 10))
  })

  test('GA-TD-014 · la recepción lleva la OC al campo tipado y respeta su límite', async ({ request }) => {
    // Esta prueba documentaba un hueco abierto y decía que fallaría el día que se resolviera.
    // `OD-04` se resolvió y `GA-REM-035` lo cerró, así que ahora comprueba el comportamiento
    // certificado: la orden viaja al campo tipado y el límite es **acumulado**.
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, 'P06OC', 'broiler')
    const codigo = `P06-OC-${Date.now()}`
    const orden = await request.post(`${API}/sap/references/import`, {
      headers: cab,
      data: { references: [{ ref_type: 'purchase_order', sap_code: codigo, quantity: 1000 }] },
    })
    expect(orden.status(), await orden.text()).toBe(201)

    const base = {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_date: hoy(), event_type: 'bird_reception', sap_document_ref: codigo,
    }

    const primera = await registrar(request, cab, { ...base, bird_movements: [{ sex: 'mixed', quantity: 600 }] })
    expect(primera.status(), await primera.text()).toBe(201)
    expect((await primera.json()).sap_document_ref,
      'la orden debe viajar al campo tipado').toBe(codigo)

    // `OD-04`: la segunda entrega parcial contra la misma orden se acepta.
    const segunda = await registrar(request, cab, { ...base, bird_movements: [{ sex: 'mixed', quantity: 400 }] })
    expect(segunda.status(), await segunda.text()).toBe(201)

    // Y el acumulado ya iguala lo ordenado: una más sobra.
    const tercera = await registrar(request, cab, { ...base, bird_movements: [{ sex: 'mixed', quantity: 1 }] })
    expect(tercera.status()).toBe(400)
    expect((await tercera.json()).rule).toBe('BR-18')
  })
})
