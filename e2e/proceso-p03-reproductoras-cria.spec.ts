/**
 * P-03 — REPRODUCTORAS · CRÍA   (`spec.md §4.4` + `§4.5`)
 *
 * La cadena de cría de un lote de reproductoras. Es la de `P-01` sin la importación de
 * abuelas —`audit/06_PROCESS_COVERAGE.md`: «idéntico a P-01 sin `grandparent_import`»—,
 * más lo que separaba a este proceso de aquél: **§4.5, la alerta por desviación de peso**.
 *
 * Ese era el bloqueo. `GA-REQ-037` exigía avisar cuando el peso se sale del estándar, y el
 * estándar no existía en ninguna parte del producto: ni tabla, ni versión, ni referencia
 * desde el lote. `OD-06` lo resolvió —Global Avícola administra curvas configurables por
 * línea genética, versionadas, sin tolerancia global— y `GA-REM-037` lo implementa.
 *
 * La curva de este escenario es artificial y se elige con números redondos para que el
 * rango a los 15 días sea comprobable a mano: interpolando (10 → 90/110) y (20 → 180/220)
 * se obtiene exactamente [135, 165]. No es la tabla de ningún proveedor real, y ninguna
 * curva se siembra en el producto.
 */
import { test, expect } from '@playwright/test'
import {
  API, cabeceraAdmin, crearMaestros, hoy, registrar, sufijo,
} from '../test-support/e2e-api'

const ORDENADO = 5_000
const PRIMERA = 3_000

/** Edad del lote al pesarlo. La curva no trae ese día: sale de interpolar 10 y 20. */
const EDAD_AL_PESAR = 15
const MINIMO_A_LOS_15 = 135
const MAXIMO_A_LOS_15 = 165

const TABLA = [
  { age_days: 10, min_weight: 90, target_weight: 100, max_weight: 110 },
  { age_days: 20, min_weight: 180, target_weight: 200, max_weight: 220 },
]

function haceDias(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toLocaleDateString('sv-SE')
}

async function post(request: any, cab: any, ruta: string, data: any) {
  const r = await request.post(`${API}${ruta}`, { headers: cab, data })
  expect(r.status(), `${ruta}: ${await r.text()}`).toBe(201)
  return await r.json()
}

function empresaDe(cab: any): number {
  const carga = JSON.parse(Buffer.from(cab.Authorization.split('.')[1], 'base64').toString())
  return carga.company_id
}

/** Granja, galpón, línea genética con curva activa, y un lote de `EDAD_AL_PESAR` días. */
async function escenarioConCurva(request: any, cab: any, prefijo: string, conCurva = true) {
  const s = sufijo()
  const companyId = empresaDe(cab)

  const granja = await post(request, cab, '/masters/farms', {
    company_id: companyId, name: `${prefijo}-granja-${s}`, code: `${prefijo}-G-${s}`,
    location: 'Escenario de certificación', farm_type: 'breeding',
  })
  const galpon = await post(request, cab, '/masters/houses', {
    farm_id: granja.id, name: `${prefijo}-galpon-${s}`, capacity: 50_000,
  })
  const linea = await post(request, cab, '/masters/genetic-lines', {
    company_id: companyId, name: `${prefijo}-linea-${s}`,
  })

  let curva: any = null
  if (conCurva) {
    curva = await post(request, cab, '/masters/weight-curves', {
      genetic_line_id: linea.id, version_label: `${prefijo}-2024`,
      is_active: true, points: TABLA,
    })
  }

  const lote = await post(request, cab, '/lots', {
    company_id: companyId, farm_id: granja.id, house_id: galpon.id,
    lot_code: `${prefijo}-LOTE-${s}`, bird_type: 'breeder', sex: 'mixed',
    genetic_line_id: linea.id, start_date: haceDias(EDAD_AL_PESAR),
  })

  return {
    companyId, farmId: granja.id, houseId: galpon.id,
    lineaId: linea.id, curvaId: curva?.id ?? null, lotId: lote.id, lote,
  }
}

async function ordenDeCompra(request: any, cab: any, cantidad = ORDENADO) {
  const codigo = `P03-OC-${sufijo().toUpperCase()}`
  const r = await request.post(`${API}/sap/references/import`, {
    headers: cab,
    data: { references: [{ ref_type: 'purchase_order', sap_code: codigo, quantity: cantidad }] },
  })
  expect(r.status(), await r.text()).toBe(201)
  return codigo
}

/** Alertas del lote atribuidas a un evento concreto. `GET /operations/alerts` (`R-38`). */
async function alertasDe(request: any, cab: any, lotId: number, eventId: number) {
  const r = await request.get(`${API}/operations/alerts?lot_id=${lotId}&limit=200`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  return (await r.json()).filter((a: any) => a.event_id === eventId)
}

test.describe('P-03 · cadena de cría de reproductoras', () => {
  test('la cadena completa se recorre de la inspección a la salida', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await escenarioConCurva(request, cab, 'P03')
    const m = await crearMaestros(request, cab, 'P03')
    const oc = await ordenDeCompra(request, cab)
    const base = { lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId, event_date: hoy() }

    const pasos: [string, any][] = [
      ['farm_inspection', { inspection_details: [{ parameter: 'Bioseguridad', value: 'ok', status: 'ok' }] }],
      ['transport_inspection', { inspection_details: [{ parameter: 'Higiene', value: 'ok', status: 'ok' }] }],
      ['bird_reception', { sap_document_ref: oc, bird_movements: [{ sex: 'mixed', quantity: PRIMERA }] }],
      ['bird_distribution', { bird_movements: [{ sex: 'mixed', quantity: PRIMERA }] }],
      ['feed_registration', { feed_movements: [{ quantity_kg: 380.0, feed_type_id: m.alimentoId }] }],
      // Dentro de norma: la cadena no debe generar alerta por sí misma.
      ['weight_recording', { bird_movements: [{ sex: 'mixed', quantity: 100, avg_weight: 150 }] }],
      ['mortality_recording', { bird_movements: [{ sex: 'mixed', quantity: 9, mortality_cause_id: m.causaMortalidadId }] }],
      ['cull_recording', { bird_movements: [{ sex: 'mixed', quantity: 4, cull_cause_id: m.causaDescarteId }] }],
      ['vaccination', { vaccine_id: m.vacunaId }],
      ['medication', { medication_id: m.medicamentoId }],
      ['bird_exit', { bird_movements: [{ sex: 'mixed', quantity: 150 }] }],
    ]

    for (const [tipo, extra] of pasos) {
      const r = await registrar(request, cab, { ...base, event_type: tipo, ...extra })
      expect(r.status(), `${tipo}: ${await r.text()}`).toBe(201)
    }

    // Se comprueba el **conjunto exacto** de tipos: un recuento aproximado pasaría aunque
    // faltara un paso de la cadena.
    const lista = await request.get(`${API}/operations?lot_id=${esc.lotId}&limit=100`, { headers: cab })
    expect(lista.status(), await lista.text()).toBe(200)
    const cuerpo = await lista.json()
    const eventos = Array.isArray(cuerpo) ? cuerpo : cuerpo.events
    const tipos = [...new Set(eventos.map((e: any) => e.event_type))].sort()
    expect(tipos).toEqual(pasos.map(([t]) => t).sort())
  })

  test('§4.5 · el peso fuera de la curva estándar levanta alerta', async ({ request }) => {
    // El bloqueo histórico de `P-03`. `GA-REQ-037` / `OD-06` / `GA-REM-037`.
    const cab = await cabeceraAdmin(request)
    const esc = await escenarioConCurva(request, cab, 'P03A')
    const base = {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_date: hoy(), event_type: 'weight_recording',
    }

    // CONTROL · el mismo pesaje, dentro del rango interpolado, no alerta.
    const dentro = await registrar(request, cab, {
      ...base, bird_movements: [{ sex: 'mixed', quantity: 100, avg_weight: 150 }],
    })
    expect(dentro.status(), await dentro.text()).toBe(201)
    expect(await alertasDe(request, cab, esc.lotId, (await dentro.json()).id)).toEqual([])

    // TRATAMIENTO · por debajo del mínimo interpolado.
    const fuera = await registrar(request, cab, {
      ...base, bird_movements: [{ sex: 'mixed', quantity: 100, avg_weight: 100 }],
    })
    expect(fuera.status(), await fuera.text()).toBe(201)
    const alertas = await alertasDe(request, cab, esc.lotId, (await fuera.json()).id)
    expect(alertas.length, 'un peso bajo norma debe avisar').toBe(1)
    expect(alertas[0].alert_type).toBe('weight_deviation')
    // El umbral citado es el **interpolado**, que no está en la tabla: prueba de que se
    // evaluó contra la curva y no contra un número fijo.
    expect(alertas[0].threshold_value).toBe(MINIMO_A_LOS_15)
    expect(alertas[0].actual_value).toBe(100)
  })

  test('§4.5 · el borde superior está dentro de norma y el exceso no', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await escenarioConCurva(request, cab, 'P03B')
    const base = {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_date: hoy(), event_type: 'weight_recording',
    }

    // CONTROL · el máximo exacto. `OD-06` no admite tolerancia porcentual en ningún sentido:
    // el límite es el de la tabla, y es inclusivo.
    const borde = await registrar(request, cab, {
      ...base, bird_movements: [{ sex: 'mixed', quantity: 50, avg_weight: MAXIMO_A_LOS_15 }],
    })
    expect(borde.status(), await borde.text()).toBe(201)
    expect(await alertasDe(request, cab, esc.lotId, (await borde.json()).id)).toEqual([])

    // TRATAMIENTO · un gramo más.
    const excedido = await registrar(request, cab, {
      ...base, bird_movements: [{ sex: 'mixed', quantity: 50, avg_weight: MAXIMO_A_LOS_15 + 1 }],
    })
    expect(excedido.status(), await excedido.text()).toBe(201)
    const alertas = await alertasDe(request, cab, esc.lotId, (await excedido.json()).id)
    expect(alertas.length, 'un gramo por encima del máximo debe avisar').toBe(1)
    expect(alertas[0].threshold_value).toBe(MAXIMO_A_LOS_15)
  })

  test('§4.5 · sin curva cargada no se inventa ningún umbral', async ({ request }) => {
    // `OD-06`: «no inventar ±5%/±10%/±20% como tolerancia global». Sin tabla no hay
    // referencia, y la ausencia de referencia se declara callando, no adivinando.
    const cab = await cabeceraAdmin(request)
    const esc = await escenarioConCurva(request, cab, 'P03C', false)
    expect(esc.lote.weight_curve_id, 'sin curva activa el lote no debe recibir ninguna').toBeNull()

    const r = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_date: hoy(), event_type: 'weight_recording',
      bird_movements: [{ sex: 'mixed', quantity: 100, avg_weight: 5 }],
    })
    expect(r.status(), await r.text()).toBe(201)
    expect(await alertasDe(request, cab, esc.lotId, (await r.json()).id)).toEqual([])
  })

  test('el lote conserva la versión de curva con la que nació', async ({ request }) => {
    // `AC08` / `AC23`. Publicar una revisión no puede reescribir la referencia contra la
    // que ya se juzgó a un lote, o los veredictos emitidos dejan de ser reproducibles.
    const cab = await cabeceraAdmin(request)
    const esc = await escenarioConCurva(request, cab, 'P03V')

    await post(request, cab, '/masters/weight-curves', {
      genetic_line_id: esc.lineaId, version_label: `P03V-2025-${sufijo()}`,
      is_active: true,
      points: [
        { age_days: 10, min_weight: 900, max_weight: 1100 },
        { age_days: 20, min_weight: 1800, max_weight: 2200 },
      ],
    })

    const r = await request.get(`${API}/lots/${esc.lotId}`, { headers: cab })
    expect(r.status(), await r.text()).toBe(200)
    expect((await r.json()).weight_curve_id,
      'activar una curva nueva reescribió la referencia de un lote existente').toBe(esc.curvaId)

    // Y la evaluación sigue usando la vieja: 150 g es normal en la de 2024 y estaría muy
    // por debajo de la de 2025. Que no alerte demuestra qué versión se consultó.
    const pesaje = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_date: hoy(), event_type: 'weight_recording',
      bird_movements: [{ sex: 'mixed', quantity: 100, avg_weight: 150 }],
    })
    expect(pesaje.status(), await pesaje.text()).toBe(201)
    expect(await alertasDe(request, cab, esc.lotId, (await pesaje.json()).id)).toEqual([])
  })
})
