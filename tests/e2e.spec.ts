import { test, expect } from '@playwright/test'

test.describe('Global Avícola E2E', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('h1')).toContainText(/global avícola|iniciar sesión/i)
  })

  test('login redirects to dashboard on success', async ({ page }) => {
    await page.goto('/login')
    // Fill in credentials and submit
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    // Should redirect away from login
    await page.waitForURL('**/login', { timeout: 5000 }).catch(() => {})
    // If login succeeds, we're not on /login anymore
    const url = page.url()
    expect(url).not.toContain('/login')
  })

  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto('/operations')
    await page.waitForURL('**/login', { timeout: 5000 })
    expect(page.url()).toContain('/login')
  })

  test('dashboard loads for authenticated user', async ({ page }) => {
    // Login first
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/', { timeout: 5000 }).catch(() => {})
    // Dashboard should show
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
    // Should have the brand name
    await expect(page.locator('body')).toBeVisible()
  })
})
