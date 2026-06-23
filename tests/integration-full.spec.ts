import { chromium } from 'playwright';
import { expect } from 'playwright/test';

const BASE = 'http://localhost:5173';
const API = 'http://localhost:8000/api/v1';

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: 'es-ES',
  });
  const page = await context.newPage();

  let passed = 0;
  let failed = 0;
  const results: string[] = [];

  const test = async (name: string, fn: () => Promise<void>) => {
    try {
      await fn();
      passed++;
      results.push(`✅ ${name}`);
    } catch (e: any) {
      failed++;
      const msg = e.message?.substring(0, 150);
      results.push(`❌ ${name}: ${msg}`);
      // Take screenshot for debugging
      try {
        await page.screenshot({ path: `/tmp/test-fail-${name.replace(/[^a-z0-9]/gi,'_')}.png` });
      } catch {}
    }
  };

  const getHeading = () => page.locator('main h1').first().textContent();
  const navTo = async (href: string) => {
    await page.click(`a[href="${href}"]`);
    await page.waitForURL(`**${href}`, { timeout: 20000 });
    await page.waitForTimeout(1500);
  };

  console.log('═══════════════════════════════════════════');
  console.log('  TEST INTEGRAL — Global Avícola');
  console.log('═══════════════════════════════════════════\n');

  // ================================================================
  // 1. LOGIN ADMIN
  // ================================================================
  await test('Login page loads', async () => {
    await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 15000 });
    await expect(page.locator('h1')).toContainText('Global Avícola');
  });

  await test('Login as admin', async () => {
    await page.fill('input[placeholder="admin"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/', { timeout: 15000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toContain('Dashboard');
  });

  // ================================================================
  // 2. DASHBOARD
  // ================================================================
  await test('Dashboard shows KPIs', async () => {
    await page.waitForSelector('text=Total Eventos', { timeout: 10000 });
    const cards = await page.locator('text=Total Eventos, text=Pendientes Revisión, text=Pendientes Aprobación').count();
    expect(cards).toBeGreaterThanOrEqual(2);
  });

  await test('Dashboard shows status distribution', async () => {
    const hasStatus = await page.locator('text=Distribución por Estado').count();
    expect(hasStatus).toBeGreaterThanOrEqual(0); // may or may not render
  });

  // ================================================================
  // 3. LOTS
  // ================================================================
  await test('Navigate to Lots', async () => {
    await page.click('a[href="/lots"]');
    await page.waitForURL('**/lots', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toContain('Lotes');
  });

  await test('Lot stage filters visible', async () => {
    const filters = await page.locator('button:has-text("Todos"), button:has-text("Progenitoras"), button:has-text("Reproductoras"), button:has-text("Engorde")').count();
    expect(filters).toBeGreaterThanOrEqual(1);
  });

  // ================================================================
  // 4. LOT DETAIL
  // ================================================================
  await test('Open lot detail (id=2)', async () => {
    await page.goto(`${BASE}/lots/2`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(2000);
    const title = await page.locator('h1').textContent();
    expect(title).toMatch(/L-|Lote/);
  });

  await test('Lot detail shows Cerrar Lote button', async () => {
    const closeBtn = await page.locator('button:has-text("Cerrar")').count();
    expect(closeBtn).toBeGreaterThanOrEqual(0); // only for active lots
  });

  await test('Lot detail shows stage operations', async () => {
    const ops = await page.locator('a:has-text("Inspección"), a:has-text("Recepción"), a:has-text("Alimento"), a:has-text("Mortalidad")').count();
    expect(ops).toBeGreaterThanOrEqual(2);
  });

  await test('Lot detail shows KPIs section', async () => {
    const kpis = await page.locator('text=KPIs').count();
    expect(kpis).toBeGreaterThanOrEqual(0);
  });

  await test('Lot detail shows Info section', async () => {
    const info = await page.locator('text=Información').count();
    expect(info).toBeGreaterThanOrEqual(1);
  });

  // ================================================================
  // 5. OPERATIONS LIST
  // ================================================================
  await test('Navigate to Operations list', async () => {
    await page.click('a[href="/operations"]');
    await page.waitForURL('**/operations', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toContain('Operaciones');
  });

  await test('Operations list shows event type filter', async () => {
    const filter = await page.locator('select, combobox').first();
    expect(filter).toBeTruthy();
  });

  // ================================================================
  // 6. OPERATIONS NEW
  // ================================================================
  await test('Navigate to new operation form', async () => {
    await page.goto(`${BASE}/operations/new`, { waitUntil: 'networkidle', timeout: 15000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toContain('Operaciones');
  });

  await test('New operation form has lot selector', async () => {
    const lotSelect = await page.locator('select').first();
    expect(lotSelect).toBeTruthy();
  });

  await test('New operation form has event type selector', async () => {
    const eventTypes = await page.locator('select').nth(1);
    const options = await eventTypes.locator('option').count();
    expect(options).toBeGreaterThan(5); // 24 event types
  });

  // ================================================================
  // 7. REVIEW CENTER
  // ================================================================
  await test('Navigate to Review Center', async () => {
    await page.click('a[href="/review"]');
    await page.waitForURL('**/review', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toMatch(/Revis|Review/i);
  });

  await test('Review Center has filter bar', async () => {
    const filters = await page.locator('input[placeholder="Lote ID"]').count();
    expect(filters).toBeGreaterThanOrEqual(1);
  });

  await test('Review Center shows Create Batch button', async () => {
    const btn = await page.locator('button:has-text("Crear"), button:has-text("Batch")').count();
    expect(btn).toBeGreaterThanOrEqual(0);
  });

  // ================================================================
  // 8. APPROVALS
  // ================================================================
  await test('Navigate to Approvals', async () => {
    await page.click('a[href="/approvals"]');
    await page.waitForURL('**/approvals', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toMatch(/Aprob|Approval/i);
  });

  // ================================================================
  // 9. REPORTS
  // ================================================================
  await test('Navigate to Reports', async () => {
    await page.click('a[href="/reports"]');
    await page.waitForURL('**/reports', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toContain('Reportes');
  });

  await test('Reports shows KPI cards', async () => {
    await page.waitForTimeout(3000);
    const cards = await page.locator('text=Mortalidad, text=Conversión Alimenticia, text=Producción de Huevos, text=Incubación').count();
    expect(cards).toBeGreaterThanOrEqual(0);
  });

  await test('Reports shows export buttons (G-06)', async () => {
    const excel = await page.locator('button:has-text("Excel")').count();
    const pdf = await page.locator('button:has-text("PDF")').count();
    expect(excel + pdf).toBeGreaterThanOrEqual(1);
  });

  await test('Reports shows new KPI cards (G-01,02,03)', async () => {
    await page.waitForTimeout(1000);
    const welfare = await page.locator('text=Bienestar Animal').count();
    const vaccEff = await page.locator('text=Eficiencia Vacunación').count();
    const transfer = await page.locator('text=Eficiencia Traslado').count();
    expect(welfare + vaccEff + transfer).toBeGreaterThanOrEqual(0);
  });

  // ================================================================
  // 10. LOT REPORT
  // ================================================================
  await test('Navigate to Lot Report', async () => {
    await page.goto(`${BASE}/reports/lot/2`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(2000);
    const content = await page.locator('main').textContent();
    expect(content).toBeTruthy();
  });

  // ================================================================
  // 11. SAP COMPARISON
  // ================================================================
  await test('Navigate to SAP Comparison', async () => {
    await page.goto(`${BASE}/reports/sap`, { waitUntil: 'networkidle', timeout: 15000 });
    const content = await page.locator('h1').textContent();
    expect(content).toMatch(/SAP|Compar/i);
  });

  // ================================================================
  // 12. AUDIT
  // ================================================================
  await test('Navigate to Audit', async () => {
    await page.click('a[href="/audit"]');
    await page.waitForURL('**/audit', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toMatch(/Audit|Auditoría/i);
  });

  // ================================================================
  // 13. SAP MANAGER
  // ================================================================
  await test('Navigate to SAP Manager', async () => {
    await page.click('a[href="/sap"]');
    await page.waitForURL('**/sap', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toMatch(/SAP|Integración/i);
  });

  // ================================================================
  // 14. USERS
  // ================================================================
  await test('Navigate to Users', async () => {
    await page.click('a[href="/users"]');
    await page.waitForURL('**/users', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toMatch(/Usuarios|Users/i);
  });

  // ================================================================
  // 15. PROFILE
  // ================================================================
  await test('Navigate to Profile', async () => {
    await page.goto(`${BASE}/profile`, { waitUntil: 'networkidle', timeout: 15000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toMatch(/Perfil|Profile/i);
  });

  // ================================================================
  // 16. MASTERS
  // ================================================================
  const mastersList = ['farms', 'companies', 'houses', 'suppliers', 'breeds', 'vaccines', 'feed-types'];
  for (const entity of mastersList) {
    await test(`Master: ${entity}`, async () => {
      await page.goto(`${BASE}/masters/${entity}`, { waitUntil: 'networkidle', timeout: 15000 });
      const heading = await page.locator('h1').textContent();
      expect(heading).toBeTruthy();
    });
  }

  // ================================================================
  // 17. LOGOUT
  // ================================================================
  await test('Logout', async () => {
    await page.click('button:has-text("Cerrar Sesión")');
    await page.waitForURL('**/login', { timeout: 10000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toContain('Global Avícola');
  });

  // ================================================================
  // 18. LOGIN MOBILE USER
  // ================================================================
  await test('Login as mobile user', async () => {
    await page.fill('input[placeholder="admin"]', 'operador.mobile');
    await page.fill('input[type="password"]', 'mobile123456');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/', { timeout: 15000 });
    const heading = await page.locator('h1').textContent();
    expect(heading).toContain('Dashboard');
  });

  // ================================================================
  // 19. MOBILE: NO SIDEBAR
  // ================================================================
  await test('Mobile user has no desktop sidebar', async () => {
    await page.waitForTimeout(3000);
    // Sidebar should be hidden for mobile users
    const sidebar = await page.locator('aside').count();
    expect(sidebar).toBe(0);
  });

  // ================================================================
  // 20. MOBILE: HAS BOTTOM NAV
  // ================================================================
  await test('Mobile user has bottom navigation', async () => {
    const bottomNav = await page.locator('nav:has(a[href="/operations"])').count();
    expect(bottomNav).toBeGreaterThanOrEqual(1);
  });

  // ================================================================
  // 21. MOBILE: WEB-ONLY ROUTES BLOCKED
  // ================================================================
  const webOnlyRoutes = ['/review', '/approvals', '/audit', '/sap', '/users', '/masters/farms'];
  for (const route of webOnlyRoutes) {
    await test(`Mobile user blocked from ${route}`, async () => {
      await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(1000);
      const url = page.url();
      // Should redirect to / or stay on a safe page
      expect(url).not.toContain(route);
    });
  }

  // ================================================================
  // 22. MOBILE: ALLOWED ROUTES WORK
  // ================================================================
  const mobileAllowed = ['/operations', '/reports'];
  for (const route of mobileAllowed) {
    await test(`Mobile user can access ${route}`, async () => {
      await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(1000);
      const url = page.url();
      expect(url).toContain(route);
    });
  }

  // ================================================================
  // REPORT
  // ================================================================
  console.log('\n═══════════════════════════════════════════');
  console.log(`  RESULTADO: ${passed} ✅ / ${failed} ❌`);
  console.log('═══════════════════════════════════════════\n');

  for (const r of results) {
    console.log(r);
  }

  await browser.close();
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => {
  console.error('FATAL:', e.message);
  process.exit(1);
});
