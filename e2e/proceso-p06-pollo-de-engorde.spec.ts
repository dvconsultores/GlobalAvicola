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
 * ESTO NO CERTIFICA `P-06`. Quedan dos huecos, y ninguno se cierra aquí:
 *
 *   GA-TD-014  `bird_reception` · la OC SAP viaja en `extra_data.sap_order_ref` y no en
 *              `sap_document_ref`, de modo que `validate_oc_limit` sale por la primera
 *              línea y `BR-18` nunca se aplica. Diferido en `C-15`, pendiente de `RC-07`.
 *   GA-REQ-037 `weight_recording` · sin alerta de peso fuera de curva.
 *
 * Lo que sí demuestra: que la cadena se recorre entera contra la pila real y que el paso
 * terminal, roto desde siempre, ahora funciona.
 * ══════════════════════════════════════════════════════════════════════════════
 */
import { test, expect } from '@playwright/test'
import {
  API, cabeceraAdmin, crearEscenario, crearMaestros, hoy, registrar,
} from '../test-support/e2e-api'

const RECIBIDAS = 5_000
const MORTALIDAD = 40
const DESCARTES = 15
const ALIMENTO_KG = 850.5

/** Recorre la cadena hasta dejar el lote listo para cerrar. Devuelve lo registrado. */
async function cadenaDeEngorde(request: any, cab: any) {
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

  for (const [tipo, extra] of pasos) {
    const r = await registrar(request, cab, { ...base, event_type: tipo, ...extra })
    expect(r.status(), `${tipo}: ${await r.text()}`).toBe(201)
  }
  return esc
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

  test('GA-TD-014 · la OC de la recepción sigue sin llegar al campo tipado', async ({ request }) => {
    // No es una prueba de éxito: **documenta el hueco abierto** que impide certificar
    // `P-06`. Si algún día empieza a fallar, será porque `GA-TD-014` se resolvió, y
    // entonces hay que revisar la certificación del proceso, no silenciar esto.
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, 'P06OC', 'broiler')

    const r = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId, event_date: hoy(),
      event_type: 'bird_reception', bird_movements: [{ sex: 'mixed', quantity: RECIBIDAS }],
      extra_data: { sap_order_ref: 'OC-P06-INERTE' },
    })
    expect(r.status()).toBe(201)

    const evento = await r.json()
    expect(evento.sap_document_ref ?? null,
      'si esto deja de ser nulo, GA-TD-014 se resolvió y BR-18 pasa a aplicarse').toBeNull()
  })
})
