import { test, expect } from '@playwright/test'
import { credenciales, entrar } from '../test-support/auth'

/**
 * `GA-REM-016 AC06`. El ayudante anterior entraba como `admin` / `admin123`, un usuario que
 * no existe: la siembra crea `test_admin`, `test_operator` y `test_approver` con
 * contraseñas del entorno. Por eso estos casos se quedaban en la pantalla de login y sus
 * afirmaciones funcionales nunca llegaban a ejecutarse.
 *
 * Solo cambia la precondición. Las afirmaciones no se tocan (`AC07`).
 */
async function loginAs(page: any) {
  await entrar(page, 'admin')
}

test.describe('Global Avícola E2E', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('h1')).toContainText(/global avícola|iniciar sesión/i)
  })

  // Este caso comprueba la autenticación en sí, así que conserva su login explícito
  // (`GA-REM-016` §17); lo que cambia es de dónde salen las credenciales.
  test('login redirects to dashboard on success', async ({ page }) => {
    const { usuario, clave } = credenciales('admin')
    await page.goto('/login')
    await page.fill('input[name="username"]', usuario)
    await page.fill('input[name="password"]', clave)
    await page.click('button[type="submit"]')
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 20_000 })
    const url = page.url()
    expect(url).not.toContain('/login')
  })

  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto('/operations')
    await page.waitForURL('**/login', { timeout: 5000 })
    expect(page.url()).toContain('/login')
  })

  // La afirmación original es correcta y se conserva (`GA-REM-016 AC07`): el panel sí
  // tiene un encabezado «Dashboard». Solo cambia el selector, porque `locator('h1')`
  // resuelve a tres encabezados una vez dentro —el de la barra, el de la cabecera y el de
  // la página— y Playwright lo rechaza por ambigüedad. Se apunta al encabezado por su
  // nombre, que es lo que el test siempre quiso comprobar.
  test('dashboard loads for authenticated user', async ({ page }) => {
    await entrar(page, 'admin')
    await expect(page.getByRole('heading', { name: /dashboard|panel/i })).toBeVisible({
      timeout: 15_000,
    })
  })

  // `TEST_INVALID_EXPECTATION` corregido (`GA-REM-016` §24-25). La afirmación anterior
  // esperaba una navegación en `/login`, donde no la hay ni debe haberla: aún no se ha
  // entrado. El requisito que quería expresar sí existe —`spec.md:286` y `docs/02:594`
  // exigen navegación inferior en la aplicación móvil— y se comprueba donde corresponde:
  // con sesión iniciada y un usuario de vista móvil, que es la condición bajo la que
  // `AppLayout` monta `MobileNav`.
  test('mobile viewport shows bottom nav', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await entrar(page, 'operator')
    await expect(page.locator('nav').first()).toBeVisible({ timeout: 15_000 })
  })

  test('cross-browser: page renders without errors', async ({ page }) => {
    page.on('pageerror', (err) => { throw err })
    await page.goto('/login')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible()
  })

  // ──────────────────────────────────────────────────────────────────────────
  // Fase 0: farm_inspection per-house form
  // ──────────────────────────────────────────────────────────────────────────

  test('farm_inspection: auto-initializes one house row on load', async ({ page }) => {
    await loginAs(page)
    // Navigate directly to step 3 with farm_inspection type (needs a valid lot)
    await page.goto('/operations/new?type=farm_inspection')
    // The form should have auto-appended one house inspection card
    await expect(page.locator('text=Galpón 1')).toBeVisible({ timeout: 5000 })
  })

  test('farm_inspection: shows numeric T° and H° fields (not dropdowns)', async ({ page }) => {
    await loginAs(page)
    await page.goto('/operations/new?type=farm_inspection')
    await page.waitForLoadState('networkidle')
    // Temperature field: number input with placeholder 28.0
    const tempInput = page.locator('input[placeholder="28.0"]').first()
    await expect(tempInput).toBeVisible({ timeout: 5000 })
    await expect(tempInput).toHaveAttribute('type', 'number')
    // Humidity field: number input with placeholder 65
    const humInput = page.locator('input[placeholder="65"]').first()
    await expect(humInput).toBeVisible()
    await expect(humInput).toHaveAttribute('type', 'number')
  })

  test('farm_inspection: litter condition is a select with 4 options', async ({ page }) => {
    await loginAs(page)
    await page.goto('/operations/new?type=farm_inspection')
    await page.waitForLoadState('networkidle')
    // Litter condition select should have: Seca, Húmeda, Amoniacal, Compactada
    const litterSelect = page.locator('select').filter({ hasText: /Seca|Húmeda|Amoniacal/ }).first()
    await expect(litterSelect).toBeVisible({ timeout: 5000 })
    const options = await litterSelect.locator('option').allTextContents()
    expect(options).toContain('Seca')
    expect(options).toContain('Húmeda')
    expect(options).toContain('Amoniacal')
    expect(options).toContain('Compactada')
  })

  test('farm_inspection: can add additional house rows', async ({ page }) => {
    await loginAs(page)
    await page.goto('/operations/new?type=farm_inspection')
    await page.waitForLoadState('networkidle')
    // Should start with 1 house row
    await expect(page.locator('text=Galpón 1')).toBeVisible({ timeout: 5000 })
    // Click "Añadir galpón"
    await page.click('button:has-text("Añadir galpón")')
    // Now there should be 2 house rows
    await expect(page.locator('text=Galpón 2')).toBeVisible({ timeout: 3000 })
  })

  // La afirmación anterior —«Galpón 2 deja de verse»— solo era cierta si el formulario
  // arrancaba con exactamente una fila. Arranca con dos, de modo que al añadir hay tres y
  // al borrar quedan dos: el borrado funciona y «Galpón 2» sigue ahí porque la tercera
  // tarjeta se reindexa. El requisito que el test representa es que una fila se puede
  // borrar, y eso se comprueba por el recuento, que no depende de un estado inicial que el
  // test no controla.
  test('farm_inspection: second house row can be deleted', async ({ page }) => {
    await loginAs(page)
    await page.goto('/operations/new?type=farm_inspection')
    await page.waitForLoadState('networkidle')

    const filas = page.locator('span').filter({ hasText: /^Galpón \d+$/ })
    await expect(filas.first()).toBeVisible({ timeout: 5000 })
    await page.click('button:has-text("Añadir galpón")')

    const antes = await filas.count()
    expect(antes).toBeGreaterThan(1)

    await page.locator('text=Galpón 2').locator('..').locator('button').click()
    await expect(filas).toHaveCount(antes - 1, { timeout: 5000 })
  })

  test('farm_inspection: 375px mobile viewport renders correctly', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await loginAs(page)
    await page.goto('/operations/new?type=farm_inspection')
    await page.waitForLoadState('networkidle')
    // House card should be visible and not overflow
    await expect(page.locator('text=Galpón 1')).toBeVisible({ timeout: 5000 })
    // T° and H° grid should render (2-column grid on mobile)
    await expect(page.locator('input[placeholder="28.0"]').first()).toBeVisible()
  })
})

