/**
 * P-11 — ACTIVACIÓN MANUAL DE LOTES EXISTENTES   (`docs/02 §3.9`)
 *
 * El mecanismo con el que un cliente incorpora los lotes que ya tiene en marcha el día que
 * instala Global Avícola. `docs/02 §3.9` lo marca «Prioridad: Crítica (para implantación)».
 *
 * Estuvo bloqueado por dos defectos, ambos certificados ya:
 *
 *     R-67   el saldo de apertura no alimentaba el balance → el lote no admitía mortalidad
 *     R-47   la fecha de inicio se descartaba → BR-06 rechazaba todo evento retroactivo
 *
 * Las seis reglas que la spec exige (`§3.9.2`) son la cadena de este proceso:
 *
 *     1 · el lote queda marcado como activado manualmente
 *     2 · se audita quién, cuándo, con qué motivo y qué datos
 *     3 · se adjunta soporte documental
 *     4 · se evita el doble conteo
 *     5 · se puede continuar la operación desde el saldo inicial
 *     6 · se genera el reporte de apertura
 */
import { test, expect } from '@playwright/test'
import {
  API, cabeceraAdmin, cabeceraAdminEnOtraEmpresa, cabeceraAprobador, cabeceraOtraEmpresa,
  crearMaestros, empresaActiva, hoy, registrar, sufijo,
} from '../test-support/e2e-api'

/** Un lote de reproductoras a mitad de ciclo: la situación real que se incorpora. */
const DIAS_DE_VIDA = 140
const MACHOS = 1_000
const HEMBRAS = 4_000
const APERTURA = MACHOS + HEMBRAS

function haceDias(n: number): string {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - n)
  return d.toISOString().slice(0, 10)
}

async function faseInicial(request: any, cab: any): Promise<number> {
  const r = await request.get(`${API}/masters/productive-phases`, { headers: cab })
  expect(r.status()).toBe(200)
  const fases = await r.json()
  const inicial = fases.find((f: any) => f.is_initial) ?? fases[0]
  if (inicial) return inicial.id
  const creada = await request.post(`${API}/masters/productive-phases`, {
    headers: cab,
    data: { name: `P11-Cría-${sufijo()}`, code: `P11-${sufijo()}`, order: 1, duration_days: 140, is_initial: true },
  })
  expect(creada.status(), await creada.text()).toBe(201)
  return (await creada.json()).id
}

/** Lote incorporado: alta hoy, ciclo iniciado hace meses. */
async function crearLoteHistorico(request: any, cab: any, prefijo: string) {
  const companyId = empresaActiva(cab)
  const s = sufijo()
  const granja = await request.post(`${API}/masters/farms`, {
    headers: cab,
    data: { company_id: companyId, name: `${prefijo}-granja-${s}`, code: `${prefijo}-G-${s}`, farm_type: 'breeding' },
  })
  expect(granja.status(), await granja.text()).toBe(201)
  const farmId = (await granja.json()).id

  const galpon = await request.post(`${API}/masters/houses`, {
    headers: cab, data: { farm_id: farmId, name: `${prefijo}-galpon-${s}`, capacity: 50_000 },
  })
  expect(galpon.status(), await galpon.text()).toBe(201)
  const houseId = (await galpon.json()).id

  const lote = await request.post(`${API}/lots`, {
    headers: cab,
    data: {
      company_id: companyId, farm_id: farmId, house_id: houseId,
      lot_code: `${prefijo}-LOTE-${s}`, bird_type: 'breeder', sex: 'mixed',
      start_date: haceDias(DIAS_DE_VIDA),
    },
  })
  expect(lote.status(), await lote.text()).toBe(201)
  return { companyId, farmId, houseId, lotId: (await lote.json()).id, lote: await lote.json() }
}

async function activar(request: any, cab: any, lotId: number, faseId: number, extra: any = {}) {
  return await request.post(`${API}/lots/activate-manual`, {
    headers: cab,
    data: {
      lot_id: lotId, activation_date: haceDias(DIAS_DE_VIDA), phase_at_activation_id: faseId,
      initial_male_count: MACHOS, initial_female_count: HEMBRAS,
      activation_reason: 'Lote existente antes de la implantación del sistema',
      support_document_url: 'https://ejemplo.invalid/soporte.pdf',
      ...extra,
    },
  })
}

test.describe('P-11 · Activación manual de lotes existentes', () => {
  test('CADENA COMPLETA · las seis reglas del proceso', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const fase = await faseInicial(request, cab)
    const esc = await crearLoteHistorico(request, cab, 'P11')
    const m = await crearMaestros(request, cab, 'P11')

    // TEMPORALIDAD · el lote representa uno ya en marcha, no uno recién iniciado (`R-47`).
    const antes = await (await request.get(`${API}/lots/${esc.lotId}`, { headers: cab })).json()
    expect(antes.start_date.slice(0, 10), 'el inicio del ciclo es histórico').toBe(haceDias(DIAS_DE_VIDA))
    expect(antes.created_at.slice(0, 10), 'el alta en el software es hoy').toBe(hoy())
    expect(antes.start_date.slice(0, 10)).not.toBe(antes.created_at.slice(0, 10))

    const activacion = await activar(request, cab, esc.lotId, fase, {
      accumulated_mortality_male: 60, accumulated_mortality_female: 140,
      accumulated_culls_male: 20, accumulated_culls_female: 30,
    })
    expect(activacion.status(), await activacion.text()).toBe(201)
    const apertura = await activacion.json()

    // REGLA 1 · el lote queda marcado como activado manualmente.
    const lote = await (await request.get(`${API}/lots/${esc.lotId}`, { headers: cab })).json()
    expect(lote.activation_type).toBe('manual')

    // REGLA 2 · auditoría: quién, cuándo, con qué motivo y qué datos.
    expect(apertura.is_manual_activation).toBe(true)
    expect(apertura.activated_by_id, 'debe constar quién activó').toBeTruthy()
    expect(apertura.activation_date.slice(0, 10)).toBe(haceDias(DIAS_DE_VIDA))
    expect(apertura.activation_reason).toBeTruthy()
    expect(apertura.initial_male_count).toBe(MACHOS)
    expect(apertura.initial_female_count).toBe(HEMBRAS)

    // REGLA 3 · soporte documental.
    expect(apertura.support_document_url, 'debe conservarse el soporte').toBeTruthy()

    // REGLA 6 · reporte de apertura consultable.
    const reporte = await request.get(`${API}/lots/${esc.lotId}/opening-balance`, { headers: cab })
    expect(reporte.status()).toBe(200)
    expect((await reporte.json()).initial_female_count).toBe(HEMBRAS)

    // REGLA 5 · se puede continuar la operación desde el saldo inicial (`R-67`), y con
    // fecha retroactiva, que es lo que `R-47` desbloqueó.
    const mortalidad = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'mortality_recording', event_date: haceDias(30),
      cause_id: m.causaMortalidadId,
      bird_movements: [{ sex: 'female', quantity: 25 }],
    })
    expect(mortalidad.status(), `la operación retroactiva debe aceptarse: ${await mortalidad.text()}`).toBe(201)

    // REGLA 4 · sin doble conteo: el histórico acumulado no se resta del saldo (`RR-08`).
    const exceso = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'mortality_recording', event_date: hoy(),
      cause_id: m.causaMortalidadId,
      bird_movements: [{ sex: 'male', quantity: APERTURA - 25 + 1 }],
    })
    expect(exceso.status(), 'el saldo debe ser 5000 − 25, ni más ni menos').toBe(400)
    expect((await exceso.json()).rule).toBe('BR-01')
    expect((await exceso.json()).detail).toContain(String(APERTURA - 25))
  })

  test('NEGATIVE PATH · un lote que ya opera no puede activarse manualmente', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const fase = await faseInicial(request, cab)
    const esc = await crearLoteHistorico(request, cab, 'P11')

    const recepcion = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'bird_reception', event_date: hoy(),
      bird_movements: [{ sex: 'mixed', quantity: 800, target_house_id: esc.houseId }],
    })
    expect(recepcion.status(), await recepcion.text()).toBe(201)

    const r = await activar(request, cab, esc.lotId, fase)
    expect(r.status(), 'activar un lote que ya opera contaría dos veces las mismas aves').toBe(409)
    expect((await r.json()).detail).toContain('dos veces')
  })

  test('NEGATIVE PATH · no se activa dos veces el mismo lote', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const fase = await faseInicial(request, cab)
    const esc = await crearLoteHistorico(request, cab, 'P11')

    expect((await activar(request, cab, esc.lotId, fase)).status()).toBe(201)
    const segunda = await activar(request, cab, esc.lotId, fase)
    expect(segunda.status()).toBe(409)
  })

  test('AUTHORIZATION · sin sesión el proceso no se alcanza', async ({ request }) => {
    const r = await request.post(`${API}/lots/activate-manual`, {
      data: { lot_id: 1, activation_date: hoy(), phase_at_activation_id: 1 },
    })
    expect(r.status()).toBe(401)
  })

  test('RBAC · un rol sin permiso de alta no puede activar', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const fase = await faseInicial(request, cab)
    const esc = await crearLoteHistorico(request, cab, 'P11')

    // CONTROL · con el rol adecuado, la misma petición se acepta.
    const permitido = await activar(request, cab, esc.lotId, fase)
    expect(permitido.status(), await permitido.text()).toBe(201)

    // TRATAMIENTO · el aprobador tiene sesión, no permiso de alta de lotes.
    const otro = await crearLoteHistorico(request, cab, 'P11')
    const aprobador = await cabeceraAprobador(request)
    const denegado = await activar(request, aprobador, otro.lotId, fase)
    expect(denegado.status()).toBe(403)
  })

  test('AISLAMIENTO · no se activa el lote de otra empresa', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const fase = await faseInicial(request, cab)
    const mio = await crearLoteHistorico(request, cab, 'P11')

    const { cabecera: adminAlla, companyId: empresaB } = await cabeceraAdminEnOtraEmpresa(request)
    const suyo = await crearLoteHistorico(request, adminAlla, 'P11B')

    // El sujeto no puede ser un Super Administrador: `activate_manual` lo exime del filtro
    // por compañía a propósito, igual que `masters/service.py:35`, así que probarlo con él
    // mediría lo contrario de lo que se busca. Se construye un usuario **acotado a la
    // empresa B y con el permiso funcional**, para que la única razón posible de una
    // denegación sea la pertenencia — la lección de `T-067-11` y de `R-72`.
    const s = sufijo()
    const rol = await request.post(`${API}/roles`, {
      headers: cab,
      data: {
        name: `P11 Operador B ${s}`,
        description: 'Rol de certificación con permiso de alta de lotes',
        permissions: [
          { module: 'lots', action: 'create' },
          { module: 'lots', action: 'read' },
          { module: 'masters', action: 'read' },
        ],
      },
    })
    expect(rol.status(), await rol.text()).toBe(201)

    const clave = `P11-Cert-${s}-Pwd`
    const usuario = await request.post(`${API}/users`, {
      headers: cab,
      data: {
        first_name: 'P11', last_name: `CertB${s}`,
        email: `p11.certb.${s}@fixtures.globalavicola.com`,
        username: `p11_certb_${s}`, password: clave,
        role_id: (await rol.json()).id, company_id: empresaB, view_type: 'web',
      },
    })
    expect(usuario.status(), await usuario.text()).toBe(201)

    const sesion = await request.post(`${API}/login`, {
      data: { username: `p11_certb_${s}`, password: clave },
    })
    expect(sesion.status(), await sesion.text()).toBe(200)
    const sujeto = { Authorization: `Bearer ${(await sesion.json()).access_token}` }
    expect(empresaActiva(sujeto), 'el sujeto debe estar en la empresa B').toBe(empresaB)

    // CONTROL · sobre el lote de SU empresa, la misma petición se acepta. Demuestra que
    // tiene el permiso y que el cuerpo es válido.
    const propio = await activar(request, sujeto, suyo.lotId, fase)
    expect(propio.status(), `control: ${await propio.text()}`).toBe(201)

    // TRATAMIENTO · sólo cambia el lote, que es de otra empresa.
    const cruzado = await activar(request, sujeto, mio.lotId, fase)
    expect(cruzado.status(), await cruzado.text()).not.toBe(201)
    expect([400, 403, 404]).toContain(cruzado.status())

    // SIDE EFFECTS · el lote ajeno sigue sin activar.
    const sinActivar = await request.get(`${API}/lots/${mio.lotId}/opening-balance`, { headers: cab })
    expect(sinActivar.status(), 'no debe existir saldo de apertura ajeno').not.toBe(200)
  })
})
