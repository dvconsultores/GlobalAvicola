/**
 * P-17-E/F — SESIÓN Y CONSISTENCIA   (SPEC 013 · `AC-SS-01`, `AC-SS-02`)
 *
 * Extiende P-17 al transporte: que un 401 redirigido por el interceptor de `api.ts` a
 * `POST /refresh` **no degrade la autoridad** de la sesión abierta, y que un 403 reconcilie
 * los permisos del store (menú incluido) **sin recargar** la página.
 */
import { test, expect } from '@playwright/test'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import {
  apiConToken,
  crearRol,
  crearUsuario,
  entrarComo,
  tokenDe,
} from '../test-support/admin-rbac'

/** Clave de los usuarios efímeros: mayúscula, minúscula, dígito y símbolo. */
const CLAVE = 'Spec013!2024'

/** Aviso de denegación del guardia de ruta (`AC-SS-02`). */
const SIN_PERMISO = /no tiene permiso|no permission|permission/i

test.describe('P-17 · sesión y consistencia (SPEC 013)', () => {
  test('P-17-E · el refresh automático conserva la autoridad', async ({ browser, request }) => {
    // `AC-SS-01`: el 401 lo absorbe el interceptor; tras `POST /refresh` la sesión se rehidrata
    // desde `/me` y la petición original se reintenta con el token nuevo. Un permiso que se
    // perdiera por ese camino se vería aquí: enlace del menú y lectura de `/audit`.
    const s = sufijo()
    const nombreRol = `p17c-rol-e-${s}`
    const username = `p17c-e-${s}`

    const cab = await cabeceraAdmin(request)
    const roleId = await crearRol(request, cab, nombreRol, [
      { module: 'audit', action: 'read' },
      { module: 'lots', action: 'read' },
    ])
    await crearUsuario(request, cab, { username, clave: CLAVE, role_id: roleId })

    const userCtx = await browser.newContext()
    const pageUser = await userCtx.newPage()
    /** Traza ordenada de las respuestas de sesión, para exigir que la `/me` sea POSTERIOR. */
    const traza: string[] = []
    const peticiones: string[] = []
    pageUser.on('request', r => peticiones.push(r.method() + ' ' + r.url()))
    pageUser.on('response', r => {
      const url = r.url().split('?')[0]
      if (url.endsWith('/api/v1/refresh')) traza.push(`refresh:${r.status()}`)
      if (url.endsWith('/api/v1/me')) traza.push(`me:${r.status()}`)
    })

    try {
      await entrarComo(pageUser, username, CLAVE)
      const enlace = pageUser.locator('a[href="/audit"]').first()
      await expect(enlace, 'con audit:read el menú debe ofrecer auditoría').toBeVisible({
        timeout: 20_000,
      })

      // Una sola petición de auditoría caduca: las siguientes (el reintento) pasan.
      let interceptadas = 0
      await pageUser.route('**/api/v1/audit**', async route => {
        interceptadas += 1
        if (interceptadas === 1) {
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Token expirado' }),
          })
          return
        }
        await route.continue()
      })

      await enlace.click()

      // El refresh ocurrió y la rehidratación vino DESPUÉS: si el orden se invirtiera, la
      // sesión seguiría con los permisos viejos del login.
      const refrescoYRehidratacion = () => {
        const i = traza.indexOf('refresh:200')
        return i >= 0 && traza.slice(i + 1).some(r => r.startsWith('me:'))
      }
      await expect
        .poll(refrescoYRehidratacion, {
          timeout: 30_000,
          message: `debe haber un refresh 200 seguido de /me: ${JSON.stringify(traza)} / interceptadas=${interceptadas} / ${JSON.stringify(peticiones.slice(-25))}`,
        })
        .toBe(true)

      // La página se pinta igual que antes del 401: mismo encabezado, sin denegación.
      await expect(
        pageUser.getByRole('heading', { name: /auditor[ií]a|audit/i }).first(),
        'la auditoría debe pintarse tras el refresh',
      ).toBeVisible({ timeout: 20_000 })
      await expect(
        pageUser.getByRole('alert').filter({ hasText: SIN_PERMISO }),
        'un refresh no puede costar un permiso',
      ).toHaveCount(0)
      await expect(enlace, 'y el menú sigue ofreciendo auditoría').toBeVisible()

      const nuevoToken = await tokenDe(pageUser)
      const permitido = await apiConToken(pageUser, '/audit?limit=1', nuevoToken)
      expect(
        permitido.status,
        `con el token renovado la lectura debe seguir autorizada: ${JSON.stringify(permitido.body)}`,
      ).toBe(200)
    } finally {
      await userCtx.close()
    }
  })

  test('P-17-F · un 403 reconcilia la sesión sin recargar', async ({ browser, request }) => {
    // `AC-SS-02`: la UI cree tener `audit:read` cuando el backend ya no lo concede. El 403 que
    // recibe al navegar dispara una rehidratación de `/me`; el store se actualiza y el menú se
    // corrige **sin recargar** — que es justo lo que el usuario no debería tener que hacer.
    const s = sufijo()
    const nombreRol = `p17c-rol-f-${s}`
    const username = `p17c-f-${s}`
    const permiso = (module: string) => ({ module, action: 'read', scope_type: 'all' })

    const cab = await cabeceraAdmin(request)
    const roleId = await crearRol(request, cab, nombreRol, [
      { module: 'audit', action: 'read' },
      { module: 'lots', action: 'read' },
    ])
    await crearUsuario(request, cab, { username, clave: CLAVE, role_id: roleId })

    const userCtx = await browser.newContext()
    const pageUser = await userCtx.newPage()
    let rehidrataciones = 0
    pageUser.on('response', r => {
      if (r.url().split('?')[0].endsWith('/api/v1/me')) rehidrataciones += 1
    })

    try {
      await entrarComo(pageUser, username, CLAVE)
      const enlace = pageUser.locator('a[href="/audit"]').first()
      await expect(enlace, 'con audit:read el menú debe ofrecer auditoría').toBeVisible({
        timeout: 20_000,
      })

      // ── REVOKE por API: el rol se queda solo con `lots:read` ─────────────────
      const revocado = await request.put(`${API}/roles/${roleId}`, {
        headers: cab,
        data: { permissions: [permiso('lots')] },
      })
      expect(revocado.status(), `PUT /roles: ${await revocado.text()}`).toBe(200)

      // El backend ya no autoriza esa credencial; la UI todavía no lo sabe.
      const denegado = await apiConToken(pageUser, '/audit?limit=1')
      expect(
        denegado.status,
        `el mismo token debe recibir 403: ${JSON.stringify(denegado.body)}`,
      ).toBe(403)

      // Marca de vida: si la página se recargara, `window` la perdería.
      await pageUser.evaluate(() => ((window as any).__p17c = 'vivo'))
      const antes = rehidrataciones

      // ── Clic en el enlace que la UI aún ofrece ⇒ 403 ⇒ reconciliación ───────
      await enlace.click()

      await expect
        .poll(() => rehidrataciones, {
          timeout: 15_000,
          message: 'el 403 debe provocar una rehidratación de /me',
        })
        .toBeGreaterThan(antes)

      // La denegación se ve y el menú deja de ofrecer auditoría, en la MISMA página.
      await expect(
        pageUser.getByRole('alert').filter({ hasText: SIN_PERMISO }).first(),
        'la sesión viva debe ver la denegación, no datos',
      ).toBeVisible({ timeout: 15_000 })
      await expect(
        pageUser.locator('a[href="/audit"]'),
        'reconciliada la sesión, el menú no debe seguir ofreciendo auditoría',
      ).toHaveCount(0, { timeout: 15_000 })
      expect(
        await pageUser.evaluate(() => (window as any).__p17c ?? null),
        'la reconciliación no puede exigir una recarga',
      ).toBe('vivo')

      // ── RESTORE por API y, ahora sí, recarga explícita ──────────────────────
      const restaurado = await request.put(`${API}/roles/${roleId}`, {
        headers: cab,
        data: { permissions: [permiso('lots'), permiso('audit')] },
      })
      expect(restaurado.status(), `PUT /roles (restore): ${await restaurado.text()}`).toBe(200)

      await pageUser.reload()
      await expect(
        pageUser.locator('a[href="/audit"]').first(),
        'devuelto audit:read, el menú vuelve a ofrecer auditoría',
      ).toBeVisible({ timeout: 20_000 })
    } finally {
      await userCtx.close()
    }
  })
})

