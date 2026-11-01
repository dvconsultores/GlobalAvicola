/**
 * P-17e · AFTER `GA-UAT-USERS-S2-01` — el cambio de rol no toca la contraseña.
 */
import { test, expect, type APIRequestContext, type Page } from '@playwright/test'
import * as fs from 'node:fs'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import { credenciales, entrar } from '../test-support/auth'
import { apiConToken, crearRol, crearUsuario, entrarComo, tokenDe } from '../test-support/admin-rbac'

/** Carpeta de evidencia del AFTER. */
const DIR = 'audit/ga-uat-users-s2-01-2026-11-01/evidence'
/**
 * Cuerpo de una petición con las claves sensibles sustituidas por su longitud: el JSON de
 * evidencia se revisa a mano y en él no caben contraseñas ni hashes.
 */
function sanitizar(postData: string | null): any {
  if (!postData) return null
  let cuerpo: any
  try {
    cuerpo = JSON.parse(postData)
  } catch {
    return '(cuerpo no JSON)'
  }
  if (cuerpo && typeof cuerpo === 'object') {
    for (const campo of ['new_password', 'password', 'current_password']) {
      if (campo in cuerpo) cuerpo[campo] = `<redactado len=${String(cuerpo[campo] ?? '').length}>`
    }
  }
  return cuerpo
}

/**
 * Abre `/users`, busca el username y devuelve la fila.
 *
 * La búsqueda se aplica al pulsar Enter y es imprescindible: el listado pide `limit=100` y el
 * usuario de la prueba es uno entre muchos.
 */
async function buscarUsuario(page: Page, username: string) {
  await page.goto('/users')
  const caja = page.locator('input[type="search"]').first()
  await expect(caja, 'la pantalla de Usuarios debe ofrecer la búsqueda').toBeVisible({
    timeout: 20_000,
  })
  await caja.fill(username)
  await caja.press('Enter')

  const fila = page.getByRole('row').filter({ hasText: username })
  await expect(fila, `la búsqueda por Enter debe dejar la fila de ${username}`).toBeVisible({
    timeout: 20_000,
  })
  return fila
}

/**
 * Abre la ficha de `username`. El botón de editar es un icono: se prueban las etiquetas
 * habituales antes de caer al último botón de la fila (`title` con «editar/edit» o el lápiz).
 */
async function abrirEditar(page: Page, username: string) {
  const fila = await buscarUsuario(page, username)
  const candidatos = [
    fila.locator(
      'button[title*="ditar" i], button[aria-label*="ditar" i],' +
        'button[title*="edit" i], button[aria-label*="edit" i]',
    ),
    fila.getByRole('button', { name: /editar|edit/i }),
    fila.locator('button:has(svg.lucide-pencil), button:has(svg[class*="pencil" i])'),
  ]

  let botonEditar = fila.locator('button').last()
  for (const candidato of candidatos) {
    if ((await candidato.count()) > 0) {
      botonEditar = candidato.first()
      break
    }
  }
  await botonEditar.click()
}

/** Marca el rol `nombreDestino` en el `<select>` del modal ya abierto. */
async function elegirRol(page: Page, nombreDestino: string) {
  await expect(
    page.locator('option', { hasText: nombreDestino }),
    `el selector de rol debe listar ${nombreDestino}`,
  ).toHaveCount(1, { timeout: 20_000 })
  const selectRol = page
    .locator('select')
    .filter({ has: page.locator('option', { hasText: nombreDestino }) })
    .first()
  const valor = await page.locator('option', { hasText: nombreDestino }).first().getAttribute('value')
  if (valor) await selectRol.selectOption(valor)
  else await selectRol.selectOption({ label: nombreDestino })
}

/**
 * Cambia el rol desde la interfaz y devuelve la red y los avisos de esa edición.
 *
 * El registro de red se engancha ANTES de Guardar: mide exactamente ese guardado.
 */
async function cambiarRol(page: Page, username: string, nombreDestino: string) {
  await abrirEditar(page, username)

  // El formulario de edición no debe pedir ni reponer contraseña: es el corazón del arreglo.
  await expect(
    page.locator('input[type="password"]'),
    'la ficha de edición no debe pedir la contraseña',
  ).toHaveCount(0, { timeout: 20_000 })

  await elegirRol(page, nombreDestino)

  const peticiones: any[] = []
  const respuestas: any[] = []

  page.on('request', req => {
    const url = new URL(req.url())
    if (!url.pathname.includes('/api/v1/users')) return
    peticiones.push({ metodo: req.method(), ruta: url.pathname, cuerpo: sanitizar(req.postData()) })
  })

  page.on('response', async res => {
    const url = new URL(res.url())
    if (!url.pathname.includes('/api/v1/users')) return
    const entrada: any = {
      metodo: res.request().method(),
      ruta: url.pathname,
      status: res.status(),
      detail: null,
    }
    if (res.status() >= 400) {
      try {
        const cuerpo = await res.json()
        entrada.detail = cuerpo?.detail ?? cuerpo
      } catch {
        entrada.detail = '(cuerpo no JSON)'
      }
    }
    respuestas.push(entrada)
  })

  await page.getByRole('button', { name: /guardar|save/i }).first().click()
  await page.waitForTimeout(2000)

  const toasts = await page.locator('[role="alert"], [role="status"]').allInnerTexts()

  // El portal pinta sus avisos en el contenedor fijo de `Toast.tsx`, que no lleva rol ARIA:
  // sin esta segunda lectura, un error visible se quedaría sin registrar.
  const avisos = await page.locator('.fixed.top-4.right-4 > div').allInnerTexts()
  for (const aviso of avisos) {
    const texto = aviso.replace(/\s+/g, ' ').trim()
    if (texto && !toasts.includes(texto)) toasts.push(texto)
  }

  // Petición y respuesta se emparejan por orden: el listener de `response` llega detrás.
  const requests = peticiones.map((peticion, i) => ({
    ...peticion,
    status: respuestas[i]?.status ?? null,
    detail: respuestas[i]?.detail ?? null,
  }))

  return { requests, toasts }
}

/** Códigos `modulo:accion` que `/me` declara para la credencial dada. */
async function permisosDe(request: APIRequestContext, token: string): Promise<string[]> {
  const r = await request.get(`${API}/me`, { headers: { Authorization: `Bearer ${token}` } })
  expect(r.status(), `GET /me con el token de U: ${await r.text()}`).toBe(200)
  const me = await r.json()
  return Array.isArray(me?.permissions) ? me.permissions.map(String).sort() : []
}

/** Estado del login de U con su clave, sin imprimir nada de la respuesta. */
async function loginDe(request: APIRequestContext, username: string, clave: string) {
  return await request.post(`${API}/login`, { data: { username, password: clave } })
}

/** Rol con el que quedó el usuario según la API de administración. */
async function rolDeUsuario(
  request: APIRequestContext,
  cab: any,
  id: number,
  nombres: Record<number, string>,
) {
  const r = await request.get(`${API}/users/${id}`, { headers: cab })
  expect(r.status(), `GET /users/${id}: ${await r.text()}`).toBe(200)
  const u: any = await r.json()
  const rolId = u.role_id ?? u.role?.id ?? null
  const nombre = u.role?.name ?? u.role_name ?? (rolId !== null ? nombres[rolId] : null)
  return { id: rolId, nombre: nombre ?? null }
}

/** Filas de auditoría para un `entity_type`/`entity_id`, vengan como vengan. */
async function filasAuditoria(
  request: APIRequestContext,
  cab: any,
  tipo: string,
  id: number,
): Promise<number> {
  const r = await request.get(`${API}/audit?entity_type=${tipo}&entity_id=${id}&limit=50`, {
    headers: cab,
  })
  expect(r.status(), `GET /audit ${tipo}: ${await r.text()}`).toBe(200)
  const b: any = await r.json()
  const filas = Array.isArray(b) ? b : (b.items ?? b.results ?? b.data ?? b.logs ?? [])
  return Array.isArray(filas) ? filas.length : 0
}

/** Acumulador de evidencia del AFTER: códigos, rutas, roles y avisos; nunca claves. */
const registro: any = {
  rol_inicial: null,
  rol_tras_ida: null,
  rol_tras_vuelta: null,
  ediciones: [] as any[],
  toasts: [] as string[],
  login_status: {} as Record<string, number>,
  permisos_me: {} as Record<string, string[]>,
  auditoria: {} as Record<string, number>,
}

test('S2-01 · rol A→B→A sin tocar la clave', async ({ browser, request }) => {
  test.setTimeout(150_000)

  const s = sufijo()
  const nombreA = `S2A-${s}`
  const nombreB = `S2B-${s}`
  const username = `p17e-s2-${s}`
  const CLAVE_U = `S2-${s}-Aa1!`

  const cab = await cabeceraAdmin(request)
  const rolA = await crearRol(request, cab, nombreA, [{ module: 'lots', action: 'read' }])
  const rolB = await crearRol(request, cab, nombreB, [{ module: 'audit', action: 'read' }])
  const usuarioId = await crearUsuario(request, cab, {
    username,
    clave: CLAVE_U,
    role_id: rolA,
  })
  const nombres: Record<number, string> = { [rolA]: nombreA, [rolB]: nombreB }
  registro.rol_inicial = { id: rolA, nombre: nombreA }

  // El MISMO token de U debe ver el cambio de rol: se guarda ahora, no se vuelve a pedir.
  const loginInicial = await loginDe(request, username, CLAVE_U)
  expect(loginInicial.status(), 'la clave inicial de U debe abrir sesión').toBe(200)
  const tokenU: string = (await loginInicial.json()).access_token
  expect(tokenU, 'el login de U debe devolver access_token').toBeTruthy()
  registro.login_status.inicial = loginInicial.status()

  const permisosIniciales = await permisosDe(request, tokenU)
  registro.permisos_me.inicial = permisosIniciales
  expect(permisosIniciales, 'el rol A concede lots:read').toContain('lots:read')
  expect(permisosIniciales, 'el rol A no concede audit:read').not.toContain('audit:read')

  // ── Sesión de administración en un contexto propio, como en `P-17b` ─────────────────────
  const { usuario: usuarioAdmin, clave: claveAdmin } = credenciales('admin')
  const ctx = await browser.newContext()
  const pageAdmin = await ctx.newPage()

  try {
    await entrarComo(pageAdmin, usuarioAdmin, claveAdmin).catch(async () => {
      await entrar(pageAdmin, 'admin')
    })

    // ── (1) IDA A→B: se cambia el rol sin escribir contraseña ────────────────────────────
    const ida = await cambiarRol(pageAdmin, username, nombreB)
    registro.ediciones.push({ paso: 'ida A→B', requests: ida.requests })
    registro.toasts.push(...ida.toasts)

    for (const aviso of ida.toasts) {
      expect(aviso, 'la edición no debe quejarse de la contraseña').not.toMatch(
        /contrase[ñn]a|password/i,
      )
    }

    const puts = ida.requests.filter(r => r.metodo === 'PUT')
    expect(
      puts.length,
      `la edición debe mandar 1 PUT /users/{id}: ${JSON.stringify(ida.requests)}`,
    ).toBe(1)
    expect(puts[0].status, `el PUT debe responder 200: ${JSON.stringify(puts[0])}`).toBe(200)
    expect(
      ida.requests.filter(r => /\/password$/.test(String(r.ruta))).length,
      'el cambio de rol no debe llamar a /password',
    ).toBe(0)
    const cuerpoPut = puts[0].cuerpo ?? {}
    expect(Object.keys(cuerpoPut)).not.toContain('password')
    expect(Object.keys(cuerpoPut)).not.toContain('new_password')

    // ── (2) Consecuencias del guardado: rol, clave y permisos de la MISMA credencial ─────
    const rolTrasIda = await rolDeUsuario(request, cab, usuarioId, nombres)
    registro.rol_tras_ida = rolTrasIda
    expect(rolTrasIda.nombre, 'el rol de U debe quedar en B').toBe(nombreB)

    const loginIda = await loginDe(request, username, CLAVE_U)
    registro.login_status.tras_ida = loginIda.status()
    expect(loginIda.status(), 'la clave de U debe seguir abriendo sesión').toBe(200)

    const permisosIda = await permisosDe(request, tokenU)
    registro.permisos_me.tras_ida = permisosIda
    expect(permisosIda, 'el rol B concede audit:read').toContain('audit:read')
    expect(permisosIda, 'el rol B ya no concede lots:read').not.toContain('lots:read')

    // ── (3) Auditoría: el cambio de rol deja rastro; el cambio de clave, ninguno ─────────
    const audClaveIda = await filasAuditoria(request, cab, 'user_password', usuarioId)
    const audUsuarioIda = await filasAuditoria(request, cab, 'user', usuarioId)
    registro.auditoria.tras_ida = { user_password: audClaveIda, user: audUsuarioIda }
    expect(audClaveIda, 'ninguna fila debe registrar cambio de contraseña').toBe(0)
    expect(audUsuarioIda, 'el cambio de rol debe quedar auditado').toBeGreaterThanOrEqual(1)

    // ── (4) VUELTA B→A: mismas aserciones, en sentido contrario ──────────────────────────
    const vuelta = await cambiarRol(pageAdmin, username, nombreA)
    registro.ediciones.push({ paso: 'vuelta B→A', requests: vuelta.requests })
    registro.toasts.push(...vuelta.toasts)

    for (const aviso of vuelta.toasts) {
      expect(aviso, 'la vuelta tampoco debe hablar de contraseña').not.toMatch(
        /contrase[ñn]a|password/i,
      )
    }

    const putsVuelta = vuelta.requests.filter(r => r.metodo === 'PUT')
    expect(
      putsVuelta.length,
      `la vuelta debe mandar 1 PUT /users/{id}: ${JSON.stringify(vuelta.requests)}`,
    ).toBe(1)
    expect(
      putsVuelta[0].status,
      `el PUT de vuelta debe responder 200: ${JSON.stringify(putsVuelta[0])}`,
    ).toBe(200)
    expect(
      vuelta.requests.filter(r => /\/password$/.test(String(r.ruta))).length,
      'la vuelta tampoco debe llamar a /password',
    ).toBe(0)
    const cuerpoVuelta = putsVuelta[0].cuerpo ?? {}
    expect(Object.keys(cuerpoVuelta)).not.toContain('password')
    expect(Object.keys(cuerpoVuelta)).not.toContain('new_password')
    const rolTrasVuelta = await rolDeUsuario(request, cab, usuarioId, nombres)
    registro.rol_tras_vuelta = rolTrasVuelta
    expect(rolTrasVuelta.nombre, 'el rol de U debe volver a A').toBe(nombreA)

    const loginVuelta = await loginDe(request, username, CLAVE_U)
    registro.login_status.tras_vuelta = loginVuelta.status()
    expect(loginVuelta.status(), 'la clave de U debe seguir intacta tras la vuelta').toBe(200)
    const permisosVuelta = await permisosDe(request, tokenU)
    registro.permisos_me.tras_vuelta = permisosVuelta
    expect(permisosVuelta, 'el rol A vuelve a conceder lots:read').toContain('lots:read')
    expect(permisosVuelta, 'el rol A ya no concede audit:read').not.toContain('audit:read')

    const audClaveVuelta = await filasAuditoria(request, cab, 'user_password', usuarioId)
    const audUsuarioVuelta = await filasAuditoria(request, cab, 'user', usuarioId)
    registro.auditoria.tras_vuelta = { user_password: audClaveVuelta, user: audUsuarioVuelta }
    expect(audClaveVuelta, 'la vuelta tampoco debe auditar cambios de contraseña').toBe(0)
    expect(audUsuarioVuelta, 'la vuelta de rol debe quedar auditada').toBeGreaterThanOrEqual(1)
  } finally {
    await ctx.close()
  }
})

/**
 * Evidencia del AFTER: se escribe una sola vez, cuando el test ya ha corrido.
 * Si no llegó a montarse el escenario, no hay nada que guardar.
 */
test.afterAll(() => {
  if (!registro?.rol_inicial) return
  fs.mkdirSync(DIR, { recursive: true })
  fs.writeFileSync(`${DIR}/04_after_e2e.json`, JSON.stringify(registro, null, 2))
})
