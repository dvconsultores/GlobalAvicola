/**
 * P-17-G — CONSISTENCIA UI/API   (SPEC 013 · `AC-UI-API-01`)
 *
 * Para cada cuenta sembrada y cada par (ruta de la interfaz → endpoint que la respalda): si la
 * API autoriza (200) la ruta debe abrirse; si niega (403) no debe quedar disponible y la
 * interfaz no debe consumir ese endpoint. El sidebar enlaza hubs, no hojas: se navega y se
 * mide lo que ocurre. El token nunca se imprime ni se escribe en la evidencia.
 */
import * as fs from 'node:fs'
import * as path from 'node:path'
import { test, expect, type Page, type Response } from '@playwright/test'
import { API } from '../test-support/e2e-api'
import { credenciales, type Rol } from '../test-support/auth'
import { entrarComo, tokenDe } from '../test-support/admin-rbac'

/** Ruta de la interfaz y endpoint que la respalda (`API` ya termina en `/api/v1`). */
const PARES = [
  { ruta: '/audit', endpoint: '/api/v1/audit?limit=1' },
  { ruta: '/users', endpoint: '/api/v1/users?limit=1' },
  { ruta: '/roles', endpoint: '/api/v1/roles' },
  { ruta: '/lots', endpoint: '/api/v1/lots?limit=1' },
  { ruta: '/cutover', endpoint: '/api/v1/cutover-batches' },
]

const CUENTAS: Rol[] = ['admin', 'operator', 'approver']

type Fila = {
  cuenta: string; ruta: string; endpoint: string
  uiPermite: boolean; status: number; huboRespuesta2xx: boolean
}

/** Filas de las tres cuentas: se escriben juntas una sola vez, en `afterAll`. */
const filas: Fila[] = []
/** Pares donde la interfaz y la API no coinciden. */
const inconsistencias: { cuenta: string; ruta: string; uiPermite: boolean; statusApi: number }[] = []
const EVIDENCIA = path.join(process.cwd(), 'audit', 'ga-uat-admin-rbac-2026-10-31', 'evidence')

test.describe.configure({ mode: 'serial' })

/** URL absoluta del endpoint: `API` ya incluye el prefijo `/api/v1`. */
const urlApi = (endpoint: string): string => `${API}${endpoint.replace(/^\/api\/v1/, '')}`

/**
 * Navega a `ruta` en la página ya autenticada y mide si la interfaz la permite y si consumió el
 * endpoint durante esa navegación. El listener se retira siempre: una medición no debe
 * contaminar la siguiente.
 */
async function medir(
  page: Page,
  ruta: string,
  endpoint: string,
): Promise<{ uiPermite: boolean; huboRespuesta2xx: boolean }> {
  const sinQuery = endpoint.split('?')[0]
  let huboRespuesta2xx = false
  const alResponder = (r: Response): void => {
    if (r.url().includes(sinQuery) && r.status() >= 200 && r.status() < 300) huboRespuesta2xx = true
  }
  page.on('response', alResponder)
  try {
    await page.goto(ruta)
    await page.waitForTimeout(2_500)
    const uiPermite =
      new URL(page.url()).pathname === ruta && (await page.locator('[role="alert"]').count()) === 0
    return { uiPermite, huboRespuesta2xx }
  } finally {
    page.off('response', alResponder)
  }
}

for (const cuenta of CUENTAS) {
  test(`P-17-G · ${cuenta}: la interfaz ofrece exactamente lo que la API autoriza`, async ({
    browser,
    request,
  }) => {
    test.setTimeout(120_000)
    const ctx = await browser.newContext()
    const page = await ctx.newPage()
    try {
      const { usuario, clave } = credenciales(cuenta)
      await entrarComo(page, usuario, clave)
      const token = await tokenDe(page) // nunca se imprime ni se registra
      const headers = { Authorization: `Bearer ${token}` }

      for (const { ruta, endpoint } of PARES) {
        const statusApi = (await request.get(urlApi(endpoint), { headers })).status()
        const { uiPermite, huboRespuesta2xx } = await medir(page, ruta, endpoint)
        filas.push({ cuenta, ruta, endpoint, uiPermite, status: statusApi, huboRespuesta2xx })

        // La interfaz y la API tienen que contar la misma historia.
        expect
          .soft(uiPermite, `${cuenta} ${ruta}: la UI permite=${uiPermite} y la API=${statusApi}`)
          .toBe(statusApi === 200)

        // Una ruta cerrada por autoridad es un 403, ni un 401 ni un 500.
        if (statusApi !== 200) {
          expect.soft(statusApi, `${cuenta} ${endpoint}: se esperaba 403`).toBe(403)
        }

        // Si la UI no ofrece la ruta, no debe estar consumiendo el endpoint protegido.
        if (!uiPermite) {
          expect
            .soft(huboRespuesta2xx, `${cuenta} ${ruta}: la UI sin ruta no debe consumir 2xx`)
            .toBe(false)
        }

        if (uiPermite !== (statusApi === 200)) {
          inconsistencias.push({ cuenta, ruta, uiPermite, statusApi })
        }
      }

      expect(inconsistencias, 'pares donde la interfaz y la API no coinciden').toEqual([])
    } finally {
      await ctx.close()
    }
  })
}

test.afterAll(() => {
  if (process.env.GA_WRITE_MATRIX !== '1') return
  fs.mkdirSync(EVIDENCIA, { recursive: true })
  fs.writeFileSync(
    path.join(EVIDENCIA, 'e2e_ui_api_consistency.json'),
    `${JSON.stringify(filas, null, 2)}\n`,
  )
})
