/**
 * P-10 — TRAZABILIDAD GENERACIONAL   (`spec.md §4.9`)
 *
 * La cadena que une tres generaciones de lotes:
 *
 *     Reproductoras (producción)
 *       │ egg_dispatch                      ┐
 *       ↓                                   ├→ EggBatch
 *     Incubadora   · egg_reception_hatchery ┘
 *       │ chick_dispatch                    ┐
 *       ↓                                   ├→ ChickBatch ──egg_batch_id──> EggBatch
 *     Engorde      · bird_reception         ┘
 *
 * El emparejamiento automático usa **el destino que el operador declaró**
 * (`destination_farm_id`), no un identificador compartido: `GA-REM-008` lo resolvió al
 * cerrar `RC-04`. Por eso cada generación vive en una granja distinta.
 *
 * `GA-REM-030` cerró `R-60`: los vínculos manuales no comprobaban pertenencia, de modo que
 * podía fabricarse un vínculo entre dos compañías —un registro sin dueño posible, porque
 * `EggBatch` y `ChickBatch` no declaran `company_id`—.
 */
import { test, expect } from '@playwright/test'
import {
  API, cabeceraAdmin, cabeceraAdminEnOtraEmpresa, crearEscenario, hoy, registrar, sufijo,
} from '../test-support/e2e-api'

const HUEVOS = 12_000
const HUEVOS_RECIBIDOS = 11_800
const POLLITOS = 10_500
const POLLITOS_RECIBIDOS = 10_400

/** Las tres generaciones, cada una en su granja: es lo que el emparejamiento necesita.
 *
 * Cada lote nace con el saldo que su despacho exigirá: `BR-02` para el huevo y `BR-04` para
 * el pollito. Son precondiciones reales del negocio, así que se **construyen**, no se
 * suponen ni se sortean.
 */
async function tresGeneraciones(request: any, cab: any) {
  const repro = await crearEscenario(request, cab, 'P10R', 'breeder')
  const incub = await crearEscenario(request, cab, 'P10I', 'hatchery')
  const engorde = await crearEscenario(request, cab, 'P10E', 'broiler')

  // `BR-02` · sin recolección no hay huevo que despachar.
  const recoleccion = await registrar(request, cab, {
    lot_id: repro.lotId, farm_id: repro.farmId, house_id: repro.houseId,
    event_type: 'egg_collection', event_date: hoy(),
    egg_movements: [{ quantity: HUEVOS * 2, egg_type: 'fertile' }],
  })
  expect(recoleccion.status(), await recoleccion.text()).toBe(201)

  // `BR-04` · sin nacimiento no hay pollito viable que despachar.
  const nacimiento = await registrar(request, cab, {
    lot_id: incub.lotId, farm_id: incub.farmId, house_id: incub.houseId,
    event_type: 'birth_registration', event_date: hoy(),
    bird_movements: [{ sex: 'mixed', quantity: POLLITOS * 2 }],
  })
  expect(nacimiento.status(), await nacimiento.text()).toBe(201)

  return { repro, incub, engorde }
}

async function arbol(request: any, cab: any, lotId: number) {
  const r = await request.get(`${API}/lots/${lotId}/traceability`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  return await r.json()
}

test.describe('P-10 · cadena generacional completa', () => {
  // `R-78`. La cadena que la spec describe **no funciona en el orden natural**. El vínculo
  // se crea solo en la rama del despacho, que busca una recepción ya existente; las dos
  // ramas de recepción se limitan a *actualizar* un vínculo previo (`if batch:`). Como en la
  // operación real se despacha antes de recibir, no se crea ninguno.
  //
  // Se marca como fallo esperado en vez de borrarse o suavizarse: la prueba dice lo que la
  // spec exige, y el día que `R-78` se corrija pasará inesperadamente y obligará a revisar
  // esta certificación. Un hallazgo escrito en una aserción avisa; en prosa se olvida.
  test('la cadena une tres generaciones y queda navegable en ambos sentidos', async ({ request }) => {
    test.fail()
    const cab = await cabeceraAdmin(request)
    const { repro, incub, engorde } = await tresGeneraciones(request, cab)

    // ── Pasos 1-2 · huevo fértil: despacho declarando destino, y recepción ──
    const despachoHuevo = await registrar(request, cab, {
      lot_id: repro.lotId, farm_id: repro.farmId, house_id: repro.houseId,
      event_type: 'egg_dispatch', event_date: hoy(),
      destination_farm_id: incub.farmId,
      egg_movements: [{ quantity: HUEVOS, egg_type: 'fertile' }],
    })
    expect(despachoHuevo.status(), await despachoHuevo.text()).toBe(201)

    const recepcionHuevo = await registrar(request, cab, {
      lot_id: incub.lotId, farm_id: incub.farmId, house_id: incub.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ quantity: HUEVOS_RECIBIDOS, egg_type: 'fertile' }],
    })
    expect(recepcionHuevo.status(), await recepcionHuevo.text()).toBe(201)

    // ── Paso 3-4 · el EggBatch existe, une lotes DISTINTOS y guarda ambas cantidades ──
    // `R-68`: lectura inmediata, sin esperas.
    const desdeRepro = await arbol(request, cab, repro.lotId)
    expect(desdeRepro.egg_batches_sent.length, 'no se creó el vínculo de huevo').toBe(1)
    const lote_huevo = desdeRepro.egg_batches_sent[0]

    expect(lote_huevo.source_lot_id).toBe(repro.lotId)
    expect(lote_huevo.hatchery_lot_id).toBe(incub.lotId)
    expect(lote_huevo.source_lot_id).not.toBe(lote_huevo.hatchery_lot_id)   // RC-04
    expect(lote_huevo.quantity_dispatched).toBe(HUEVOS)
    expect(lote_huevo.quantity_received, 'la recepción no completó el vínculo')
      .toBe(HUEVOS_RECIBIDOS)
    expect(String(lote_huevo.dispatch_date).slice(0, 10)).toBe(hoy())
    expect(String(lote_huevo.reception_date).slice(0, 10)).toBe(hoy())

    // ── Pasos 5-6 · pollito: incubadora → engorde ──
    const despachoPollito = await registrar(request, cab, {
      lot_id: incub.lotId, farm_id: incub.farmId, house_id: incub.houseId,
      event_type: 'chick_dispatch', event_date: hoy(),
      destination_farm_id: engorde.farmId,
      bird_movements: [{ sex: 'mixed', quantity: POLLITOS }],
    })
    expect(despachoPollito.status(), await despachoPollito.text()).toBe(201)

    const recepcionPollito = await registrar(request, cab, {
      lot_id: engorde.lotId, farm_id: engorde.farmId, house_id: engorde.houseId,
      event_type: 'bird_reception', event_date: hoy(),
      bird_movements: [{ sex: 'mixed', quantity: POLLITOS_RECIBIDOS }],
    })
    expect(recepcionPollito.status(), await recepcionPollito.text()).toBe(201)

    // ── Paso 7 · el ChickBatch enlaza hacia atrás con la generación anterior ──
    const desdeIncub = await arbol(request, cab, incub.lotId)
    expect(desdeIncub.chick_batches_sent.length, 'no se creó el vínculo de pollito').toBe(1)
    const lote_pollito = desdeIncub.chick_batches_sent[0]

    expect(lote_pollito.hatchery_lot_id).toBe(incub.lotId)
    expect(lote_pollito.destination_lot_id).toBe(engorde.lotId)
    expect(lote_pollito.quantity_dispatched).toBe(POLLITOS)
    expect(lote_pollito.quantity_received).toBe(POLLITOS_RECIBIDOS)
    expect(lote_pollito.egg_batch_id, 'el pollito no referencia el lote de huevo del que salió')
      .toBe(lote_huevo.id)

    // ── Paso 8 · navegación bidireccional, que es lo que la spec exige ──
    // Desde la incubadora se ve de dónde vino y a dónde fue: es el nodo intermedio.
    expect(desdeIncub.egg_batches_received.map((b: any) => b.source_lot_id))
      .toContain(repro.lotId)
    const desdeEngorde = await arbol(request, cab, engorde.lotId)
    expect(desdeEngorde.chick_batches_received.map((b: any) => b.hatchery_lot_id))
      .toContain(incub.lotId)
  })

  // Mientras `R-78` siga abierto este negativo pasa **por el motivo equivocado** —no se crea
  // ningún vínculo en ningún caso—, así que hoy no demuestra la abstención que pretende.
  // Se conserva porque volverá a ser significativo en cuanto el positivo funcione.
  test('un despacho sin destino declarado no inventa el vínculo', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const { repro, incub } = await tresGeneraciones(request, cab)

    // Sin `destination_farm_id` no hay señal inequívoca: adivinar sería peor que abstenerse.
    const despacho = await registrar(request, cab, {
      lot_id: repro.lotId, farm_id: repro.farmId, house_id: repro.houseId,
      event_type: 'egg_dispatch', event_date: hoy(),
      egg_movements: [{ quantity: HUEVOS, egg_type: 'fertile' }],
    })
    expect(despacho.status()).toBe(201)
    const recepcion = await registrar(request, cab, {
      lot_id: incub.lotId, farm_id: incub.farmId, house_id: incub.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ quantity: HUEVOS_RECIBIDOS, egg_type: 'fertile' }],
    })
    expect(recepcion.status()).toBe(201)

    expect((await arbol(request, cab, repro.lotId)).egg_batches_sent).toHaveLength(0)
    expect((await arbol(request, cab, incub.lotId)).egg_batches_received).toHaveLength(0)
  })

  test('ningún lote queda enlazado consigo mismo', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const { repro } = await tresGeneraciones(request, cab)

    // Despacho dirigido a su **propia** granja: la coincidencia que `RC-04` temía.
    const despacho = await registrar(request, cab, {
      lot_id: repro.lotId, farm_id: repro.farmId, house_id: repro.houseId,
      event_type: 'egg_dispatch', event_date: hoy(),
      destination_farm_id: repro.farmId,
      egg_movements: [{ quantity: HUEVOS, egg_type: 'fertile' }],
    })
    expect(despacho.status()).toBe(201)

    const t = await arbol(request, cab, repro.lotId)
    for (const b of [...t.egg_batches_sent, ...t.egg_batches_received]) {
      expect(b.source_lot_id, 'un lote quedó enlazado consigo mismo').not.toBe(b.hatchery_lot_id)
    }
  })

  test('el enlace manual sigue disponible cuando el automático no es posible', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const { repro, incub } = await tresGeneraciones(request, cab)

    const manual = await request.post(`${API}/lots/egg-batches`, {
      headers: cab,
      data: {
        source_lot_id: repro.lotId, hatchery_lot_id: incub.lotId,
        quantity_dispatched: HUEVOS, dispatch_date: hoy(),
      },
    })
    expect(manual.status(), await manual.text()).toBe(201)

    const t = await arbol(request, cab, incub.lotId)
    expect(t.egg_batches_received.map((b: any) => b.source_lot_id)).toContain(repro.lotId)
  })

  test('R-60 · un vínculo no puede unir lotes de compañías distintas', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const { cabecera: otra } = await cabeceraAdminEnOtraEmpresa(request)

    const { repro, incub } = await tresGeneraciones(request, cab)
    const ajeno = await crearEscenario(request, otra, `P10X${sufijo()}`, 'hatchery')

    // CONTROL · el mismo actor, la misma llamada, dentro de una sola compañía.
    const propio = await request.post(`${API}/lots/egg-batches`, {
      headers: cab,
      data: {
        source_lot_id: repro.lotId, hatchery_lot_id: incub.lotId,
        quantity_dispatched: HUEVOS, dispatch_date: hoy(),
      },
    })
    expect(propio.status(), `CONTROL falló: ${await propio.text()}`).toBe(201)

    // TRATAMIENTO · lo único que cambia es de quién es el lote destino.
    const cruzado = await request.post(`${API}/lots/egg-batches`, {
      headers: cab,
      data: {
        source_lot_id: repro.lotId, hatchery_lot_id: ajeno.lotId,
        quantity_dispatched: HUEVOS, dispatch_date: hoy(),
      },
    })
    expect(cruzado.status(), 'se creó un vínculo entre compañías').toBe(400)
    expect((await cruzado.json()).rule).toBe('BR-07')

    // Sin efectos: el lote ajeno queda como estaba.
    const t = await arbol(request, otra, ajeno.lotId)
    expect(t.egg_batches_received).toHaveLength(0)
    expect(t.egg_batches_sent).toHaveLength(0)
  })
})
