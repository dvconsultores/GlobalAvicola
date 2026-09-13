/**
 * P-05 — INCUBACIÓN   (`spec.md §4.7`)
 *
 * Recibe huevos fértiles de reproductoras (`P-04`) y produce pollitos de un día. Su cadena
 * es propia y no se deriva de los procesos de postura:
 *
 *     egg_reception_hatchery  →  incubation_load  →  ovoscopy
 *
 * con `BR-03`: no puede cargarse en incubadora más de lo recibido.
 *
 * Que `P-04` esté certificado no certifica esto (`§47`). Aquí se ejecuta con evidencia
 * propia y fixtures propios.
 */
import { test, expect } from '@playwright/test'
import {
  API, cabeceraAdmin, cabeceraAdminEnOtraEmpresa, cabeceraAprobador, cabeceraOtraEmpresa,
  crearEscenario, crearMaestros, empresaActiva, hoy, registrar, saldoEnIncubadora,
} from '../test-support/e2e-api'

const P = 'P05'

test.describe('P-05 · Incubación', () => {
  test('HAPPY PATH · recepción de huevos y carga de incubadora dentro de lo recibido', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'hatchery')

    expect(await saldoEnIncubadora(request, cab, esc.lotId), 'lote nuevo sin huevos').toBe(0)

    const recepcion = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 1000 }],
    })
    expect(recepcion.status(), await recepcion.text()).toBe(201)
    expect(await saldoEnIncubadora(request, cab, esc.lotId)).toBe(1000)

    const carga = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'incubation_load', event_date: hoy(),
      hatchery_params: [
        { quantity_loaded: 800, temperature: 37.6, humidity: 55, co2: 0.4, turning: true },
      ],
    })
    expect(carga.status(), await carga.text()).toBe(201)

    // DERIVED STATE · lo cargado sale del disponible en incubadora.
    expect(await saldoEnIncubadora(request, cab, esc.lotId)).toBe(200)

    const ovoscopia = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'ovoscopy', event_date: hoy(),
      egg_movements: [{ egg_type: 'infertile', quantity: 40 }],
    })
    expect(ovoscopia.status(), await ovoscopia.text()).toBe(201)
  })


  // La cadena documentada de la incubadora (`audit/06_PROCESS_COVERAGE.md`). No basta con
  // el tramo distintivo: `§48` prohíbe certificar por capacidad.
  test('CADENA COMPLETA · los pasos documentados de la incubadora se registran', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'hatchery')
    await crearMaestros(request, cab, P)
    const comun = { lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId, event_date: hoy() }

    const pasos: Array<[string, any]> = [
      ['hatchery_inspection', { inspection_details: [{ parameter: 'temperatura', value: '24' }] }],
      ['egg_reception_hatchery', { egg_movements: [{ egg_type: 'fertile', quantity: 1000 }] }],
      ['egg_classification', { egg_movements: [{ egg_type: 'fertile', quantity: 950, classification_date: hoy() }] }],
      ['incubation_load', { hatchery_params: [{ quantity_loaded: 900, temperature: 37.6, humidity: 55, co2: 0.4, turning: true }] }],
      ['ovoscopy', { egg_movements: [{ egg_type: 'infertile', quantity: 50 }] }],
      ['transfer_to_hatcher', { hatchery_params: [{ quantity_transferred: 850, temperature: 36.9, humidity: 65 }] }],
      // `BR-21` (`GA-REM-021-C` / `B13`): sanos + débiles explícitos (Σ ≤ nacidos).
      ['birth_registration', { bird_movements: [{ sex: 'mixed', quantity: 800 }],
                               chicks_healthy: 780, chicks_weak: 20 }],
      ['chick_dispatch', { bird_movements: [{ sex: 'mixed', quantity: 700 }] }],
    ]

    const fallidos: string[] = []
    for (const [tipo, extra] of pasos) {
      const r = await registrar(request, cab, { ...comun, event_type: tipo, ...extra })
      if (r.status() !== 201) fallidos.push(`${tipo} → ${r.status()} ${await r.text()}`)
    }
    expect(fallidos, 'todos los pasos de la cadena deben registrarse').toEqual([])

    // DERIVED STATE · 1000 recibidos − 900 cargados.
    expect(await saldoEnIncubadora(request, cab, esc.lotId)).toBe(100)
  })

  test('NEGATIVE PATH · BR-03 rechaza cargar más de lo recibido', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'hatchery')

    await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 500 }],
    })

    const exceso = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'incubation_load', event_date: hoy(),
      hatchery_params: [{ quantity_loaded: 501, temperature: 37.6, humidity: 55 }],
    })
    expect(exceso.status()).toBe(400)
    const cuerpo = await exceso.json()
    expect(cuerpo.rule).toBe('BR-03')
    expect(cuerpo.detail, 'el mensaje debe indicar lo disponible').toContain('500')

    // SIDE EFFECTS · la denegación no consume huevos.
    expect(await saldoEnIncubadora(request, cab, esc.lotId)).toBe(500)
  })

  test('VALIDATION · sin recepción previa no puede cargarse la incubadora', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'hatchery')

    const sinRecepcion = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'incubation_load', event_date: hoy(),
      hatchery_params: [{ quantity_loaded: 10, temperature: 37.6, humidity: 55 }],
    })
    expect(sinRecepcion.status()).toBe(400)
    expect((await sinRecepcion.json()).rule).toBe('BR-03')
  })

  test('AUTHORIZATION · sin sesión el proceso no se alcanza', async ({ request }) => {
    const sinSesion = await request.post(`${API}/operations`, {
      data: { event_type: 'egg_reception_hatchery', event_date: hoy(), egg_movements: [] },
    })
    expect(sinSesion.status()).toBe(401)
  })

  test('RBAC · un rol sin permiso de registro no puede recibir huevos', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'hatchery')
    const cuerpo = {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 100 }],
    }

    const permitido = await registrar(request, cab, cuerpo)
    expect(permitido.status(), await permitido.text()).toBe(201)

    const aprobador = await cabeceraAprobador(request)
    const denegado = await registrar(request, aprobador, cuerpo)
    expect(denegado.status()).toBe(403)
    expect((await denegado.json()).detail).toContain('operations:create')
  })

  test('AISLAMIENTO · el mismo registro vale en la empresa propia y no en la ajena', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const mio = await crearEscenario(request, cab, P, 'hatchery')
    await registrar(request, cab, {
      lot_id: mio.lotId, farm_id: mio.farmId, house_id: mio.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 300 }],
    })

    const { cabecera: adminAlla } = await cabeceraAdminEnOtraEmpresa(request)
    const suyo = await crearEscenario(request, adminAlla, `${P}B`, 'hatchery')
    const ajena = await cabeceraOtraEmpresa(request)
    expect(empresaActiva(ajena)).not.toBe(mio.companyId)

    // CONTROL · sobre su propio lote, el mismo cuerpo se acepta.
    const propio = await registrar(request, ajena, {
      lot_id: suyo.lotId, farm_id: suyo.farmId, house_id: suyo.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 200 }],
    })
    expect(propio.status(), `control: ${await propio.text()}`).toBe(201)

    // TRATAMIENTO · solo cambia el lote, que es de otra empresa.
    const cruzado = await registrar(request, ajena, {
      lot_id: mio.lotId, farm_id: mio.farmId, house_id: mio.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 200 }],
    })
    expect(cruzado.status(), await cruzado.text()).not.toBe(201)

    // SIDE EFFECTS · el disponible del lote ajeno no se movió.
    expect(await saldoEnIncubadora(request, cab, mio.lotId)).toBe(300)
  })

  test('AUDIT · la carga de incubadora conserva sus parámetros y su autor', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'hatchery')
    await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_reception_hatchery', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 400 }],
    })
    const r = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'incubation_load', event_date: hoy(),
      hatchery_params: [{ quantity_loaded: 300, temperature: 37.8, humidity: 56, co2: 0.5 }],
    })
    expect(r.status(), await r.text()).toBe(201)

    const detalle = await (await request.get(`${API}/operations/${(await r.json()).id}`, { headers: cab })).json()
    expect(detalle.company_id).toBe(esc.companyId)
    expect(detalle.registered_by_id).toBeTruthy()
    const params = detalle.hatchery_params ?? []
    expect(params.length, 'los parámetros de incubación deben persistir').toBeGreaterThan(0)
    expect(params[0].quantity_loaded).toBe(300)
    expect(params[0].temperature).toBeCloseTo(37.8, 1)
  })
})
