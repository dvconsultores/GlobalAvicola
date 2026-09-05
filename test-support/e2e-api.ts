/**
 * Utilidades de API para las certificaciones de proceso — `GA-REM-016`.
 *
 * Cada proceso crea sus propias precondiciones. No se apoya en lotes, granjas ni eventos
 * residuales del entorno: un test que da por supuesto «el lote 2» no prueba el proceso,
 * prueba que ese lote siga ahí.
 */
import { expect, type APIRequestContext } from '@playwright/test'

export const API = 'http://127.0.0.1:8099/api/v1'

/** Fecha de hoy en ISO. Nunca literales: caducan solas por `BR-19` (`R-28`).
 *
 * `R-80`. Usaba `toISOString()`, que da el día **UTC**, mientras el backend llama «hoy» al
 * día **local del servidor** (`date.today()` en `BR-06` y `BR-19`). Entre la medianoche
 * local y la UTC los dos no coinciden y la suite se rechazaba a sí misma con `BR-06`:
 * «fecha anterior a la activación del lote». No era un defecto del producto sino de esta
 * utilidad, y se manifestaba solo durante esa franja.
 *
 * `sv-SE` produce `YYYY-MM-DD` en hora local, que es el mismo día del calendario que el
 * servidor está viviendo.
 */
export function hoy(): string {
  return new Date().toLocaleDateString('sv-SE')
}

/** Día en curso **en UTC**, para contrastar columnas que guardan instantes UTC.
 *
 * `R-80`. `created_at` se fija con `func.now()` y viaja como instante UTC, mientras que
 * `hoy()` da el día local del servidor —que es lo que el producto llama «hoy» en `BR-06`—.
 * Cada comparación debe hacerse en el marco de lo que mira; mezclarlos rompe la suite entre
 * una medianoche y la otra.
 */
export function hoyUtc(): string {
  return new Date().toISOString().slice(0, 10)
}

/** Sufijo único por escenario, para que dos ejecuciones no colisionen. */
export function sufijo(): string {
  return Math.random().toString(36).slice(2, 10)
}

/**
 * Empresa **activa** de la cabecera, leída del token.
 *
 * No se usa `/me`: devuelve la empresa **persistida** del usuario, no aquella en la que la
 * sesión está situada (`R-66`). Con un administrador que ha cambiado de compañía, las dos
 * difieren, y montar un escenario con la equivocada produce un `Farm no encontrado`
 * desconcertante. La empresa activa vive en el token, que es lo que el backend usa.
 */
export function empresaActiva(cabecera: { Authorization: string }): number {
  const carga = cabecera.Authorization.split('.')[1]
  const json = Buffer.from(carga, 'base64url').toString('utf8')
  const claim = JSON.parse(json).company_id
  expect(claim, 'el token debe declarar una empresa').toBeTruthy()
  return Number(claim)
}

async function token(request: APIRequestContext, usuario: string, clave: string) {
  const r = await request.post(`${API}/login`, { data: { username: usuario, password: clave } })
  expect(r.status(), `login de ${usuario}`).toBe(200)
  return (await r.json()).access_token as string
}

export async function cabeceraAdmin(request: APIRequestContext) {
  const clave = process.env.GA_TEST_ADMIN_PASSWORD
  if (!clave) throw new Error('GA_TEST_ADMIN_PASSWORD no definida: use bash scripts_e2e.sh')
  return { Authorization: `Bearer ${await token(request, 'test_admin', clave)}` }
}

/**
 * Usuario de la **otra** empresa, con rol operador.
 *
 * Tiene `operations:create`, y eso es deliberado: una denegación por falta de permiso no
 * demuestra aislamiento entre empresas. Es la lección de `T-067-11`.
 */
export async function cabeceraOtraEmpresa(request: APIRequestContext) {
  const clave = process.env.GA_TEST_OPERATOR_PASSWORD
  if (!clave) throw new Error('GA_TEST_OPERATOR_PASSWORD no definida: use bash scripts_e2e.sh')
  return { Authorization: `Bearer ${await token(request, 'test_otra_empresa', clave)}` }
}

/**
 * Administrador situado en otra empresa.
 *
 * El operador de la segunda empresa tiene `operations:create` pero no `masters:create`, de
 * modo que no puede montar su propio escenario. Lo monta el administrador cambiando de
 * compañía —el camino que `R-48` habilitó— y el operador queda como **sujeto** de las
 * pruebas de aislamiento, que es donde importa que tenga el permiso funcional.
 */
export async function cabeceraAdminEnOtraEmpresa(request: APIRequestContext) {
  const cab = await cabeceraAdmin(request)
  const yo = await (await request.get(`${API}/me`, { headers: cab })).json()

  const empresas = await request.get(`${API}/masters/companies`, { headers: cab })
  expect(empresas.status()).toBe(200)
  const otra = (await empresas.json()).find((c: any) => c.id !== yo.company_id)
  expect(otra, 'debe existir una segunda empresa para probar aislamiento').toBeTruthy()

  const cambio = await request.post(`${API}/switch-company`, {
    headers: cab, data: { company_id: otra.id },
  })
  expect(cambio.status(), `switch-company: ${await cambio.text()}`).toBe(200)
  return {
    cabecera: { Authorization: `Bearer ${(await cambio.json()).access_token}` },
    companyId: otra.id as number,
  }
}

/** Aprobador: tiene sesión y permisos de revisión, pero **no** `operations:create`. */
export async function cabeceraAprobador(request: APIRequestContext) {
  const clave = process.env.GA_TEST_APPROVER_PASSWORD
  if (!clave) throw new Error('GA_TEST_APPROVER_PASSWORD no definida: use bash scripts_e2e.sh')
  return { Authorization: `Bearer ${await token(request, 'test_approver', clave)}` }
}

export interface Escenario {
  companyId: number
  farmId: number
  houseId: number
  lotId: number
  codigo: string
}

async function crear(request: APIRequestContext, cabecera: any, ruta: string, data: any) {
  const r = await request.post(`${API}${ruta}`, { headers: cabecera, data })
  expect(r.status(), `${ruta}: ${await r.text()}`).toBe(201)
  return await r.json()
}

/** Granja, galpón y lote propios del escenario, en la empresa de quien llama. */
export async function crearEscenario(
  request: APIRequestContext,
  cabecera: any,
  prefijo: string,
  birdType = 'breeder',
): Promise<Escenario> {
  const s = sufijo()

  const companyId = empresaActiva(cabecera)

  const granja = await crear(request, cabecera, '/masters/farms', {
    company_id: companyId, name: `${prefijo}-granja-${s}`, code: `${prefijo}-G-${s}`,
    location: 'Escenario de certificación', farm_type: 'breeding',
  })
  const galpon = await crear(request, cabecera, '/masters/houses', {
    farm_id: granja.id, name: `${prefijo}-galpon-${s}`, capacity: 50_000,
  })
  const lote = await crear(request, cabecera, '/lots', {
    company_id: companyId, farm_id: granja.id, house_id: galpon.id,
    lot_code: `${prefijo}-LOTE-${s}`, bird_type: birdType, sex: 'mixed',
  })

  return { companyId, farmId: granja.id, houseId: galpon.id, lotId: lote.id, codigo: lote.lot_code }
}

export interface Maestros {
  causaMortalidadId: number
  causaDescarteId: number
  vacunaId: number
  medicamentoId: number
  alimentoId: number
}

/** Catálogos que la cadena completa necesita. Se crean por escenario, no se suponen. */
export async function crearMaestros(
  request: APIRequestContext, cabecera: any, prefijo: string,
): Promise<Maestros> {
  const companyId = empresaActiva(cabecera)
  const s = sufijo()
  const uno = async (ruta: string, extra: any = {}) =>
    (await crear(request, cabecera, ruta, { company_id: companyId, name: `${prefijo}-${ruta.split('/').pop()}-${s}`, ...extra })).id
  return {
    causaMortalidadId: await uno('/masters/mortality-causes'),
    causaDescarteId: await uno('/masters/cull-causes'),
    vacunaId: await uno('/masters/vaccines'),
    medicamentoId: await uno('/masters/medications'),
    alimentoId: await uno('/masters/feed-types'),
  }
}

/** Registra un evento operativo. Devuelve la respuesta sin exigir un código concreto. */
export async function registrar(request: APIRequestContext, cabecera: any, data: any) {
  return await request.post(`${API}/operations`, { headers: cabecera, data })
}

/** Saldo de huevos del lote, derivado igual que `get_egg_balance`: recolección − despacho. */
export async function saldoDeHuevos(
  request: APIRequestContext, cabecera: any, lotId: number,
): Promise<number> {
  const lista = await request.get(`${API}/operations?lot_id=${lotId}&limit=100`, { headers: cabecera })
  expect(lista.status()).toBe(200)
  let total = 0
  for (const evento of await lista.json()) {
    if (evento.status === 'cancelled') continue
    if (!['egg_collection', 'egg_dispatch'].includes(evento.event_type)) continue
    const detalle = await request.get(`${API}/operations/${evento.id}`, { headers: cabecera })
    const cantidad = ((await detalle.json()).egg_movements ?? [])
      .reduce((a: number, m: any) => a + m.quantity, 0)
    total += evento.event_type === 'egg_collection' ? cantidad : -cantidad
  }
  return total
}

/** Huevos disponibles en incubadora: recepción − cargado en incubadoras. */
export async function saldoEnIncubadora(
  request: APIRequestContext, cabecera: any, lotId: number,
): Promise<number> {
  const lista = await request.get(`${API}/operations?lot_id=${lotId}&limit=100`, { headers: cabecera })
  expect(lista.status()).toBe(200)
  let total = 0
  for (const evento of await lista.json()) {
    if (evento.status === 'cancelled') continue
    const detalle = await (await request.get(`${API}/operations/${evento.id}`, { headers: cabecera })).json()
    if (evento.event_type === 'egg_reception_hatchery') {
      total += (detalle.egg_movements ?? []).reduce((a: number, m: any) => a + m.quantity, 0)
    } else if (evento.event_type === 'incubation_load') {
      total -= (detalle.hatchery_params ?? []).reduce((a: number, p: any) => a + (p.quantity_loaded ?? 0), 0)
    }
  }
  return total
}
