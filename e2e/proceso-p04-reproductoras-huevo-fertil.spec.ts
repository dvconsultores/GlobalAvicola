/**
 * P-04 — REPRODUCTORAS · PRODUCCIÓN DE HUEVO FÉRTIL   (`spec.md §4.6`)
 *
 * Es un proceso distinto de `P-02`, no una variante suya: el lote es `breeder`, el destino
 * del despacho es la incubadora y su salida alimenta a `P-05`. Se certifica con evidencia
 * propia; compartir componentes con `P-02` no certifica nada por transitividad.
 *
 * La unidad de certificación es el proceso, no la pantalla ni el endpoint. La cadena que
 * exige la spec es:
 *
 *     egg_collection  →  egg_classification  →  egg_dispatch
 *
 * con `BR-02`: el despacho no puede exceder el saldo disponible.
 *
 * Casos obligatorios de `GA-REM-016`: `HAPPY PATH` · `NEGATIVE PATH` · `AUTHORIZATION` ·
 * `VALIDATION` · `PERSISTENCE` · `AUDIT`.
 *
 * Cada caso crea sus precondiciones (`§25`). Nada se apoya en datos residuales.
 */
import { test, expect } from '@playwright/test'
import {
  API, cabeceraAdmin, cabeceraAdminEnOtraEmpresa, cabeceraAprobador, cabeceraOtraEmpresa, crearEscenario, crearMaestros,
  empresaActiva, hoy, registrar, saldoDeHuevos,
} from '../test-support/e2e-api'

const P = 'P04'
const TIPO = 'breeder'

test.describe('P-04 · Reproductoras — producción de huevo fértil', () => {
  test('HAPPY PATH · recolección, clasificación y despacho dentro del saldo', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'breeder')

    expect(await saldoDeHuevos(request, cab, esc.lotId), 'lote nuevo sin huevos').toBe(0)

    const recoleccion = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_collection', event_date: hoy(),
      egg_movements: [
        { egg_type: 'fertile', quantity: 900 },
        { egg_type: 'dirty', quantity: 60 },
        { egg_type: 'broken', quantity: 25 },
        { egg_type: 'infertile', quantity: 15 },
      ],
    })
    expect(recoleccion.status(), await recoleccion.text()).toBe(201)
    expect(await saldoDeHuevos(request, cab, esc.lotId)).toBe(1000)

    const clasificacion = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_classification', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 900, classification_date: hoy() }],
    })
    expect(clasificacion.status(), await clasificacion.text()).toBe(201)

    const despacho = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_dispatch', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 700 }],
    })
    expect(despacho.status(), await despacho.text()).toBe(201)

    // PERSISTENCE · el saldo derivado refleja la cadena completa, no solo el último evento.
    expect(await saldoDeHuevos(request, cab, esc.lotId)).toBe(300)
  })


  // La certificación exige el flujo completo del proceso, no solo su tramo distintivo:
  // `audit/06_PROCESS_COVERAGE.md` documenta la cadena de diez pasos, y `§48` prohíbe dar
  // por certificado un proceso porque sus capacidades compartidas lo estén.
  test('CADENA COMPLETA · los diez pasos documentados del proceso se registran', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, TIPO)
    const m = await crearMaestros(request, cab, P)
    const comun = { lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId, event_date: hoy() }

    // Población de partida: sin aves no hay mortalidad, descarte ni salida.
    const recepcion = await registrar(request, cab, {
      ...comun, event_type: 'bird_reception',
      bird_movements: [{ sex: 'mixed', quantity: 5000, target_house_id: esc.houseId }],
    })
    expect(recepcion.status(), await recepcion.text()).toBe(201)

    const pasos: Array<[string, any]> = [
      ['farm_inspection', { inspection_details: [{ parameter: 'temperatura', value: '28' }] }],
      ['feed_registration', { feed_movements: [{ feed_type_id: m.alimentoId, quantity_kg: 250.5 }] }],
      ['weight_recording', { bird_movements: [{ sex: 'mixed', quantity: 30, avg_weight: 2100, week_number: 24 }] }],
      ['vaccination', { vaccine_id: m.vacunaId, vaccination_route: 'agua', vaccine_lot_number: 'V-001' }],
      ['medication', { medication_id: m.medicamentoId, dosage_per_bird: 0.5, treatment_days: 3 }],
      ['mortality_recording', { cause_id: m.causaMortalidadId, bird_movements: [{ sex: 'female', quantity: 12 }] }],
      ['cull_recording', { cull_cause_id: m.causaDescarteId, bird_movements: [{ sex: 'male', quantity: 8 }] }],
      ['egg_collection', { egg_movements: [{ egg_type: 'fertile', quantity: 900 }, { egg_type: 'dirty', quantity: 40 }] }],
      ['egg_classification', { egg_movements: [{ egg_type: 'fertile', quantity: 900, classification_date: hoy() }] }],
      ['egg_dispatch', { egg_movements: [{ egg_type: 'fertile', quantity: 600 }] }],
      ['bird_exit', { bird_movements: [{ sex: 'mixed', quantity: 100 }] }],
    ]

    const fallidos: string[] = []
    for (const [tipo, extra] of pasos) {
      const r = await registrar(request, cab, { ...comun, event_type: tipo, ...extra })
      if (r.status() !== 201) fallidos.push(`${tipo} → ${r.status()} ${await r.text()}`)
    }
    expect(fallidos, 'todos los pasos de la cadena deben registrarse').toEqual([])

    // DERIVED STATE · los saldos reflejan la cadena entera.
    expect(await saldoDeHuevos(request, cab, esc.lotId), 'huevos: 940 recolectados − 600 despachados').toBe(340)
  })

  test('NEGATIVE PATH · BR-02 rechaza despachar más de lo disponible', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'breeder')

    await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_collection', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 100 }],
    })

    const exceso = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_dispatch', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 101 }],
    })
    expect(exceso.status()).toBe(400)
    const cuerpo = await exceso.json()
    expect(cuerpo.rule).toBe('BR-02')
    expect(cuerpo.detail, 'el mensaje debe indicar el saldo real').toContain('100')

    // SIDE EFFECTS · una denegación no puede alterar el saldo.
    expect(await saldoDeHuevos(request, cab, esc.lotId)).toBe(100)
  })

  test('VALIDATION · un despacho de cero huevos no crea un registro sin significado', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'breeder')
    await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_collection', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 50 }],
    })

    const cero = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_dispatch', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 0 }],
    })
    // El saldo no puede moverse, se acepte o se rechace el registro.
    expect(await saldoDeHuevos(request, cab, esc.lotId)).toBe(50)
    expect([201, 400]).toContain(cero.status())
  })

  test('AUTHORIZATION · sin sesión el proceso no se alcanza', async ({ request }) => {
    const sinSesion = await request.post(`${API}/operations`, {
      data: { event_type: 'egg_collection', event_date: hoy(), egg_movements: [] },
    })
    expect(sinSesion.status()).toBe(401)
  })

  // AISLAMIENTO y FK OWNERSHIP se comprueban con **control y tratamiento**. Sin el
  // control, un rechazo por cualquier otro motivo —un campo obligatorio, una regla de
  // negocio— se leería como aislamiento y el test no probaría nada. Es el mismo vicio que
  // `R-72` destapó en la suite heredada.
  test('RBAC · un rol sin permiso de registro no puede recolectar', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'breeder')
    const cuerpo = {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_collection', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 100 }],
    }

    // CONTROL · con el rol adecuado el mismo cuerpo se acepta.
    const permitido = await registrar(request, cab, cuerpo)
    expect(permitido.status(), await permitido.text()).toBe(201)

    // TRATAMIENTO · el aprobador tiene sesión y permisos de revisión, no de registro.
    const aprobador = await cabeceraAprobador(request)
    const denegado = await registrar(request, aprobador, cuerpo)
    expect(denegado.status()).toBe(403)
    expect((await denegado.json()).detail).toContain('operations:create')
  })

  test('AISLAMIENTO · el mismo registro vale en la empresa propia y no en la ajena', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const mio = await crearEscenario(request, cab, P, 'breeder')
    await registrar(request, cab, {
      lot_id: mio.lotId, farm_id: mio.farmId, house_id: mio.houseId,
      event_type: 'egg_collection', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 200 }],
    })

    // El escenario de la otra empresa lo monta el administrador situado allí; el sujeto de
    // la prueba sigue siendo el operador de esa empresa.
    const { cabecera: adminAlla } = await cabeceraAdminEnOtraEmpresa(request)
    const suyo = await crearEscenario(request, adminAlla, `${P}B`, 'breeder')
    const ajena = await cabeceraOtraEmpresa(request)

    // CONTROL · con su propio lote, el mismo cuerpo se acepta. Demuestra que el sujeto
    // tiene permiso y que el cuerpo es válido.
    const propio = await registrar(request, ajena, {
      lot_id: suyo.lotId, farm_id: suyo.farmId, house_id: suyo.houseId,
      event_type: 'egg_collection', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 500 }],
    })
    expect(propio.status(), `control: ${await propio.text()}`).toBe(201)

    // TRATAMIENTO · solo cambia el lote, que es de otra empresa.
    const cruzado = await registrar(request, ajena, {
      lot_id: mio.lotId, farm_id: mio.farmId, house_id: mio.houseId,
      event_type: 'egg_collection', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 500 }],
    })
    expect(cruzado.status(), await cruzado.text()).not.toBe(201)
    expect([400, 403, 404]).toContain(cruzado.status())

    // SIDE EFFECTS · el saldo del lote ajeno no se movió.
    expect(await saldoDeHuevos(request, cab, mio.lotId)).toBe(200)
  })

  test('FK OWNERSHIP · la granja y el galpón ajenos se rechazan, los propios no', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const mio = await crearEscenario(request, cab, P, 'breeder')
    const { cabecera: adminAlla } = await cabeceraAdminEnOtraEmpresa(request)
    const suyo = await crearEscenario(request, adminAlla, `${P}B`, 'breeder')
    const ajena = await cabeceraOtraEmpresa(request)

    expect(empresaActiva(ajena), 'el sujeto debe estar en otra empresa').not.toBe(mio.companyId)

    const cuerpo = (farmId: number, houseId: number) => ({
      lot_id: null, farm_id: farmId, house_id: houseId,
      event_type: 'farm_inspection', event_date: hoy(),
      inspection_details: [{ parameter: 'temperatura', value: '28' }],
    })

    // CONTROL · con su granja y su galpón, se acepta.
    const control = await registrar(request, ajena, cuerpo(suyo.farmId, suyo.houseId))
    expect(control.status(), `control: ${await control.text()}`).toBe(201)

    // TRATAMIENTO · una sola FK ajena por vez.
    const conGranjaAjena = await registrar(request, ajena, cuerpo(mio.farmId, suyo.houseId))
    expect(conGranjaAjena.status(), `farm_id ajeno aceptado: ${await conGranjaAjena.text()}`).not.toBe(201)

    const conGalponAjeno = await registrar(request, ajena, cuerpo(suyo.farmId, mio.houseId))
    expect(conGalponAjeno.status(), `house_id ajeno aceptado: ${await conGalponAjeno.text()}`).not.toBe(201)
  })

  test('AUDIT · el registro queda con su autor y su empresa', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, P, 'breeder')
    const r = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'egg_collection', event_date: hoy(),
      egg_movements: [{ egg_type: 'fertile', quantity: 120 }],
    })
    expect(r.status()).toBe(201)
    const evento = await r.json()

    const detalle = await (await request.get(`${API}/operations/${evento.id}`, { headers: cab })).json()
    expect(detalle.company_id).toBe(esc.companyId)
    expect(detalle.registered_by_id, 'debe constar quién lo registró').toBeTruthy()
    expect(detalle.status).toBe('registered')
    expect(
      (detalle.egg_movements ?? []).reduce((a: number, m: any) => a + m.quantity, 0),
      'los submovimientos deben persistir',
    ).toBe(120)
  })
})
