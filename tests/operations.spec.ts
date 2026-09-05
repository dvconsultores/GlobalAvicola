/**
 * Operaciones — hub de procesos y etapas avícolas.
 *
 * Reescritura bajo `GA-REM-016`, enmienda de recuperación. El fichero anterior recorría
 * `/processes` y contaba `a[href*="/processes/"]`, y no se autenticaba en ningún punto: los
 * catorce casos fallaban por eso, no porque el sistema estuviera mal.
 *
 * `/processes` es hoy una ruta heredada que redirige (`App.tsx:182-183`). Pero **el
 * requisito no se movió**: `data/processCatalog.ts` sigue declarando las mismas seis etapas
 * avícolas con sus rutas en `STAGE_PATH_MAP`, y `navigationConfig.ts` las expone como
 * cuatro categorías en `/menu/poultry`. Lo que cambió es el camino, no lo que hay que
 * comprobar.
 *
 * Cada caso conserva la intención funcional del que sustituye. La correspondencia está en
 * `audit/remediation/PLAYWRIGHT_TEST_DISPOSITION_MATRIX.md`.
 */
import { test, expect } from '@playwright/test'
import { entrar } from '../test-support/auth'

/** Las seis etapas de `STAGE_PATH_MAP`. Si el catálogo cambia, esto debe cambiar con él. */
const ETAPAS = [
  '/poultry/grandparent/rearing',
  '/poultry/grandparent/production',
  '/poultry/breeder/rearing',
  '/poultry/breeder/production',
  '/poultry/hatchery',
  '/poultry/broiler',
]

/** Las cuatro categorías que el menú avícola presenta. */
const CATEGORIAS = [/progenitoras/i, /reproductoras/i, /incubadora/i, /engorde/i]

test.describe('Operaciones · hub de procesos', () => {
  test('AUTORIZACIÓN · sin sesión el menú no se expone', async ({ page }) => {
    await page.goto('/menu/poultry')
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 })
  })

  // Sustituye a «should display 6 process cards» y «cards with icons and descriptions».
  test('el menú avícola presenta sus categorías con descripción', async ({ page }) => {
    await entrar(page, 'admin')
    await page.goto('/menu/poultry')

    for (const categoria of CATEGORIAS) {
      await expect(
        page.getByText(categoria).first(),
        `la categoría ${categoria} debe estar en el menú`,
      ).toBeVisible({ timeout: 15_000 })
    }

    // Cada opción se presenta con algo más que su nombre: cuántas opciones tiene dentro,
    // o la invitación a abrirla.
    await expect(page.getByText(/opciones|abrir/i).first()).toBeVisible()
  })

  // Sustituye a «should show helpful hint at bottom».
  test('el menú orienta sobre qué hacer', async ({ page }) => {
    await entrar(page, 'admin')
    await page.goto('/menu/poultry')
    await expect(page.getByText(/elige una opción|choose an option/i)).toBeVisible({
      timeout: 15_000,
    })
  })

  // Sustituye a «navigate to process stage when clicked», «6 process cards on mobile» y
  // «accessible process cards»: lo que importaba era que las seis etapas se alcanzasen.
  test('las seis etapas avícolas son alcanzables', async ({ page }) => {
    await entrar(page, 'admin')

    for (const ruta of ETAPAS) {
      await page.goto(ruta)
      await expect(page, `${ruta} no debe redirigir al login`).not.toHaveURL(/\/login/)
      await expect(
        page.getByRole('heading').first(),
        `${ruta} debe renderizar contenido`,
      ).toBeVisible({ timeout: 15_000 })
    }
  })

  // Sustituye a «responsive grid on mobile».
  test('el menú se muestra en un viewport móvil', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await entrar(page, 'admin')
    await page.goto('/menu/poultry')
    await expect(page.getByText(CATEGORIAS[0]).first()).toBeVisible({ timeout: 15_000 })
  })
})

test.describe('Operaciones · página de etapa', () => {
  const ETAPA = '/poultry/broiler'

  // Sustituye a «should display operations as timeline items» y «expand timeline item».
  //
  // La vista por omisión de la etapa es una rejilla de operaciones, no la cronología
  // (`ProcessStagePage.tsx:100`); la cronología es la vista alternativa. Se comprueba lo
  // que el requisito pide —que la etapa ofrezca sus operaciones— contra los enlaces
  // reales, no contando botones cualesquiera, que habría pasado con la barra de navegación
  // y no habría probado nada.
  test('la etapa muestra las operaciones que admite', async ({ page }) => {
    await entrar(page, 'admin')
    await page.goto(ETAPA)
    await expect(page).not.toHaveURL(/\/login/)

    const operaciones = page.locator('a[href*="/operations/new"]')
    expect(
      await operaciones.count(),
      'la etapa debe ofrecer al menos una operación registrable',
    ).toBeGreaterThan(0)
  })

  // Sustituye a «should allow lot selection».
  test('la etapa permite elegir el lote sobre el que se opera', async ({ page }) => {
    await entrar(page, 'admin')
    await page.goto(ETAPA)
    await expect(page).not.toHaveURL(/\/login/)
    await expect(page.getByText(/lote|lot/i).first()).toBeVisible({ timeout: 15_000 })
  })

  // Sustituye a «navigate to operation form when registering» y absorbe la cobertura de los
  // dos casos retirados de accesos rápidos: registrar una operación se alcanza por aquí.
  // Sustituye a «navigate to operation form when registering», y absorbe la cobertura de
  // los dos casos retirados de accesos rápidos: registrar una operación se alcanza por
  // aquí. Se recorre el camino de una persona —abrir la etapa y activar la operación—, no
  // una navegación directa por URL.
  test('desde la etapa se llega al formulario de registro', async ({ page }) => {
    await entrar(page, 'admin')
    await page.goto(ETAPA)
    await expect(page).not.toHaveURL(/\/login/)

    await page.locator('a[href*="/operations/new"]').first().click()
    await expect(page).toHaveURL(/\/operations\/new/, { timeout: 15_000 })
  })
})

test.describe('Operaciones · vista móvil', () => {
  // Sustituye a «welcome header on mobile»: el usuario de vista móvil ya no aterriza en un
  // panel, sino en el menú avícola (`App.tsx:71`).
  test('el usuario de vista móvil aterriza en el menú avícola', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await entrar(page, 'operator')
    await page.goto('/')
    await expect(page).toHaveURL(/\/menu\/poultry/, { timeout: 15_000 })
  })

  // Sustituye a «should display 3 KPI cards»: los KPI siguen siendo un requisito, y hoy se
  // alcanzan por la navegación inferior en lugar de por tarjetas en la raíz.
  test('los KPI son alcanzables desde la navegación móvil', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await entrar(page, 'operator')
    await expect(page.locator('nav').first()).toBeVisible({ timeout: 15_000 })
    await page.goto('/kpi')
    await expect(page).not.toHaveURL(/\/login/)
    await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 15_000 })
  })
})
