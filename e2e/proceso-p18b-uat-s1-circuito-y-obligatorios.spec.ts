/**
 * `GA-UAT-BREEDER-CRIA-S1-2026-11-10` · spec `015` §4 — E2E P18B.
 *
 * Matriz de obligatorios por operación y circuito Reproductoras/Cría: qué dato exige cada
 * evento (`BR-08`, `BR-01`, `B05`, `RR-20`..`RR-23`, `BR-20`), qué persiste, cómo se revisa,
 * qué deja en auditoría y cómo se comporta el saldo (`D4`: por total de aves, no por sexo).
 *
 * Escenario propio (`crearEscenario`): granja, galpón y lote breeder nuevos, más los catálogos
 * que la cadena necesita. Un negativo que el producto acepte no detiene el recorrido: se
 * acumula en `fallos` y el último caso deja el rojo con la lista completa — así una operación
 * que no cumple el contrato no oculta la evidencia de las demás (se escribe siempre).
 */
import { test, expect, type APIRequestContext } from '@playwright/test'
import * as fs from 'node:fs'
import {
  API, LOTE_DE_VACUNA, hoy, cabeceraAdmin, cabeceraAprobador, crearEscenario, crearMaestros, registrar,
  type Escenario, type Maestros,
} from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

const PREFIJO = 'S1P18B'
const DIR = 'audit/ga-uat-breeder-cria-s1-2026-11-10/evidence'
const CAPTURAS = `${DIR}/screenshots`

test.describe.configure({ mode: 'serial' })

let admin: any
let operador: any
let aprobador: any
let esc: Escenario
let maestros: Maestros
let casos: Caso[] = []

/** Ids de los 201 de la matriz, por tipo de evento (la parte 2 los recorre). */
const creados: Record<string, number> = {}
/** Discrepancias de contrato: el último caso las convierte en el rojo, todas juntas. */
const fallos: string[] = []
/** Observaciones que no son defecto (p. ej. un 422 de pydantic en inglés). */
const observaciones: string[] = []
/** Contrato por operación, tal como lo exige el §4 del spec (servidor y cliente). */
interface Caso {
  tipo: string
  nombre: string
  /** Datos sin los cuales el evento no dice nada (para la evidencia). */
  contrato: string[]
  /** Payload mínimo válido, además de lote/tipo/fecha y —si aplica— granja y galpón. */
  minimo: any
  /** `BR-08`: el evento exige granja y galpón. */
  ubicacion: boolean
  /** «Vacío»: solo lote, tipo y fecha (+ ubicación cuando se declara). */
  vacios: Array<{ nombre: string; extra: Extra; ubicacion: boolean; negativo: boolean }>
  /** Un obligatorio omitido por vez. */
  omisiones: Array<{ nombre: string; extra: Extra; ubicacion: boolean }>
}

/** Un cuerpo fijo o uno que se calcula al enviarlo (el saldo cambia durante el recorrido). */
type Extra = any | ((request: APIRequestContext) => any)

const evidencia: Record<string, any> = {
  spec: '015-breeder-cria-uat-s1',
  generado: new Date().toISOString(),
  contrato: 'POST /api/v1/operations · matriz de obligatorios del §4',
  escenario: {},
  operaciones: {},
  saldo: {},
  ui: {},
  observaciones: [],
  fallos: [],
}

async function comoOperador(request: APIRequestContext) {
  const clave = process.env.GA_TEST_OPERATOR_PASSWORD
  if (!clave) throw new Error('GA_TEST_OPERATOR_PASSWORD no definida: use bash scripts_e2e.sh')
  const r = await request.post(`${API}/login`, {
    data: { username: 'test_operator', password: clave },
  })
  expect(r.status(), `login de test_operator: ${await r.text()}`).toBe(200)
  return { Authorization: `Bearer ${(await r.json()).access_token}` }
}

/** Cuerpo canónico del evento: lote, tipo y fecha; granja y galpón solo cuando `BR-08` aplica. */
function cuerpo(tipo: string, extra: Extra = {}, ubicacion = true) {
  return {
    lot_id: esc.lotId,
    event_type: tipo,
    event_date: hoy(),
    ...(ubicacion ? { farm_id: esc.farmId, house_id: esc.houseId } : {}),
    ...extra,
  }
}

async function jsonSeguro(r: any) {
  try {
    return await r.json()
  } catch {
    return {}
  }
}
/** `detail` escalar (regla de negocio) o lista de `msg` (422 de pydantic). */
function mensajesDeError(cuerpoError: any): { texto: string; lista: string[] } {
  const detalle = cuerpoError?.detail
  if (Array.isArray(detalle)) {
    const lista = detalle.map((d: any) => String(d?.msg ?? d))
    const texto = detalle
      .map((d: any) => `${(d?.loc ?? []).join('.')}: ${d?.msg ?? d}`)
      .join(' | ')
    return { texto, lista }
  }
  return { texto: String(detalle ?? ''), lista: [String(detalle ?? '')] }
}

/** Texto que jamás debe viajar al operador: códigos internos y mensajes del framework. */
const PROHIBIDO = /BR-\d|RR-\d|Input should|Field required/i

/**
 * (d) Mensajes de los negativos. Un `422` de pydantic trae el texto en inglés: eso se
 * REPORTA como observación (con el campo), no se falla por ello —el contrato de idioma es
 * del mensaje de negocio, no del framework—. Un `detail` de negocio con código sí es fallo.
 */
function revisarMensaje(operacion: string, caso: string, status: number, cuerpoError: any) {
  const { texto, lista } = mensajesDeError(cuerpoError)
  if (Array.isArray(cuerpoError?.detail)) {
    if (lista.some(m => /Input should|Field required|validation error/i.test(m))) {
      const nota = `${operacion} · ${caso}: ${status} de pydantic en inglés — ${texto}`
      observaciones.push(nota)
      test.info().annotations.push({ type: 'observación', description: nota })
    }
    return
  }
  if (PROHIBIDO.test(texto)) {
    fallos.push(`${operacion} · ${caso}: el mensaje filtra un código o texto técnico — «${texto}»`)
  }
}

/** Compara y acumula: una discrepancia no detiene la evidencia del resto de la matriz. */
function comparar(contexto: string, obtenido: any, esperado: any) {
  const igual = JSON.stringify(obtenido ?? null) === JSON.stringify(esperado ?? null)
  if (!igual) {
    fallos.push(
      `${contexto}: se obtuvo ${JSON.stringify(obtenido ?? null)} y se esperaba ` +
      JSON.stringify(esperado ?? null),
    )
  }
  return { obtenido: obtenido ?? null, esperado: esperado ?? null, ok: igual }
}
/** Total de operaciones del lote (`X-Total-Count`): prueba que un negativo no creó fila. */
async function totalDelLote(request: APIRequestContext): Promise<number> {
  const trozo = esc.codigo.split('-').pop()!.toLowerCase()
  const r = await request.get(`${API}/operations?lot_code=${trozo}&limit=100`, { headers: admin })
  expect(r.status(), `listado por código de lote: ${await r.text()}`).toBe(200)
  return Number(r.headers()['x-total-count'])
}

/** Saldo de aves del lote, derivado de las operaciones (la regla de `proceso-02`). */
async function saldoDeAves(request: APIRequestContext, lotId: number): Promise<number> {
  const lista = await request.get(`${API}/operations?lot_id=${lotId}&limit=100`, { headers: admin })
  expect(lista.status(), `listado del lote ${lotId}: ${await lista.text()}`).toBe(200)
  const entradas = new Set(['bird_reception', 'birth_registration'])
  const salidas = new Set(['mortality_recording', 'cull_recording', 'bird_exit', 'chick_dispatch'])
  let total = 0
  for (const evento of await lista.json()) {
    if (evento.status === 'cancelled') continue
    if (!entradas.has(evento.event_type) && !salidas.has(evento.event_type)) continue
    const detalle = await jsonSeguro(
      await request.get(`${API}/operations/${evento.id}`, { headers: admin }),
    )
    const suma = (detalle.bird_movements ?? [])
      .reduce((a: number, m: any) => a + (m.quantity ?? 0), 0)
    total += entradas.has(evento.event_type) ? suma : -suma
  }
  return total
}

/** El `extra` puede depender del estado (p. ej. «saldo + 1»): se resuelve al enviarlo. */
async function resolver(extra: Extra, request: APIRequestContext) {
  return typeof extra === 'function' ? await extra(request) : extra
}
/**
 * La matriz del §4, en el orden del circuito: recepción primero (de ella sale el saldo),
 * después el control diario y las salidas.
 */
function construirCasos(): Caso[] {
  const filasReceptoras = () => [
    { sex: 'male', quantity: 100, avg_weight: 2.0 },
    { sex: 'female', quantity: 880, avg_weight: 1.8 },
  ]
  const aves = (n: number) => ({ bird_movements: [{ sex: 'mixed', quantity: n }] })
  const sobreSaldo = async (request: APIRequestContext) =>
    aves((await saldoDeAves(request, esc.lotId)) + 1)
  const cuadre = () => ({ received_total: 1000, dead_on_arrival: 15, rejected_on_arrival: 5 })

  return [
    {
      tipo: 'bird_reception',
      nombre: 'Recepción de aves (breeder)',
      contrato: [
        'granja + galpón (BR-08)', 'received_total', 'dead_on_arrival',
        'rejected_on_arrival', 'received_total = Σ filas + muertas + rechazadas (BR-20)',
      ],
      ubicacion: true,
      minimo: { ...cuadre(), bird_movements: filasReceptoras() },
      vacios: [
        { nombre: 'sin cuadre', extra: {}, ubicacion: true, negativo: true },
      ],
      omisiones: [
        {
          nombre: 'sin received_total',
          extra: { dead_on_arrival: 15, rejected_on_arrival: 5, bird_movements: filasReceptoras() },
          ubicacion: true,
        },
        {
          nombre: 'sin dead_on_arrival',
          extra: { received_total: 1000, rejected_on_arrival: 5, bird_movements: filasReceptoras() },
          ubicacion: true,
        },
        {
          nombre: 'sin rejected_on_arrival',
          extra: { received_total: 1000, dead_on_arrival: 15, bird_movements: filasReceptoras() },
          ubicacion: true,
        },
        {
          nombre: 'filas que no cuadran',
          extra: {
            ...cuadre(),
            bird_movements: [
              { sex: 'male', quantity: 100, avg_weight: 2.0 },
              { sex: 'female', quantity: 879, avg_weight: 1.8 },
            ],
          },
          ubicacion: true,
        },
      ],
    },
    {
      tipo: 'bird_distribution',
      nombre: 'Distribución de aves',
      contrato: [
        'granja + galpón (BR-08)',
        '≥1 movimiento, cantidades ≥ 0 y Σ > 0 (RR-29, OD-S2-03): el vacío con ubicación ya no es un registro',
      ],
      ubicacion: true,
      minimo: aves(10),
      vacios: [
        { nombre: 'solo ubicación (sin movimientos)', extra: {}, ubicacion: true, negativo: true },
      ],
      omisiones: [
        { nombre: 'suma cero', extra: aves(0), ubicacion: true },
        { nombre: 'sin galpón', extra: { ...aves(10), farm_id: esc.farmId }, ubicacion: false },
        { nombre: 'sin granja', extra: { ...aves(10), house_id: esc.houseId }, ubicacion: false },
      ],
    },
    {
      tipo: 'farm_inspection',
      nombre: 'Inspección de granja',
      contrato: [
        'granja (BR-08)', 'galpón (BR-08)', 'paridad cliente-servidor (§4.2)',
        'al menos un dato: valor, observación o evidencia (RR-28, OD-S2-02)',
      ],
      ubicacion: true,
      minimo: { observations: 'Inspección sin novedades' },
      vacios: [
        { nombre: 'sin granja ni galpón', extra: {}, ubicacion: false, negativo: true },
        { nombre: 'con granja y galpón pero sin contenido', extra: {}, ubicacion: true, negativo: true },
      ],
      omisiones: [
        { nombre: 'sin galpón', extra: { observations: 'Inspección sin novedades', farm_id: esc.farmId }, ubicacion: false },
        { nombre: 'sin granja', extra: { observations: 'Inspección sin novedades', house_id: esc.houseId }, ubicacion: false },
        {
          nombre: 'solo valores por defecto',
          extra: { inspection_details: [{ parameter: 'Bioseguridad', value: '', value_numeric: null }] },
          ubicacion: true,
        },
      ],
    },
    {
      tipo: 'feed_registration',
      nombre: 'Registro de alimento',
      contrato: [
        '≥1 fila de feed_movements con quantity_kg > 0 (RR-23)',
        'feed_type_id presente (RR-33, OD-S2-07); la fase se deriva del lote (RR-34)',
      ],
      ubicacion: false,
      minimo: { feed_movements: [{ quantity_kg: 12.5, feed_type_id: maestros.alimentoId }] },
      vacios: [{ nombre: 'sin filas de alimento', extra: {}, ubicacion: false, negativo: true }],
      omisiones: [
        { nombre: 'con kg 0', extra: { feed_movements: [{ quantity_kg: 0, feed_type_id: maestros.alimentoId }] }, ubicacion: false },
        { nombre: 'sin tipo de alimento', extra: { feed_movements: [{ quantity_kg: 12.5 }] }, ubicacion: false },
      ],
    },
    {
      tipo: 'water_consumption',
      nombre: 'Consumo de agua',
      contrato: ['water_liters presente (B05)', 'water_liters > 0 (RR-11)'],
      ubicacion: false,
      minimo: { water_liters: 120.5 },
      vacios: [{ nombre: 'sin litros', extra: {}, ubicacion: false, negativo: true }],
      omisiones: [
        { nombre: 'sin litros (omitido)', extra: {}, ubicacion: false },
        { nombre: 'con 0 litros', extra: { water_liters: 0 }, ubicacion: false },
      ],
    },
    {
      tipo: 'weight_recording',
      nombre: 'Pesaje',
      contrato: ['≥1 fila de bird_movements con avg_weight > 0 (RR-20)'],
      ubicacion: false,
      minimo: { bird_movements: [{ sex: 'male', avg_weight: 2.1 }] },
      vacios: [{ nombre: 'sin peso', extra: {}, ubicacion: false, negativo: true }],
      omisiones: [
        {
          nombre: 'con avg_weight 0',
          extra: { bird_movements: [{ sex: 'male', avg_weight: 0 }] },
          ubicacion: false,
        },
      ],
    },
    {
      tipo: 'vaccination',
      nombre: 'Vacunación',
      contrato: ['vaccine_id presente (RR-21)', 'vaccine_lot_number con texto (RR-31, OD-S2-05)'],
      ubicacion: false,
      minimo: { vaccine_id: maestros.vacunaId, vaccine_lot_number: LOTE_DE_VACUNA },
      vacios: [{ nombre: 'sin vacuna', extra: {}, ubicacion: false, negativo: true }],
      omisiones: [
        { nombre: 'sin vacuna (omitida)', extra: { vaccine_lot_number: LOTE_DE_VACUNA }, ubicacion: false },
        { nombre: 'sin lote de vacuna', extra: { vaccine_id: maestros.vacunaId }, ubicacion: false },
        { nombre: 'lote de vacuna en blanco', extra: { vaccine_id: maestros.vacunaId, vaccine_lot_number: '   ' }, ubicacion: false },
      ],
    },
    {
      tipo: 'medication',
      nombre: 'Medicación',
      contrato: ['medication_id presente (RR-22)'],
      ubicacion: false,
      minimo: { medication_id: maestros.medicamentoId },
      vacios: [{ nombre: 'sin medicamento', extra: {}, ubicacion: false, negativo: true }],
      omisiones: [{ nombre: 'sin medicamento (omitido)', extra: {}, ubicacion: false }],
    },
    {
      tipo: 'mortality_recording',
      nombre: 'Mortalidad',
      contrato: [
        'Σ bird_movements.quantity > 0 (BR-01)', 'total ≤ saldo de aves (BR-01, D4)',
        'cause_id presente; «Desconocida» si no se determinó (RR-32, OD-S2-06)',
      ],
      ubicacion: false,
      minimo: { ...aves(3), cause_id: maestros.causaMortalidadId },
      vacios: [{ nombre: 'sin cantidad', extra: { cause_id: maestros.causaMortalidadId }, ubicacion: false, negativo: true }],
      omisiones: [
        { nombre: 'cantidad 0', extra: { ...aves(0), cause_id: maestros.causaMortalidadId }, ubicacion: false },
        {
          nombre: 'cantidad > saldo',
          extra: async (r: APIRequestContext) => ({ ...(await sobreSaldo(r)), cause_id: maestros.causaMortalidadId }),
          ubicacion: false,
        },
        { nombre: 'sin causa', extra: aves(3), ubicacion: false },
      ],
    },
    {
      tipo: 'cull_recording',
      nombre: 'Descarte',
      contrato: [
        'Σ bird_movements.quantity > 0 (BR-01)', 'total ≤ saldo de aves (BR-01, D4)',
        'cull_cause_id presente; «Desconocida» si no se determinó (RR-32, OD-S2-06)',
      ],
      ubicacion: false,
      minimo: { ...aves(2), cull_cause_id: maestros.causaDescarteId },
      vacios: [{ nombre: 'sin cantidad', extra: { cull_cause_id: maestros.causaDescarteId }, ubicacion: false, negativo: true }],
      omisiones: [
        { nombre: 'cantidad 0', extra: { ...aves(0), cull_cause_id: maestros.causaDescarteId }, ubicacion: false },
        {
          nombre: 'cantidad > saldo',
          extra: async (r: APIRequestContext) => ({ ...(await sobreSaldo(r)), cull_cause_id: maestros.causaDescarteId }),
          ubicacion: false,
        },
        { nombre: 'sin causa', extra: aves(2), ubicacion: false },
      ],
    },
    {
      tipo: 'bird_exit',
      nombre: 'Salida de aves',
      contrato: [
        'granja + galpón (BR-08)', 'Σ bird_movements.quantity > 0 (BR-01)',
        'total ≤ saldo de aves (BR-01, D4)', 'transporte y destino OPCIONALES (D3)',
      ],
      ubicacion: true,
      minimo: aves(5),
      vacios: [{ nombre: 'sin cantidad (con granja y galpón)', extra: {}, ubicacion: true, negativo: true }],
      omisiones: [
        { nombre: 'cantidad 0', extra: aves(0), ubicacion: true },
        { nombre: 'cantidad > saldo', extra: sobreSaldo, ubicacion: true },
        { nombre: 'sin galpón', extra: { ...aves(1), farm_id: esc.farmId }, ubicacion: false },
      ],
    },
  ]
}
test.describe('P18B · obligatorios por operación y circuito Reproductoras/Cría (spec 015)', () => {
  test.beforeAll(async ({ request }) => {
    admin = await cabeceraAdmin(request)
    operador = await comoOperador(request)
    aprobador = await cabeceraAprobador(request)
    esc = await crearEscenario(request, admin, PREFIJO, 'breeder')
    maestros = await crearMaestros(request, admin, PREFIJO)
    casos = construirCasos()
    // Evidencia sanitizada: identificadores y códigos; nunca credenciales.
    evidencia.escenario = {
      lote_id: esc.lotId,
      codigo: esc.codigo,
      granja_id: esc.farmId,
      galpon_id: esc.houseId,
      maestros,
    }
  })

  test('Parte 1 · matriz de obligatorios por operación (§4)', async ({ request }) => {
    for (const caso of casos) {
      const fila: any = {
        operacion: caso.nombre,
        contrato: caso.contrato,
        ubicacion_obligatoria: caso.ubicacion,
        vacios: {},
        minimo: null,
        omisiones: {},
      }
      evidencia.operaciones[caso.tipo] = fila

      // (a) «vacío»: para algunas operaciones es el mínimo (contrato = solo ubicación).
      for (const vacio of caso.vacios) {
        const antes = await totalDelLote(request)
        const r = await registrar(
          request, operador,
          cuerpo(caso.tipo, await resolver(vacio.extra, request), vacio.ubicacion),
        )
        const status = r.status()
        const respuesta = await jsonSeguro(r)
        fila.vacios[vacio.nombre] = status
        if (vacio.negativo) {
          if (status < 400 || status >= 500) {
            fallos.push(
              `${caso.tipo} · vacío «${vacio.nombre}»: ${status} (se esperaba 4xx) — ` +
              JSON.stringify(respuesta).slice(0, 300),
            )
          } else {
            revisarMensaje(caso.tipo, `vacío «${vacio.nombre}»`, status, respuesta)
          }
          const despues = await totalDelLote(request)
          if (despues !== antes) {
            fallos.push(
              `${caso.tipo} · vacío «${vacio.nombre}»: el negativo creó fila ` +
              `(${antes} → ${despues} operaciones del lote)`,
            )
          }
        } else if (status !== 201) {
          fallos.push(
            `${caso.tipo} · vacío «${vacio.nombre}»: ${status} (su contrato es solo ubicación y ` +
            `debía ser 201) — ${JSON.stringify(respuesta).slice(0, 300)}`,
          )
        }
      }
      // (b) «solo obligatorios»: el payload mínimo válido se crea.
      const minimo = await registrar(
        request, operador, cuerpo(caso.tipo, await resolver(caso.minimo, request), caso.ubicacion),
      )
      const cuerpoMinimo = await jsonSeguro(minimo)
      fila.minimo = minimo.status()
      if (minimo.status() === 201) {
        creados[caso.tipo] = cuerpoMinimo.id
      } else {
        fallos.push(
          `${caso.tipo} · mínimo: ${minimo.status()} (se esperaba 201) — ` +
          JSON.stringify(cuerpoMinimo).slice(0, 300),
        )
      }

      // (c) «omitir uno a la vez»: 4xx y sin fila nueva.
      for (const omision of caso.omisiones) {
        const antes = await totalDelLote(request)
        const r = await registrar(
          request, operador,
          cuerpo(caso.tipo, await resolver(omision.extra, request), omision.ubicacion),
        )
        const status = r.status()
        const respuesta = await jsonSeguro(r)
        fila.omisiones[omision.nombre] = status
        if (status < 400 || status >= 500) {
          fallos.push(
            `${caso.tipo} · ${omision.nombre}: ${status} (se esperaba 4xx) — ` +
            JSON.stringify(respuesta).slice(0, 300),
          )
        } else {
          revisarMensaje(caso.tipo, omision.nombre, status, respuesta)
        }
        const despues = await totalDelLote(request)
        if (despues !== antes) {
          fallos.push(
            `${caso.tipo} · ${omision.nombre}: se persistió una fila ` +
            `(${antes} → ${despues} operaciones del lote)`,
          )
        }
      }
    }
  })
  /** Lo enviado vuelve en el detalle: el evento conserva el dato que lo justifica. */
  function verificarDetalle(tipo: string, detalle: any) {
    const suma = (filas: any[] | undefined) =>
      (filas ?? []).reduce((a: number, f: any) => a + (f.quantity ?? 0), 0)
    const ecos: Record<string, any> = {}
    const c = (campo: string, obtenido: any, esperado: any) => {
      ecos[campo] = comparar(`${tipo} · ${campo}`, obtenido, esperado)
    }
    switch (tipo) {
      case 'bird_reception':
        c('received_total', detalle.received_total, 1000)
        c('dead_on_arrival', detalle.dead_on_arrival, 15)
        c('rejected_on_arrival', detalle.rejected_on_arrival, 5)
        c('Σ filas alojadas', suma(detalle.bird_movements), 980)
        c('avg_weight hembras', detalle.bird_movements?.find((m: any) => m.sex === 'female')?.avg_weight, 1.8)
        break
      case 'bird_distribution':
      case 'farm_inspection':
        c('farm_id', detalle.farm_id, esc.farmId)
        c('house_id', detalle.house_id, esc.houseId)
        break
      case 'feed_registration':
        c('feed_movements[0].quantity_kg', detalle.feed_movements?.[0]?.quantity_kg, 12.5)
        break
      case 'water_consumption':
        c('water_liters', detalle.water_liters, 120.5)
        break
      case 'weight_recording':
        c('bird_movements[0].avg_weight', detalle.bird_movements?.[0]?.avg_weight, 2.1)
        c('cantidad no inventada', detalle.bird_movements?.[0]?.quantity ?? 0, 0)
        break
      case 'vaccination':
        c('vaccine_id', detalle.vaccine_id, maestros.vacunaId)
        break
      case 'medication':
        c('medication_id', detalle.medication_id, maestros.medicamentoId)
        break
      case 'mortality_recording':
        c('Σ bird_movements.quantity', suma(detalle.bird_movements), 3)
        break
      case 'cull_recording':
        c('Σ bird_movements.quantity', suma(detalle.bird_movements), 2)
        break
      case 'bird_exit':
        c('Σ bird_movements.quantity', suma(detalle.bird_movements), 5)
        c('transport_id (D3: opcional)', detalle.transport_id ?? null, null)
        c('destination_farm_id (D3: opcional)', detalle.destination_farm_id ?? null, null)
        c('destination_plant_id (D3: opcional)', detalle.destination_plant_id ?? null, null)
        break
      default:
        c('tipo reconocido por el detalle', detalle.event_type, tipo)
    }
    return ecos
  }
  test('Parte 2 · persistencia, historial, revisión y auditoría de cada 201', async ({ request }) => {
    const trozo = esc.codigo.split('-').pop()!.toLowerCase()
    const listado = await request.get(`${API}/operations?lot_code=${trozo}&limit=100`, {
      headers: admin,
    })
    expect(listado.status(), await listado.text()).toBe(200)
    const filas = await listado.json()
    const total = Number(listado.headers()['x-total-count'])
    if (total !== filas.length) {
      fallos.push(
        `historial · X-Total-Count (${total}) no coincide con las filas devueltas (${filas.length})`,
      )
    }

    // El aprobador sembrado no tiene `review:read`: se deja constancia una sola vez.
    const colaAprobador = await request.get(
      `${API}/review/pending?lot_id=${esc.lotId}&status=pending_review&limit=100`,
      { headers: aprobador },
    )
    if (colaAprobador.status() !== 200) {
      const nota =
        `El aprobador de pruebas no lee la bandeja de revisión (/review/pending → ` +
        `${colaAprobador.status()}): su rol siembra approvals:approve sin review:read. ` +
        'La cola se verifica con el administrador, que sí tiene el permiso.'
      observaciones.push(nota)
      test.info().annotations.push({ type: 'observación', description: nota })
    }

    for (const [tipo, id] of Object.entries(creados)) {
      const fila = evidencia.operaciones[tipo]
      const datos: any = { id, detalle: null, envio: null, estado: null, en_cola: null, auditoria: [] }

      const detalleResp = await request.get(`${API}/operations/${id}`, { headers: admin })
      datos.detalle = detalleResp.status()
      if (detalleResp.status() !== 200) {
        fallos.push(`${tipo} · detalle: ${detalleResp.status()} — ${(await detalleResp.text()).slice(0, 200)}`)
      } else {
        datos.ecos = verificarDetalle(tipo, await detalleResp.json())
      }

      if (!filas.some((e: any) => e.id === id)) {
        fallos.push(`${tipo} · el evento ${id} no aparece al filtrar por el código del lote`)
      }
      datos.en_historial = filas.some((e: any) => e.id === id)

      // El registrante lo envía a revisión y el revisor lo ve en su cola.
      const envio = await request.post(`${API}/operations/${id}/submit`, { headers: operador })
      datos.envio = envio.status()
      if (envio.status() !== 200) {
        fallos.push(`${tipo} · envío a revisión: ${envio.status()} — ${(await envio.text()).slice(0, 200)}`)
      } else {
        datos.estado = (await envio.json()).status
        comparar(`${tipo} · estado tras enviar`, datos.estado, 'pending_review')
      }

      const cola = await request.get(
        `${API}/review/pending?lot_id=${esc.lotId}&status=${datos.estado ?? 'pending_review'}&limit=100`,
        { headers: admin },
      )
      const enCola = cola.status() === 200
        ? ((await cola.json()).events ?? []).some((e: any) => e.id === id)
        : false
      datos.en_cola = enCola
      if (!enCola) {
        fallos.push(`${tipo} · el revisor no ve el evento ${id} en la cola de revisión (${cola.status()})`)
      }

      const auditoria = await request.get(
        `${API}/audit?entity_type=operational_event&entity_id=${id}&limit=100`,
        { headers: admin },
      )
      if (auditoria.status() === 200) {
        datos.auditoria = ((await auditoria.json()).logs ?? []).map((l: any) => l.action)
      }
      if (!datos.auditoria.includes('created')) {
        fallos.push(
          `${tipo} · la auditoría no tiene la acción 'created' (${auditoria.status()}; ` +
          `acciones: ${datos.auditoria.join(',') || 'ninguna'})`,
        )
      }
      fila.parte2 = datos
    }
  })
  test('Parte 3 · saldo (BR-01 / D4): por total de aves, nunca negativo', async ({ request }) => {
    const saldo = await saldoDeAves(request, esc.lotId)
    evidencia.saldo.abierto = saldo
    // La recepción suma sus FILAS (100 + 880 = 980 aves alojadas; las muertas al arribo y las
    // rechazadas no entran al galpón). Saldo = 980 − 3 mortalidad − 2 descarte − 5 salida.
    const esperado = 980 - 3 - 2 - 5
    evidencia.saldo.esperado = esperado
    if (saldo !== esperado) {
      fallos.push(`saldo · tras las operaciones: ${saldo}, se esperaba ${esperado}`)
    }

    // NEGATIVO · por encima del saldo: 400 en español, con el saldo y sin códigos internos.
    const excedido = saldo + 1
    const r = await registrar(request, operador, cuerpo('mortality_recording', {
      cause_id: maestros.causaMortalidadId,
      bird_movements: [{ sex: 'mixed', quantity: excedido }],
    }, false))
    const cuerpoR = await jsonSeguro(r)
    const detalle = String(cuerpoR.detail ?? '')
    const { lista } = mensajesDeError(cuerpoR)
    evidencia.saldo.excedido = { enviado: excedido, status: r.status(), detalle, regla: cuerpoR.rule ?? null }
    if (r.status() !== 400) {
      fallos.push(`saldo · mortalidad por encima del saldo: ${r.status()} (se esperaba 400)`)
    }
    if (!detalle.includes(String(saldo))) {
      fallos.push(`saldo · el mensaje no nombra el saldo disponible (${saldo}): «${detalle}»`)
    }
    if (PROHIBIDO.test(detalle) || lista.some(m => PROHIBIDO.test(m))) {
      fallos.push(`saldo · el mensaje filtra un código interno: «${detalle}»`)
    }
    const intacto = await saldoDeAves(request, esc.lotId)
    if (intacto !== saldo) {
      fallos.push(`saldo · un negativo movió el saldo (${saldo} → ${intacto})`)
    }

    // D4 (decisión, no defecto): el saldo se lleva por TOTAL de aves vivas, no por sexo. Una
    // mortalidad cuyas filas suman menos que el saldo se acepta aunque una fila supere la
    // población de ese sexo (los machos recibidos eran 100).
    const d4 = await registrar(request, operador, cuerpo('mortality_recording', {
      cause_id: maestros.causaMortalidadId,
      bird_movements: [
        { sex: 'male', quantity: 300 },
        { sex: 'female', quantity: 200 },
      ],
    }, false))
    evidencia.saldo.d4 = { status: d4.status(), filas: { male: 300, female: 200 }, total: 500 }
    if (d4.status() !== 201) {
      fallos.push(
        `saldo · D4: filas ♂300/♀200 con total 500 ≤ saldo ${saldo} debían aceptarse — ` +
        `${d4.status()} ${JSON.stringify(await jsonSeguro(d4)).slice(0, 200)}`,
      )
    }

    const final = await saldoDeAves(request, esc.lotId)
    evidencia.saldo.final = final
    if (d4.status() === 201 && final !== saldo - 500) {
      fallos.push(`saldo · tras la mortalidad D4 el saldo es ${final} y se esperaba ${saldo - 500}`)
    }
    if (final < 0) {
      fallos.push(`saldo · el saldo final quedó negativo (${final})`)
    }
  })
  test('Parte 4 · UI: «enviar vacío» no llama al backend y muestra el mensaje inline', async ({
    page, request,
  }) => {
    await entrar(page, 'admin')
    const posts: string[] = []
    page.on('request', req => {
      if (req.method() === 'POST' && new URL(req.url()).pathname === '/api/v1/operations') {
        posts.push(req.url())
      }
    })
    fs.mkdirSync(CAPTURAS, { recursive: true })
    const guardar = () => page.locator('#operation-form button[type="submit"]')
    const esperarPost = () =>
      page.waitForResponse(r =>
        r.request().method() === 'POST' && new URL(r.url()).pathname === '/api/v1/operations')
    const captura = async (nombre: string) => {
      await page.screenshot({ path: `${CAPTURAS}/${nombre}`, fullPage: true })
    }

    // MORTALIDAD · la cantidad total es obligatoria (`BR-01`, D2).
    await page.goto(`/operations/new?lot_id=${esc.lotId}&type=mortality_recording`)
    await expect(guardar(), 'el formulario ofrece Guardar').toBeVisible({ timeout: 20_000 })
    const cantidad = page.locator('input[name="bird_movements.0.quantity"]')
    await expect(cantidad, 'la cantidad de la mortalidad está a la vista').toBeVisible()
    await guardar().click()
    await expect(
      page.getByText('Registre una cantidad mayor a cero.'),
      'mensaje inline de la cantidad obligatoria',
    ).toBeVisible()
    comparar('UI · mortalidad vacía: peticiones POST', posts.length, 0)
    await captura('p18b_mortalidad_vacio.png')

    await cantidad.fill('4')
    // `RR-32` (`OD-S2-06`): sin causa tampoco hay POST; «Desconocida» es un valor explícito.
    await guardar().click()
    await expect(
      page.getByText('Seleccione la causa de la mortalidad (use «Desconocida» si no se pudo determinar)'),
      'mensaje inline de la causa obligatoria',
    ).toBeVisible()
    comparar('UI · mortalidad sin causa: peticiones POST', posts.length, 0)
    await page.getByRole('button', { name: 'Seleccionar causa...' }).first().click()
    const buscarCausa = page.getByPlaceholder(/Buscar/i).first()
    if (await buscarCausa.count()) await buscarCausa.fill('Desconocida')
    await page.getByRole('button', { name: 'Desconocida', exact: true }).first().click()
    const respuesta = esperarPost()
    await guardar().click()
    const guardada = await respuesta
    await expect(
      page.getByText('Registro guardado exitosamente').first(),
      'el formulario confirma el guardado',
    ).toBeVisible({ timeout: 20_000 })
    comparar('UI · mortalidad con cantidad: HTTP del POST', guardada.status(), 201)
    await captura('p18b_mortalidad_guardada.png')
    evidencia.ui.mortalidad = { vacio: 'mensaje inline, 0 POST', guardado: guardada.status() }
    // AGUA · litros > 0 (`B05`/`RR-11`): el cliente ya lo exige (§4.2).
    await page.goto(`/operations/new?lot_id=${esc.lotId}&type=water_consumption`)
    await expect(guardar(), 'el formulario de agua ofrece Guardar').toBeVisible({ timeout: 20_000 })
    const litros = page.locator('input[name="water_liters"]')
    await expect(litros, 'los litros están a la vista').toBeVisible()
    const antesAgua = posts.length
    await guardar().click()
    await expect(
      page.getByText('Registre los litros de agua (mayor a cero).'),
      'mensaje inline de los litros obligatorios',
    ).toBeVisible()
    comparar('UI · agua vacía: peticiones POST', posts.length, antesAgua)

    await litros.fill('130.5')
    const respuestaAgua = esperarPost()
    await guardar().click()
    comparar('UI · agua con litros: HTTP del POST', (await respuestaAgua).status(), 201)
    evidencia.ui.agua = { vacio: 'mensaje inline, 0 POST', guardado: 201 }

    // VACUNACIÓN · `vaccine_id` (`RR-21`).
    const vacunas = (await jsonSeguro(
      await request.get(`${API}/masters/vaccines?limit=100`, { headers: admin }),
    )) as any[]
    const nombreVacuna = (vacunas ?? []).find((v: any) => v.id === maestros.vacunaId)?.name
    expect(nombreVacuna, 'la vacuna del escenario debe estar en el catálogo').toBeTruthy()

    await page.goto(`/operations/new?lot_id=${esc.lotId}&type=vaccination`)
    await expect(guardar(), 'el formulario de vacunación ofrece Guardar').toBeVisible({ timeout: 20_000 })
    const antesVacuna = posts.length
    await guardar().click()
    await expect(
      page.getByText('Seleccione la vacuna aplicada.'),
      'mensaje inline de la vacuna obligatoria',
    ).toBeVisible()
    comparar('UI · vacunación sin vacuna: peticiones POST', posts.length, antesVacuna)

    await page.getByRole('button', { name: 'Seleccionar vacuna...' }).first().click()
    await page.getByRole('button', { name: String(nombreVacuna) }).first().click()
    // `RR-31` (`OD-S2-05`): la vacunación nueva declara el lote de la vacuna.
    await page.locator('input[name="vaccine_lot_number"]').first().fill(LOTE_DE_VACUNA)
    const respuestaVacuna = esperarPost()
    await guardar().click()
    comparar('UI · vacunación con vacuna: HTTP del POST', (await respuestaVacuna).status(), 201)
    evidencia.ui.vacunacion = { vacio: 'mensaje inline, 0 POST', guardado: 201, vacuna: nombreVacuna }
    evidencia.ui.capturas = [
      `${CAPTURAS}/p18b_mortalidad_vacio.png`,
      `${CAPTURAS}/p18b_mortalidad_guardada.png`,
    ]
  })
  test('Cierre · el contrato de la matriz (§4) se cumple en todas las operaciones', async () => {
    test.info().annotations.push({
      type: 'contrato',
      description: `${fallos.length} discrepancias · ${observaciones.length} observaciones`,
    })
    expect(
      fallos,
      `Discrepancias de contrato (${fallos.length}):\n${fallos.join('\n')}`,
    ).toEqual([])
  })

  test.afterAll(() => {
    for (const caso of casos) {
      const fila = evidencia.operaciones[caso.tipo]
      if (!fila) continue
      const suyo = (texto: string) => texto.startsWith(caso.tipo)
      fila.resultado = fallos.some(suyo) ? 'FALLO' : observaciones.some(suyo) ? 'OBSERVACIÓN' : 'PASS'
      fila.observaciones = observaciones.filter(suyo)
    }
    evidencia.observaciones = observaciones
    evidencia.fallos = fallos
    fs.mkdirSync(DIR, { recursive: true })
    fs.writeFileSync(
      `${DIR}/e2e_p18b_matriz_obligatorios.json`,
      JSON.stringify(evidencia, null, 2),
    )
  })
})















