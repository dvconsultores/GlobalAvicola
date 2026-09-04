import { defineConfig, devices } from '@playwright/test'

/**
 * Configuración E2E única del repositorio — `GA-REM-016 AC01`.
 *
 * Antes existían dos suites y **una sola** configuración: `frontend/playwright.config.ts`
 * cubría `frontend/tests/`, y los 1 065 LOC de `tests/` en la raíz quedaban huérfanos —
 * ningún ejecutor los descubría, de modo que su estado real era desconocido.
 *
 * `AC01` exige que ningún fichero quede fuera por falta de configuración. Esta
 * configuración descubre ambas suites. Que la suite heredada falle no es motivo para
 * seguir ocultándola: es el mismo criterio que la Wave 1.5 aplicó al backend, cuando 101
 * tests llevaban meses escritos sin haberse ejecutado nunca.
 *
 * Navegadores: solo `chromium`. Es el único instalado en el entorno de certificación, y
 * declararlo es preferible a listar cinco proyectos que no pueden ejecutarse. La matriz
 * multi-navegador de `frontend/playwright.config.ts` se conserva para cuando el entorno
 * disponga de los demás.
 */
export default defineConfig({
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.GA_E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      // Certificación de procesos de la Wave 3.
      name: 'procesos',
      testDir: './e2e',
      use: { ...devices['Desktop Chrome'] },
    },
    // La suite de `frontend/tests` **no** se incluye aquí: sus ficheros importan
    // `@playwright/test`, que desde `frontend/` resuelve a la copia anidada del propio
    // frontend (1.61.1) en lugar de a la de la raíz (1.61.0). Son dos instalaciones
    // distintas: los tests se registran en una y el ejecutor mira la otra, de modo que
    // desde aquí aparecen como «No tests found».
    //
    // Se ejecuta con su propia configuración —`frontend/playwright.config.ts`, que existe
    // desde junio— y su estado consta en `E2E_TEST_INVENTORY.md`. Unificar las dos
    // instalaciones es deuda registrada como `R-61`, fuera del alcance de esta Wave.
    {
      // Suite heredada de la raíz: descubierta por primera vez. Su estado se documenta
      // en `audit/remediation/E2E_TEST_INVENTORY.md`.
      //
      // `testMatch` excluye dos ficheros que **no son tests**: `integration-full.spec.ts`
      // e `integration-test.ts` son scripts con un `main()` que lanza chromium a mano.
      // El primero lleva sufijo `.spec.ts` sin serlo, y su carga rompía el descubridor
      // para todo el proyecto. No se borran —no es cleanup lo que toca aquí— pero se
      // declara que no son suites.
      name: 'heredada',
      testDir: './tests',
      testMatch: ['e2e.spec.ts', 'operations.spec.ts'],
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
