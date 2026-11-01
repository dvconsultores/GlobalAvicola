/**
 * P-17 — AUTORIDAD DINÁMICA EN NAVEGADOR REAL   (SPEC 013 · `AC-E2E-01`, `AC-UI-01/02`, `AC-SS-02`)
 *
 * Las suites de autorización por API demuestran que el backend decide bien. Lo que **no**
 * demuestran es lo que ve una persona: que al retirar un permiso la sesión abierta deja de
 * poder leer, que la interfaz lo refleja sin volver a entrar, y que los diálogos de
 * administración son realmente clicables — no una capa tapada por el modal que los abre.
 *
 *   `AC-SS-02`  una sesión que conserva permisos cacheados del login sigue mandando después de
 *               que se los quiten: la revocación no surte efecto hasta el siguiente login.
 *   `AC-UI-01`  el `ConfirmDialog` del portal quedaba por debajo del `Modal` que lo invoca:
 *               el botón se ve y no recibe el clic.
 *   `AC-UI-02`  el panel mezclaba la concesión viva con el histórico, de modo que una unidad
 *               re-concedida seguía anunciándose como «revocada».
 *
 * Por eso cada caso encadena ALLOW → REVOKE → DENY → RESTORE → ALLOW **con el mismo token** y
 * a través de la interfaz siempre que la interfaz tenga algo que decir.
 */
import { test, expect, type Page } from '@playwright/test'
import { API, cabeceraAdmin, crearEscenario, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'
import {
  apiConToken,
  codigosEfectivos,
  crearRol,
  crearUsuario,
  entrarComo,
  tokenDe,
} from '../test-support/admin-rbac'

/** Clave de los usuarios efímeros: mayúscula, minúscula, dígito y símbolo. */
const CLAVE = 'Spec013!2024'

/** Escapa un literal para usarlo dentro de una expresión regular. */
function esc(texto: string): string {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Pares `modulo:accion` que declara `/me`, vengan como cadenas o como objetos. */
function permisosDe(me: any): string[] {
  return ((me?.permissions ?? []) as any[])
    .map(p => (typeof p === 'string' ? p : `${p?.module}:${p?.action}`))
    .filter((p: string) => p.includes(':'))
}

/**
 * Edita los permisos de un rol desde `/roles`, la superficie real de administración.
 *
 * El modal se abre con el botón de **la fila del rol** —no con «Nuevo rol»—: editar y crear
 * son acciones distintas y confundirlas dejaría sin probar el camino que aquí importa.
 */
async function editarRol(
  page: Page,
  nombre: string,
  cambios: { marcar?: string[]; desmarcar?: string[] },
): Promise<void> {
  await page.goto('/roles')
  await expect(page.getByRole('button', { name: /nuevo rol|new role/i })).toBeVisible({
    timeout: 20_000,
  })

  const fila = page.getByRole('row').filter({ hasText: nombre })
  await expect(fila, 'el rol debe aparecer en el listado de /roles').toBeVisible({ timeout: 20_000 })
  await fila.getByRole('button', { name: /editar rol|edit role/i }).click()

  for (const permiso of cambios.desmarcar ?? []) {
    const casilla = page.getByRole('checkbox', { name: permiso }).first()
    await expect(casilla, `${permiso} debe estar en el catálogo`).toBeVisible()
    await casilla.uncheck()
  }
  for (const permiso of cambios.marcar ?? []) {
    const casilla = page.getByRole('checkbox', { name: permiso }).first()
    await expect(casilla, `${permiso} debe estar en el catálogo`).toBeVisible()
    await casilla.check()
  }

  await page.getByRole('button', { name: /guardar|save/i }).click()
  // El modal se cierra cuando el backend confirma: esperar el cierre evita leer la respuesta
  // de autorización antes de que el cambio esté persistido.
  await expect(page.getByRole('button', { name: /guardar|save/i })).toBeHidden({ timeout: 20_000 })
}

test.describe('P-17 · autoridad dinámica (SPEC 013)', () => {
  test('P-17-A · permiso: ALLOW → REVOKE → DENY → RESTORE → ALLOW (mismo token, UI + API)', async ({
    browser,
    request,
  }) => {
    // `AC-SS-02`: un permiso retirado debe dejar de autorizar **en la sesión ya abierta**.
    const s = sufijo()
    const nombreRol = `p17-rol-${s}`
    const username = `p17-a-${s}`

    const cab = await cabeceraAdmin(request)
    const roleId = await crearRol(request, cab, nombreRol, [
      { module: 'audit', action: 'read' },
      { module: 'lots', action: 'read' },
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
      // La página se pinta con su título y sin estado de denegación. `/audit` lista tarjetas,
      // no una tabla: se comprueba el encabezado, que es lo que existe en ambas ramas.
      await pageUser.goto('/audit')
      await expect(pageUser.getByRole('heading', { name: /auditor[ií]a|audit/i }).first()).toBeVisible(
        { timeout: 20_000 },
      )
      await expect(
        pageUser.getByRole('alert').filter({ hasText: /no tiene permiso|no permission|permission/i }),
        'con permiso no debe aparecer ningún aviso de denegación',
      ).toHaveCount(0)

      const permitido = await apiConToken(pageUser, '/audit?limit=1')
      expect(permitido.status, `audit con permiso: ${JSON.stringify(permitido.body)}`).toBe(200)

      // El token que se reutiliza en todo el caso: si cambiara, la prueba no probaría nada.
      const token = await tokenDe(pageUser)

      // ── REVOKE (administración, por la interfaz) ─────────────────────────────
      await editarRol(pageAdmin, nombreRol, { marcar: ['lots:read'], desmarcar: ['audit:read'] })

      // ── DENY inmediato, sin recargar ni volver a entrar ──────────────────────
      const denegado = await apiConToken(pageUser, '/audit?limit=1', token)
      expect(
        denegado.status,
        `tras revocar, el mismo token debe recibir 403: ${JSON.stringify(denegado.body)}`,
      ).toBe(403)
      expect(String(denegado.body?.detail ?? '')).toMatch(/permiso requerido:\s*audit:read/i)

      const me = await apiConToken(pageUser, '/me', token)
      expect(me.status).toBe(200)
      const permisos = permisosDe(me.body)
      expect(permisos, 'audit:read no debe seguir declarado').not.toContain('audit:read')
      expect(permisos, 'lots:read no se retiró y debe seguir').toContain('lots:read')

      // ── La interfaz de la sesión viva refleja la denegación ──────────────────
      // No es el `ErrorState` de la página: el guardia de ruta corta antes y muestra su propio
      // aviso. Lo que importa es que la sesión abierta ve una denegación y ningún dato.
      await pageUser.goto('/audit')
      const sinPermiso = pageUser
        .getByRole('alert')
        .filter({ hasText: /permiso|permission/i })
        .first()
      await expect(sinPermiso, 'la sesión viva debe ver la denegación, no datos').toBeVisible({
        timeout: 20_000,
      })
      await expect(
        pageUser.getByRole('heading', { name: /auditor[ií]a|audit/i }),
        'la pantalla autorizada de auditoría no debe montarse',
      ).toHaveCount(0)

      await pageUser.reload()
      // La señal de sesión viva es el armazón de la aplicación; `/lots` no es un enlace del
      // menú (vive dentro de «Gestión Avícola»), así que no sirve para esperar.
      await expect(
        pageUser.getByRole('button', { name: /cerrar sesi[oó]n|log ?out|sign ?out/i }).first(),
      ).toBeVisible({ timeout: 20_000 })
      await expect(
        pageUser.locator('a[href="/audit"]'),
        'sin audit:read el menú no debe ofrecer auditoría',
      ).toHaveCount(0)

      // ── RESTORE (administración, por la interfaz) ────────────────────────────
      await editarRol(pageAdmin, nombreRol, { marcar: ['audit:read'] })

      // ── ALLOW otra vez, con el MISMO token ───────────────────────────────────
      const restaurado = await apiConToken(pageUser, '/audit?limit=1', token)
      expect(
        restaurado.status,
        `tras restaurar, el mismo token debe volver a leer: ${JSON.stringify(restaurado.body)}`,
      ).toBe(200)
      expect(permisosDe((await apiConToken(pageUser, '/me', token)).body)).toContain('audit:read')

      await pageUser.reload()
      await expect(pageUser.locator('a[href="/audit"]').first()).toBeVisible({ timeout: 20_000 })
      await pageUser.goto('/audit')
      await expect(pageUser.getByRole('heading', { name: /auditor[ií]a|audit/i }).first()).toBeVisible(
        { timeout: 20_000 },
      )
      await expect(pageUser.getByRole('alert').filter({ hasText: /permiso|permission/i })).toHaveCount(0)
    } finally {
      await userCtx.close()
      await adminCtx.close()
    }
  })

  test('P-17-B · unidad de negocio: ALLOW → REVOKE → DENY → RESTORE → ALLOW (panel de Usuarios)', async ({
    browser,
    request,
  }) => {
    // `AC-UI-01` (el diálogo del portal es clicable), `AC-UI-02` (manda la concesión viva),
    // `AC-UI-03` (empresa frente a usuario) y `AC-UI-04` (el diálogo dice a quién y qué).
    const s = sufijo()
    const nombreRol = `p17-rol-${s}`
    const username = `p17-b-${s}`

    const cab = await cabeceraAdmin(request)

    // La empresa necesita las dos unidades habilitadas para poder concederlas.
    for (const codigo of ['breeder', 'broiler']) {
      const r = await request.patch(`${API}/business-units/${codigo}/enable`, { headers: cab })
      expect([200, 201], `habilitar ${codigo}: ${await r.text()}`).toContain(r.status())
    }

    const roleId = await crearRol(request, cab, nombreRol, [{ module: 'lots', action: 'read' }])
    const userId = await crearUsuario(request, cab, { username, clave: CLAVE, role_id: roleId })

    const concesion = await request.post(`${API}/users/${userId}/business-units`, {
      headers: cab,
      data: { code: 'broiler' },
    })
    expect([200, 201], `conceder broiler: ${await concesion.text()}`).toContain(concesion.status())

    // Un lote real de la unidad concedida: es el recurso cuya visibilidad cambia.
    const escenario = await crearEscenario(request, cab, `P17B-${s}`, 'broiler')

    const adminCtx = await browser.newContext()
    const userCtx = await browser.newContext()
    const pageAdmin = await adminCtx.newPage()
    const pageUser = await userCtx.newPage()

    try {
      await entrar(pageAdmin, 'admin')
      await entrarComo(pageUser, username, CLAVE)

      // ── ALLOW ────────────────────────────────────────────────────────────────
      const lotePermitido = await apiConToken(pageUser, `/lots/${escenario.lotId}`)
      expect(
        lotePermitido.status,
        `el lote de broiler debe verse con la concesión viva: ${JSON.stringify(lotePermitido.body)}`,
      ).toBe(200)
      expect(codigosEfectivos((await apiConToken(pageUser, '/me')).body)).toContain('broiler')
      const token = await tokenDe(pageUser)

      // ── Panel de unidades de negocio de U, desde `/users` ────────────────────
      await pageAdmin.goto('/users')
      const fila = pageAdmin.getByRole('row').filter({ hasText: username })
      await expect(fila, 'el usuario debe aparecer en /users').toBeVisible({ timeout: 20_000 })

      const botonPanel = fila.getByRole('button', {
        name: new RegExp(`unidades de negocio[\\s\\S]*${esc(username)}`, 'i'),
      })
      await expect(botonPanel, 'el botón del panel debe nombrar al usuario').toBeVisible()
      await botonPanel.click()

      const panel = pageAdmin.getByRole('dialog').first()
      await expect(panel).toBeVisible({ timeout: 20_000 })

      // `AC-UI-03`: el panel distingue lo que la **empresa** habilita de lo que este **usuario**
      // tiene concedido. Sin esa separación, administrar unidades es adivinar.
      await expect(panel.getByText(/empresa:|company:/i).first()).toBeVisible()
      await expect(panel.getByText(/usuario:|user:/i).first()).toBeVisible()

      // Cada unidad es un `listitem` con su estado y su botón. El panel la rotula con su nombre
      // de negocio, no con el código: «Engorde» en español, «Broiler» en inglés.
      const UNIDAD = /engorde|broiler/i
      const filaUnidad = () => panel.getByRole('listitem').filter({ hasText: UNIDAD })

      // ── REVOKE desde el panel, confirmando en el diálogo del portal (`AC-UI-01`) ──
      await expect(
        filaUnidad(),
        'el panel debe listar la unidad concedida, y una sola vez',
      ).toHaveCount(1)
      const revocar = filaUnidad().getByRole('button', { name: /revocar|revoke/i })
      await expect(revocar).toBeVisible()
      await revocar.click()

      // El diálogo del portal se monta **después** del modal que lo invoca, de modo que con el
      // panel delante es el segundo diálogo. Se fija por posición y no por `.last()` porque al
      // cerrarse `.last()` volvería a resolver al panel y la comprobación de cierre sería vacua.
      const confirmacion = pageAdmin.getByRole('dialog').nth(1)
      await expect(confirmacion).toBeVisible({ timeout: 20_000 })
      // `AC-UI-04`: la confirmación nombra al usuario y la unidad, no «¿seguro?».
      await expect(confirmacion).toContainText(new RegExp(esc(username)))
      await expect(confirmacion).toContainText(UNIDAD)

      const confirmarRevocar = confirmacion.getByRole('button', { name: /revocar|revoke/i })
      await expect(
        confirmarRevocar,
        'el botón del diálogo debe recibir el clic: si el Modal lo tapa, aquí se ve',
      ).toBeVisible()
      await confirmarRevocar.click()
      await expect(confirmacion).toBeHidden({ timeout: 20_000 })

      // `AC-UI-02`: tras revocar, la unidad deja de estar viva y se ofrece concederla.
      await expect(filaUnidad().getByRole('button', { name: /conceder|grant/i })).toBeVisible({
        timeout: 20_000,
      })

      // ── DENY con el MISMO token, sin recargar ni volver a entrar ─────────────
      const loteDenegado = await apiConToken(pageUser, `/lots/${escenario.lotId}`, token)
      expect(
        loteDenegado.status,
        `sin concesión viva el lote no debe existir para el usuario: ${JSON.stringify(loteDenegado.body)}`,
      ).toBe(404)
      const meSinBroiler = await apiConToken(pageUser, '/me', token)
      expect(meSinBroiler.status).toBe(200)
      expect(codigosEfectivos(meSinBroiler.body)).not.toContain('broiler')

      // ── RESTORE desde el mismo panel ─────────────────────────────────────────
      const conceder = filaUnidad().getByRole('button', { name: /conceder|grant/i })
      await expect(conceder).toBeVisible()
      await conceder.click()

      // `AC-UI-02`: re-concedida significa «Concedida» **y** «Efectiva», nunca «Revocada
      // (histórica)». El histórico no puede secuestrar el estado de la concesión viva.
      await expect(
        filaUnidad().getByText(/concedida|granted/i).first(),
        'la concesión viva debe anunciarse como concedida',
      ).toBeVisible({ timeout: 20_000 })
      await expect(
        filaUnidad().getByText(/efectiva|effective/i).first(),
        'y como efectiva',
      ).toBeVisible()
      await expect(
        filaUnidad().getByText(/revocada\s*\((hist[oó]rica|historical)\)/i),
        'la unidad viva no puede seguir anunciándose como revocada histórica',
      ).toHaveCount(0)

      // ── ALLOW otra vez, con el MISMO token ───────────────────────────────────
      const loteRestaurado = await apiConToken(pageUser, `/lots/${escenario.lotId}`, token)
      expect(
        loteRestaurado.status,
        `re-concedida la unidad, el mismo token debe volver a ver el lote: ${JSON.stringify(loteRestaurado.body)}`,
      ).toBe(200)
      expect(codigosEfectivos((await apiConToken(pageUser, '/me', token)).body)).toContain('broiler')

      // ── El histórico conserva lo ocurrido y solo una concesión está viva ─────
      const listado = await request.get(`${API}/users/${userId}/business-units`, { headers: cab })
      expect(listado.status()).toBe(200)
      const filasBroiler = ((await listado.json()) as any[]).filter(f => f.code === 'broiler')
      expect(filasBroiler, 'revocar y re-conceder deja dos filas de broiler').toHaveLength(2)

      const vivas = filasBroiler.filter(f => f.is_effective === true)
      expect(vivas, `exactamente una concesión viva: ${JSON.stringify(filasBroiler)}`).toHaveLength(1)
      expect(vivas[0].revoked_at, 'la concesión viva no puede estar revocada').toBeNull()
      expect(
        filasBroiler.filter(f => f.is_effective === false && f.revoked_at !== null),
        'la revocada conserva su fecha: el histórico no se borra',
      ).toHaveLength(1)
    } finally {
      await userCtx.close()
      await adminCtx.close()
    }
  })
})

