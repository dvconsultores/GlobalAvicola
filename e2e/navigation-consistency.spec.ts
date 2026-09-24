import { test, expect, type Page } from '@playwright/test'

/**
 * `specs/004-frontend-navigation-ui-consistency-remediation` · E2E de navegación (AC05/06/08/10/16-19).
 *
 * Spec AUTÓNOMO: no requiere backend real — todas las llamadas `/api/v1/**` se
 * stubbean con `page.route()`. La app se autentica por token en `sessionStorage`
 * (mismo mecanismo de arranque que producción) y `/me` se responde con un usuario
 * sintético. Solo depende del dev server de Vite (baseURL del config raíz).
 */

const API = '**/api/v1/**'

function fakeJwt(payload: Record<string, unknown>): string {
  const b64 = (o: unknown) => Buffer.from(JSON.stringify(o)).toString('base64url')
  return `${b64({ alg: 'none', typ: 'JWT' })}.${b64(payload)}.e2e-signature`
}

const WEB_USER = {
  id: 1, username: 'nav-tester', first_name: 'Nav', last_name: 'Tester', email: 'nav@example.com',
  role_id: 1, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
  company_name: 'Avícola Test', permissions: ['dashboard:read', 'operations:read', 'lots:read', 'masters:read'],
  company_business_units: ['broiler'], granted_business_units: ['broiler'], effective_business_units: ['broiler'],
}
const MOBILE_USER = { ...WEB_USER, view_type: 'mobile' }
const NO_PERMS_USER = {
  ...WEB_USER, permissions: ['dashboard:read'],
  granted_business_units: [], effective_business_units: [],
}

const LOTS = [
  { id: 91, lot_code: 'L-BO-NAV-01', bird_type: 'broiler', status: 'active' },
  { id: 92, lot_code: 'L-GP-NAV-01', bird_type: 'grandparent', status: 'active' },
]

async function boot(page: Page, user: Record<string, unknown>, viewType: 'web' | 'mobile') {
  await page.route(API, async (route) => {
    const url = route.request().url()
    if (url.includes('/me')) return route.fulfill({ json: user })
    if (/\/lots(\?|$)/.test(url)) {
      return route.fulfill({ json: LOTS, headers: { 'X-Total-Count': String(LOTS.length) } })
    }
    return route.fulfill({ json: [] })
  })
  const token = fakeJwt({ sub: '1', username: 'nav-tester', role_id: 1, view_type: viewType, company_id: 1 })
  await page.addInitScript((t: string) => {
    sessionStorage.setItem('access_token', t)
    sessionStorage.setItem('refresh_token', 'e2e-refresh')
  }, token)
}

/** El hub legacy (pre-menú) no debe montarse jamás. */
async function expectNoLegacyHub(page: Page) {
  await expect(page.getByText('Centro de Operaciones')).toHaveCount(0)
  await expect(page.getByText('Elige un Proceso')).toHaveCount(0)
}

test.describe('004 · navegación y consistencia UI', () => {
  test('UX-01 · /poultry redirige al hub estándar y no reaparece la UI legacy', async ({ page }) => {
    await boot(page, WEB_USER, 'web')
    await page.goto('/poultry')
    await expect(page).toHaveURL(/\/menu\/poultry$/)
    await expectNoLegacyHub(page)
  })

  test('AC02/AC19 · deep-link a etapa: back visible con fallback canónico al hub', async ({ page }) => {
    await boot(page, WEB_USER, 'web')
    await page.goto('/poultry/broiler')
    const back = page.getByTestId('back-navigation')
    await expect(back).toBeVisible()
    await expect(back).toContainText('Volver')
    await back.click()
    await expect(page).toHaveURL(/\/menu\/poultry$/)
    await expectNoLegacyHub(page)
  })

  test('AC05/AC06 · browser back/forward mantiene la UI estándar (sin legacy, sin pérdida de sesión)', async ({ page }) => {
    await boot(page, WEB_USER, 'web')
    await page.goto('/menu/poultry')
    await page.goto('/poultry/broiler')
    await page.getByTestId('back-navigation').click()
    await expect(page).toHaveURL(/\/menu\/poultry$/)

    await page.goBack()
    await expect(page).toHaveURL(/\/poultry\/broiler$/)
    await expect(page.getByTestId('back-navigation')).toBeVisible()

    await page.goForward()
    await expect(page).toHaveURL(/\/menu\/poultry$/)
    await expectNoLegacyHub(page)
  })

  test('AC10 · el filtro del listado de lotes se preserva al volver', async ({ page }) => {
    await boot(page, WEB_USER, 'web')
    await page.goto('/lots')
    await expect(page.getByText('L-BO-NAV-01').filter({ visible: true })).toBeVisible()
    await expect(page.getByText('L-GP-NAV-01').filter({ visible: true })).toBeVisible()

    await page.getByTestId('lot-filter-broiler').click()
    await expect(page.getByTestId('lot-filter-broiler')).toHaveAttribute('aria-pressed', 'true')
    await expect(page.getByText('L-GP-NAV-01').filter({ visible: true })).toHaveCount(0)

    // Navegar fuera y volver por browser-back (retorno real lista→detalle→lista).
    await page.goto('/poultry/broiler')
    await page.goBack()
    await expect(page).toHaveURL(/\/lots$/)
    await expect(page.getByTestId('lot-filter-broiler')).toHaveAttribute('aria-pressed', 'true')
    await expect(page.getByText('L-BO-NAV-01').filter({ visible: true })).toBeVisible()
    await expect(page.getByText('L-GP-NAV-01').filter({ visible: true })).toHaveCount(0)
  })

  test('AC13 · el RBAC no se evade: sin operations:read la etapa deniega y no hay back', async ({ page }) => {
    await boot(page, NO_PERMS_USER as Record<string, unknown>, 'web')
    await page.goto('/poultry/broiler')
    await expect(page.getByText('No tiene permiso para ver esta sección.')).toBeVisible()
    await expect(page.getByTestId('back-navigation')).toHaveCount(0)
  })

  test('AC16 · mobile 360px: back visible, sin overflow horizontal', async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 780 })
    await boot(page, MOBILE_USER, 'mobile')
    await page.goto('/poultry/broiler')
    const back = page.getByTestId('back-navigation')
    await expect(back).toBeVisible()
    const box = await back.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.x).toBeGreaterThanOrEqual(0)
    expect(box!.x + box!.width).toBeLessThanOrEqual(360)
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    expect(overflow).toBeLessThanOrEqual(1)
  })

  test('AC17 · mobile 390px: back visible, sin overflow horizontal', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await boot(page, MOBILE_USER, 'mobile')
    await page.goto('/poultry/broiler')
    await expect(page.getByTestId('back-navigation')).toBeVisible()
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    expect(overflow).toBeLessThanOrEqual(1)
  })

  test('AC18 · desktop: back visible en la etapa y hub estándar', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await boot(page, WEB_USER, 'web')
    await page.goto('/poultry/broiler')
    await expect(page.getByTestId('back-navigation')).toBeVisible()
    await page.goto('/menu/poultry')
    await expectNoLegacyHub(page)
  })
})
