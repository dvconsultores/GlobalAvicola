import { test, expect } from '@playwright/test'

// Helper: login and return page ready for use
async function loginAs(page: any, username = 'admin', password = 'admin123') {
  await page.goto('/login')
  await page.fill('input[name="username"]', username)
  await page.fill('input[name="password"]', password)
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/(dashboard|$)/, { timeout: 8000 }).catch(() => {})
}

test.describe('Global Avícola E2E', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('h1')).toContainText(/global avícola|iniciar sesión/i)
  })

  test('login redirects to dashboard on success', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/login', { timeout: 5000 }).catch(() => {})
    const url = page.url()
    expect(url).not.toContain('/login')
  })

  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto('/operations')
    await page.waitForURL('**/login', { timeout: 5000 })
    expect(page.url()).toContain('/login')
  })

  test('dashboard loads for authenticated user', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/', { timeout: 5000 }).catch(() => {})
    await expect(page.locator('h1')).toContainText(/dashboard|panel/i)
  })

  test('mobile viewport shows bottom nav', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/login')
    await expect(page.locator('nav')).toBeVisible()
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

  test('farm_inspection: second house row can be deleted', async ({ page }) => {
    await loginAs(page)
    await page.goto('/operations/new?type=farm_inspection')
    await page.waitForLoadState('networkidle')
    await page.click('button:has-text("Añadir galpón")')
    await expect(page.locator('text=Galpón 2')).toBeVisible()
    // Delete the second row (trash button, first occurrence after index 0)
    const trashButtons = page.locator('button[type="button"]').filter({ hasText: '' })
    // The delete button uses Trash2 icon — locate by aria or position after second card
    await page.locator('text=Galpón 2').locator('..').locator('button').click()
    await expect(page.locator('text=Galpón 2')).not.toBeVisible({ timeout: 2000 })
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

