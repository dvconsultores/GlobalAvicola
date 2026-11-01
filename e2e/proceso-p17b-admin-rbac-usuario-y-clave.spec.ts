/**
 * P-17b — LA CUENTA COMO OBJETO DE AUTORIDAD   (SPEC 013 · `AC-E2E-01`, `AC-UI-05`, `AR-22`)
 *
 * `P-17` demuestra que un permiso o una unidad retirados dejan de autorizar **en la sesión ya
 * abierta**. Falta el otro sujeto de la autorización: la propia cuenta. Desactivar a alguien no
 * es un cambio de permisos —es apagar la credencial— y por eso se comprueba en dos direcciones:
 *
 *   `AC-E2E-01`  ACTIVE → INACTIVE → DENY → REACTIVAR → ALLOW, con el **mismo token** en la
 *                mano y sin recargar la sesión del afectado. Si el token siguiera valiendo, el
 *                botón de desactivar sería decorativo.
 *   `AC-UI-05`   el cambio de contraseña se hace desde `/profile`, sin llamar a la API a mano:
 *                discrepancia, longitud mínima, error del servidor y éxito tienen que ser
 *                legibles en pantalla, y la clave vieja tiene que dejar de abrir la puerta.
 *   `AR-22`      la búsqueda de `/users` (Enter) es la única forma fiable de llegar a una fila:
 *                el listado pide `limit=100` y el usuario efímero no tiene por qué estar en la
 *                primera página.
 *
 * Dos contextos de navegador: el administrador no comparte cookies ni `sessionStorage` con el
 * usuario, de modo que lo que ocurre en uno no puede «arreglar» lo del otro por rebote.
 */
import { test, expect, type Locator, type Page } from '@playwright/test'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'
import { apiConToken, crearRol, crearUsuario, entrarComo, tokenDe } from '../test-support/admin-rbac'

/** Clave de los usuarios efímeros: mayúscula, minúscula, dígito y símbolo. */
const CLAVE = 'Spec013!2024'

/** Nueva clave de `P-17-D`: distinta de la vieja y con la misma composición. */
const CLAVE_NUEVA = 'SpecNueva!2024x'

/** Mensajes que la pantalla de login puede mostrar cuando la cuenta está apagada. */
const ERROR_LOGIN = /desactivada|deactivated|inactiv|incorrect|inv[aá]lid|no es correcta/i

/**
 * Abre `/users`, busca el username y devuelve la fila.
 *
 * La búsqueda se aplica al pulsar Enter y es imprescindible: el listado pide `limit=100` y el
 * usuario de la prueba es uno entre muchos, así que darlo por visible sería confiar en el
 * orden de una página que no controlamos.
 */
async function buscarUsuario(page: Page, username: string): Promise<Locator> {
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

/** El chip de estado de la fila, que es un botón: pulsarlo cambia el estado de la cuenta. */
function chip(fila: Locator, estado: 'Activo' | 'Inactivo'): Locator {
  return fila.getByRole('button', { name: new RegExp(`^${estado}$`, 'i') })
}

/**
 * Intenta entrar por la interfaz **sin exigir éxito**.
 *
 * `entrarComo` da por hecho que el login funciona; aquí varias veces no debe funcionar y lo que
 * hay que comprobar es justamente que la pantalla se queda en `/login` y lo explica.
 */
async function intentarLogin(page: Page, username: string, clave: string): Promise<void> {
  await page.goto('/login')
  await page
    .getByLabel(/usuario|username/i)
    .fill(username)
    .catch(async () => {
      await page.locator('input[name="username"], input#login-username').first().fill(username)
    })
  await page.locator('input[type="password"]').first().fill(clave)
  await page.locator('button[type="submit"]').first().click()
}

/**
 * Espera a que un texto aparezca en lo visible de la página.
 *
 * Se apoya en el texto renderizado y no en un selector concreto porque el portal rotula sus
 * avisos de varias maneras (aviso en línea, alerta o toast): lo que el caso certifica es que
 * una persona lo lee, no en qué etiqueta vive.
 */
async function verTexto(page: Page, patron: RegExp, timeout = 20_000): Promise<void> {
  await expect
    .poll(async () => (await page.locator('body').innerText()).replace(/\s+/g, ' '), { timeout })
    .toMatch(patron)
}

/** Rellena los tres campos de `/profile` en el orden real de la pantalla. */
async function rellenarClaves(
  page: Page,
  actual: string,
  nueva: string,
  confirmacion: string,
): Promise<void> {
  const campos = page.locator('input[type="password"]')
  await expect(campos, 'el formulario de perfil debe tener tres campos de contraseña').toHaveCount(3)
  await campos.nth(0).fill(actual)
  await campos.nth(1).fill(nueva)
  await campos.nth(2).fill(confirmacion)
}

/** Pulsa «Actualizar contraseña», el envío real de la pantalla de perfil. */
async function enviarClaves(page: Page): Promise<void> {
  const enviar = page.getByRole('button', { name: /actualizar contrase|update password/i }).first()
  await expect(enviar).toBeVisible({ timeout: 20_000 })
  await enviar.click()
}

/** Cierra la sesión por la barra lateral, si es que sigue abierta. */
async function cerrarSesion(page: Page): Promise<void> {
  if (/\/login/.test(page.url())) return
  const salir = page.getByRole('button', { name: /cerrar sesi[oó]n|log ?out|sign ?out/i }).first()
  await expect(salir).toBeVisible({ timeout: 20_000 })
  await salir.click()
  await expect(page, 'tras cerrar sesión se vuelve al login').toHaveURL(/\/login/, {
    timeout: 20_000,
  })
}

test.describe('P-17b · cuenta desactivada y contraseña propia (SPEC 013)', () => {
  test('P-17-C · usuario: ACTIVE → INACTIVE → DENY → REACTIVAR (mismo token, UI + API)', async ({
    browser,
    request,
  }) => {
    // `AC-E2E-01`: apagar la cuenta tiene que apagar la credencial, no solo el próximo login.
    const s = sufijo()
    const username = `p17b-c-${s}`

    const cab = await cabeceraAdmin(request)
    const roleId = await crearRol(request, cab, `p17b-rol-${s}`, [
      { module: 'lots', action: 'read' },
      { module: 'audit', action: 'read' },
    ])
    await crearUsuario(request, cab, { username, clave: CLAVE, role_id: roleId })

    const adminCtx = await browser.newContext()
    const userCtx = await browser.newContext()
    const pageAdmin = await adminCtx.newPage()
    const pageUser = await userCtx.newPage()

    try {
      await entrar(pageAdmin, 'admin')
      await entrarComo(pageUser, username, CLAVE)

      // ── ALLOW ────────────────────────────────────────────────────────────────
      const mePermitido = await apiConToken(pageUser, '/me')
      expect(
        mePermitido.status,
        `con la cuenta activa /me debe responder: ${JSON.stringify(mePermitido.body)}`,
      ).toBe(200)

      // El token que se reutiliza durante todo el caso: cambiar de token escondería el defecto.
      const token = await tokenDe(pageUser)

      // ── INACTIVE desde `/users`, por la interfaz ─────────────────────────────
      const fila = await buscarUsuario(pageAdmin, username)
      await expect(chip(fila, 'Activo'), 'la cuenta empieza activa').toBeVisible({
        timeout: 20_000,
      })
      await chip(fila, 'Activo').click()
      await expect(
        chip(fila, 'Inactivo'),
        'tras desactivar, la propia fila debe anunciar el estado nuevo',
      ).toBeVisible({ timeout: 20_000 })

      // ── DENY inmediato, en la sesión viva y con el MISMO token ───────────────
      const meDenegado = await apiConToken(pageUser, '/me', token)
      expect(
        meDenegado.status,
        `desactivada la cuenta, el mismo token no puede seguir leyendo: ${JSON.stringify(meDenegado.body)}`,
      ).toBe(401)

      // La interfaz de esa sesión tampoco puede quedarse con datos: al pedir una ruta
      // protegida el `refresh` falla y la app expulsa al login.
      await pageUser.goto('/audit')
      await expect(pageUser, 'la sesión desactivada debe terminar en /login').toHaveURL(/\/login/, {
        timeout: 20_000,
      })

      // Y no puede volver a entrar: el backend responde 403 «Cuenta desactivada».
      await intentarLogin(pageUser, username, CLAVE)
      await expect(pageUser, 'un usuario desactivado no puede entrar').toHaveURL(/\/login/, {
        timeout: 20_000,
      })
      await verTexto(pageUser, ERROR_LOGIN)

      // ── REACTIVAR desde la misma fila ────────────────────────────────────────
      await expect(
        chip(fila, 'Inactivo'),
        'el administrador debe seguir viendo la cuenta inactiva',
      ).toBeVisible({ timeout: 20_000 })
      await chip(fila, 'Inactivo').click()
      await expect(chip(fila, 'Activo'), 'reactivar devuelve la cuenta a activo').toBeVisible({
        timeout: 20_000,
      })

      // ── ALLOW otra vez: la credencial vuelve a servir ────────────────────────
      await entrarComo(pageUser, username, CLAVE)
      const auditPermitido = await apiConToken(pageUser, '/audit?limit=1')
      expect(
        auditPermitido.status,
        `reactivada la cuenta debe volver a autorizar: ${JSON.stringify(auditPermitido.body)}`,
      ).toBe(200)

      // ── Segunda vuelta: la papelera con su confirmación ─────────────────────
      // `AR-22` dejó la búsqueda como camino a la fila; aquí se usa la acción destructiva
      // explícita, que pasa por `ConfirmDialog` y no por el chip.
      const filaOtraVez = await buscarUsuario(pageAdmin, username)
      await expect(chip(filaOtraVez, 'Activo')).toBeVisible({ timeout: 20_000 })
      const papelera = filaOtraVez.getByRole('button', {
        name: /desactivar usuario|deactivate user/i,
      })
      await expect(papelera, 'la fila debe ofrecer la papelera de desactivar').toBeVisible({
        timeout: 20_000,
      })
      await papelera.click()

      const confirmacion = pageAdmin.getByRole('dialog').first()
      await expect(confirmacion, 'la papelera debe abrir una confirmación').toBeVisible({
        timeout: 20_000,
      })
      await confirmacion.getByRole('button', { name: /^desactivar$/i }).click()
      await expect(confirmacion).toBeHidden({ timeout: 20_000 })
      await expect(
        chip(filaOtraVez, 'Inactivo'),
        'confirmar la papelera deja la cuenta inactiva',
      ).toBeVisible({ timeout: 20_000 })

      // Lo que cierra el caso: el login del afectado, desde fuera del navegador.
      const login = await request.post(`${API}/login`, { data: { username, password: CLAVE } })
      expect(
        login.status(),
        `el login de una cuenta desactivada debe ser 403: ${await login.text()}`,
      ).toBe(403)
    } finally {
      await userCtx.close()
      await adminCtx.close()
    }
  })

  test('P-17-D · contraseña propia por la pantalla de Perfil (UI + API)', async ({
    browser,
    request,
  }) => {
    // `AC-UI-05`: el cambio de clave es una pantalla, no un endpoint. Lo que aquí se juzga es
    // lo que la pantalla dice en cada intento y qué credencial queda válida al final.
    const s = sufijo()
    const username = `p17b-d-${s}`

    const cab = await cabeceraAdmin(request)
    const roleId = await crearRol(request, cab, `p17b-rol-${s}`, [
      { module: 'lots', action: 'read' },
    ])
    await crearUsuario(request, cab, { username, clave: CLAVE, role_id: roleId })

    const userCtx = await browser.newContext()
    const pageUser = await userCtx.newPage()

    // Cuántas veces la pantalla llegó a pedir el cambio de contraseña. Un formulario que
    // valida en cliente no debe mandar una confirmación discrepante al servidor.
    let peticionesDeClave = 0
    pageUser.on('request', peticion => {
      if (peticion.method() !== 'GET' && /\/users\/[^/]+\/password/.test(peticion.url())) {
        peticionesDeClave += 1
      }
    })

    try {
      await entrarComo(pageUser, username, CLAVE)
      await pageUser.goto('/profile')
      await expect(
        pageUser.locator('input[type="password"]').first(),
        'el perfil debe ofrecer el formulario de contraseña',
      ).toBeVisible({ timeout: 20_000 })

      // ── (a) nueva ≠ confirmación: se avisa y no se llama al servidor ─────────
      peticionesDeClave = 0
      await rellenarClaves(pageUser, CLAVE, CLAVE_NUEVA, `${CLAVE_NUEVA}-otra`)
      await enviarClaves(pageUser)
      await verTexto(pageUser, /no coinciden|no son iguales|coincidir|match|discrepan/i)
      // Margen corto para que una petición tardía, si existiera, llegue a contarse.
      await pageUser.waitForTimeout(1500)
      expect(
        peticionesDeClave,
        'una confirmación discrepante no debe llegar al servidor: la valida la pantalla',
      ).toBe(0)

      // ── (b) nueva de 7 caracteres: se avisa del mínimo ──────────────────────
      await rellenarClaves(pageUser, CLAVE, 'Ab1!xyz', 'Ab1!xyz')
      await enviarClaves(pageUser)
      await verTexto(pageUser, /m[ií]nimo|al menos 8|8 caracteres|at least 8|minimum|too short/i)

      // ── (c) actual incorrecta: manda el mensaje del servidor, no un éxito ────
      await rellenarClaves(pageUser, 'ClaveEquivocada!1', CLAVE_NUEVA, CLAVE_NUEVA)
      await enviarClaves(pageUser)
      await verTexto(pageUser, /no es correcta|incorrecta|incorrect|inv[aá]lid|actual password/i)
      expect(
        (await pageUser.locator('body').innerText()).replace(/\s+/g, ' '),
        'un intento fallido no puede anunciarse como actualizado',
      ).not.toMatch(/actualizada|updated/i)

      // ── (d) actual correcta + nueva válida: éxito real ──────────────────────
      await rellenarClaves(pageUser, CLAVE, CLAVE_NUEVA, CLAVE_NUEVA)
      await enviarClaves(pageUser)
      await verTexto(pageUser, /actualizada|updated/i)
      expect(peticionesDeClave, 'el intento bueno sí debe llegar al servidor').toBeGreaterThan(0)

      // ── La clave vieja deja de abrir y la nueva abre ────────────────────────
      await cerrarSesion(pageUser)
      await intentarLogin(pageUser, username, CLAVE)
      await expect(pageUser, 'la clave vieja ya no debe entrar').toHaveURL(/\/login/, {
        timeout: 20_000,
      })
      await verTexto(pageUser, /incorrect|inv[aá]lid|no es correcta|credenciales|desactivada/i)

      await entrarComo(pageUser, username, CLAVE_NUEVA)
      const me = await apiConToken(pageUser, '/me')
      expect(me.status, `con la clave nueva la sesión debe servir: ${JSON.stringify(me.body)}`).toBe(
        200,
      )

      // Y desde fuera del navegador, contra el login de verdad: vieja 401, nueva 200.
      const vieja = await request.post(`${API}/login`, {
        data: { username, password: CLAVE },
      })
      expect(vieja.status(), `login con la clave vieja: ${await vieja.text()}`).toBe(401)

      const nueva = await request.post(`${API}/login`, {
        data: { username, password: CLAVE_NUEVA },
      })
      expect(nueva.status(), `login con la clave nueva: ${await nueva.text()}`).toBe(200)
    } finally {
      await userCtx.close()
    }
  })
})

