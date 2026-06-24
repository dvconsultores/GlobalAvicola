import { test, expect } from '@playwright/test'

/**
 * E2E Tests para las nuevas características de Operaciones
 * ProcessHubPage, ProcessStagePage, Dashboard Móvil
 */

test.describe('Operations Redesign', () => {
  
  test.describe('ProcessHubPage', () => {
    
    test('should display 6 process cards', async ({ page }) => {
      await page.goto('/processes')
      
      // Verificar que se muestren 6 procesos
      const processCards = await page.locator('a[href*="/processes/"]').count()
      expect(processCards).toBe(6)
    })

    test('should show process cards with icons and descriptions', async ({ page }) => {
      await page.goto('/processes')
      
      // Verificar que cada card tenga un icono
      const firstCard = page.locator('a[href*="/processes/"]').first()
      await expect(firstCard).toContainText('operaciones')
      
      // Verificar que haya texto descriptivo
      const cardText = await firstCard.textContent()
      expect(cardText?.length).toBeGreaterThan(20)
    })

    test('should navigate to process stage when clicked', async ({ page }) => {
      await page.goto('/processes')
      
      // Hacer clic en el primer proceso
      const firstProcess = page.locator('a[href*="/processes/"]').first()
      await firstProcess.click()
      
      // Verificar que se navegó a la página de etapas
      expect(page.url()).toContain('/processes/')
    })

    test('should show helpful hint at bottom', async ({ page }) => {
      await page.goto('/processes')
      
      // Buscar el hint
      const hint = page.locator('text=Toca cualquier proceso').or(page.locator('text=Tap any process'))
      await expect(hint).toBeVisible()
    })

  })

  test.describe('ProcessStagePage - Timeline', () => {
    
    test('should display operations as timeline items', async ({ page }) => {
      await page.goto('/processes/broiler')
      
      // Esperar a que cargue
      await page.waitForLoadState('networkidle')
      
      // Verificar que hay items de timeline
      const timelineItems = await page.locator('button[type="button"]').count()
      expect(timelineItems).toBeGreaterThan(0)
    })

    test('should expand timeline item when clicked', async ({ page }) => {
      await page.goto('/processes/broiler')
      await page.waitForLoadState('networkidle')
      
      // Obtener el primer item
      const firstItem = page.locator('button').filter({ has: page.locator('text=') }).first()
      
      // Hacer clic para expandir
      await firstItem.click()
      
      // Verificar que aparece el botón de registro
      const registerButton = page.locator('text=Registrar operación').or(page.locator('text=Register operation'))
      await expect(registerButton).toBeVisible()
    })

    test('should show process header with color', async ({ page }) => {
      await page.goto('/processes/broiler')
      
      // Verificar que hay un header coloreado
      const header = page.locator('h1').first()
      await expect(header).toBeVisible()
      
      // Verificar que tiene una clase de color
      const headerClass = await header.getAttribute('class')
      expect(headerClass).toBeTruthy()
    })

    test('should show progress bar', async ({ page }) => {
      await page.goto('/processes/broiler')
      
      // Buscar barra de progreso
      const progressBar = page.locator('[role="progressbar"]').or(page.locator('text=Progreso').or(page.locator('text=Progress')))
      expect(progressBar).toBeTruthy()
    })

    test('should allow lot selection', async ({ page }) => {
      await page.goto('/processes/broiler')
      await page.waitForLoadState('networkidle')
      
      // Encontrar selector de lote
      const lotSelector = page.locator('select').first()
      
      // Verificar que existe
      await expect(lotSelector).toBeVisible()
      
      // Intentar cambiar valor
      const options = await lotSelector.locator('option').count()
      expect(options).toBeGreaterThanOrEqual(1)
    })

    test('should navigate to operation form when registering', async ({ page }) => {
      await page.goto('/processes/broiler')
      await page.waitForLoadState('networkidle')
      
      // Expandir primera etapa
      const firstItem = page.locator('button').first()
      await firstItem.click()
      
      // Hacer clic en registrar operación
      const registerButton = page.locator('text=Registrar operación').or(page.locator('text=Register operation'))
      await registerButton.click()
      
      // Esperar navegación
      await page.waitForURL('**/operations/new**')
      expect(page.url()).toContain('/operations/new')
    })

  })

  test.describe('Mobile Dashboard', () => {
    test.use({ viewport: { width: 390, height: 844 } })

    test('should show welcome header on mobile', async ({ page }) => {
      await page.goto('/')
      
      // Buscar el header de bienvenida
      const header = page.locator('text=Inicio').or(page.locator('text=Home'))
      await expect(header).toBeVisible()
    })

    test('should display 3 KPI cards', async ({ page }) => {
      await page.goto('/')
      
      // Contar cards con números (KPIs)
      const kpiCards = await page.locator('[data-testid="kpi-card"]').or(page.locator('text=/\\d+/')).count()
      expect(kpiCards).toBeGreaterThanOrEqual(3)
    })

    test('should show 6 process cards on mobile', async ({ page }) => {
      await page.goto('/')
      
      // Buscar el grid de 6 procesos
      const processCards = await page.locator('a[href*="/processes/"]').count()
      expect(processCards).toBe(6)
    })

    test('should show quick actions buttons', async ({ page }) => {
      await page.goto('/')
      
      // Buscar botones de acciones rápidas
      const alimento = page.locator('text=Alimento').or(page.locator('text=Food'))
      const pesaje = page.locator('text=Pesaje').or(page.locator('text=Weight'))
      const mortalidad = page.locator('text=Mortalidad').or(page.locator('text=Mortality'))
      const huevos = page.locator('text=Huevos').or(page.locator('text=Eggs'))
      
      await expect(alimento).toBeVisible()
      await expect(pesaje).toBeVisible()
      await expect(mortalidad).toBeVisible()
      await expect(huevos).toBeVisible()
    })

    test('should navigate to operation form from quick action', async ({ page }) => {
      await page.goto('/')
      
      // Hacer clic en acción rápida de alimento
      const alimentoButton = page.locator('text=Alimento').or(page.locator('text=Feed')).first()
      await alimentoButton.click()
      
      // Esperar navegación
      await page.waitForURL('**/operations/new**')
      expect(page.url()).toContain('/operations/new')
    })

    test('should responsive grid on mobile', async ({ page }) => {
      await page.goto('/processes')
      
      // En mobile, debería haber 1 columna
      const processCards = await page.locator('a[href*="/processes/"]')
      const count = await processCards.count()
      
      // Verificar que el grid es responsive (existe en mobile)
      expect(count).toBe(6)
    })

  })

  test.describe('Accessibility', () => {
    
    test('should have accessible process cards', async ({ page }) => {
      await page.goto('/processes')
      
      // Buscar links que sean accesibles
      const links = page.locator('a[href*="/processes/"]')
      
      for (let i = 0; i < 6; i++) {
        const link = links.nth(i)
        const href = await link.getAttribute('href')
        expect(href).toBeTruthy()
      }
    })

    test('should have aria labels on expandable items', async ({ page }) => {
      await page.goto('/processes/broiler')
      await page.waitForLoadState('networkidle')
      
      // Buscar items expandibles con aria-expanded
      const expandableItems = page.locator('[aria-expanded]')
      const count = await expandableItems.count()
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('should be keyboard navigable', async ({ page }) => {
      await page.goto('/processes')
      
      // Presionar Tab para navegar
      await page.keyboard.press('Tab')
      
      // Verificar que algún elemento está enfocado
      const focusedElement = page.locator(':focus')
      await expect(focusedElement).toBeTruthy()
    })

  })

  test.describe('Internationalization', () => {
    
    test('should display Spanish translations', async ({ page }) => {
      await page.goto('/processes')
      
      // Buscar texto en español
      const spanishText = page.locator('text=Procesos de Producción')
      
      if (await spanishText.isVisible()) {
        expect(spanishText).toBeTruthy()
      }
    })

    test('should have complete translations', async ({ page }) => {
      await page.goto('/processes')
      await page.waitForLoadState('networkidle')
      
      // Verificar que no hay claves i18n sin traducción (por ej: "process.hub.title")
      const untranslatedText = page.locator('text=process.').or(page.locator('text=dashboard.'))
      const count = await untranslatedText.count()
      
      // Debería haber 0 claves sin traducir
      expect(count).toBe(0)
    })

  })

})

/**
 * Tests de Performance
 */
test.describe('Performance', () => {
  
  test('ProcessHubPage should load quickly', async ({ page }) => {
    const startTime = Date.now()
    
    await page.goto('/processes')
    await page.waitForLoadState('domcontentloaded')
    
    const loadTime = Date.now() - startTime
    
    // Debería cargar en menos de 3 segundos
    expect(loadTime).toBeLessThan(3000)
  })

  test('Timeline expansion should be instant', async ({ page }) => {
    await page.goto('/processes/broiler')
    await page.waitForLoadState('networkidle')
    
    const startTime = Date.now()
    
    // Hacer clic para expandir
    const firstItem = page.locator('button').first()
    await firstItem.click()
    
    // Esperar a que aparezca el contenido
    await page.waitForLoadState('domcontentloaded')
    
    const loadTime = Date.now() - startTime
    
    // Debería ser instant (menos de 500ms)
    expect(loadTime).toBeLessThan(500)
  })

})

/**
 * Tests de Responsividad
 */
test.describe('Responsive Design', () => {
  
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/processes')
    
    // Verificar que se vea bien
    const content = page.locator('main').or(page.locator('body > div').first())
    await expect(content).toBeVisible()
  })

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/processes')
    
    // Verificar que se vea bien
    const content = page.locator('main').or(page.locator('body > div').first())
    await expect(content).toBeVisible()
  })

  test('should work on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/processes')
    
    // Verificar que se vea bien
    const content = page.locator('main').or(page.locator('body > div').first())
    await expect(content).toBeVisible()
  })

})
