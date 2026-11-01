/**
 * Utilidades de administración para las pruebas de autoridad **dinámica** — SPEC 013.
 *
 * El punto que estas pruebas certifican es que la autoridad (permisos y unidades de negocio)
 * se resuelve **en cada petición**, no en el momento del login. Por eso todo aquí trabaja con
 * un token ya emitido: la sesión del usuario no se toca y, sin embargo, la respuesta del
 * backend debe cambiar. Un `reload`, un nuevo login o un token recién acuñado esconderían
 * justo el defecto que se busca (`AC-SS-02`).
 *
 * Se usan nombres únicos (`p17-…-${sufijo()}`) para que dos ejecuciones seguidas no se pisen:
 * los roles y usuarios creados aquí no se borran, y una segunda pasada encontraría los de la
 * primera.
 */
import { expect, type APIRequestContext, type Page } from '@playwright/test'
import { API, empresaActiva, sufijo } from './e2e-api'

/** Un permiso con la forma que espera `POST /roles`. */
export interface Permiso {
  module: string
  action: string
}

/** Cabecera de administración (la que devuelve `cabeceraAdmin`) o cualquier `{ Authorization }`. */
type Cabecera = { Authorization: string }

/**
 * Login por la interfaz con credenciales arbitrarias.
 *
 * `entrar` de `auth.ts` solo conoce los tres usuarios sembrados; estas pruebas crean los
 * suyos por API y necesitan entrar con ellos por la pantalla, igual que una persona.
 */
export async function entrarComo(page: Page, username: string, clave: string): Promise<void> {
  await page.goto('/login')
  await page
    .getByLabel(/usuario|username/i)
    .fill(username)
    .catch(async () => {
      await page.locator('input[name="username"], input#login-username').first().fill(username)
    })
  await page.locator('input[type="password"]').first().fill(clave)
  await page.locator('button[type="submit"]').first().click()

  await expect(
    page,
    `el login de ${username} debe llevar fuera de /login`,
  ).not.toHaveURL(/\/login/, { timeout: 20_000 })
}

/** Rol nuevo con el conjunto exacto de permisos pedido. Devuelve su `id`. */
export async function crearRol(
  request: APIRequestContext,
  cab: Cabecera,
  nombre: string,
  permisos: Permiso[],
): Promise<number> {
  const r = await request.post(`${API}/roles`, {
    headers: cab,
    data: {
      name: nombre,
      description: `SPEC 013 ${nombre}`,
      // `scope_type: "all"` es el alcance que la interfaz usa por defecto: sin él el permiso
      // existe pero no autoriza sobre ningún recurso.
      permissions: permisos.map(p => ({ ...p, scope_type: 'all' })),
    },
  })
  expect(r.status(), `POST /roles: ${await r.text()}`).toBe(201)
  return (await r.json()).id
}

/**
 * Usuario nuevo con el rol indicado. Devuelve su `id`.
 *
 * No se manda `company_id`: el administrador de pruebas está situado en su empresa y el alta
 * resuelve la compañía sola. Si una instalación la exige, se reintenta declarándola desde la
 * empresa **activa** del token —no desde `/me`, que devuelve la persistida (`R-66`)—.
 */
export async function crearUsuario(
  request: APIRequestContext,
  cab: Cabecera,
  datos: { username: string; clave: string; role_id: number; email?: string },
): Promise<number> {
  const cuerpo = {
    username: datos.username,
    first_name: 'Prueba',
    last_name: `SPEC013 ${sufijo()}`,
    email: datos.email ?? `${datos.username}@example.com`,
    password: datos.clave,
    role_id: datos.role_id,
  }

  let r = await request.post(`${API}/users`, { headers: cab, data: cuerpo })
  if (r.status() === 201) return (await r.json()).id

  const mensaje = await r.text()
  if (/company/i.test(mensaje)) {
    r = await request.post(`${API}/users`, {
      headers: cab,
      data: { ...cuerpo, company_id: empresaActiva(cab) },
    })
    expect(r.status(), `POST /users (con company_id): ${await r.text()}`).toBe(201)
    return (await r.json()).id
  }

  expect(r.status(), `POST /users: ${mensaje}`).toBe(201)
  return (await r.json()).id
}

/** Token de la sesión viva en el navegador, sin pasar por la red. */
export async function tokenDe(page: Page): Promise<string> {
  const token = await page.evaluate(() => sessionStorage.getItem('access_token'))
  expect(token, 'la sesión del navegador debe tener access_token en sessionStorage').toBeTruthy()
  return token as string
}

/**
 * Petición a la API **desde dentro del navegador**, con el token que la sesión ya tenía.
 *
 * Dos cosas importan y ninguna es cosmética:
 *   · el token se reutiliza tal cual, así que un 403 aquí demuestra que el backend re-resolvió
 *     los permisos de esa misma credencial;
 *   · la petición sale del propio navegador (el frontend proxya `/api` al backend), de modo
 *     que se ejercita el mismo camino que la interfaz, no un cliente privilegiado paralelo.
 */
export async function apiConToken(
  page: Page,
  path: string,
  token?: string,
): Promise<{ status: number; body: any }> {
  const usado = token ?? (await tokenDe(page))
  return await page.evaluate(
    async ({ path, token }) => {
      const r = await fetch(`/api/v1${path}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const texto = await r.text()
      let body: any = texto
      try {
        body = JSON.parse(texto)
      } catch {
        /* una respuesta no JSON se devuelve como texto: el fallo se ve en la afirmación */
      }
      return { status: r.status, body }
    },
    { path, token: usado },
  )
}

/** Códigos de las unidades de negocio efectivas que declara `/me`, vengan como vengan. */
export function codigosEfectivos(me: any): string[] {
  const unidades = me?.effective_business_units ?? me?.business_units ?? []
  return (unidades as any[])
    .map(u => (typeof u === 'string' ? u : u?.code))
    .filter((c): c is string => typeof c === 'string')
}
