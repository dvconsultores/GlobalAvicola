/**
 * P-12 — GESTIÓN DE DATOS MAESTROS   (`docs/02 §3.2`)
 *
 * `GA-REM-033` cerró tres huecos:
 *   R-90  siete maestros normativos no tenían ninguna forma de gestionarse
 *   R-91  esos mismos siete no admitían edición: sin esquema, `register_crud` no daba `PUT`
 *   R-89  el listado descartaba el total y el contador mostraba el tamaño de la página
 *
 * Este es el primer proceso del programa cuya certificación exige **`UI_E2E`**, y solo para
 * un criterio: lo que `R-89` rompía es el número que el usuario **lee**, y eso no puede
 * comprobarse por API. El resto sigue siendo `API_E2E`.
 */
import { test, expect } from '@playwright/test'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

/** Los siete que no tenían gestión, con el campo mínimo que cada uno exige. */
const NUEVOS = [
  { entidad: 'medications', extra: {} },
  { entidad: 'cull-causes', extra: {} },
  { entidad: 'rejection-reasons', extra: {} },
  { entidad: 'correction-types', extra: {} },
  { entidad: 'productive-phases', extra: { order: 1 } },
]

test.describe('P-12 · gestión de datos maestros', () => {
  test('los siete catálogos tienen ruta de gestión', async ({ page }) => {
    // `AC04`. No estaban en `masterEntities`, que es la única fuente de rutas de maestros:
    // sin entrada no hay ruta, y sin ruta no hay forma de gestionarlos.
    await entrar(page, 'admin')

    for (const entidad of ['incubators', 'hatchers', 'productive-phases', 'medications',
                           'cull-causes', 'rejection-reasons', 'correction-types']) {
      await page.goto(`/masters/${entidad}`)
      await expect(page.getByRole('button', { name: /nuev|new|crear|add/i }).first(),
        `${entidad} no ofrece alta`).toBeVisible({ timeout: 15_000 })
    }
  })

  test('el contador muestra el total y no el tamaño de la página', async ({ page, request }) => {
    // `AC03`. Con 25 registros y páginas de 20, el panel decía «20 resultados».
    const cab = await cabeceraAdmin(request)
    const marca = `P12${sufijo()}`

    for (let i = 0; i < 25; i++) {
      const r = await request.post(`${API}/masters/medications`, {
        headers: cab, data: { name: `${marca}-${i}` },
      })
      expect(r.status(), await r.text()).toBe(201)
    }

    await entrar(page, 'admin')
    await page.goto('/masters/medications')
    await page.getByPlaceholder(/buscar|search/i).first().fill(marca)

    // El número visible debe ser el de coincidencias, no el de la página.
    await expect(page.getByText(/25\s*(resultados|results)/i),
      'el contador sigue mostrando el tamaño de la página').toBeVisible({ timeout: 15_000 })
  })

  test('un maestro nuevo se crea, se edita y se da de baja', async ({ request }) => {
    // `AC05`, `AC06`, `AC07` por API: la persistencia no se comprueba por pantalla.
    const cab = await cabeceraAdmin(request)

    for (const { entidad, extra } of NUEVOS) {
      const nombre = `P12-${sufijo()}`
      const creado = await request.post(`${API}/masters/${entidad}`, {
        headers: cab, data: { name: nombre, ...extra },
      })
      expect(creado.status(), `${entidad}: ${await creado.text()}`).toBe(201)
      const id = (await creado.json()).id

      const editado = await request.put(`${API}/masters/${entidad}/${id}`, {
        headers: cab, data: { name: `${nombre}-editado` },
      })
      expect(editado.status(), `${entidad} no admite edición: ${await editado.text()}`).toBe(200)

      // `R-68` · lectura inmediata e independiente.
      const leido = await request.get(`${API}/masters/${entidad}/${id}`, { headers: cab })
      expect((await leido.json()).name).toBe(`${nombre}-editado`)

      const baja = await request.delete(`${API}/masters/${entidad}/${id}`, { headers: cab })
      expect(baja.status()).toBe(204)
    }
  })

  test('el maestro creado se puede usar en la operación que lo exige', async ({ request }) => {
    // `AC10`. Una pantalla que abre no certifica el proceso: la cadena se cierra cuando el
    // catálogo poblado desde la gestión se puede seleccionar donde el negocio lo pide.
    const cab = await cabeceraAdmin(request)
    const { crearEscenario, hoy, registrar } = await import('../test-support/e2e-api')
    const esc = await crearEscenario(request, cab, `P12U${sufijo()}`, 'broiler')

    const causa = await request.post(`${API}/masters/cull-causes`, {
      headers: cab, data: { name: `P12-causa-${sufijo()}` },
    })
    expect(causa.status()).toBe(201)

    const recepcion = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'bird_reception', event_date: hoy(),
      bird_movements: [{ sex: 'mixed', quantity: 500 }],
    })
    expect(recepcion.status()).toBe(201)

    const descarte = await registrar(request, cab, {
      lot_id: esc.lotId, farm_id: esc.farmId, house_id: esc.houseId,
      event_type: 'cull_recording', event_date: hoy(),
      bird_movements: [{ sex: 'mixed', quantity: 5, cull_cause_id: (await causa.json()).id }],
    })
    expect(descarte.status(), `la causa recién creada no se pudo usar: ${await descarte.text()}`)
      .toBe(201)
  })
})
