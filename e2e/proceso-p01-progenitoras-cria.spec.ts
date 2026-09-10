/**
 * P-01 — PROGENITORAS · CRÍA   (`spec.md §4.4`)
 *
 * La cadena de la fase de cría de un lote de abuelas, desde la importación hasta la salida.
 * Las operaciones de huevo pertenecen a `P-02` —Producción—, ya certificado.
 *
 * Estuvo bloqueado por `GA-TD-014`: la orden de compra se guardaba en `extra_data` y el
 * campo tipado quedaba nulo, de modo que `BR-18` nunca se aplicaba. `OD-04`, resuelta por el
 * propietario, permitió activarlo: **una misma OC puede recibirse en varias entregas
 * parciales**, y la protección es la cantidad acumulada.
 *
 * `§4.4` **no** exige alertas por desviación —eso es `§4.5`, y por eso `GA-REQ-037` bloquea
 * a `P-03` pero no a este proceso—.
 */
import { test, expect } from '@playwright/test'
import {
  API, cabeceraAdmin, crearEscenario, crearMaestros, hoy, registrar, sufijo,
} from '../test-support/e2e-api'

const ORDENADO = 5_000
const PRIMERA = 3_000
const SEGUNDA = 2_000

async function ordenDeCompra(request: any, cab: any, cantidad = ORDENADO) {
  const codigo = `P01-OC-${sufijo().toUpperCase()}`
  const r = await request.post(`${API}/sap/references/import`, {
    headers: cab,
    data: { references: [{ ref_type: 'purchase_order', sap_code: codigo, quantity: cantidad }] },
  })
  expect(r.status(), await r.text()).toBe(201)
  return codigo
}

test.describe('P-01 · cadena de cría de progenitoras', () => {
  test('la cadena completa se recorre de la importación a la salida', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P01${sufijo()}`, 'grandparent')
    const m = await crearMaestros(request, cab, 'P01')
    const oc = await ordenDeCompra(request, cab)
    const base = { lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId, event_date: hoy() }

    const pasos: [string, any][] = [
      // `GA-REM-042` (`R-152`, `BR-22`): la importación lleva el plan de `docs/02 §3.4.1`; embarcada = recibida + mortalidad en traslado;
      // recibida = ♂ + ♀; proveedor y transporte de la empresa (`crearMaestros`). Runtime E2E: `BLOCKED_RUNTIME` (`R-164`).
      ['grandparent_import', { sap_document_ref: oc, supplier_id: m.proveedorId, transport_id: m.transporteId,
        bird_movements: [{ sex: 'male', quantity: 40 }, { sex: 'female', quantity: 60 }],
        extra_data: { import_plan: { origin_country: 'Francia', purchased_total: 110, shipped_total: 105, received_total: 100, transit_mortality: 5,
          departure_date: hoy(), arrival_date: hoy(), reception_condition: 'buena', quarantine_days: 21, initial_health_inspection: 'sin hallazgos' } } }],
      ['farm_inspection', { inspection_details: [{ parameter: 'Bioseguridad', value: 'ok', status: 'ok' }] }],
      ['transport_inspection', { inspection_details: [{ parameter: 'Higiene', value: 'ok', status: 'ok' }] }],
      ['bird_reception', { sap_document_ref: oc, bird_movements: [{ sex: 'mixed', quantity: PRIMERA }] }],
      ['bird_distribution', { bird_movements: [{ sex: 'mixed', quantity: PRIMERA }] }],
      ['feed_registration', { feed_movements: [{ quantity_kg: 420.5, feed_type_id: m.alimentoId }] }],
      ['weight_recording', { bird_movements: [{ sex: 'mixed', quantity: 100, avg_weight: 1800 }] }],
      ['mortality_recording', { bird_movements: [{ sex: 'mixed', quantity: 12, mortality_cause_id: m.causaMortalidadId }] }],
      ['cull_recording', { bird_movements: [{ sex: 'mixed', quantity: 5, cull_cause_id: m.causaDescarteId }] }],
      ['vaccination', { vaccine_id: m.vacunaId }],
      ['medication', { medication_id: m.medicamentoId }],
      ['bird_exit', { bird_movements: [{ sex: 'mixed', quantity: 200 }] }],
    ]

    for (const [tipo, extra] of pasos) {
      const r = await registrar(request, cab, { ...base, event_type: tipo, ...extra })
      expect(r.status(), `${tipo}: ${await r.text()}`).toBe(201)
    }

    // Los doce pasos quedan registrados y son consultables. Se comprueba el **conjunto
    // exacto** de tipos: un recuento aproximado pasaría aunque faltara un paso.
    const lista = await request.get(`${API}/operations?lot_id=${esc.lotId}&limit=100`, { headers: cab })
    expect(lista.status(), await lista.text()).toBe(200)
    const cuerpo = await lista.json()
    const eventos = Array.isArray(cuerpo) ? cuerpo : cuerpo.events
    const tipos = [...new Set(eventos.map((e: any) => e.event_type))].sort()
    expect(tipos).toEqual(pasos.map(([t]) => t).sort())
  })

  test('OD-04 · la orden de compra admite entregas parciales y frena el exceso', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P01OC${sufijo()}`, 'grandparent')
    const oc = await ordenDeCompra(request, cab)
    const base = {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_date: hoy(), event_type: 'bird_reception', sap_document_ref: oc,
    }

    // Primera parcial.
    const uno = await registrar(request, cab, { ...base, bird_movements: [{ sex: 'mixed', quantity: PRIMERA }] })
    expect(uno.status(), await uno.text()).toBe(201)

    // Segunda parcial contra la **misma** orden: la decisión del propietario en acción.
    const dos = await registrar(request, cab, { ...base, bird_movements: [{ sex: 'mixed', quantity: SEGUNDA }] })
    expect(dos.status(), `OD-04: la segunda parcial debe aceptarse — ${await dos.text()}`).toBe(201)

    // El acumulado ya iguala lo ordenado: una sola ave más sobra.
    const tres = await registrar(request, cab, { ...base, bird_movements: [{ sex: 'mixed', quantity: 1 }] })
    expect(tres.status(), 'sin tolerancia: el exceso se rechaza').toBe(400)
    expect((await tres.json()).rule).toBe('BR-18')
    // El motivo es la cantidad, no la repetición de la referencia.
    expect((await tres.json()).detail.toLowerCase()).not.toContain('duplic')
  })

  test('la referencia de la orden queda en el campo tipado', async ({ request }) => {
    // `GA-TD-014`. Sin esto el comparativo SAP salía vacío y `BR-18` era inaplicable.
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P01T${sufijo()}`, 'grandparent')
    const oc = await ordenDeCompra(request, cab)

    const r = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'bird_reception', event_date: hoy(), sap_document_ref: oc,
      bird_movements: [{ sex: 'mixed', quantity: 100 }],
    })
    expect(r.status()).toBe(201)
    expect((await r.json()).sap_document_ref,
      'la orden debe viajar al campo tipado, no solo a extra_data').toBe(oc)
  })
})
