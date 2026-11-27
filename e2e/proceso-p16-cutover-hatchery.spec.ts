/**
 * P-16-INC — INCUBADORA — CARGAS INICIALES v4 (SPEC 006 · remediación post-certificación de GA-REQ-061,
 * contrato actualizado por SPEC 018).
 *
 * Certificación por BU **sin transitividad**: este spec recorre por la interfaz el ciclo completo
 * (crear carga → plantilla de la unidad → subir XLSX → validar → preview → enviar → aprobar con
 * otro actor → aplicar → reconciliación → lote migrado → primer evento post-corte → CUT-GL-02).
 * El journal queda en `test-results/spec-006/e2e-hatchery-xlsx.json`.
 *
 * SPEC 018 (§1.2/D-4): la incubadora deja `eggs_discarded` y captura el desglose de no incubables.
 * Aquí la fila canónica se ajusta a ceros **conocidos** para que el saldo «recibidos − cargados −
 * no incubables» conserve los 1 000 huevos que carga el primer evento post-corte; el desglose
 * 500/300/200 con fosa 25 —y el `eggs_in_process` V4 (fosa PRE-CARGA, SPEC 018 §9 · D-23) que
 * arrastra— se certifica aparte en `proceso-spec018-cutover-hatchery-v4.spec.ts` y en
 * `proceso-spec018d-hatchery-v4-fosa-od02.spec.ts`.
 */
import { expect, test } from '@playwright/test'
import { API, cabeceraAdmin } from '../test-support/e2e-api'
import { leerPlantilla } from '../test-support/cutover'
import { flujoPorBu } from '../test-support/cutover-flow'

const COLUMNAS_V4 = [
  'legacy_lot_code', 'existing_lot_code', 'hatchery_code', 'incubator_name', 'hatcher_name', 'source_lot_code',
  'generation', 'egg_origin', 'reception_date', 'set_date', 'expected_hatch_date', 'eggs_received', 'eggs_set',
  'eggs_non_incubable_oversized', 'eggs_non_incubable_dirty', 'eggs_non_incubable_broken', 'eggs_transferred',
  'fertile_eggs_to_pit', 'chicks_hatched', 'chicks_available', 'source_system', 'source_reference', 'notes',
]

test.describe('P-16 · Cargas Iniciales v4 — incubadora', () => {
  test('hatchery: ciclo completo por UI con plantilla XLSX v4 y primer evento post-corte', async ({ page, browser, request }) => {
    test.setTimeout(240_000)
    const { batch } = await flujoPorBu(page, browser, request, {
      bu: 'hatchery',
      formato: 'xlsx',
      ajustarFilas: filas => filas.map(fila => ({
        ...fila,
        // Ceros conocidos: el saldo BR-03 de la apertura queda en 1 000 = lo que carga el evento post-corte.
        eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
        // Fosa en cero conocido: la fosa es PRE-CARGA y saldría del saldo por cargar (SPEC 018 §9).
        fertile_eggs_to_pit: 0,
      })),
    })

    // ── 12 · SPEC 018: la plantilla de la carga es la v4 (Meta + nombre de descarga del servidor) ──
    const cab = await cabeceraAdmin(request)
    const plantilla = await request.get(`${API}/cutover-templates/hatchery?format=xlsx&batch_id=${batch.id}`, { headers: cab })
    expect(plantilla.status(), await plantilla.text()).toBe(200)
    expect(String(plantilla.headers()['content-disposition'] ?? '')).toContain('cutover_template_hatchery_v4.xlsx')
    const libro = leerPlantilla(await plantilla.body())
    expect(libro.meta.template_version, 'la incubadora vigente es v4').toBe('v4')
    expect(libro.meta.schema_id).toBe('CUTOVER_HATCHERY_V4')
    expect(libro.cabecera).toEqual(COLUMNAS_V4)
    expect(libro.cabecera).not.toContain('eggs_discarded')
    const detalle = await (await request.get(`${API}/cutover-batches/${batch.id}`, { headers: cab })).json()
    expect(detalle.template_version).toBe('v4')
    expect(detalle.status).toBe('applied')
  })
})
