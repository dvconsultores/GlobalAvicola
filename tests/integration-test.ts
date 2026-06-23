import { chromium } from 'playwright';

const BASE = 'http://localhost:5173';
const TIMEOUT = 25000;

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'es-ES' });
  const page = await context.newPage();
  page.setDefaultTimeout(TIMEOUT);

  let passed = 0, failed = 0;
  const results: string[] = [];

  const test = async (name: string, fn: () => Promise<void>) => {
    try { await fn(); passed++; results.push(`✅ ${name}`); }
    catch (e: any) { failed++; results.push(`❌ ${name}: ${e.message?.substring(0,150)}`); }
  };

  const h1 = () => page.locator('main h1').first().textContent();
  const nav = async (href: string) => {
    await page.click(`a[href="${href}"]`);
    await page.waitForURL(`**${href}`, { timeout: 20000 });
    await page.waitForTimeout(1500);
  };

  console.log('═══════════════════════════════════════════');
  console.log('  TEST INTEGRAL — Global Avicola v0.1.0');
  console.log('═══════════════════════════════════════════\n');

  // 1. LOGIN ADMIN
  await test('Login page loads', async () => {
    await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
    const t = await page.locator('h1').first().textContent();
    if (!t?.includes('Global')) throw new Error(`Got: ${t}`);
  });

  await test('Login as admin', async () => {
    await page.fill('input[placeholder="admin"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/', { timeout: TIMEOUT });
    await page.waitForTimeout(2000);
    const t = await h1();
    if (!t?.includes('Dashboard')) throw new Error(`Got: ${t}`);
  });

  // 2. DASHBOARD
  await test('Dashboard has KPIs', async () => {
    const c = await page.locator('text=Total Eventos').count();
    if (c === 0) throw new Error('No KPIs');
  });

  await test('Dashboard has sidebar', async () => {
    const c = await page.locator('aside').count();
    if (c === 0) throw new Error('No sidebar for admin');
  });

  // 3. LOTS
  await test('Navigate Lots', async () => {
    await nav('/lots');
    const t = await h1();
    if (!t?.includes('Lotes')) throw new Error(`Got: ${t}`);
  });

  await test('Lots stage filters', async () => {
    const c = await page.locator('button:has-text("Todos")').count();
    if (c === 0) throw new Error('No stage filter');
  });

  // 4. LOT DETAIL
  await test('Lot detail loads', async () => {
    await page.goto(`${BASE}/lots/2`, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
    await page.waitForTimeout(3000);
    const t = await h1();
    if (!t || t === 'Cargando...') throw new Error('Still loading');
  });

  await test('Lot detail has operations', async () => {
    const c = await page.locator('a:has-text("Inspección"), a:has-text("Recepción"), a:has-text("Alimento")').count();
    if (c === 0) throw new Error('No stage operations');
  });

  // 5. OPERATIONS
  await test('Navigate Operations', async () => {
    await nav('/operations');
    const t = await h1();
    if (!t?.includes('Operaciones')) throw new Error(`Got: ${t}`);
  });

  await test('New operation form', async () => {
    await page.goto(`${BASE}/operations/new`, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
    await page.waitForTimeout(2000);
    const t = await h1();
    if (!t) throw new Error('Form not loaded');
  });

  // 6. REVIEW
  await test('Navigate Review', async () => {
    await nav('/review');
    const t = await h1();
    if (!t) throw new Error('Review not loaded');
  });

  // 7. APPROVALS
  await test('Navigate Approvals', async () => {
    await nav('/approvals');
    const t = await h1();
    if (!t) throw new Error('Approvals not loaded');
  });

  // 8. REPORTS
  await test('Navigate Reports', async () => {
    await nav('/reports');
    const t = await h1();
    if (!t?.includes('Reportes')) throw new Error(`Got: ${t}`);
  });

  await test('Reports export buttons', async () => {
    await page.waitForTimeout(3000);
    const c = await page.locator('button:has-text("Excel"), button:has-text("PDF")').count();
    if (c === 0) throw new Error('No export buttons');
  });

  // 9. AUDIT
  await test('Navigate Audit', async () => {
    await nav('/audit');
    const t = await h1();
    if (!t) throw new Error('Audit not loaded');
  });

  // 10. SAP
  await test('Navigate SAP', async () => {
    await nav('/sap');
    const t = await h1();
    if (!t) throw new Error('SAP not loaded');
  });

  // 11. USERS
  await test('Navigate Users', async () => {
    await nav('/users');
    const t = await h1();
    if (!t) throw new Error('Users not loaded');
  });

  // 12. PROFILE
  await test('Navigate Profile', async () => {
    await page.goto(`${BASE}/profile`, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
    await page.waitForTimeout(2000);
    const t = await h1();
    if (!t) throw new Error('Profile not loaded');
  });

  // 13. MASTERS
  for (const e of ['farms','companies','breeds','vaccines']) {
    await test(`Master ${e}`, async () => {
      await page.goto(`${BASE}/masters/${e}`, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
      await page.waitForTimeout(2000);
      const t = await h1();
      if (!t) throw new Error(`Master ${e} not loaded`);
    });
  }

  // 14. LOGOUT
  await test('Logout', async () => {
    await page.click('button:has-text("Cerrar Sesión")');
    await page.waitForURL('**/login', { timeout: 15000 });
    const t = await page.locator('h1').first().textContent();
    if (!t?.includes('Global')) throw new Error('Logout failed');
  });

  // 15. MOBILE LOGIN
  await test('Mobile login', async () => {
    await page.fill('input[placeholder="admin"]', 'operador.mobile');
    await page.fill('input[type="password"]', 'mobile123456');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/', { timeout: TIMEOUT });
    await page.waitForTimeout(2000);
    if (page.url().includes('login')) throw new Error('Mobile login failed');
  });

  // 16. MOBILE VIEW
  await test('Mobile: no sidebar', async () => {
    await page.waitForTimeout(3000);
    const c = await page.locator('aside').count();
    if (c > 0) throw new Error('Sidebar visible for mobile');
  });

  await test('Mobile: has bottom nav', async () => {
    const c = await page.locator('nav a').count();
    if (c < 2) throw new Error(`Nav links: ${c}`);
  });

  // 17. MOBILE ROUTE GUARDS
  for (const r of ['/review','/approvals','/audit','/sap','/users','/masters/farms']) {
    await test(`Mobile blocked: ${r}`, async () => {
      await page.goto(`${BASE}${r}`, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
      await page.waitForTimeout(2000);
      if (page.url().includes(r)) throw new Error(`Should be blocked from ${r}`);
    });
  }

  for (const r of ['/operations','/reports']) {
    await test(`Mobile allowed: ${r}`, async () => {
      await page.goto(`${BASE}${r}`, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
      await page.waitForTimeout(2000);
      if (!page.url().includes(r)) throw new Error(`Should access ${r}`);
    });
  }

  // REPORT
  console.log(`\n═══════════════════════════════════════════`);
  console.log(`  RESULTADO: ${passed} ✅ / ${failed} ❌`);
  console.log(`═══════════════════════════════════════════\n`);
  for (const r of results) console.log(r);

  await browser.close();
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
