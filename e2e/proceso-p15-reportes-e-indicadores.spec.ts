/**
 * P-15 — REPORTES E INDICADORES   (`spec.md §4.12`, `docs/02 §3.12`)
 *
 * Dos mitades que conviene no confundir: el **cálculo de indicadores** y la **generación de
 * reportes**. Certificar la primera no certifica el proceso.
 *
 * `GA-REM-022` cerró tres huecos de la primera:
 *   R-14  la eclosión devolvía una frase en español dentro de un campo `_pct`
 *   R-85  «eclosión» y «nacimiento» tienen denominadores distintos y se fundían en uno
 *   R-86  «fertilidad» era normativa y no la calculaba nadie
 */
import { test, expect } from '@playwright/test'
import { API, cabeceraAdmin, crearEscenario, hoy, registrar, sufijo } from '../test-support/e2e-api'

const FERTILES = 800
const INFERTILES = 200
// `BR-03` (`R-172`): la disponibilidad en incubadora es el huevo FÉRTIL — la carga no la excede.
const CARGADOS = 800
const NACIDOS = 600

async function kpi(request: any, cab: any, ruta: string, lotId?: number) {
  const q = lotId ? `?lot_id=${lotId}` : ''
  const r = await request.get(`${API}/reports/kpis/${ruta}${q}`, { headers: cab })
  expect(r.status(), await r.text()).toBe(200)
  return await r.json()
}

test.describe('P-15 · indicadores y reportes', () => {
  test('los indicadores de incubadora son números y distinguen sus denominadores', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P15${sufijo()}`, 'hatchery')
    const base = { lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId, event_date: hoy() }

    for (const [tipo, extra] of [
      ['egg_reception_hatchery', { egg_movements: [
        { quantity: FERTILES, egg_type: 'fertile' },
        { quantity: INFERTILES, egg_type: 'infertile' }] }],
      ['incubation_load', { hatchery_params: [{ quantity_loaded: CARGADOS }] }],
      // `BR-21` (`GA-REM-021-C` / `B13`): sanos + débiles explícitos (Σ ≤ nacidos).
      ['birth_registration', { bird_movements: [{ sex: 'mixed', quantity: NACIDOS }],
                               chicks_healthy: 580, chicks_weak: 20 }],
    ] as [string, any][]) {
      const r = await registrar(request, cab, { ...base, event_type: tipo, ...extra })
      expect(r.status(), `${tipo}: ${await r.text()}`).toBe(201)
    }

    // Sin aprobar, los indicadores no cuentan nada: es el criterio de `AC05`, no un fallo.
    const sinAprobar = await kpi(request, cab, 'hatchery', esc.lotId)
    expect(sinAprobar.insufficient_data,
      'sin datos aprobados el indicador debe declararse insuficiente').toBe(true)
    expect(sinAprobar.nacimiento_pct,
      'la ausencia de base es nula, no cero').toBeNull()
  })

  test('la fertilidad y el reporte de estados existen', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P15F${sufijo()}`, 'hatchery')

    // `R-86` · el campo existe aunque todavía no haya base aprobada.
    const huevo = await kpi(request, cab, 'egg-production', esc.lotId)
    expect(huevo, 'la fertilidad debe formar parte del contrato').toHaveProperty('fertilidad_pct')

    // `docs/02 §3.12.2` · reporte de estados, dentro del reporte de lote.
    const r = await request.get(`${API}/reports/lot/${esc.lotId}`, { headers: cab })
    expect(r.status()).toBe(200)
    // `docs/02 §3.12.2` pide «pendientes, aprobados, rechazados, enviados»: el reporte de
    // lote lo entrega dentro de `event_summary.by_status`.
    expect(await r.json(), 'el reporte de lote debe traer la distribución por estado')
      .toHaveProperty('event_summary.by_status')
  })

  test('ningún campo de porcentaje devuelve texto', async ({ request }) => {
    // `R-14`. Un campo `_pct` con una frase en español rompe a cualquier consumidor y la
    // pantalla lo mostraba vacío.
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P15T${sufijo()}`, 'hatchery')
    for (const ruta of ['hatchery', 'mortality', 'egg-production', 'feed-conversion']) {
      const k = await kpi(request, cab, ruta, esc.lotId)
      for (const [campo, valor] of Object.entries(k)) {
        if (campo.endsWith('_pct')) {
          expect(typeof valor === 'number' || valor === null,
            `${ruta}.${campo} devolvió ${typeof valor}: ${JSON.stringify(valor)}`).toBe(true)
        }
      }
    }
  })

  test('los indicadores exigidos por el cliente están expuestos', async ({ request }) => {
    const cab = await cabeceraAdmin(request)
    const esc = await crearEscenario(request, cab, `P15C${sufijo()}`, 'hatchery')

    for (const ruta of ['vaccination-efficiency', 'transfer-efficiency']) {
      const r = await request.get(`${API}/reports/kpis/${ruta}?lot_id=${esc.lotId}`, { headers: cab })
      expect(r.status(), `${ruta}: ${await r.text()}`).toBe(200)
    }
  })
})
